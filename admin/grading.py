import streamlit as st
import pandas as pd
import json
import base64
import io
from datetime import datetime
from database.supabase_models import get_database
from auth.login import get_current_user
from admin.ai_grader import grade_essay_with_ai
from core.grading_logic import calculate_auto_score, run_essay_auto_grading
import plotly.express as px
import plotly.graph_objects as go
from .pdf_report import generate_pdf_report

# --- Safe Imports ---
# Đảm bảo các hàm này tồn tại trong các module tương ứng
try:
    from admin.ai_grader import grade_essay_with_ai
except ImportError:
    def grade_essay_with_ai(*args, **kwargs):
        st.error("Lỗi: Không thể tải mô-đun AI Grader.")
        return {'suggested_score': 0.0, 'feedback': 'Lỗi AI Grader'}

try:
    from admin.word_parser import render_mathjax
except ImportError:
    def render_mathjax():
        st.warning("Lỗi: Không thể tải hàm render_mathjax.")

# --- Helper Function ---
def format_datetime(datetime_str):
    """Format datetime string một cách an toàn."""
    try:
        if isinstance(datetime_str, str):
            # Chuyển đổi từ ISO format có múi giờ UTC (Z)
            dt_utc = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            # Bạn có thể chuyển về múi giờ địa phương nếu muốn
            # from pytz import timezone
            # local_tz = timezone("Asia/Ho_Chi_Minh")
            # dt_local = dt_utc.astimezone(local_tz)
            return dt_utc.strftime('%d/%m/%Y %H:%M')
        return "N/A"
    except (ValueError, TypeError):
        return str(datetime_str) or "N/A"

# --- Main Page Function ---
def show_grading():
    """Giao diện chấm bài chính với bộ lọc được tích hợp vào trang chính."""
    st.header("✅ Chấm bài và Quản lý kết quả")
    
    db = get_database()
    
    # --- PHẦN 1: LẤY DỮ LIỆU ĐỀ THI ---
    try:
        all_exams_raw = db.get_all_exams()
        if not all_exams_raw:
            st.info("📝 Hiện tại không có đề thi nào trong hệ thống.")
            if st.button("➕ Tạo đề thi mới"):
                st.session_state.current_page = "create_exam"
                st.rerun()
            return
        
        all_exams_raw.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    except Exception as e:
        st.error(f"❌ Lỗi khi tải danh sách đề thi: {e}")
        return

    # --- PHẦN 2: HIỂN THỊ BỘ LỌC TRÊN GIAO DIỆN CHÍNH ---
    st.subheader("🔍 Lựa chọn đề thi và bộ lọc")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            # Tạo danh sách lựa chọn cho selectbox
            exam_options = {
                f"{exam['title']} ({exam.get('class_name', 'N/A')})": exam['id']
                for exam in all_exams_raw
            }
            selected_exam_title = st.selectbox(
                label="Chọn đề thi để chấm:",
                options=exam_options.keys(),
                key="selected_exam_title_grading",
                index=None,
                placeholder="Tìm và chọn một đề thi..."
            )
            selected_exam_id = exam_options.get(selected_exam_title)

        with col2:
            st.selectbox(
                "Lọc theo trạng thái:",
                ["Tất cả", "Chưa chấm", "Đã chấm"],
                key="filter_grading_status"
            )

        with col3:
            st.selectbox(
                "Sắp xếp theo:",
                ["Thời gian nộp", "Tên học sinh", "Điểm"],
                key="sort_grading_by"
            )

    st.markdown("---")

    # --- PHẦN 3: HIỂN THỊ NỘI DUNG DỰA TRÊN LỰA CHỌN ---
    if not selected_exam_id:
        st.info("☝️ Vui lòng chọn một đề thi từ ô bên trên để bắt đầu.")
        # (Phần gợi ý các đề thi cần chấm vẫn có thể giữ lại nếu muốn)
        return

    # Nếu đã chọn một đề thi, tiếp tục hiển thị các phần còn lại
    try:
        selected_exam_details = db.get_exam_by_id(selected_exam_id)
        if not selected_exam_details:
            st.error("Không thể tải chi tiết đề thi. Vui lòng thử lại.")
            return

        # Hiển thị tổng quan và các tab
        show_exam_grading_overview(selected_exam_details, db)
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Danh sách bài làm", 
            "✏️ Chấm chi tiết", 
            "📊 Thống kê", 
            "📤 Xuất kết quả"
        ])
        
        with tab1: show_submissions_list(selected_exam_id, db)
        with tab2: show_detailed_grading(selected_exam_id, db)
        with tab3: show_grading_statistics(selected_exam_id, db)
        with tab4: show_export_results(selected_exam_id, db)

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi hiển thị trang chấm bài: {e}")
        st.exception(e)

