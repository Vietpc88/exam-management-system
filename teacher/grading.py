import streamlit as st
import pandas as pd
import json
import base64
from datetime import datetime, timedelta

# Safe imports
try:
    from database.models import *
    from auth.login import get_current_user
    from teacher.word_parser import render_mathjax
except ImportError:
    # Fallback if modules don't exist
    def get_current_user():
        return {'id': 'mock_teacher_id', 'ho_ten': 'Mock Teacher', 'username': 'teacher', 'role': 'teacher'}
    
    def render_mathjax():
        st.markdown("""
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
        window.MathJax = {
            tex: {inlineMath: [['], ['\\(', '\\)']]},
            svg: {fontCache: 'global'}
        };
        </script>
        """, unsafe_allow_html=True)

def show_grading():
    """Giao diện chấm bài chính"""
    st.header("✅ Chấm bài")
    
    user = get_current_user()
    db = get_database()
    
    # Lấy danh sách đề thi từ database thật
    try:
        exams_data = db.get_exams_by_teacher(user['id'])
        
        # Convert to format expected by UI
        exams = []
        for exam_data in exams_data:
            exams.append({
                'id': exam_data['id'],
                'title': exam_data['title'],
                'class_name': exam_data.get('class_name', 'Unknown'),
                'created_at': exam_data.get('created_at', ''),
                'time_limit': exam_data.get('time_limit', 60),
                'start_time': exam_data.get('start_time'),
                'end_time': exam_data.get('end_time'),
                'total_points': exam_data.get('total_points', 0),
                'total_questions': exam_data.get('total_questions', 0)
            })
            
    except Exception as e:
        st.error(f"❌ Lỗi lấy danh sách đề thi: {str(e)}")
        exams = []
    
    if not exams:
        st.info("📝 Bạn chưa có đề thi nào cần chấm!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Tạo đề thi mới", use_container_width=True):
                st.session_state.current_page = "create_exam"
                st.rerun()
        with col2:
            if st.button("📊 Xem thống kê", use_container_width=True):
                st.session_state.current_page = "statistics"
                st.rerun()
        return
    
    # Sidebar để chọn đề thi
    with st.sidebar:
        st.write("### 📝 Chọn đề thi để chấm")
        
        selected_exam_id = st.selectbox(
            "Đề thi:",
            options=[exam['id'] for exam in exams],
            format_func=lambda x: next(
                f"{exam['title']} ({exam['class_name']})" 
                for exam in exams if exam['id'] == x
            ),
            key="selected_exam_grading"
        )
        
        # Lọc theo trạng thái
        filter_status = st.selectbox(
            "Lọc theo trạng thái:",
            ["Tất cả", "Chưa chấm", "Đã chấm", "Chấm một phần"],
            key="filter_grading_status"
        )
        
        # Sắp xếp
        sort_by = st.selectbox(
            "Sắp xếp theo:",
            ["Thời gian nộp", "Tên học sinh", "Điểm", "Trạng thái"],
            key="sort_grading_by"
        )
    
    # Hiển thị thông tin đề thi được chọn
    selected_exam = next(exam for exam in exams if exam['id'] == selected_exam_id)
    show_exam_grading_overview(selected_exam, db)
    
    # Tabs chấm bài
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Danh sách bài làm", 
        "✏️ Chấm chi tiết", 
        "📊 Thống kê", 
        "📤 Xuất kết quả"
    ])
    
    with tab1:
        show_submissions_list(selected_exam_id, filter_status, sort_by, db)
    
    with tab2:
        show_detailed_grading(selected_exam_id, db)
    
    with tab3:
        show_grading_statistics(selected_exam_id, db)
    
    with tab4:
        show_export_results(selected_exam_id, db)

