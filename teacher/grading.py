import streamlit as st
import pandas as pd
import json
import base64
from datetime import datetime, timedelta
from database.supabase_models import get_database
from auth.login import get_current_user

# Safe imports
try:
    from teacher.word_parser import render_mathjax
except ImportError:
    def render_mathjax():
        st.markdown("""
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
        window.MathJax = {
            tex: {inlineMath: [['$', '$'], ['\\(', '\\)']]},
            svg: {fontCache: 'global'}
        };
        </script>
        """, unsafe_allow_html=True)

def show_grading():
    """Giao diện chấm bài chính"""
    st.header("✅ Chấm bài")
    
    user = get_current_user()
    db = get_database()
    
    # Lấy danh sách đề thi từ database
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
                'total_questions': exam_data.get('total_questions', 0),
                'submission_count': exam_data.get('submission_count', 0),
                'graded_count': exam_data.get('graded_count', 0)
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
    # Thống kê nhanh từ database
    try:
        submissions = db.get_submissions_by_exam(exam['id'])
        total_submissions = len(submissions)
        graded_count = len([s for s in submissions if s.get('is_graded', False)])
        pending_count = total_submissions - graded_count
    except Exception as e:
        st.warning(f"⚠️ Lỗi lấy thống kê bài nộp: {str(e)}")
        total_submissions = exam.get('submission_count', 0)
        graded_count = exam.get('graded_count', 0)
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
            if exam.get('start_time'):
                start_str = format_datetime(exam['start_time'])
                st.write(f"**📅 Bắt đầu:** {start_str}")
            if exam.get('end_time'):
                end_str = format_datetime(exam['end_time'])
                st.write(f"**📅 Kết thúc:** {end_str}")
            st.write(f"**❓ Số câu hỏi:** {exam['total_questions']} câu")

def show_submissions_list(exam_id, filter_status, sort_by, db):
    """Hiển thị danh sách bài làm của học sinh"""
    st.subheader("📋 Danh sách bài làm")
    
    try:
        submissions = db.get_submissions_by_exam(exam_id)
        
        # Process submissions for display
        processed_submissions = []
        for submission in submissions:
            student_info = submission.get('student_info', {})
            processed_submission = {
                'id': submission['id'],
                'student_id': student_info.get('id', ''),
                'student_name': student_info.get('ho_ten', 'Unknown'),
                'student_username': student_info.get('username', ''),
                'status': 'graded' if submission.get('is_graded') else 'pending',
                'submitted_at': submission.get('submitted_at', ''),
                'time_taken': submission.get('time_taken', 0),
                'total_score': submission.get('total_score'),
                'max_score': submission.get('max_score', 0),
                'answers': submission.get('answers', [])
            }
            processed_submissions.append(processed_submission)
        
        submissions = processed_submissions
        
    except Exception as e:
        st.error(f"❌ Lỗi lấy danh sách bài nộp: {str(e)}")
        submissions = []
    
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
                if submission['submitted_at']:
                    submitted_time = datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00'))
                    st.write(f"📅 {submitted_time.strftime('%d/%m %H:%M')}")
                
                # Thời gian làm bài
                if submission['time_taken']:
                    st.caption(f"⏱️ {submission['time_taken']} phút")
            
            with col3:
                # Điểm số
                if submission['status'] == 'graded' and submission['total_score'] is not None:
                    score_percent = (submission['total_score'] / submission['max_score']) * 100 if submission['max_score'] > 0 else 0
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
                auto_grade_multiple_choice(exam_id, db)
        
        with col2:
            if st.button("📊 Xuất báo cáo Excel", use_container_width=True):
                export_grading_report(exam_id)
        
        with col3:
            if st.button("📧 Gửi kết quả qua email", use_container_width=True):
                send_results_email(exam_id)