def show_exam_grading_overview(exam, db):
    """Hiển thị tổng quan về đề thi cần chấm."""
    submissions = db.get_submissions_by_exam(exam['id'])
    total_submissions = len(submissions)
    graded_count = len([s for s in submissions if s.get('is_graded')])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Đã nộp", total_submissions)
    col2.metric("✅ Đã chấm", graded_count)
    col3.metric("⏳ Chờ chấm", total_submissions - graded_count)
    progress = (graded_count / total_submissions * 100) if total_submissions > 0 else 0
    col4.metric("📈 Tiến độ", f"{progress:.1f}%")
    if total_submissions > 0: st.progress(progress / 100)

def show_submissions_list(exam_id, db):
    """Hiển thị danh sách bài làm của học sinh."""
    st.subheader("📋 Danh sách bài làm")
    filter_status = st.session_state.get("filter_grading_status", "Tất cả")
    sort_by = st.session_state.get("sort_grading_by", "Thời gian nộp")

    try:
        submissions_raw = db.get_submissions_by_exam(exam_id)
        exam_info = db.get_exam_by_id(exam_id)
        max_score_exam = exam_info.get('total_points', 10) if exam_info else 10
        
        submissions = [
            {
                'id': s['id'], 'student_id': s.get('student_info', {}).get('id', ''),
                'student_name': s.get('student_info', {}).get('ho_ten', 'N/A'),
                'student_username': s.get('student_info', {}).get('username', 'N/A'),
                'status': 'graded' if s.get('is_graded') else 'pending',
                'submitted_at': s.get('submitted_at', ''), 'time_taken': s.get('time_taken', 0),
                'score': s.get('score'), 'max_score': s.get('max_score', max_score_exam),
                'answers': s.get('answers', [])
            } for s in submissions_raw
        ]
    except Exception as e:
        st.error(f"❌ Lỗi lấy danh sách bài nộp: {e}"); return

    if filter_status == "Chưa chấm": submissions = [s for s in submissions if s['status'] == 'pending']
    elif filter_status == "Đã chấm": submissions = [s for s in submissions if s['status'] == 'graded']

    sort_key_map = {"Thời gian nộp": "submitted_at", "Tên học sinh": "student_name", "Điểm": "score"}
    reverse_sort = sort_by in ["Thời gian nộp", "Điểm"]
    submissions.sort(key=lambda x: x.get(sort_key_map[sort_by]) or ('' if isinstance(x.get(sort_key_map[sort_by]), str) else 0), reverse=reverse_sort)

    if not submissions: st.info("📝 Không có bài làm nào phù hợp."); return

    for sub in submissions:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([4, 3, 2, 2])
            c1.write(f"{'✅' if sub['status'] == 'graded' else '⏳'} **{sub['student_name']}** (`@{sub['student_username']}`)")
            c2.caption(f"Nộp lúc: {format_datetime(sub['submitted_at'])}")
            if sub.get('score') is not None: c3.metric("Điểm", f"{sub['score']:.2f}", f"/{sub['max_score']}")
            else: c3.metric("Điểm", "--")
            if c4.button("Chấm bài" if sub['status'] == 'pending' else "Xem lại", key=f"grade_{sub['id']}", use_container_width=True):
                st.session_state.selected_submission_to_grade = sub
                st.rerun()