def show_exam_grading_overview(exam, db):
    """Hiển thị tổng quan về đề thi cần chấm"""
    # Thống kê nhanh từ database thật
    try:
        submissions = db.get_submissions_by_exam(exam['id'])
        total_submissions = len(submissions)
        graded_count = len([s for s in submissions if s.get('is_graded', False)])
        pending_count = total_submissions - graded_count
    except Exception as e:
        st.warning(f"⚠️ Lỗi lấy thống kê bài nộp: {str(e)}")
        total_submissions = 0
        graded_count = 0
        pending_count = 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📝 Đề thi", exam['title'][:20] + "...")
    
    with col2:
        st.metric("👥 Đã nộp", total_submissions)
    
    with col3:
        st.metric("✅ Đã chấm", graded_count)
    
    with col4:
        st.metric("⏳ Chờ chấm", pending_count)
    
    with col5:
        progress = (graded_count / total_submissions * 100) if total_submissions > 0 else 0
        st.metric("📈 Tiến độ", f"{progress:.1f}%")
    
    # Progress bar
    if total_submissions > 0:
        st.progress(graded_count / total_submissions)
    
    # Thông tin đề thi
    with st.expander("ℹ️ Thông tin đề thi", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**📚 Lớp:** {exam['class_name']}")
            st.write(f"**⏱️ Thời gian:** {exam['time_limit']} phút")
            st.write(f"**📊 Tổng điểm:** {exam['total_points']} điểm")
        
        with col2:
            if exam.get('start_time'):
                st.write(f"**📅 Bắt đầu:** {exam['start_time'][:16]}")
            if exam.get('end_time'):
                st.write(f"**📅 Kết thúc:** {exam['end_time'][:16]}")
            st.write(f"**❓ Số câu hỏi:** {exam['total_questions']} câu")

def show_submissions_list(exam_id, filter_status, sort_by):
    """Hiển thị danh sách bài làm của học sinh"""
    st.subheader("📋 Danh sách bài làm")
    
    submissions = get_exam_submissions(exam_id)
    
    # Lọc theo trạng thái
    if filter_status != "Tất cả":
        status_map = {
            "Chưa chấm": "pending",
            "Đã chấm": "graded", 
            "Chấm một phần": "partial"
        }
        submissions = [s for s in submissions if s['status'] == status_map[filter_status]]
    
    # Sắp xếp
    if sort_by == "Thời gian nộp":
        submissions.sort(key=lambda x: x['submitted_at'], reverse=True)
    elif sort_by == "Tên học sinh":
        submissions.sort(key=lambda x: x['student_name'])
    elif sort_by == "Điểm":
        submissions.sort(key=lambda x: x['total_score'] or 0, reverse=True)
    elif sort_by == "Trạng thái":
        submissions.sort(key=lambda x: x['status'])
    
    if not submissions:
        st.info("📝 Không có bài làm nào phù hợp với bộ lọc!")
        return
    
    # Hiển thị danh sách
    for submission in submissions:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                # Tên học sinh và thông tin
                status_icon = {
                    "pending": "⏳",
                    "graded": "✅", 
                    "partial": "🔶"
                }.get(submission['status'], "❓")
                
                st.write(f"{status_icon} **{submission['student_name']}**")
                st.caption(f"ID: {submission['student_id']} | {submission['student_username']}")
            
            with col2:
                # Thời gian nộp
                submitted_time = datetime.fromisoformat(submission['submitted_at'])
                st.write(f"📅 {submitted_time.strftime('%d/%m %H:%M')}")
                
                # Thời gian làm bài
                if submission['start_time'] and submission['submitted_at']:
                    start_time = datetime.fromisoformat(submission['start_time'])
                    duration = submitted_time - start_time
                    st.caption(f"⏱️ {duration.seconds // 60} phút")
            
            with col3:
                # Điểm số
                if submission['status'] == 'graded':
                    score_percent = (submission['total_score'] / submission['max_score']) * 100
                    color = "green" if score_percent >= 80 else "orange" if score_percent >= 50 else "red"
                    st.markdown(f"<span style='color: {color}'><b>{submission['total_score']:.1f}/{submission['max_score']}</b></span>", 
                              unsafe_allow_html=True)
                    st.caption(f"{score_percent:.1f}%")
                else:
                    st.write("--/--")
                    st.caption("Chưa chấm")
            
            with col4:
                # Trạng thái chi tiết
                status_text = {
                    "pending": "Chờ chấm",
                    "graded": "Đã chấm",
                    "partial": "Chấm 1 phần"
                }.get(submission['status'], "Không xác định")
                
                if submission['status'] == 'partial':
                    graded_questions = len([q for q in submission['answers'] if q.get('score') is not None])
                    total_questions = len(submission['answers'])
                    st.write(f"{graded_questions}/{total_questions}")
                
                st.caption(status_text)
            
            with col5:
                # Actions
                if st.button("✏️ Chấm", key=f"grade_{submission['id']}", help="Chấm bài"):
                    st.session_state.grading_submission = submission
                    st.session_state.show_grading_detail = True
                    st.rerun()
                
                if submission['status'] == 'graded':
                    if st.button("👁️ Xem", key=f"view_{submission['id']}", help="Xem kết quả"):
                        st.session_state.viewing_submission = submission
                        st.session_state.show_view_result = True
                        st.rerun()
            
            st.divider()
    
    # Bulk actions
    if submissions:
        st.write("### 🔧 Thao tác hàng loạt")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤖 Chấm tự động trắc nghiệm", use_container_width=True):
                auto_grade_multiple_choice(exam_id)
        
        with col2:
            if st.button("📊 Xuất báo cáo Excel", use_container_width=True):
                export_grading_report(exam_id)
        
        with col3:
            if st.button("📧 Gửi kết quả qua email", use_container_width=True):
                send_results_email(exam_id)

def show_detailed_grading(exam_id):
    """Giao diện chấm bài chi tiết"""
    st.subheader("✏️ Chấm bài chi tiết")
    
    # Kiểm tra có bài cần chấm được chọn không
    if not st.session_state.get("show_grading_detail"):
        st.info("👆 Chọn một bài làm từ danh sách ở tab 'Danh sách bài làm' để bắt đầu chấm!")
        return
    
    submission = st.session_state.get("grading_submission")
    if not submission:
        st.error("❌ Không tìm thấy bài làm để chấm!")
        return
    
    # Load MathJax cho hiển thị công thức
    render_mathjax()
    
    # Header thông tin học sinh
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3>👤 {submission['student_name']} ({submission['student_username']})</h3>
        <p>📅 Nộp bài: {submission['submitted_at'][:16]} | ⏱️ Thời gian làm: {submission.get('duration', 'N/A')} phút</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Lấy thông tin đề thi và câu trả lời
    exam_questions = get_exam_questions(exam_id)
    student_answers = submission['answers']
    
    # Form chấm bài
    with st.form("grading_form"):
        total_score = 0
        max_total_score = sum(q['points'] for q in exam_questions)
        
        for i, question in enumerate(exam_questions):
            student_answer = next((ans for ans in student_answers if ans['question_id'] == question['id']), None)
            
            st.markdown(f"### 📝 Câu {i+1}: ({question['points']} điểm)")
            
            # Hiển thị câu hỏi
            st.markdown(question['question'])
            
            # Hiển thị hình ảnh nếu có
            if question.get('image_data'):
                try:
                    image_bytes = base64.b64decode(question['image_data'])
                    st.image(image_bytes, caption=f"Hình ảnh câu {i+1}", use_column_width=True)
                except:
                    st.caption("🖼️ Có hình ảnh đính kèm")
            
            # Hiển thị đáp án đúng và câu trả lời học sinh
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🎯 Đáp án đúng:**")
                show_correct_answer(question)
            
            with col2:
                st.write("**📝 Câu trả lời học sinh:**")
                show_student_answer(question, student_answer)
            
            # Chấm điểm
            st.write("**📊 Chấm điểm:**")
            
            if question['type'] in ['multiple_choice', 'true_false', 'short_answer']:
                # Tự động chấm hoặc đã có điểm
                auto_score = calculate_auto_score(question, student_answer)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score = st.number_input(
                        f"Điểm câu {i+1}",
                        min_value=0.0,
                        max_value=float(question['points']),
                        value=student_answer.get('score', auto_score) if student_answer else 0.0,
                        step=0.25,
                        key=f"score_{question['id']}"
                    )
                
                with col2:
                    if auto_score is not None:
                        st.write(f"**Tự động:** {auto_score}/{question['points']}")
                        if st.button(f"✅ Dùng điểm tự động", key=f"auto_{question['id']}"):
                            st.session_state[f"score_{question['id']}"] = auto_score
                
                with col3:
                    # Hiển thị phần trăm
                    percentage = (score / question['points']) * 100 if question['points'] > 0 else 0
                    color = "green" if percentage >= 80 else "orange" if percentage >= 50 else "red"
                    st.markdown(f"<span style='color: {color}'>{percentage:.1f}%</span>", unsafe_allow_html=True)
                
            elif question['type'] == 'essay':
                # Chấm thủ công cho tự luận
                score = st.number_input(
                    f"Điểm câu {i+1}",
                    min_value=0.0,
                    max_value=float(question['points']),
                    value=student_answer.get('score', 0.0) if student_answer else 0.0,
                    step=0.25,
                    key=f"score_{question['id']}"
                )
                
                # Nhận xét
                comment = st.text_area(
                    f"Nhận xét câu {i+1}",
                    value=student_answer.get('comment', '') if student_answer else '',
                    placeholder="Nhập nhận xét cho học sinh...",
                    key=f"comment_{question['id']}"
                )
            
            total_score += st.session_state.get(f"score_{question['id']}", 0)
            
            # Hiển thị lời giải nếu có
            if question.get('solution'):
                with st.expander(f"💡 Lời giải câu {i+1}", expanded=False):
                    st.markdown(question['solution'])
            
            st.divider()
        
        # Tổng kết điểm
        st.markdown(f"""
        <div style='background: #f0f2f6; padding: 15px; border-radius: 10px; margin: 20px 0;'>
            <h3>📊 Tổng kết</h3>
            <p><strong>Tổng điểm:</strong> {total_score:.1f}/{max_total_score} điểm</p>
            <p><strong>Phần trăm:</strong> {(total_score/max_total_score*100):.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Nhận xét tổng
        general_comment = st.text_area(
            "💬 Nhận xét chung",
            value=submission.get('general_comment', ''),
            placeholder="Nhận xét tổng quát về bài làm của học sinh...",
            key="general_comment"
        )
        
        # Buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Lưu điểm", use_container_width=True, type="primary"):
                save_grading_scores(submission, exam_questions, general_comment)
        
        with col2:
            if st.form_submit_button("📧 Lưu và gửi kết quả", use_container_width=True):
                save_grading_scores(submission, exam_questions, general_comment, send_notification=True)
        
        with col3:
            if st.form_submit_button("❌ Hủy", use_container_width=True):
                st.session_state.show_grading_detail = False
                if 'grading_submission' in st.session_state:
                    del st.session_state.grading_submission
                st.rerun()

def show_correct_answer(question):
    """Hiển thị đáp án đúng cho câu hỏi"""
    if question['type'] == 'multiple_choice':
        for i, option in enumerate(question['options']):
            prefix = "✅" if chr(65+i) == question['correct_answer'] else "  "
            st.write(f"{prefix} {chr(65+i)}. {option}")
    
    elif question['type'] == 'true_false':
        if 'statements' in question and question['statements']:
            for stmt in question['statements']:
                icon = "✅" if stmt.get('is_correct', False) else "❌"
                st.write(f"{icon} {stmt['letter']}) {stmt['text']}")
        else:
            st.write(f"Đáp án: {question.get('correct_answer', 'N/A')}")
    
    elif question['type'] == 'short_answer':
        answers = question.get('sample_answers', [])
        if answers:
            st.write("Đáp án mẫu:")
            for ans in answers:
                st.write(f"• {ans}")
    
    elif question['type'] == 'essay':
        st.write("📄 Câu tự luận - chấm theo tiêu chí")
        if question.get('grading_criteria'):
            st.caption(f"Tiêu chí: {question['grading_criteria']}")

def show_student_answer(question, student_answer):
    """Hiển thị câu trả lời của học sinh"""
    if not student_answer:
        st.warning("❌ Học sinh chưa trả lời câu này")
        return
    
    if question['type'] == 'multiple_choice':
        st.write(f"**Chọn:** {student_answer.get('selected_option', 'Chưa chọn')}")
    
    elif question['type'] == 'true_false':
        selected = student_answer.get('selected_answers', [])
        if selected:
            st.write(f"**Chọn:** {', '.join(selected)}")
        else:
            st.write("Chưa chọn")
    
    elif question['type'] == 'short_answer':
        answer_text = student_answer.get('answer_text', '')
        if answer_text:
            st.write(f"**Trả lời:** {answer_text}")
        else:
            st.write("Chưa trả lời")
    
    elif question['type'] == 'essay':
        answer_text = student_answer.get('answer_text', '')
        image_data = student_answer.get('image_data')
        
        if answer_text:
            st.write("**Văn bản:**")
            st.text_area("", value=answer_text, disabled=True, key=f"essay_view_{student_answer.get('id', 'temp')}")
        
        if image_data:
            st.write("**Hình ảnh bài làm:**")
            try:
                image_bytes = base64.b64decode(image_data)
                st.image(image_bytes, caption="Bài làm học sinh", use_column_width=True)
            except:
                st.error("Lỗi hiển thị hình ảnh")
        
        if not answer_text and not image_data:
            st.write("Chưa có bài làm")

def calculate_auto_score(question, student_answer):
    """Tính điểm tự động cho câu hỏi"""
    if not student_answer:
        return 0.0
    
    if question['type'] == 'multiple_choice':
        if student_answer.get('selected_option') == question.get('correct_answer'):
            return float(question['points'])
        else:
            return 0.0
    
    elif question['type'] == 'true_false':
        if 'statements' in question and question['statements']:
            correct_letters = [stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)]
            selected_letters = student_answer.get('selected_answers', [])
            
            if set(correct_letters) == set(selected_letters):
                return float(question['points'])
            else:
                return 0.0
        else:
            # Fallback cho format cũ
            if student_answer.get('selected_option') == question.get('correct_answer'):
                return float(question['points'])
            else:
                return 0.0
    
    elif question['type'] == 'short_answer':
        student_text = student_answer.get('answer_text', '').strip()
        correct_answers = question.get('sample_answers', [])
        case_sensitive = question.get('case_sensitive', False)
        
        if not case_sensitive:
            student_text = student_text.lower()
            correct_answers = [ans.lower() for ans in correct_answers]
        
        if student_text in correct_answers:
            return float(question['points'])
        else:
            return 0.0
    
    # Essay không tự động chấm
    return None

def save_grading_scores(submission, exam_questions, general_comment, send_notification=False):
    """Lưu điểm chấm"""
    try:
        # Lưu điểm từng câu
        scores = {}
        comments = {}
        total_score = 0
        
        for question in exam_questions:
            score = st.session_state.get(f"score_{question['id']}", 0)
            comment = st.session_state.get(f"comment_{question['id']}", '')
            
            scores[question['id']] = score
            comments[question['id']] = comment
            total_score += score
        
        # TODO: Lưu vào database
        # update_submission_scores(submission['id'], scores, comments, total_score, general_comment)
        
        st.success("✅ Đã lưu điểm thành công!")
        
        if send_notification:
            # TODO: Gửi thông báo cho học sinh
            st.success("📧 Đã gửi kết quả cho học sinh!")
        
        # Reset form
        st.session_state.show_grading_detail = False
        if 'grading_submission' in st.session_state:
            del st.session_state.grading_submission
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi lưu điểm: {str(e)}")

def show_grading_statistics(exam_id):
    """Hiển thị thống kê chấm bài"""
    st.subheader("📊 Thống kê chấm bài")
    
    submissions = get_exam_submissions(exam_id)
    exam_info = get_exam_info(exam_id)
    
    if not submissions:
        st.info("📝 Chưa có bài nộp nào!")
        return
    
    # Thống kê tổng quan
    graded_submissions = [s for s in submissions if s['status'] == 'graded']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📥 Tổng bài nộp", len(submissions))
    
    with col2:
        st.metric("✅ Đã chấm", len(graded_submissions))
    
    with col3:
        if graded_submissions:
            avg_score = sum(s['total_score'] for s in graded_submissions) / len(graded_submissions)
            st.metric("📈 Điểm TB", f"{avg_score:.1f}")
        else:
            st.metric("📈 Điểm TB", "--")
    
    with col4:
        progress = len(graded_submissions) / len(submissions) * 100 if submissions else 0
        st.metric("📊 Tiến độ", f"{progress:.1f}%")
    
    if not graded_submissions:
        st.info("📊 Cần chấm ít nhất 1 bài để hiển thị thống kê!")
        return
    
    # Biểu đồ phân bố điểm
    st.write("### 📈 Phân bố điểm số")
    
    scores = [s['total_score'] for s in graded_submissions]
    max_score = exam_info['total_points']
    
    # Tạo histogram
    score_ranges = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
    score_counts = [0] * 5
    
    for score in scores:
        percentage = (score / max_score) * 100
        if percentage <= 20:
            score_counts[0] += 1
        elif percentage <= 40:
            score_counts[1] += 1
        elif percentage <= 60:
            score_counts[2] += 1
        elif percentage <= 80:
            score_counts[3] += 1
        else:
            score_counts[4] += 1
    
    chart_data = pd.DataFrame({
        'Khoảng điểm': score_ranges,
        'Số học sinh': score_counts
    })
    
    st.bar_chart(chart_data.set_index('Khoảng điểm'))
    
    # Thống kê theo câu hỏi
    st.write("### 📝 Thống kê theo câu hỏi")
    
    question_stats = calculate_question_statistics(exam_id, graded_submissions)
    
    if question_stats:
        df_stats = pd.DataFrame(question_stats)
        st.dataframe(df_stats, use_container_width=True)
    
    # Top học sinh
    st.write("### 🏆 Xếp hạng")
    
    sorted_submissions = sorted(graded_submissions, key=lambda x: x['total_score'], reverse=True)
    
    for i, submission in enumerate(sorted_submissions[:10]):
        rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        percentage = (submission['total_score'] / max_score) * 100
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.write(rank_icon)
        
        with col2:
            st.write(f"**{submission['student_name']}**")
        
        with col3:
            st.write(f"{submission['total_score']:.1f} ({percentage:.1f}%)")

def show_export_results(exam_id):
    """Xuất kết quả chấm bài"""
    st.subheader("📤 Xuất kết quả")
    
    submissions = get_exam_submissions(exam_id)
    graded_submissions = [s for s in submissions if s['status'] == 'graded']
    
    if not graded_submissions:
        st.info("📝 Chưa có bài nào được chấm để xuất kết quả!")
        return
    
    # Tùy chọn xuất
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Xuất Excel")
        
        include_details = st.checkbox("Bao gồm chi tiết từng câu", value=True)
        include_comments = st.checkbox("Bao gồm nhận xét", value=True)
        
        if st.button("📥 Tải file Excel", use_container_width=True):
            excel_data = prepare_excel_export(exam_id, graded_submissions, include_details, include_comments)
            st.download_button(
                label="💾 Download Excel",
                data=excel_data,
                file_name=f"ket_qua_cham_bai_{exam_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        st.write("### 📧 Gửi kết quả")
        
        send_to_students = st.checkbox("Gửi cho học sinh", value=True)
        send_to_parents = st.checkbox("Gửi cho phụ huynh", value=False)
        
        email_template = st.selectbox(
            "Mẫu email:",
            ["Thông báo kết quả chuẩn", "Thông báo có nhận xét", "Tùy chỉnh"]
        )
        
        if st.button("📧 Gửi email hàng loạt", use_container_width=True):
            send_bulk_results_email(exam_id, graded_submissions, send_to_students, send_to_parents, email_template)
    
    # Preview kết quả
    st.write("### 👁️ Preview kết quả")
    
    preview_data = []
    for submission in graded_submissions[:5]:  # Chỉ hiển thị 5 bài đầu
        percentage = (submission['total_score'] / submission['max_score']) * 100
        preview_data.append({
            'Học sinh': submission['student_name'],
            'Điểm': f"{submission['total_score']:.1f}/{submission['max_score']}",
            'Phần trăm': f"{percentage:.1f}%",
            'Xếp loại': get_grade_classification(percentage),
            'Nhận xét': submission.get('general_comment', '')[:50] + "..." if submission.get('general_comment') else ""
        })
    
    if preview_data:
        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True)
        
        if len(graded_submissions) > 5:
            st.caption(f"... và {len(graded_submissions) - 5} học sinh khác")

def auto_grade_multiple_choice(exam_id):
    """Chấm tự động câu trắc nghiệm và đúng/sai"""
    try:
        submissions = get_exam_submissions(exam_id)
        exam_questions = get_exam_questions(exam_id)
        
        auto_gradable_types = ['multiple_choice', 'true_false', 'short_answer']
        auto_questions = [q for q in exam_questions if q['type'] in auto_gradable_types]
        
        if not auto_questions:
            st.warning("⚠️ Đề thi này không có câu hỏi có thể chấm tự động!")
            return
        
        graded_count = 0
        
        for submission in submissions:
            if submission['status'] == 'pending':
                scores = {}
                total_auto_score = 0
                
                for question in auto_questions:
                    student_answer = next((ans for ans in submission['answers'] if ans['question_id'] == question['id']), None)
                    auto_score = calculate_auto_score(question, student_answer)
                    
                    if auto_score is not None:
                        scores[question['id']] = auto_score
                        total_auto_score += auto_score
                
                # TODO: Cập nhật database
                # update_submission_auto_scores(submission['id'], scores, total_auto_score)
                graded_count += 1
        
        st.success(f"✅ Đã chấm tự động {graded_count} bài!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi chấm tự động: {str(e)}")

def get_grade_classification(percentage):
    """Phân loại học lực theo phần trăm"""
    if percentage >= 90:
        return "Xuất sắc"
    elif percentage >= 80:
        return "Giỏi"
    elif percentage >= 70:
        return "Khá"
    elif percentage >= 50:
        return "Trung bình"
    else:
        return "Yếu"

# Mock database functions - Thay thế bằng implementation thực tế

def get_teacher_exams_for_grading(teacher_id):
    """Mock function - lấy danh sách đề thi cần chấm"""
    return [
        {
            'id': 1,
            'title': 'Kiểm tra 15 phút - Toán 10',
            'class_name': 'Lớp 10A1',
            'total_points': 10.0,
            'total_questions': 10,
            'time_limit': 15,
            'start_time': '2024-02-01T08:00:00',
            'end_time': '2024-02-01T09:00:00',
            'submission_count': 25,
            'graded_count': 10
        }
    ]

def get_exam_submissions(exam_id):
    """Mock function - lấy danh sách bài làm"""
    return [
        {
            'id': 1,
            'student_id': 1,
            'student_name': 'Nguyễn Văn A',
            'student_username': 'nguyenvana',
            'status': 'pending',
            'submitted_at': '2024-02-01T08:30:00',
            'start_time': '2024-02-01T08:15:00',
            'total_score': None,
            'max_score': 10.0,
            'answers': []
        }
    ]

def get_exam_questions(exam_id):
    """Mock function - lấy câu hỏi của đề thi"""
    return [
        {
            'id': 1,
            'type': 'multiple_choice',
            'question': 'Câu hỏi trắc nghiệm mẫu?',
            'points': 1.0,
            'options': ['Đáp án A', 'Đáp án B', 'Đáp án C', 'Đáp án D'],
            'correct_answer': 'A'
        }
    ]

def get_exam_info(exam_id):
    """Mock function - lấy thông tin đề thi"""
    return {
        'id': exam_id,
        'title': 'Kiểm tra mẫu',
        'total_points': 10.0,
        'total_questions': 10
    }

def calculate_question_statistics(exam_id, graded_submissions):
    """Tính thống kê theo câu hỏi"""
    # Mock implementation
    return [
        {
            'Câu': 1,
            'Loại': 'Trắc nghiệm',
            'Điểm TB': 0.8,
            'Tỷ lệ đúng': '80%',
            'Độ khó': 'Dễ'
        }
    ]

def prepare_excel_export(exam_id, submissions, include_details, include_comments):
    """Chuẩn bị dữ liệu xuất Excel"""
    # Mock implementation
    data = []
    for submission in submissions:
        row = {
            'Học sinh': submission['student_name'],
            'Username': submission['student_username'],
            'Điểm': submission['total_score'],
            'Phần trăm': (submission['total_score'] / submission['max_score']) * 100
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    excel_buffer = pd.io.common.BytesIO()
    df.to_excel(excel_buffer, index=False)
    return excel_buffer.getvalue()

def send_bulk_results_email(exam_id, submissions, send_to_students, send_to_parents, template):
    """Gửi email kết quả hàng loạt"""
    # Mock implementation
    st.success(f"📧 Đã gửi email cho {len(submissions)} học sinh!")

def export_grading_report(exam_id):
    """Xuất báo cáo chấm bài"""
    st.info("📊 Tính năng xuất báo cáo đang được phát triển...")

def send_results_email(exam_id):
    """Gửi kết quả qua email"""
    st.info("📧 Tính năng gửi email đang được phát triển..."),

def show_grading():
    """Giao diện chấm bài chính"""
    st.header("✅ Chấm bài")
    
    user = get_current_user()
    
    # Lấy danh sách đề thi để chấm
    exams = get_teacher_exams_for_grading(user['id'])
    
    if not exams:
        st.info("📝 Bạn chưa có đề thi nào cần chấm!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Tạo đề thi mới", use_container_width=True):
                st.session_state.current_page = "create_exam"
                st.rerun()
        with col2:
            if st.button("📊 Xem thống kê", use_container_width=True):
                st.session_state.current_page = "statistics"
                st.rerun()
        return
    
    # Sidebar để chọn đề thi
    with st.sidebar:
        st.write("### 📝 Chọn đề thi để chấm")
        
        selected_exam_id = st.selectbox(
            "Đề thi:",
            options=[exam['id'] for exam in exams],
            format_func=lambda x: next(
                f"{exam['title']} ({exam['class_name']})" 
                for exam in exams if exam['id'] == x
            ),
            key="selected_exam_grading"
        )
        
        # Lọc theo trạng thái
        filter_status = st.selectbox(
            "Lọc theo trạng thái:",
            ["Tất cả", "Chưa chấm", "Đã chấm", "Chấm một phần"],
            key="filter_grading_status"
        )
        
        # Sắp xếp
        sort_by = st.selectbox(
            "Sắp xếp theo:",
            ["Thời gian nộp", "Tên học sinh", "Điểm", "Trạng thái"],
            key="sort_grading_by"
        )
    
    # Hiển thị thông tin đề thi được chọn
    selected_exam = next(exam for exam in exams if exam['id'] == selected_exam_id)
    show_exam_grading_overview(selected_exam)
    
    # Tabs chấm bài
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Danh sách bài làm", 
        "✏️ Chấm chi tiết", 
        "📊 Thống kê", 
        "📤 Xuất kết quả"
    ])
    
    with tab1:
        show_submissions_list(selected_exam_id, filter_status, sort_by)
    
    with tab2:
        show_detailed_grading(selected_exam_id)
    
    with tab3:
        show_grading_statistics(selected_exam_id)
    
    with tab4:
        show_export_results(selected_exam_id)

def show_exam_grading_overview(exam):
    """Hiển thị tổng quan về đề thi cần chấm"""
    # Thống kê nhanh
    submissions = get_exam_submissions(exam['id'])
    total_submissions = len(submissions)
    graded_count = len([s for s in submissions if s['status'] == 'graded'])
    pending_count = total_submissions - graded_count
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📝 Đề thi", exam['title'][:20] + "...")
    
    with col2:
        st.metric("👥 Đã nộp", total_submissions)
    
    with col3:
        st.metric("✅ Đã chấm", graded_count)
    
    with col4:
        st.metric("⏳ Chờ chấm", pending_count)
    
    with col5:
        progress = (graded_count / total_submissions * 100) if total_submissions > 0 else 0
        st.metric("📈 Tiến độ", f"{progress:.1f}%")
    
    # Progress bar
    if total_submissions > 0:
        st.progress(graded_count / total_submissions)
    
    # Thông tin đề thi
    with st.expander("ℹ️ Thông tin đề thi", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**📚 Lớp:** {exam['class_name']}")
            st.write(f"**⏱️ Thời gian:** {exam['time_limit']} phút")
            st.write(f"**📊 Tổng điểm:** {exam['total_points']} điểm")
        
        with col2:
            st.write(f"**📅 Bắt đầu:** {exam['start_time'][:16]}")
            st.write(f"**📅 Kết thúc:** {exam['end_time'][:16]}")
            st.write(f"**❓ Số câu hỏi:** {exam['total_questions']} câu")

def show_submissions_list(exam_id, filter_status, sort_by):
    """Hiển thị danh sách bài làm của học sinh"""
    st.subheader("📋 Danh sách bài làm")
    
    submissions = get_exam_submissions(exam_id)
    
    # Lọc theo trạng thái
    if filter_status != "Tất cả":
        status_map = {
            "Chưa chấm": "pending",
            "Đã chấm": "graded", 
            "Chấm một phần": "partial"
        }
        submissions = [s for s in submissions if s['status'] == status_map[filter_status]]
    
    # Sắp xếp
    if sort_by == "Thời gian nộp":
        submissions.sort(key=lambda x: x['submitted_at'], reverse=True)
    elif sort_by == "Tên học sinh":
        submissions.sort(key=lambda x: x['student_name'])
    elif sort_by == "Điểm":
        submissions.sort(key=lambda x: x['total_score'] or 0, reverse=True)
    elif sort_by == "Trạng thái":
        submissions.sort(key=lambda x: x['status'])
    
    if not submissions:
        st.info("📝 Không có bài làm nào phù hợp với bộ lọc!")
        return
    
    # Hiển thị danh sách
    for submission in submissions:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                # Tên học sinh và thông tin
                status_icon = {
                    "pending": "⏳",
                    "graded": "✅", 
                    "partial": "🔶"
                }.get(submission['status'], "❓")
                
                st.write(f"{status_icon} **{submission['student_name']}**")
                st.caption(f"ID: {submission['student_id']} | {submission['student_username']}")
            
            with col2:
                # Thời gian nộp
                submitted_time = datetime.fromisoformat(submission['submitted_at'])
                st.write(f"📅 {submitted_time.strftime('%d/%m %H:%M')}")
                
                # Thời gian làm bài
                if submission['start_time'] and submission['submitted_at']:
                    start_time = datetime.fromisoformat(submission['start_time'])
                    duration = submitted_time - start_time
                    st.caption(f"⏱️ {duration.seconds // 60} phút")
            
            with col3:
                # Điểm số
                if submission['status'] == 'graded':
                    score_percent = (submission['total_score'] / submission['max_score']) * 100
                    color = "green" if score_percent >= 80 else "orange" if score_percent >= 50 else "red"
                    st.markdown(f"<span style='color: {color}'><b>{submission['total_score']:.1f}/{submission['max_score']}</b></span>", 
                              unsafe_allow_html=True)
                    st.caption(f"{score_percent:.1f}%")
                else:
                    st.write("--/--")
                    st.caption("Chưa chấm")
            
            with col4:
                # Trạng thái chi tiết
                status_text = {
                    "pending": "Chờ chấm",
                    "graded": "Đã chấm",
                    "partial": "Chấm 1 phần"
                }.get(submission['status'], "Không xác định")
                
                if submission['status'] == 'partial':
                    graded_questions = len([q for q in submission['answers'] if q.get('score') is not None])
                    total_questions = len(submission['answers'])
                    st.write(f"{graded_questions}/{total_questions}")
                
                st.caption(status_text)
            
            with col5:
                # Actions
                if st.button("✏️ Chấm", key=f"grade_{submission['id']}", help="Chấm bài"):
                    st.session_state.grading_submission = submission
                    st.session_state.show_grading_detail = True
                    st.rerun()
                
                if submission['status'] == 'graded':
                    if st.button("👁️ Xem", key=f"view_{submission['id']}", help="Xem kết quả"):
                        st.session_state.viewing_submission = submission
                        st.session_state.show_view_result = True
                        st.rerun()
            
            st.divider()
    
    # Bulk actions
    if submissions:
        st.write("### 🔧 Thao tác hàng loạt")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤖 Chấm tự động trắc nghiệm", use_container_width=True):
                auto_grade_multiple_choice(exam_id)
        
        with col2:
            if st.button("📊 Xuất báo cáo Excel", use_container_width=True):
                export_grading_report(exam_id)
        
        with col3:
            if st.button("📧 Gửi kết quả qua email", use_container_width=True):
                send_results_email(exam_id)

def show_detailed_grading(exam_id):
    """Giao diện chấm bài chi tiết"""
    st.subheader("✏️ Chấm bài chi tiết")
    
    # Kiểm tra có bài cần chấm được chọn không
    if not st.session_state.get("show_grading_detail"):
        st.info("👆 Chọn một bài làm từ danh sách ở tab 'Danh sách bài làm' để bắt đầu chấm!")
        return
    
    submission = st.session_state.get("grading_submission")
    if not submission:
        st.error("❌ Không tìm thấy bài làm để chấm!")
        return
    
    # Load MathJax cho hiển thị công thức
    render_mathjax()
    
    # Header thông tin học sinh
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3>👤 {submission['student_name']} ({submission['student_username']})</h3>
        <p>📅 Nộp bài: {submission['submitted_at'][:16]} | ⏱️ Thời gian làm: {submission.get('duration', 'N/A')} phút</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Lấy thông tin đề thi và câu trả lời
    exam_questions = get_exam_questions(exam_id)
    student_answers = submission['answers']
    
    # Form chấm bài
    with st.form("grading_form"):
        total_score = 0
        max_total_score = sum(q['points'] for q in exam_questions)
        
        for i, question in enumerate(exam_questions):
            student_answer = next((ans for ans in student_answers if ans['question_id'] == question['id']), None)
            
            st.markdown(f"### 📝 Câu {i+1}: ({question['points']} điểm)")
            
            # Hiển thị câu hỏi
            st.markdown(question['question'])
            
            # Hiển thị hình ảnh nếu có
            if question.get('image_data'):
                try:
                    image_bytes = base64.b64decode(question['image_data'])
                    st.image(image_bytes, caption=f"Hình ảnh câu {i+1}", use_column_width=True)
                except:
                    st.caption("🖼️ Có hình ảnh đính kèm")
            
            # Hiển thị đáp án đúng và câu trả lời học sinh
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🎯 Đáp án đúng:**")
                show_correct_answer(question)
            
            with col2:
                st.write("**📝 Câu trả lời học sinh:**")
                show_student_answer(question, student_answer)
            
            # Chấm điểm
            st.write("**📊 Chấm điểm:**")
            
            if question['type'] in ['multiple_choice', 'true_false', 'short_answer']:
                # Tự động chấm hoặc đã có điểm
                auto_score = calculate_auto_score(question, student_answer)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score = st.number_input(
                        f"Điểm câu {i+1}",
                        min_value=0.0,
                        max_value=float(question['points']),
                        value=student_answer.get('score', auto_score) if student_answer else 0.0,
                        step=0.25,
                        key=f"score_{question['id']}"
                    )
                
                with col2:
                    if auto_score is not None:
                        st.write(f"**Tự động:** {auto_score}/{question['points']}")
                        if st.button(f"✅ Dùng điểm tự động", key=f"auto_{question['id']}"):
                            st.session_state[f"score_{question['id']}"] = auto_score
                
                with col3:
                    # Hiển thị phần trăm
                    percentage = (score / question['points']) * 100 if question['points'] > 0 else 0
                    color = "green" if percentage >= 80 else "orange" if percentage >= 50 else "red"
                    st.markdown(f"<span style='color: {color}'>{percentage:.1f}%</span>", unsafe_allow_html=True)
                
            elif question['type'] == 'essay':
                # Chấm thủ công cho tự luận
                score = st.number_input(
                    f"Điểm câu {i+1}",
                    min_value=0.0,
                    max_value=float(question['points']),
                    value=student_answer.get('score', 0.0) if student_answer else 0.0,
                    step=0.25,
                    key=f"score_{question['id']}"
                )
                
                # Nhận xét
                comment = st.text_area(
                    f"Nhận xét câu {i+1}",
                    value=student_answer.get('comment', '') if student_answer else '',
                    placeholder="Nhập nhận xét cho học sinh...",
                    key=f"comment_{question['id']}"
                )
            
            total_score += st.session_state.get(f"score_{question['id']}", 0)
            
            # Hiển thị lời giải nếu có
            if question.get('solution'):
                with st.expander(f"💡 Lời giải câu {i+1}", expanded=False):
                    st.markdown(question['solution'])
            
            st.divider()
        
        # Tổng kết điểm
        st.markdown(f"""
        <div style='background: #f0f2f6; padding: 15px; border-radius: 10px; margin: 20px 0;'>
            <h3>📊 Tổng kết</h3>
            <p><strong>Tổng điểm:</strong> {total_score:.1f}/{max_total_score} điểm</p>
            <p><strong>Phần trăm:</strong> {(total_score/max_total_score*100):.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Nhận xét tổng
        general_comment = st.text_area(
            "💬 Nhận xét chung",
            value=submission.get('general_comment', ''),
            placeholder="Nhận xét tổng quát về bài làm của học sinh...",
            key="general_comment"
        )
        
        # Buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Lưu điểm", use_container_width=True, type="primary"):
                save_grading_scores(submission, exam_questions, general_comment)
        
        with col2:
            if st.form_submit_button("📧 Lưu và gửi kết quả", use_container_width=True):
                save_grading_scores(submission, exam_questions, general_comment, send_notification=True)
        
        with col3:
            if st.form_submit_button("❌ Hủy", use_container_width=True):
                st.session_state.show_grading_detail = False
                if 'grading_submission' in st.session_state:
                    del st.session_state.grading_submission
                st.rerun()

def show_correct_answer(question):
    """Hiển thị đáp án đúng cho câu hỏi"""
    if question['type'] == 'multiple_choice':
        for i, option in enumerate(question['options']):
            prefix = "✅" if chr(65+i) == question['correct_answer'] else "  "
            st.write(f"{prefix} {chr(65+i)}. {option}")
    
    elif question['type'] == 'true_false':
        if 'statements' in question and question['statements']:
            for stmt in question['statements']:
                icon = "✅" if stmt.get('is_correct', False) else "❌"
                st.write(f"{icon} {stmt['letter']}) {stmt['text']}")
        else:
            st.write(f"Đáp án: {question.get('correct_answer', 'N/A')}")
    
    elif question['type'] == 'short_answer':
        answers = question.get('sample_answers', [])
        if answers:
            st.write("Đáp án mẫu:")
            for ans in answers:
                st.write(f"• {ans}")
    
    elif question['type'] == 'essay':
        st.write("📄 Câu tự luận - chấm theo tiêu chí")
        if question.get('grading_criteria'):
            st.caption(f"Tiêu chí: {question['grading_criteria']}")

def show_student_answer(question, student_answer):
    """Hiển thị câu trả lời của học sinh"""
    if not student_answer:
        st.warning("❌ Học sinh chưa trả lời câu này")
        return
    
    if question['type'] == 'multiple_choice':
        st.write(f"**Chọn:** {student_answer.get('selected_option', 'Chưa chọn')}")
    
    elif question['type'] == 'true_false':
        selected = student_answer.get('selected_answers', [])
        if selected:
            st.write(f"**Chọn:** {', '.join(selected)}")
        else:
            st.write("Chưa chọn")
    
    elif question['type'] == 'short_answer':
        answer_text = student_answer.get('answer_text', '')
        if answer_text:
            st.write(f"**Trả lời:** {answer_text}")
        else:
            st.write("Chưa trả lời")
    
    elif question['type'] == 'essay':
        answer_text = student_answer.get('answer_text', '')
        image_data = student_answer.get('image_data')
        
        if answer_text:
            st.write("**Văn bản:**")
            st.text_area("", value=answer_text, disabled=True, key=f"essay_view_{student_answer.get('id', 'temp')}")
        
        if image_data:
            st.write("**Hình ảnh bài làm:**")
            try:
                image_bytes = base64.b64decode(image_data)
                st.image(image_bytes, caption="Bài làm học sinh", use_column_width=True)
            except:
                st.error("Lỗi hiển thị hình ảnh")
        
        if not answer_text and not image_data:
            st.write("Chưa có bài làm")

def calculate_auto_score(question, student_answer):
    """Tính điểm tự động cho câu hỏi"""
    if not student_answer:
        return 0.0
    
    if question['type'] == 'multiple_choice':
        if student_answer.get('selected_option') == question.get('correct_answer'):
            return float(question['points'])
        else:
            return 0.0
    
    elif question['type'] == 'true_false':
        if 'statements' in question and question['statements']:
            correct_letters = [stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)]
            selected_letters = student_answer.get('selected_answers', [])
            
            if set(correct_letters) == set(selected_letters):
                return float(question['points'])
            else:
                return 0.0
        else:
            # Fallback cho format cũ
            if student_answer.get('selected_option') == question.get('correct_answer'):
                return float(question['points'])
            else:
                return 0.0
    
    elif question['type'] == 'short_answer':
        student_text = student_answer.get('answer_text', '').strip()
        correct_answers = question.get('sample_answers', [])
        case_sensitive = question.get('case_sensitive', False)
        
        if not case_sensitive:
            student_text = student_text.lower()
            correct_answers = [ans.lower() for ans in correct_answers]
        
        if student_text in correct_answers:
            return float(question['points'])
        else:
            return 0.0
    
    # Essay không tự động chấm
    return None

def save_grading_scores(submission, exam_questions, general_comment, send_notification=False):
    """Lưu điểm chấm"""
    try:
        # Lưu điểm từng câu
        scores = {}
        comments = {}
        total_score = 0
        
        for question in exam_questions:
            score = st.session_state.get(f"score_{question['id']}", 0)
            comment = st.session_state.get(f"comment_{question['id']}", '')
            
            scores[question['id']] = score
            comments[question['id']] = comment
            total_score += score
        
        # TODO: Lưu vào database
        # update_submission_scores(submission['id'], scores, comments, total_score, general_comment)
        
        st.success("✅ Đã lưu điểm thành công!")
        
        if send_notification:
            # TODO: Gửi thông báo cho học sinh
            st.success("📧 Đã gửi kết quả cho học sinh!")
        
        # Reset form
        st.session_state.show_grading_detail = False
        if 'grading_submission' in st.session_state:
            del st.session_state.grading_submission
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi lưu điểm: {str(e)}")

def show_grading_statistics(exam_id):
    """Hiển thị thống kê chấm bài"""
    st.subheader("📊 Thống kê chấm bài")
    
    submissions = get_exam_submissions(exam_id)
    exam_info = get_exam_info(exam_id)
    
    if not submissions:
        st.info("📝 Chưa có bài nộp nào!")
        return
    
    # Thống kê tổng quan
    graded_submissions = [s for s in submissions if s['status'] == 'graded']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📥 Tổng bài nộp", len(submissions))
    
    with col2:
        st.metric("✅ Đã chấm", len(graded_submissions))
    
    with col3:
        if graded_submissions:
            avg_score = sum(s['total_score'] for s in graded_submissions) / len(graded_submissions)
            st.metric("📈 Điểm TB", f"{avg_score:.1f}")
        else:
            st.metric("📈 Điểm TB", "--")
    
    with col4:
        progress = len(graded_submissions) / len(submissions) * 100 if submissions else 0
        st.metric("📊 Tiến độ", f"{progress:.1f}%")
    
    if not graded_submissions:
        st.info("📊 Cần chấm ít nhất 1 bài để hiển thị thống kê!")
        return
    
    # Biểu đồ phân bố điểm
    st.write("### 📈 Phân bố điểm số")
    
    scores = [s['total_score'] for s in graded_submissions]
    max_score = exam_info['total_points']
    
    # Tạo histogram
    score_ranges = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
    score_counts = [0] * 5
    
    for score in scores:
        percentage = (score / max_score) * 100
        if percentage <= 20:
            score_counts[0] += 1
        elif percentage <= 40:
            score_counts[1] += 1
        elif percentage <= 60:
            score_counts[2] += 1
        elif percentage <= 80:
            score_counts[3] += 1
        else:
            score_counts[4] += 1
    
    chart_data = pd.DataFrame({
        'Khoảng điểm': score_ranges,
        'Số học sinh': score_counts
    })
    
    st.bar_chart(chart_data.set_index('Khoảng điểm'))
    
    # Thống kê theo câu hỏi
    st.write("### 📝 Thống kê theo câu hỏi")
    
    question_stats = calculate_question_statistics(exam_id, graded_submissions)
    
    if question_stats:
        df_stats = pd.DataFrame(question_stats)
        st.dataframe(df_stats, use_container_width=True)
    
    # Top học sinh
    st.write("### 🏆 Xếp hạng")
    
    sorted_submissions = sorted(graded_submissions, key=lambda x: x['total_score'], reverse=True)
    
    for i, submission in enumerate(sorted_submissions[:10]):
        rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        percentage = (submission['total_score'] / max_score) * 100
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.write(rank_icon)
        
        with col2:
            st.write(f"**{submission['student_name']}**")
        
        with col3:
            st.write(f"{submission['total_score']:.1f} ({percentage:.1f}%)")

def show_export_results(exam_id):
    """Xuất kết quả chấm bài"""
    st.subheader("📤 Xuất kết quả")
    
    submissions = get_exam_submissions(exam_id)
    graded_submissions = [s for s in submissions if s['status'] == 'graded']
    
    if not graded_submissions:
        st.info("📝 Chưa có bài nào được chấm để xuất kết quả!")
        return
    
    # Tùy chọn xuất
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Xuất Excel")
        
        include_details = st.checkbox("Bao gồm chi tiết từng câu", value=True)
        include_comments = st.checkbox("Bao gồm nhận xét", value=True)
        
        if st.button("📥 Tải file Excel", use_container_width=True):
            excel_data = prepare_excel_export(exam_id, graded_submissions, include_details, include_comments)
            st.download_button(
                label="💾 Download Excel",
                data=excel_data,
                file_name=f"ket_qua_cham_bai_{exam_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        st.write("### 📧 Gửi kết quả")
        
        send_to_students = st.checkbox("Gửi cho học sinh", value=True)
        send_to_parents = st.checkbox("Gửi cho phụ huynh", value=False)
        
        email_template = st.selectbox(
            "Mẫu email:",
            ["Thông báo kết quả chuẩn", "Thông báo có nhận xét", "Tùy chỉnh"]
        )
        
        if st.button("📧 Gửi email hàng loạt", use_container_width=True):
            send_bulk_results_email(exam_id, graded_submissions, send_to_students, send_to_parents, email_template)
    
    # Preview kết quả
    st.write("### 👁️ Preview kết quả")
    
    preview_data = []
    for submission in graded_submissions[:5]:  # Chỉ hiển thị 5 bài đầu
        percentage = (submission['total_score'] / submission['max_score']) * 100
        preview_data.append({
            'Học sinh': submission['student_name'],
            'Điểm': f"{submission['total_score']:.1f}/{submission['max_score']}",
            'Phần trăm': f"{percentage:.1f}%",
            'Xếp loại': get_grade_classification(percentage),
            'Nhận xét': submission.get('general_comment', '')[:50] + "..." if submission.get('general_comment') else ""
        })
    
    if preview_data:
        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True)
        
        if len(graded_submissions) > 5:
            st.caption(f"... và {len(graded_submissions) - 5} học sinh khác")

def auto_grade_multiple_choice(exam_id):
    """Chấm tự động câu trắc nghiệm và đúng/sai"""
    try:
        submissions = get_exam_submissions(exam_id)
        exam_questions = get_exam_questions(exam_id)
        
        auto_gradable_types = ['multiple_choice', 'true_false', 'short_answer']
        auto_questions = [q for q in exam_questions if q['type'] in auto_gradable_types]
        
        if not auto_questions:
            st.warning("⚠️ Đề thi này không có câu hỏi có thể chấm tự động!")
            return
        
        graded_count = 0
        
        for submission in submissions:
            if submission['status'] == 'pending':
                scores = {}
                total_auto_score = 0
                
                for question in auto_questions:
                    student_answer = next((ans for ans in submission['answers'] if ans['question_id'] == question['id']), None)
                    auto_score = calculate_auto_score(question, student_answer)
                    
                    if auto_score is not None:
                        scores[question['id']] = auto_score
                        total_auto_score += auto_score
                
                # TODO: Cập nhật database
                # update_submission_auto_scores(submission['id'], scores, total_auto_score)
                graded_count += 1
        
        st.success(f"✅ Đã chấm tự động {graded_count} bài!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi chấm tự động: {str(e)}")

def get_grade_classification(percentage):
    """Phân loại học lực theo phần trăm"""
    if percentage >= 90:
        return "Xuất sắc"
    elif percentage >= 80:
        return "Giỏi"
    elif percentage >= 70:
        return "Khá"
    elif percentage >= 50:
        return "Trung bình"
    else:
        return "Yếu"

# Mock database functions - Thay thế bằng implementation thực tế

def get_teacher_exams_for_grading(teacher_id):
    """Mock function - lấy danh sách đề thi cần chấm"""
    return [
        {
            'id': 1,
            'title': 'Kiểm tra 15 phút - Toán 10',
            'class_name': 'Lớp 10A1',
            'total_points': 10.0,
            'total_questions': 10,
            'time_limit': 15,
            'start_time': '2024-02-01T08:00:00',
            'end_time': '2024-02-01T09:00:00',
            'submission_count': 25,
            'graded_count': 10
        }
    ]

def get_exam_submissions(exam_id):
    """Mock function - lấy danh sách bài làm"""
    return [
        {
            'id': 1,
            'student_id': 1,
            'student_name': 'Nguyễn Văn A',
            'student_username': 'nguyenvana',
            'status': 'pending',
            'submitted_at': '2024-02-01T08:30:00',
            'start_time': '2024-02-01T08:15:00',
            'total_score': None,
            'max_score': 10.0,
            'answers': []
        }
    ]

def get_exam_questions(exam_id):
    """Mock function - lấy câu hỏi của đề thi"""
    return [
        {
            'id': 1,
            'type': 'multiple_choice',
            'question': 'Câu hỏi trắc nghiệm mẫu?',
            'points': 1.0,
            'options': ['Đáp án A', 'Đáp án B', 'Đáp án C', 'Đáp án D'],
            'correct_answer': 'A'
        }
    ]

def get_exam_info(exam_id):
    """Mock function - lấy thông tin đề thi"""
    return {
        'id': exam_id,
        'title': 'Kiểm tra mẫu',
        'total_points': 10.0,
        'total_questions': 10
    }

def calculate_question_statistics(exam_id, graded_submissions):
    """Tính thống kê theo câu hỏi"""
    # Mock implementation
    return [
        {
            'Câu': 1,
            'Loại': 'Trắc nghiệm',
            'Điểm TB': 0.8,
            'Tỷ lệ đúng': '80%',
            'Độ khó': 'Dễ'
        }
    ]

def prepare_excel_export(exam_id, submissions, include_details, include_comments):
    """Chuẩn bị dữ liệu xuất Excel"""
    # Mock implementation
    data = []
    for submission in submissions:
        row = {
            'Học sinh': submission['student_name'],
            'Username': submission['student_username'],
            'Điểm': submission['total_score'],
            'Phần trăm': (submission['total_score'] / submission['max_score']) * 100
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    excel_buffer = pd.io.common.BytesIO()
    df.to_excel(excel_buffer, index=False)
    return excel_buffer.getvalue()

def send_bulk_results_email(exam_id, submissions, send_to_students, send_to_parents, template):
    """Gửi email kết quả hàng loạt"""
    # Mock implementation
    st.success(f"📧 Đã gửi email cho {len(submissions)} học sinh!")

def export_grading_report(exam_id):
    """Xuất báo cáo chấm bài"""
    st.info("📊 Tính năng xuất báo cáo đang được phát triển...")

def send_results_email(exam_id):
    """Gửi kết quả qua email"""
    st.info("📧 Tính năng gửi email đang được phát triển...")

def show_grading():
    """Giao diện chấm bài chính"""
    st.header("✅ Chấm bài")
    
    user = get_current_user()
    
    # Lấy danh sách đề thi để chấm
    exams = get_teacher_exams_for_grading(user['id'])
    
    if not exams:
        st.info("📝 Bạn chưa có đề thi nào cần chấm!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Tạo đề thi mới", use_container_width=True):
                st.session_state.current_page = "create_exam"
                st.rerun()
        with col2:
            if st.button("📊 Xem thống kê", use_container_width=True):
                st.session_state.current_page = "statistics"
                st.rerun()
        return
    
    # Sidebar để chọn đề thi
    with st.sidebar:
        st.write("### 📝 Chọn đề thi để chấm")
        
        selected_exam_id = st.selectbox(
            "Đề thi:",
            options=[exam['id'] for exam in exams],
            format_func=lambda x: next(
                f"{exam['title']} ({exam['class_name']})" 
                for exam in exams if exam['id'] == x
            ),
            key="selected_exam_grading"
        )
        
        # Lọc theo trạng thái
        filter_status = st.selectbox(
            "Lọc theo trạng thái:",
            ["Tất cả", "Chưa chấm", "Đã chấm", "Chấm một phần"],
            key="filter_grading_status"
        )
        
        # Sắp xếp
        sort_by = st.selectbox(
            "Sắp xếp theo:",
            ["Thời gian nộp", "Tên học sinh", "Điểm", "Trạng thái"],
            key="sort_grading_by"
        )
    
    # Hiển thị thông tin đề thi được chọn
    selected_exam = next(exam for exam in exams if exam['id'] == selected_exam_id)
    show_exam_grading_overview(selected_exam)
    
    # Tabs chấm bài
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Danh sách bài làm", 
        "✏️ Chấm chi tiết", 
        "📊 Thống kê", 
        "📤 Xuất kết quả"
    ])
    
    with tab1:
        show_submissions_list(selected_exam_id, filter_status, sort_by)
    
    with tab2:
        show_detailed_grading(selected_exam_id)
    
    with tab3:
        show_grading_statistics(selected_exam_id)
    
    with tab4:
        show_export_results(selected_exam_id)

def show_exam_grading_overview(exam):
    """Hiển thị tổng quan về đề thi cần chấm"""
    # Thống kê nhanh
    submissions = get_exam_submissions(exam['id'])
    total_submissions = len(submissions)
    graded_count = len([s for s in submissions if s['status'] == 'graded'])
    pending_count = total_submissions - graded_count
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📝 Đề thi", exam['title'][:20] + "...")
    
    with col2:
        st.metric("👥 Đã nộp", total_submissions)
    
    with col3:
        st.metric("✅ Đã chấm", graded_count)
    
    with col4:
        st.metric("⏳ Chờ chấm", pending_count)
    
    with col5:
        progress = (graded_count / total_submissions * 100) if total_submissions > 0 else 0
        st.metric("📈 Tiến độ", f"{progress:.1f}%")
    
    # Progress bar
    if total_submissions > 0:
        st.progress(graded_count / total_submissions)
    
    # Thông tin đề thi
    with st.expander("ℹ️ Thông tin đề thi", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**📚 Lớp:** {exam['class_name']}")
            st.write(f"**⏱️ Thời gian:** {exam['time_limit']} phút")
            st.write(f"**📊 Tổng điểm:** {exam['total_points']} điểm")
        
        with col2:
            st.write(f"**📅 Bắt đầu:** {exam['start_time'][:16]}")
            st.write(f"**📅 Kết thúc:** {exam['end_time'][:16]}")
            st.write(f"**❓ Số câu hỏi:** {exam['total_questions']} câu")

def show_submissions_list(exam_id, filter_status, sort_by):
    """Hiển thị danh sách bài làm của học sinh"""
    st.subheader("📋 Danh sách bài làm")
    
    submissions = get_exam_submissions(exam_id)
    
    # Lọc theo trạng thái
    if filter_status != "Tất cả":
        status_map = {
            "Chưa chấm": "pending",
            "Đã chấm": "graded", 
            "Chấm một phần": "partial"
        }
        submissions = [s for s in submissions if s['status'] == status_map[filter_status]]
    
    # Sắp xếp
    if sort_by == "Thời gian nộp":
        submissions.sort(key=lambda x: x['submitted_at'], reverse=True)
    elif sort_by == "Tên học sinh":
        submissions.sort(key=lambda x: x['student_name'])
    elif sort_by == "Điểm":
        submissions.sort(key=lambda x: x['total_score'] or 0, reverse=True)
    elif sort_by == "Trạng thái":
        submissions.sort(key=lambda x: x['status'])
    
    if not submissions:
        st.info("📝 Không có bài làm nào phù hợp với bộ lọc!")
        return
    
    # Hiển thị danh sách
    for submission in submissions:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                # Tên học sinh và thông tin
                status_icon = {
                    "pending": "⏳",
                    "graded": "✅", 
                    "partial": "🔶"
                }.get(submission['status'], "❓")
                
                st.write(f"{status_icon} **{submission['student_name']}**")
                st.caption(f"ID: {submission['student_id']} | {submission['student_username']}")
            
            with col2:
                # Thời gian nộp
                submitted_time = datetime.fromisoformat(submission['submitted_at'])
                st.write(f"📅 {submitted_time.strftime('%d/%m %H:%M')}")
                
                # Thời gian làm bài
                if submission['start_time'] and submission['submitted_at']:
                    start_time = datetime.fromisoformat(submission['start_time'])
                    duration = submitted_time - start_time
                    st.caption(f"⏱️ {duration.seconds // 60} phút")
            
            with col3:
                # Điểm số
                if submission['status'] == 'graded':
                    score_percent = (submission['total_score'] / submission['max_score']) * 100
                    color = "green" if score_percent >= 80 else "orange" if score_percent >= 50 else "red"
                    st.markdown(f"<span style='color: {color}'><b>{submission['total_score']:.1f}/{submission['max_score']}</b></span>", 
                              unsafe_allow_html=True)
                    st.caption(f"{score_percent:.1f}%")
                else:
                    st.write("--/--")
                    st.caption("Chưa chấm")
            
            with col4:
                # Trạng thái chi tiết
                status_text = {
                    "pending": "Chờ chấm",
                    "graded": "Đã chấm",
                    "partial": "Chấm 1 phần"
                }.get(submission['status'], "Không xác định")
                
                if submission['status'] == 'partial':
                    graded_questions = len([q for q in submission['answers'] if q.get('score') is not None])
                    total_questions = len(submission['answers'])
                    st.write(f"{graded_questions}/{total_questions}")
                
                st.caption(status_text)
            
            with col5:
                # Actions
                if st.button("✏️ Chấm", key=f"grade_{submission['id']}", help="Chấm bài"):
                    st.session_state.grading_submission = submission
                    st.session_state.show_grading_detail = True
                    st.rerun()
                
                if submission['status'] == 'graded':
                    if st.button("👁️ Xem", key=f"view_{submission['id']}", help="Xem kết quả"):
                        st.session_state.viewing_submission = submission
                        st.session_state.show_view_result = True
                        st.rerun()
            
            st.divider()
    
    # Bulk actions
    if submissions:
        st.write("### 🔧 Thao tác hàng loạt")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤖 Chấm tự động trắc nghiệm", use_container_width=True):
                auto_grade_multiple_choice(exam_id)
        
        with col2:
            if st.button("📊 Xuất báo cáo Excel", use_container_width=True):
                export_grading_report(exam_id)
        
        with col3:
            if st.button("📧 Gửi kết quả qua email", use_container_width=True):
                send_results_email(exam_id)

def show_detailed_grading(exam_id):
    """Giao diện chấm bài chi tiết"""
    st.subheader("✏️ Chấm bài chi tiết")
    
    # Kiểm tra có bài cần chấm được chọn không
    if not st.session_state.get("show_grading_detail"):
        st.info("👆 Chọn một bài làm từ danh sách ở tab 'Danh sách bài làm' để bắt đầu chấm!")
        return
    
    submission = st.session_state.get("grading_submission")
    if not submission:
        st.error("❌ Không tìm thấy bài làm để chấm!")
        return
    
    # Load MathJax cho hiển thị công thức
    render_mathjax()
    
    # Header thông tin học sinh
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3>👤 {submission['student_name']} ({submission['student_username']})</h3>
        <p>📅 Nộp bài: {submission['submitted_at'][:16]} | ⏱️ Thời gian làm: {submission.get('duration', 'N/A')} phút</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Lấy thông tin đề thi và câu trả lời
    exam_questions = get_exam_questions(exam_id)
    student_answers = submission['answers']
    
    # Form chấm bài
    with st.form("grading_form"):
        total_score = 0
        max_total_score = sum(q['points'] for q in exam_questions)
        
        for i, question in enumerate(exam_questions):
            student_answer = next((ans for ans in student_answers if ans['question_id'] == question['id']), None)
            
            st.markdown(f"### 📝 Câu {i+1}: ({question['points']} điểm)")
            
            # Hiển thị câu hỏi
            st.markdown(question['question'])
            
            # Hiển thị hình ảnh nếu có
            if question.get('image_data'):
                try:
                    image_bytes = base64.b64decode(question['image_data'])
                    st.image(image_bytes, caption=f"Hình ảnh câu {i+1}", use_column_width=True)
                except:
                    st.caption("🖼️ Có hình ảnh đính kèm")
            
            # Hiển thị đáp án đúng và câu trả lời học sinh
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🎯 Đáp án đúng:**")
                show_correct_answer(question)
            
            with col2:
                st.write("**📝 Câu trả lời học sinh:**")
                show_student_answer(question, student_answer)
            
            # Chấm điểm
            st.write("**📊 Chấm điểm:**")
            
            if question['type'] in ['multiple_choice', 'true_false', 'short_answer']:
                # Tự động chấm hoặc đã có điểm
                auto_score = calculate_auto_score(question, student_answer)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score = st.number_input(
                        f"Điểm câu {i+1}",
                        min_value=0.0,
                        max_value=float(question['points']),
                        value=student_answer.get('score', auto_score) if student_answer else 0.0,
                        step=0.25,
                        key=f"score_{question['id']}"
                    )
                
                with col2:
                    if auto_score is not None:
                        st.write(f"**Tự động:** {auto_score}/{question['points']}")
                        if st.button(f"✅ Dùng điểm tự động", key=f"auto_{question['id']}"):
                            st.session_state[f"score_{question['id']}"] = auto_score
                
                with col3:
                    # Hiển thị phần trăm
                    percentage = (score / question['points']) * 100 if question['points'] > 0 else 0
                    color = "green" if percentage >= 80 else "orange" if percentage >= 50 else "red"
                    st.markdown(f"<span style='color: {color}'>{percentage:.1f}%</span>", unsafe_allow_html=True)
                
            elif question['type'] == 'essay':
                # Chấm thủ công cho tự luận
                score = st.number_input(
                    f"Điểm câu {i+1}",
                    min_value=0.0,
                    max_value=float(question['points']),
                    value=student_answer.get('score', 0.0) if student_answer else 0.0,
                    step=0.25,
                    key=f"score_{question['id']}"
                )
                
                # Nhận xét
                comment = st.text_area(
                    f"Nhận xét câu {i+1}",
                    value=student_answer.get('comment', '') if student_answer else '',
                    placeholder="Nhập nhận xét cho học sinh...",
                    key=f"comment_{question['id']}"
                )
            
            total_score += st.session_state.get(f"score_{question['id']}", 0)
            
            # Hiển thị lời giải nếu có
            if question.get('solution'):
                with st.expander(f"💡 Lời giải câu {i+1}", expanded=False):
                    st.markdown(question['solution'])
            
            st.divider()
        
        # Tổng kết điểm
        st.markdown(f"""
        <div style='background: #f0f2f6; padding: 15px; border-radius: 10px; margin: 20px 0;'>
            <h3>📊 Tổng kết</h3>
            <p><strong>Tổng điểm:</strong> {total_score:.1f}/{max_total_score} điểm</p>
            <p><strong>Phần trăm:</strong> {(total_score/max_total_score*100):.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Nhận xét tổng
        general_comment = st.text_area(
            "💬 Nhận xét chung",
            value=submission.get('general_comment', ''),
            placeholder="Nhận xét tổng quát về bài làm của học sinh...",
            key="general_comment"
        )
        
        # Buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Lưu điểm", use_container_width=True, type="primary"):
                save_grading_scores(submission, exam_questions, general_comment)
        
        with col2:
            if st.form_submit_button("📧 Lưu và gửi kết quả", use_container_width=True):
                save_grading_scores(submission, exam_questions, general_comment, send_notification=True)
        
        with col3:
            if st.form_submit_button("❌ Hủy", use_container_width=True):
                st.session_state.show_grading_detail = False
                if 'grading_submission' in st.session_state:
                    del st.session_state.grading_submission
                st.rerun()

def show_correct_answer(question):
    """Hiển thị đáp án đúng cho câu hỏi"""
    if question['type'] == 'multiple_choice':
        for i, option in enumerate(question['options']):
            prefix = "✅" if chr(65+i) == question['correct_answer'] else "  "
            st.write(f"{prefix} {chr(65+i)}. {option}")
    
    elif question['type'] == 'true_false':
        if 'statements' in question and question['statements']:
            for stmt in question['statements']:
                icon = "✅" if stmt.get('is_correct', False) else "❌"
                st.write(f"{icon} {stmt['letter']}) {stmt['text']}")
        else:
            st.write(f"Đáp án: {question.get('correct_answer', 'N/A')}")
    
    elif question['type'] == 'short_answer':
        answers = question.get('sample_answers', [])
        if answers:
            st.write("Đáp án mẫu:")
            for ans in answers:
                st.write(f"• {ans}")
    
    elif question['type'] == 'essay':
        st.write("📄 Câu tự luận - chấm theo tiêu chí")
        if question.get('grading_criteria'):
            st.caption(f"Tiêu chí: {question['grading_criteria']}")

def show_student_answer(question, student_answer):
    """Hiển thị câu trả lời của học sinh"""
    if not student_answer:
        st.warning("❌ Học sinh chưa trả lời câu này")
        return
    
    if question['type'] == 'multiple_choice':
        st.write(f"**Chọn:** {student_answer.get('selected_option', 'Chưa chọn')}")
    
    elif question['type'] == 'true_false':
        selected = student_answer.get('selected_answers', [])
        if selected:
            st.write(f"**Chọn:** {', '.join(selected)}")
        else:
            st.write("Chưa chọn")
    
    elif question['type'] == 'short_answer':
        answer_text = student_answer.get('answer_text', '')
        if answer_text:
            st.write(f"**Trả lời:** {answer_text}")
        else:
            st.write("Chưa trả lời")
    
    elif question['type'] == 'essay':
        answer_text = student_answer.get('answer_text', '')
        image_data = student_answer.get('image_data')
        
        if answer_text:
            st.write("**Văn bản:**")
            st.text_area("", value=answer_text, disabled=True, key=f"essay_view_{student_answer.get('id', 'temp')}")
        
        if image_data:
            st.write("**Hình ảnh bài làm:**")
            try:
                image_bytes = base64.b64decode(image_data)
                st.image(image_bytes, caption="Bài làm học sinh", use_column_width=True)
            except:
                st.error("Lỗi hiển thị hình ảnh")
        
        if not answer_text and not image_data:
            st.write("Chưa có bài làm")

def calculate_auto_score(question, student_answer):
    """Tính điểm tự động cho câu hỏi"""
    if not student_answer:
        return 0.0
    
    if question['type'] == 'multiple_choice':
        if student_answer.get('selected_option') == question.get('correct_answer'):
            return float(question['points'])
        else:
            return 0.0
    
    elif question['type'] == 'true_false':
        if 'statements' in question and question['statements']:
            correct_letters = [stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)]
            selected_letters = student_answer.get('selected_answers', [])
            
            if set(correct_letters) == set(selected_letters):
                return float(question['points'])
            else:
                return 0.0
        else:
            # Fallback cho format cũ
            if student_answer.get('selected_option') == question.get('correct_answer'):
                return float(question['points'])
            else:
                return 0.0
    
    elif question['type'] == 'short_answer':
        student_text = student_answer.get('answer_text', '').strip()
        correct_answers = question.get('sample_answers', [])
        case_sensitive = question.get('case_sensitive', False)
        
        if not case_sensitive:
            student_text = student_text.lower()
            correct_answers = [ans.lower() for ans in correct_answers]
        
        if student_text in correct_answers:
            return float(question['points'])
        else:
            return 0.0
    
    # Essay không tự động chấm
    return None

def save_grading_scores(submission, exam_questions, general_comment, send_notification=False):
    """Lưu điểm chấm"""
    try:
        # Lưu điểm từng câu
        scores = {}
        comments = {}
        total_score = 0
        
        for question in exam_questions:
            score = st.session_state.get(f"score_{question['id']}", 0)
            comment = st.session_state.get(f"comment_{question['id']}", '')
            
            scores[question['id']] = score
            comments[question['id']] = comment
            total_score += score
        
        # TODO: Lưu vào database
        # update_submission_scores(submission['id'], scores, comments, total_score, general_comment)
        
        st.success("✅ Đã lưu điểm thành công!")
        
        if send_notification:
            # TODO: Gửi thông báo cho học sinh
            st.success("📧 Đã gửi kết quả cho học sinh!")
        
        # Reset form
        st.session_state.show_grading_detail = False
        if 'grading_submission' in st.session_state:
            del st.session_state.grading_submission
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi lưu điểm: {str(e)}")

def show_grading_statistics(exam_id):
    """Hiển thị thống kê chấm bài"""
    st.subheader("📊 Thống kê chấm bài")
    
    submissions = get_exam_submissions(exam_id)
    exam_info = get_exam_info(exam_id)
    
    if not submissions:
        st.info("📝 Chưa có bài nộp nào!")
        return
    
    # Thống kê tổng quan
    graded_submissions = [s for s in submissions if s['status'] == 'graded']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📥 Tổng bài nộp", len(submissions))
    
    with col2:
        st.metric("✅ Đã chấm", len(graded_submissions))
    
    with col3:
        if graded_submissions:
            avg_score = sum(s['total_score'] for s in graded_submissions) / len(graded_submissions)
            st.metric("📈 Điểm TB", f"{avg_score:.1f}")
        else:
            st.metric("📈 Điểm TB", "--")
    
    with col4:
        progress = len(graded_submissions) / len(submissions) * 100 if submissions else 0
        st.metric("📊 Tiến độ", f"{progress:.1f}%")
    
    if not graded_submissions:
        st.info("📊 Cần chấm ít nhất 1 bài để hiển thị thống kê!")
        return
    
    # Biểu đồ phân bố điểm
    st.write("### 📈 Phân bố điểm số")
    
    scores = [s['total_score'] for s in graded_submissions]
    max_score = exam_info['total_points']
    
    # Tạo histogram
    score_ranges = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
    score_counts = [0] * 5
    
    for score in scores:
        percentage = (score / max_score) * 100
        if percentage <= 20:
            score_counts[0] += 1
        elif percentage <= 40:
            score_counts[1] += 1
        elif percentage <= 60:
            score_counts[2] += 1
        elif percentage <= 80:
            score_counts[3] += 1
        else:
            score_counts[4] += 1
    
    chart_data = pd.DataFrame({
        'Khoảng điểm': score_ranges,
        'Số học sinh': score_counts
    })
    
    st.bar_chart(chart_data.set_index('Khoảng điểm'))
    
    # Thống kê theo câu hỏi
    st.write("### 📝 Thống kê theo câu hỏi")
    
    question_stats = calculate_question_statistics(exam_id, graded_submissions)
    
    if question_stats:
        df_stats = pd.DataFrame(question_stats)
        st.dataframe(df_stats, use_container_width=True)
    
    # Top học sinh
    st.write("### 🏆 Xếp hạng")
    
    sorted_submissions = sorted(graded_submissions, key=lambda x: x['total_score'], reverse=True)
    
    for i, submission in enumerate(sorted_submissions[:10]):
        rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        percentage = (submission['total_score'] / max_score) * 100
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.write(rank_icon)
        
        with col2:
            st.write(f"**{submission['student_name']}**")
        
        with col3:
            st.write(f"{submission['total_score']:.1f} ({percentage:.1f}%)")

def show_export_results(exam_id):
    """Xuất kết quả chấm bài"""
    st.subheader("📤 Xuất kết quả")
    
    submissions = get_exam_submissions(exam_id)
    graded_submissions = [s for s in submissions if s['status'] == 'graded']
    
    if not graded_submissions:
        st.info("📝 Chưa có bài nào được chấm để xuất kết quả!")
        return
    
    # Tùy chọn xuất
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Xuất Excel")
        
        include_details = st.checkbox("Bao gồm chi tiết từng câu", value=True)
        include_comments = st.checkbox("Bao gồm nhận xét", value=True)
        
        if st.button("📥 Tải file Excel", use_container_width=True):
            excel_data = prepare_excel_export(exam_id, graded_submissions, include_details, include_comments)
            st.download_button(
                label="💾 Download Excel",
                data=excel_data,
                file_name=f"ket_qua_cham_bai_{exam_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        st.write("### 📧 Gửi kết quả")
        
        send_to_students = st.checkbox("Gửi cho học sinh", value=True)
        send_to_parents = st.checkbox("Gửi cho phụ huynh", value=False)
        
        email_template = st.selectbox(
            "Mẫu email:",
            ["Thông báo kết quả chuẩn", "Thông báo có nhận xét", "Tùy chỉnh"]
        )
        
        if st.button("📧 Gửi email hàng loạt", use_container_width=True):
            send_bulk_results_email(exam_id, graded_submissions, send_to_students, send_to_parents, email_template)
    
    # Preview kết quả
    st.write("### 👁️ Preview kết quả")
    
    preview_data = []
    for submission in graded_submissions[:5]:  # Chỉ hiển thị 5 bài đầu
        percentage = (submission['total_score'] / submission['max_score']) * 100
        preview_data.append({
            'Học sinh': submission['student_name'],
            'Điểm': f"{submission['total_score']:.1f}/{submission['max_score']}",
            'Phần trăm': f"{percentage:.1f}%",
            'Xếp loại': get_grade_classification(percentage),
            'Nhận xét': submission.get('general_comment', '')[:50] + "..." if submission.get('general_comment') else ""
        })
    
    if preview_data:
        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True)
        
        if len(graded_submissions) > 5:
            st.caption(f"... và {len(graded_submissions) - 5} học sinh khác")

def auto_grade_multiple_choice(exam_id):
    """Chấm tự động câu trắc nghiệm và đúng/sai"""
    try:
        submissions = get_exam_submissions(exam_id)
        exam_questions = get_exam_questions(exam_id)
        
        auto_gradable_types = ['multiple_choice', 'true_false', 'short_answer']
        auto_questions = [q for q in exam_questions if q['type'] in auto_gradable_types]
        
        if not auto_questions:
            st.warning("⚠️ Đề thi này không có câu hỏi có thể chấm tự động!")
            return
        
        graded_count = 0
        
        for submission in submissions:
            if submission['status'] == 'pending':
                scores = {}
                total_auto_score = 0
                
                for question in auto_questions:
                    student_answer = next((ans for ans in submission['answers'] if ans['question_id'] == question['id']), None)
                    auto_score = calculate_auto_score(question, student_answer)
                    
                    if auto_score is not None:
                        scores[question['id']] = auto_score
                        total_auto_score += auto_score
                
                # TODO: Cập nhật database
                # update_submission_auto_scores(submission['id'], scores, total_auto_score)
                graded_count += 1
        
        st.success(f"✅ Đã chấm tự động {graded_count} bài!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Lỗi chấm tự động: {str(e)}")

def get_grade_classification(percentage):
    """Phân loại học lực theo phần trăm"""
    if percentage >= 90:
        return "Xuất sắc"
    elif percentage >= 80:
        return "Giỏi"
    elif percentage >= 70:
        return "Khá"
    elif percentage >= 50:
        return "Trung bình"
    else:
        return "Yếu"

# Mock database functions - Thay thế bằng implementation thực tế

def get_teacher_exams_for_grading(teacher_id):
    """Mock function - lấy danh sách đề thi cần chấm"""
    return [
        {
            'id': 1,
            'title': 'Kiểm tra 15 phút - Toán 10',
            'class_name': 'Lớp 10A1',
            'total_points': 10.0,
            'total_questions': 10,
            'time_limit': 15,
            'start_time': '2024-02-01T08:00:00',
            'end_time': '2024-02-01T09:00:00',
            'submission_count': 25,
            'graded_count': 10
        }
    ]

def get_exam_submissions(exam_id):
    """Mock function - lấy danh sách bài làm"""
    return [
        {
            'id': 1,
            'student_id': 1,
            'student_name': 'Nguyễn Văn A',
            'student_username': 'nguyenvana',
            'status': 'pending',
            'submitted_at': '2024-02-01T08:30:00',
            'start_time': '2024-02-01T08:15:00',
            'total_score': None,
            'max_score': 10.0,
            'answers': []
        }
    ]

def get_exam_questions(exam_id):
    """Mock function - lấy câu hỏi của đề thi"""
    return [
        {
            'id': 1,
            'type': 'multiple_choice',
            'question': 'Câu hỏi trắc nghiệm mẫu?',
            'points': 1.0,
            'options': ['Đáp án A', 'Đáp án B', 'Đáp án C', 'Đáp án D'],
            'correct_answer': 'A'
        }
    ]

def get_exam_info(exam_id):
    """Mock function - lấy thông tin đề thi"""
    return {
        'id': exam_id,
        'title': 'Kiểm tra mẫu',
        'total_points': 10.0,
        'total_questions': 10
    }

def calculate_question_statistics(exam_id, graded_submissions):
    """Tính thống kê theo câu hỏi"""
    # Mock implementation
    return [
        {
            'Câu': 1,
            'Loại': 'Trắc nghiệm',
            'Điểm TB': 0.8,
            'Tỷ lệ đúng': '80%',
            'Độ khó': 'Dễ'
        }
    ]

def prepare_excel_export(exam_id, submissions, include_details, include_comments):
    """Chuẩn bị dữ liệu xuất Excel"""
    # Mock implementation
    data = []
    for submission in submissions:
        row = {
            'Học sinh': submission['student_name'],
            'Username': submission['student_username'],
            'Điểm': submission['total_score'],
            'Phần trăm': (submission['total_score'] / submission['max_score']) * 100
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    excel_buffer = pd.io.common.BytesIO()
    df.to_excel(excel_buffer, index=False)
    return excel_buffer.getvalue()

def send_bulk_results_email(exam_id, submissions, send_to_students, send_to_parents, template):
    """Gửi email kết quả hàng loạt"""
    # Mock implementation
    st.success(f"📧 Đã gửi email cho {len(submissions)} học sinh!")

def export_grading_report(exam_id):
    """Xuất báo cáo chấm bài"""
    st.info("📊 Tính năng xuất báo cáo đang được phát triển...")

def send_results_email(exam_id):
    """Gửi kết quả qua email"""
    st.info("📧 Tính năng gửi email đang được phát triển...")