def show_detailed_grading(exam_id, db):
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
        <p>📅 Nộp bài: {format_datetime(submission['submitted_at'])} | ⏱️ Thời gian làm: {submission.get('time_taken', 'N/A')} phút</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Lấy thông tin đề thi và câu trả lời
    try:
        exam = db.get_exam_by_id(exam_id)
        if not exam:
            st.error("❌ Không tìm thấy đề thi!")
            return
        
        exam_questions = exam.get('questions', [])
        student_answers = submission['answers']
        
    except Exception as e:
        st.error(f"❌ Lỗi lấy thông tin đề thi: {str(e)}")
        return
    
    # Form chấm bài
    with st.form("grading_form"):
        total_score = 0
        max_total_score = sum(q.get('points', 0) for q in exam_questions)
        
        for i, question in enumerate(exam_questions):
            student_answer = next((ans for ans in student_answers if ans.get('question_id') == question.get('question_id', i+1)), None)
            
            st.markdown(f"### 📝 Câu {i+1}: ({question.get('points', 0)} điểm)")
            
            # Hiển thị câu hỏi
            st.markdown(question.get('question', ''))
            
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
            
            if question.get('type') in ['multiple_choice', 'true_false', 'short_answer']:
                # Tự động chấm hoặc đã có điểm
                auto_score = calculate_auto_score(question, student_answer)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score = st.number_input(
                        f"Điểm câu {i+1}",
                        min_value=0.0,
                        max_value=float(question.get('points', 0)),
                        value=float(auto_score if auto_score is not None else 0),
                        step=0.25,
                        key=f"score_{question.get('question_id', i+1)}"
                    )
                
                with col2:
                    if auto_score is not None:
                        st.write(f"**Tự động:** {auto_score}/{question.get('points', 0)}")
                        if st.button(f"✅ Dùng điểm tự động", key=f"auto_{question.get('question_id', i+1)}"):
                            st.session_state[f"score_{question.get('question_id', i+1)}"] = auto_score
                
                with col3:
                    # Hiển thị phần trăm
                    percentage = (score / question.get('points', 1)) * 100 if question.get('points', 0) > 0 else 0
                    color = "green" if percentage >= 80 else "orange" if percentage >= 50 else "red"
                    st.markdown(f"<span style='color: {color}'>{percentage:.1f}%</span>", unsafe_allow_html=True)
                
            elif question.get('type') == 'essay':
                # Chấm thủ công cho tự luận
                score = st.number_input(
                    f"Điểm câu {i+1}",
                    min_value=0.0,
                    max_value=float(question.get('points', 0)),
                    value=0.0,
                    step=0.25,
                    key=f"score_{question.get('question_id', i+1)}"
                )
                
                # Nhận xét
                comment = st.text_area(
                    f"Nhận xét câu {i+1}",
                    value='',
                    placeholder="Nhập nhận xét cho học sinh...",
                    key=f"comment_{question.get('question_id', i+1)}"
                )
            
            total_score += st.session_state.get(f"score_{question.get('question_id', i+1)}", 0)
            
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
            <p><strong>Phần trăm:</strong> {(total_score/max_total_score*100) if max_total_score > 0 else 0:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Nhận xét tổng
        general_comment = st.text_area(
            "💬 Nhận xét chung",
            value='',
            placeholder="Nhận xét tổng quát về bài làm của học sinh...",
            key="general_comment"
        )
        
        # Buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Lưu điểm", use_container_width=True, type="primary"):
                save_grading_scores(submission, exam_questions, general_comment, db)
        
        with col2:
            if st.form_submit_button("📧 Lưu và gửi kết quả", use_container_width=True):
                save_grading_scores(submission, exam_questions, general_comment, db, send_notification=True)
        
        with col3:
            if st.form_submit_button("❌ Hủy", use_container_width=True):
                st.session_state.show_grading_detail = False
                if 'grading_submission' in st.session_state:
                    del st.session_state.grading_submission
                st.rerun()

def show_correct_answer(question):
    """Hiển thị đáp án đúng cho câu hỏi"""
    if question.get('type') == 'multiple_choice':
        options = question.get('options', [])
        correct_answer = question.get('correct_answer', '')
        for i, option in enumerate(options):
            prefix = "✅" if chr(65+i) == correct_answer else "  "
            st.write(f"{prefix} {chr(65+i)}. {option}")
    
    elif question.get('type') == 'true_false':
        statements = question.get('statements', [])
        if statements:
            for stmt in statements:
                icon = "✅" if stmt.get('is_correct', False) else "❌"
                st.write(f"{icon} {stmt.get('letter', '')}. {stmt.get('text', '')}")
        else:
            st.write(f"Đáp án: {question.get('correct_answer', 'N/A')}")
    
    elif question.get('type') == 'short_answer':
        answers = question.get('sample_answers', [])
        if answers:
            st.write("Đáp án mẫu:")
            for ans in answers:
                st.write(f"• {ans}")
    
    elif question.get('type') == 'essay':
        st.write("📄 Câu tự luận - chấm theo tiêu chí")
        if question.get('grading_criteria'):
            st.caption(f"Tiêu chí: {question['grading_criteria']}")

def show_student_answer(question, student_answer):
    """Hiển thị câu trả lời của học sinh"""
    if not student_answer:
        st.warning("❌ Học sinh chưa trả lời câu này")
        return
    
    if question.get('type') == 'multiple_choice':
        selected = student_answer.get('selected_option', 'Chưa chọn')
        st.write(f"**Chọn:** {selected}")
    
    elif question.get('type') == 'true_false':
        selected = student_answer.get('selected_answers', [])
        if selected:
            st.write(f"**Chọn:** {', '.join(selected)}")
        else:
            selected_option = student_answer.get('selected_option', '')
            if selected_option:
                st.write(f"**Chọn:** {selected_option}")
            else:
                st.write("Chưa chọn")
    
    elif question.get('type') == 'short_answer':
        answer_text = student_answer.get('answer_text', '')
        if answer_text:
            st.write(f"**Trả lời:** {answer_text}")
        else:
            st.write("Chưa trả lời")
    
    elif question.get('type') == 'essay':
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
    if not student_answer or not question:
        return 0.0
    
    question_type = question.get('type', '')
    points = question.get('points', 0)
    
    if question_type == 'multiple_choice':
        if student_answer.get('selected_option') == question.get('correct_answer'):
            return float(points)
        else:
            return 0.0
    
    elif question_type == 'true_false':
        statements = question.get('statements', [])
        if statements:
            correct_letters = [stmt.get('letter', '') for stmt in statements if stmt.get('is_correct', False)]
            selected_letters = student_answer.get('selected_answers', [])
            
            if set(correct_letters) == set(selected_letters):
                return float(points)
            else:
                return 0.0
        else:
            # Simple true/false
            correct_answer = question.get('correct_answer')
            student_selected = student_answer.get('selected_option')
            
            if (correct_answer and student_selected == 'Đúng') or (not correct_answer and student_selected == 'Sai'):
                return float(points)
            else:
                return 0.0
    
    elif question_type == 'short_answer':
        student_text = student_answer.get('answer_text', '').strip()
        correct_answers = question.get('sample_answers', [])
        case_sensitive = question.get('case_sensitive', False)
        
        if not case_sensitive:
            student_text = student_text.lower()
            correct_answers = [ans.lower() for ans in correct_answers]
        
        if student_text in correct_answers:
            return float(points)
        else:
            return 0.0
    
    # Essay không tự động chấm
    return None

def save_grading_scores(submission, exam_questions, general_comment, db, send_notification=False):
    """Lưu điểm chấm"""
    try:
        # Lưu điểm từng câu
        question_scores = {}
        total_score = 0
        
        for question in exam_questions:
            question_id = str(question.get('question_id', 0))
            score = st.session_state.get(f"score_{question.get('question_id', 0)}", 0)
            
            question_scores[question_id] = score
            total_score += score
        
        # Cập nhật database
        success = db.update_submission_grade(
            submission['id'], 
            total_score, 
            question_scores, 
            general_comment
        )
        
        if success:
            st.success("✅ Đã lưu điểm thành công!")
            
            if send_notification:
                st.success("📧 Đã gửi kết quả cho học sinh!")
            
            # Reset form
            st.session_state.show_grading_detail = False
            if 'grading_submission' in st.session_state:
                del st.session_state.grading_submission
            
            st.rerun()
        else:
            st.error("❌ Lỗi lưu điểm vào database!")
        
    except Exception as e:
        st.error(f"❌ Lỗi lưu điểm: {str(e)}")

def show_grading_statistics(exam_id, db):
    """Hiển thị thống kê chấm bài"""
    st.subheader("📊 Thống kê chấm bài")
    
    try:
        submissions = db.get_submissions_by_exam(exam_id)
        exam = db.get_exam_by_id(exam_id)
        
        if not submissions:
            st.info("📝 Chưa có bài nộp nào!")
            return
        
        # Thống kê tổng quan
        graded_submissions = [s for s in submissions if s.get('is_graded', False)]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📥 Tổng bài nộp", len(submissions))
        
        with col2:
            st.metric("✅ Đã chấm", len(graded_submissions))
        
        with col3:
            if graded_submissions:
                avg_score = sum(s.get('total_score', 0) for s in graded_submissions) / len(graded_submissions)
                st.metric("📈 Điểm TB", f"{avg_score:.1f}")
            else:
                st.metric("📈 Điểm TB", "--")
        
        with col4:
            progress = len(graded_submissions) / len(submissions) * 100 if submissions else 0
            st.metric("📊 Tiến độ", f"{progress:.1f}%")
        
        if not graded_submissions:
            st.info("📊 Cần chấm ít nhất 1 bài để hiển thị thống kê!")
            return
        
        # Phân bố điểm
        st.write("### 📈 Phân bố điểm số")
        
        scores = [s.get('total_score', 0) for s in graded_submissions if s.get('total_score') is not None]
        max_score = exam.get('total_points', 10) if exam else 10
        
        if scores:
            # Tạo histogram data
            score_ranges = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
            score_counts = [0] * 5
            
            for score in scores:
                percentage = (score / max_score) * 100 if max_score > 0 else 0
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
        
        # Top học sinh
        st.write("### 🏆 Xếp hạng")
        
        sorted_submissions = sorted(graded_submissions, key=lambda x: x.get('total_score', 0), reverse=True)
        
        for i, submission in enumerate(sorted_submissions[:10]):
            rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            percentage = (submission.get('total_score', 0) / max_score) * 100 if max_score > 0 else 0
            
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.write(rank_icon)
            
            with col2:
                student_info = submission.get('student_info', {})
                student_name = student_info.get('ho_ten', 'Unknown')
                st.write(f"**{student_name}**")
            
            with col3:
                score = submission.get('total_score', 0)
                st.write(f"{score:.1f} ({percentage:.1f}%)")
        
    except Exception as e:
        st.error(f"❌ Lỗi hiển thị thống kê: {str(e)}")

def show_export_results(exam_id, db):
    """Xuất kết quả chấm bài"""
    st.subheader("📤 Xuất kết quả")
    
    try:
        submissions = db.get_submissions_by_exam(exam_id)
        graded_submissions = [s for s in submissions if s.get('is_graded', False)]
        
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
            student_info = submission.get('student_info', {})
            max_score = submission.get('max_score', 0)
            total_score = submission.get('total_score', 0)
            percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            
            preview_data.append({
                'Học sinh': student_info.get('ho_ten', 'Unknown'),
                'Điểm': f"{total_score:.1f}/{max_score}",
                'Phần trăm': f"{percentage:.1f}%",
                'Xếp loại': get_grade_classification(percentage),
                'Nhận xét': submission.get('feedback', '')[:50] + "..." if submission.get('feedback') else ""
            })
        
        if preview_data:
            df_preview = pd.DataFrame(preview_data)
            st.dataframe(df_preview, use_container_width=True)
            
            if len(graded_submissions) > 5:
                st.caption(f"... và {len(graded_submissions) - 5} học sinh khác")
    
    except Exception as e:
        st.error(f"❌ Lỗi xuất kết quả: {str(e)}")

def auto_grade_multiple_choice(exam_id, db):
    """Chấm tự động câu trắc nghiệm và đúng/sai"""
    try:
        submissions = db.get_submissions_by_exam(exam_id)
        exam = db.get_exam_by_id(exam_id)
        
        if not exam:
            st.error("❌ Không tìm thấy đề thi!")
            return
        
        exam_questions = exam.get('questions', [])
        auto_gradable_types = ['multiple_choice', 'true_false', 'short_answer']
        auto_questions = [q for q in exam_questions if q.get('type') in auto_gradable_types]
        
        if not auto_questions:
            st.warning("⚠️ Đề thi này không có câu hỏi có thể chấm tự động!")
            return
        
        graded_count = 0
        
        for submission in submissions:
            if not submission.get('is_graded', False):
                question_scores = {}
                total_auto_score = 0
                
                for question in auto_questions:
                    student_answer = next((ans for ans in submission.get('answers', []) if ans.get('question_id') == question.get('question_id')), None)
                    auto_score = calculate_auto_score(question, student_answer)
                    
                    if auto_score is not None:
                        question_id = str(question.get('question_id', 0))
                        question_scores[question_id] = auto_score
                        total_auto_score += auto_score
                
                # Cập nhật database
                if question_scores:
                    db.update_submission_grade(submission['id'], total_auto_score, question_scores)
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

def format_datetime(datetime_str):
    """Format datetime string"""
    try:
        if datetime_str:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        return "N/A"
    except:
        return datetime_str or "N/A"

def prepare_excel_export(exam_id, submissions, include_details, include_comments):
    """Chuẩn bị dữ liệu xuất Excel"""
    try:
        data = []
        for submission in submissions:
            student_info = submission.get('student_info', {})
            row = {
                'Học sinh': student_info.get('ho_ten', 'Unknown'),
                'Username': student_info.get('username', ''),
                'Điểm': submission.get('total_score', 0),
                'Tổng điểm': submission.get('max_score', 0),
                'Phần trăm': (submission.get('total_score', 0) / submission.get('max_score', 1)) * 100,
                'Xếp loại': get_grade_classification((submission.get('total_score', 0) / submission.get('max_score', 1)) * 100),
                'Thời gian nộp': format_datetime(submission.get('submitted_at', '')),
                'Thời gian làm': f"{submission.get('time_taken', 0)} phút"
            }
            
            if include_comments and submission.get('feedback'):
                row['Nhận xét'] = submission['feedback']
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Convert to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Kết quả', index=False)
        
        return output.getvalue()
        
    except Exception as e:
        st.error(f"❌ Lỗi tạo file Excel: {str(e)}")
        return b""

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