def show_detailed_grading(exam_id, db):
    """Giao diện chấm bài chi tiết, đã sửa lỗi st.button trong st.form."""
    st.subheader("✏️ Chấm bài chi tiết")
    render_mathjax()

    if "selected_submission_to_grade" not in st.session_state:
        st.info("👆 Vui lòng chọn một bài làm từ tab 'Danh sách bài làm' để bắt đầu.")
        return

    submission = st.session_state.selected_submission_to_grade
    exam = db.get_exam_by_id(exam_id)
    if not exam or not submission:
        st.error("Lỗi tải dữ liệu đề thi hoặc bài nộp.")
        return

    st.markdown(f"#### 👤 Bài làm của: **{submission['student_name']}**")
    
    # --- Vòng lặp để hiển thị câu hỏi VÀ nút AI (nằm ngoài form) ---
    for i, question in enumerate(exam.get('questions', [])):
        q_id = question.get('question_id', i + 1)
        student_answer = next((ans for ans in submission['answers'] if ans.get('question_id') == q_id), None)
        
        with st.container(border=True):
            st.markdown(f"**Câu {i+1}:** {question['question']} *({question['points']} điểm)*")
            
            # Chỉ hiển thị nút chấm AI cho câu tự luận
            if question.get('type') == 'essay':
                # Hiển thị bài làm tự luận
                if student_answer:
                    if student_answer.get('answer_text'): 
                        st.text_area("Bài làm (văn bản):", student_answer['answer_text'], disabled=True, key=f"essay_text_view_{q_id}")
                    if student_answer.get('image_data'): 
                        try: 
                            st.image(base64.b64decode(student_answer['image_data']), caption="Bài làm (hình ảnh)")
                        except Exception as e: 
                            st.error(f"Lỗi hiển thị hình ảnh bài làm: {e}")
                else: 
                    st.warning("Học sinh không làm câu này.")

                # <<< NÚT AI ĐÃ ĐƯỢC ĐƯA RA NGOÀI FORM >>>
                if st.button(f"🤖 Chấm câu {i+1} bằng AI", key=f"ai_button_{q_id}", use_container_width=True):
                    rubric = question.get('grading_criteria', '')
                    if not rubric:
                        st.warning("Câu hỏi này thiếu tiêu chí chấm điểm (rubric) cho AI.")
                    else:
                        with st.spinner("AI đang phân tích..."):
                            ai_result = grade_essay_with_ai(
                                question_text=question.get('question', ''),
                                grading_rubric=rubric, max_score=float(question['points']),
                                student_answer_text=student_answer.get('answer_text', '') if student_answer else '',
                                student_image_base64=student_answer.get('image_data', None) if student_answer else None
                            )
                        # Lưu kết quả vào session state và rerun để form cập nhật
                        st.session_state[f"score_{q_id}"] = ai_result['suggested_score']
                        st.session_state[f"comment_{q_id}"] = ai_result['feedback']
                        st.rerun()

    # --- Form để nhập điểm và lưu ---
    with st.form(key="grading_form"):
        st.markdown("---")
        st.subheader("📝 Bảng điểm chi tiết")
        
        question_scores_map = {}
        total_score = 0
        
        for i, question in enumerate(exam.get('questions', [])):
            q_id = question.get('question_id', i + 1)
            
            st.markdown(f"**Điểm cho câu {i+1}:**")
            
            # Lấy giá trị từ session_state (do AI hoặc người dùng nhập trước đó)
            default_score = st.session_state.get(f"score_{q_id}", 0.0)
            
            # Đối với câu trắc nghiệm, tính điểm tự động nếu chưa có điểm
            if question.get('type') in ['multiple_choice', 'true_false', 'short_answer'] and default_score == 0.0:
                 student_answer = next((ans for ans in submission['answers'] if ans.get('question_id') == q_id), None)
                 default_score = calculate_auto_score(question, student_answer)

            score = st.number_input(
                f"Điểm câu {i+1}", 
                min_value=0.0, max_value=float(question['points']), 
                value=default_score, 
                step=0.25, 
                key=f"score_input_{q_id}", # Dùng key khác để tránh xung đột
                label_visibility="collapsed"
            )
            
            if question.get('type') == 'essay':
                st.text_area(
                    f"Nhận xét câu {i+1}", 
                    value=st.session_state.get(f"comment_{q_id}", ""), 
                    key=f"comment_input_{q_id}"
                )
            
            question_scores_map[str(q_id)] = score
            total_score += score

        st.divider()
        st.subheader("Tổng kết")
        final_score = st.number_input("Điểm tổng kết cuối cùng", value=total_score, min_value=0.0, max_value=float(exam.get('total_points', 100)))
        general_feedback = st.text_area("Nhận xét chung cho bài làm", key="general_feedback")
        
        submitted = st.form_submit_button("💾 Lưu điểm và Hoàn thành chấm", type="primary", use_container_width=True)
        if submitted:
            success = db.update_submission_grade(
                submission_id=submission['id'], 
                total_score=final_score, 
                question_scores=question_scores_map, 
                feedback=general_feedback
            )
            if success:
                st.success("✅ Đã lưu điểm thành công!")
                # Xóa state để quay lại danh sách
                if 'selected_submission_to_grade' in st.session_state:
                    del st.session_state.selected_submission_to_grade
                st.rerun()
            else:
                st.error("❌ Lỗi khi lưu điểm vào cơ sở dữ liệu.")



def show_grading_statistics(exam_id, db):
    """Hiển thị thống kê chi tiết cho đề thi đã được chấm."""
    st.subheader("📊 Thống kê và Phân tích kết quả")

    try:
        submissions = db.get_submissions_by_exam(exam_id)
        exam = db.get_exam_by_id(exam_id)
        
        if not exam or not submissions:
            st.info("📝 Chưa có đủ dữ liệu để tạo thống kê.")
            return

        graded_submissions = [s for s in submissions if s.get('is_graded')]
        if not graded_submissions:
            st.info("📊 Cần có ít nhất một bài đã chấm để xem thống kê.")
            return

    except Exception as e:
        st.error(f"Lỗi tải dữ liệu thống kê: {e}"); return

    # --- THỐNG KÊ TỔNG QUAN ---
    scores = [s.get('score', 0) for s in graded_submissions if s.get('score') is not None]
    max_score = exam.get('total_points', 10)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Số bài đã chấm", len(graded_submissions))
    col2.metric("Điểm trung bình", f"{pd.Series(scores).mean():.2f}")
    col3.metric("Điểm cao nhất", f"{pd.Series(scores).max():.2f}")
    col4.metric("Điểm thấp nhất", f"{pd.Series(scores).min():.2f}")

    st.divider()

    # --- BIỂU ĐỒ PHÂN BỐ ĐIỂM ---
    st.write("#### Phân bố điểm số")
    fig_hist = px.histogram(
        x=scores,
        nbins=10,
        labels={'x': 'Khoảng điểm', 'y': 'Số lượng học sinh'},
        title=f"Phổ điểm của {len(scores)} bài làm"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # --- PHÂN TÍCH ĐỘ KHÓ TỪNG CÂU ---
    st.write("#### Phân tích độ khó từng câu")
    st.caption("Dựa trên tỷ lệ trả lời đúng của học sinh.")

    exam_questions = exam.get('questions', [])
    question_analysis = []
    
    for i, q in enumerate(exam_questions):
        q_id_str = str(q.get('question_id', i + 1))
        q_points = q.get('points', 1)
        correct_count = 0
        total_attempts = 0
        
        for sub in graded_submissions:
            q_scores = sub.get('question_scores', {})
            if q_id_str in q_scores:
                total_attempts += 1
                # Coi là đúng nếu học sinh đạt điểm tối đa cho câu đó
                if q_scores[q_id_str] >= q_points:
                    correct_count += 1
        
        correct_rate = (correct_count / total_attempts * 100) if total_attempts > 0 else 0
        question_analysis.append({
            'Câu': f"Câu {i+1}",
            'Tỷ lệ đúng (%)': correct_rate,
            'Độ khó': 'Dễ' if correct_rate > 70 else 'Trung bình' if correct_rate > 40 else 'Khó'
        })

    if question_analysis:
        df_analysis = pd.DataFrame(question_analysis)
        fig_bar = px.bar(
            df_analysis,
            x='Câu',
            y='Tỷ lệ đúng (%)',
            color='Độ khó',
            title="Tỷ lệ trả lời đúng theo từng câu",
            color_discrete_map={'Dễ': 'green', 'Trung bình': 'orange', 'Khó': 'red'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def show_export_results(exam_id, db):
    """Xuất kết quả chấm bài ra PDF với luồng xử lý đáng tin cậy."""
    st.subheader("📤 Xuất báo cáo kết quả")
    st.write("Xuất báo cáo chi tiết kết quả bài làm của từng học sinh ra file PDF.")

    try:
        submissions = db.get_submissions_by_exam(exam_id)
        exam = db.get_exam_by_id(exam_id)
        graded_submissions = [s for s in submissions if s.get('is_graded')]

        if not graded_submissions:
            st.info("📝 Chưa có bài nào được chấm để xuất kết quả."); return
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}"); return
    
    student_data = [{
        'ID': sub['id'],
        'Họ và tên': sub.get('student_info', {}).get('ho_ten', 'N/A'),
    } for sub in graded_submissions]
    
    df_students = pd.DataFrame(student_data)
    
    selected_id = st.selectbox(
        "Chọn một học sinh để xuất báo cáo:",
        options=df_students['ID'],
        format_func=lambda x: df_students[df_students['ID'] == x]['Họ và tên'].iloc[0],
        index=None,
        placeholder="Chọn học sinh...",
        key="pdf_student_select"
    )

    if selected_id:
        submission_to_export = next((s for s in graded_submissions if s['id'] == selected_id), None)
        
        if submission_to_export:
            # Nút để bắt đầu quá trình tạo PDF
            if st.button("📄 Tạo báo cáo PDF", use_container_width=True, type="primary"):
                with st.spinner("Đang tạo file PDF, vui lòng chờ..."):
                    pdf_data = generate_pdf_report(exam, submission_to_export)
                
                # Lưu kết quả vào session_state
                if pdf_data:
                    st.session_state.pdf_data_ready = pdf_data
                    st.session_state.pdf_filename = f"KetQua_{submission_to_export.get('student_info', {}).get('ho_ten', 'student')}_{exam_id[:8]}.pdf"
                else:
                    # Lỗi đã được lưu trong session_state bởi generate_pdf_report
                    if 'pdf_data_ready' in st.session_state:
                        del st.session_state.pdf_data_ready # Xóa dữ liệu cũ nếu có lỗi
                st.rerun() # Chạy lại để hiển thị nút download hoặc lỗi

    # --- Hiển thị nút download hoặc thông báo lỗi ---
    # Khối code này sẽ chạy sau khi rerun ở trên
    if 'pdf_error' in st.session_state:
        st.error(st.session_state.pdf_error)
        # Xóa lỗi sau khi hiển thị để không hiện lại ở lần sau
        del st.session_state.pdf_error

    if 'pdf_data_ready' in st.session_state and st.session_state.pdf_data_ready:
        st.success("🎉 Đã tạo báo cáo PDF thành công!")
        st.download_button(
            label="📥 Tải file PDF về máy",
            data=st.session_state.pdf_data_ready,
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            use_container_width=True
        )
        # Tùy chọn: Xóa dữ liệu sau khi hiển thị nút download
        # del st.session_state.pdf_data_ready
        # del st.session_state.pdf_filename