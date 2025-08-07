

import streamlit as st
import json
import base64
from datetime import datetime, timezone
from database.supabase_models import get_database
from auth.login import get_current_user
from core.grading_logic import calculate_auto_score, run_essay_auto_grading
# Import hàm xem kết quả từ module khác để chuyển hướng
from .view_results import show_exam_result_detail

def show_take_exam():
    """Hiển thị và thực hiện bài thi"""
    st.header("📝 Làm bài thi")
    
    user = get_current_user()
    db = get_database()
    
    # Xử lý làm bài thi
    if st.session_state.get("taking_exam") and st.session_state.get("selected_exam_id"):
        show_exam_interface(user, db)
        return
    
    # Xử lý xem kết quả (nếu người dùng bấm vào từ trang này)
    if st.session_state.get("view_exam_result") and st.session_state.get("selected_exam_id"):
        show_exam_result_detail(user, db)
        return

    # Nếu chưa chọn lớp, hiển thị danh sách lớp
    if not st.session_state.get("selected_class_id"):
        show_class_selection_for_exam(user, db)
        return
    
    class_id = st.session_state.selected_class_id
    
    try:
        exams = db.client.table('exams').select('*, classes:class_id (ten_lop)').eq('class_id', class_id).eq('is_published', True).execute()
        
        available_exams = []
        for exam in exams.data or []:
            now_utc = datetime.now(timezone.utc)
            start_time_str = exam.get('start_time')
            end_time_str = exam.get('end_time')
            start_time_utc = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')) if start_time_str else None
            end_time_utc = datetime.fromisoformat(end_time_str.replace('Z', '+00:00')) if end_time_str else None
            
            submission = db.get_student_submission(exam['id'], user['id'])
            
            exam['is_available'] = True
            exam['status'] = "Có thể làm"
            exam['has_submitted'] = bool(submission)
            
            if submission:
                exam['status'] = "Đã nộp"
                exam['submission_score'] = submission.get('score')
                exam['is_graded'] = submission.get('is_graded', False)
            elif start_time_utc and now_utc < start_time_utc:
                exam['status'] = "Chưa mở"
                exam['is_available'] = False
            elif end_time_utc and now_utc > end_time_utc:
                exam['status'] = "Đã đóng"
                exam['is_available'] = False
            
            available_exams.append(exam)
        
        if not available_exams:
            st.info("📝 Lớp này chưa có đề thi nào!")
            if st.button("⬅️ Quay lại danh sách lớp"):
                del st.session_state.selected_class_id
                st.session_state.current_page = "my_classes"
                st.rerun()
            return
        
        st.subheader(f"📚 Đề thi lớp: {available_exams[0]['classes']['ten_lop']}")
        if st.button("⬅️ Quay lại danh sách lớp"):
            del st.session_state.selected_class_id
            st.session_state.current_page = "my_classes"
            st.rerun()
        st.divider()
        
        for exam in available_exams:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"### 📝 {exam['title']}")
                    st.write(f"⏱️ Thời gian: {exam['time_limit']} phút | 📊 Tổng điểm: {exam['total_points']}")
                with col2:
                    status_color = {"Có thể làm": "🟢", "Đã nộp": "✅", "Chưa mở": "🟡", "Đã đóng": "🔴"}
                    st.write(f"{status_color.get(exam['status'], '❓')} {exam['status']}")
                    if exam['has_submitted'] and exam['is_graded'] and exam.get('submission_score') is not None:
                        score_percent = (exam['submission_score'] / exam['total_points']) * 100 if exam['total_points'] > 0 else 0
                        st.write(f"📊 Điểm: {exam['submission_score']:.1f}/{exam['total_points']} ({score_percent:.1f}%)")
                with col3:
                    if exam['has_submitted']:
                        if st.button("👁️ Xem kết quả", key=f"view_result_{exam['id']}"):
                            st.session_state.selected_exam_id = exam['id']
                            st.session_state.current_page = "view_results" # Chuyển trang
                            st.rerun()
                    elif exam['is_available']:
                        if st.button("📝 Làm bài", key=f"take_exam_{exam['id']}"):
                            st.session_state.selected_exam_id = exam['id']
                            st.session_state.taking_exam = True
                            st.session_state.exam_start_time = datetime.now(timezone.utc).isoformat()
                            st.rerun()
                    else:
                        st.button("🚫", disabled=True, key=f"disabled_{exam['id']}")
                st.divider()

    except Exception as e:
        st.error(f"❌ Lỗi lấy danh sách đề thi: {str(e)}")

def show_class_selection_for_exam(user, db):
    st.subheader("📚 Chọn lớp để xem đề thi")
    classes = db.get_classes_by_student(user['id'])
    if not classes:
        st.info("📚 Bạn chưa tham gia lớp học nào!")
        return
    for class_info in classes:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**📚 {class_info['ten_lop']}** ({class_info['ma_lop']})")
        with col2:
            if st.button("➡️ Xem đề thi", key=f"select_class_{class_info['id']}"):
                st.session_state.selected_class_id = class_info['id']
                st.rerun()

def show_exam_interface(user, db):
    exam_id = st.session_state.selected_exam_id
    exam = db.get_exam_by_id(exam_id)
    if not exam:
        st.error("❌ Không tìm thấy đề thi!")
        return
    
    now_utc = datetime.now(timezone.utc)
    start_time_iso = st.session_state.get('exam_start_time')
    if start_time_iso:
        start_time_utc = datetime.fromisoformat(start_time_iso)
    else:
        start_time_utc = now_utc
        st.session_state.exam_start_time = now_utc.isoformat()

    time_elapsed_seconds = int((now_utc - start_time_utc).total_seconds())
    time_limit_seconds = exam.get('time_limit', 60) * 60
    time_remaining_sec = max(0, time_limit_seconds - time_elapsed_seconds)
    time_remaining_min = int(time_remaining_sec // 60)

    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    if time_remaining_sec <= 0 and not st.session_state.form_submitted:
        st.error("⏰ Đã hết thời gian làm bài! Hệ thống sẽ tự động nộp bài của bạn.")
        # Đây là nơi logic tự động nộp bài sẽ được gọi
        # st.session_state.form_submitted = True # Ngăn nộp lại
        # submit_exam(...)
        st.button("Quay về trang đề thi")
        st.stop()
    if 'submission_successful' not in st.session_state:
        st.session_state.submission_successful = False

    if st.session_state.get('submission_successful'):
        st.success("✅ Đã nộp bài thành công!")
        st.balloons()
        
        # Hiển thị kết quả tạm thời ngay lập tức
        from .view_results import show_exam_result_detail
        st.info("Dưới đây là kết quả phần trắc nghiệm của bạn. Phần tự luận (nếu có) đang được chấm.")
        
        # Giả lập user và db object để truyền vào hàm xem kết quả
        user = get_current_user()
        db = get_database()
        show_exam_result_detail(user, db, submission_id=st.session_state.last_submission_id)

        if st.button("⬅️ Quay lại trang đề thi"):
            # Reset các state
            st.session_state.taking_exam = False
            del st.session_state.submission_successful
            if 'last_submission_id' in st.session_state: del st.session_state.last_submission_id
            st.rerun()
        return  
    # Header
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3>📝 {exam['title']}</h3>
        <p>⏱️ Thời gian còn lại: <span id="timer">{time_remaining_min}</span> phút | 📊 Tổng điểm: {exam['total_points']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Hướng dẫn làm bài
    if exam.get('instructions'):
        with st.expander("📋 Hướng dẫn làm bài", expanded=False):
            st.markdown(exam['instructions'])
    
    # Form làm bài
    with st.form("exam_form"):
        answers = []
        
        for i, question in enumerate(exam['questions']):
            st.markdown(f"### Câu {i+1}: ({question['points']} điểm)")
            st.markdown(question['question'])
            
            if question.get('image_data'):
                try:
                    image_bytes = base64.b64decode(question['image_data'])
                    st.image(image_bytes, caption=f"Hình ảnh câu {i+1}", width=300)
                except:
                    st.caption("🖼️ Có hình ảnh đính kèm")
            
            answer = {}
            answer['question_id'] = question.get('question_id', i+1)
            
            if question['type'] == 'multiple_choice':
                options_dict = {f"{chr(ord('A')+k)}": v for k, v in enumerate(question['options'])}
                selected = st.radio(
                    "Chọn đáp án:",
                    options=options_dict.keys(),
                    format_func=lambda x: f"{x}. {options_dict[x]}",
                    key=f"mc_{i}",
                    index=None
                )
                answer['selected_option'] = selected
            
            elif question['type'] == 'true_false':
                if question.get('statements'):
                    st.write("**Tích vào phương án Đúng:**")
                    selected_answers = []
                    for stmt in question['statements']:
                        is_true = st.checkbox(
                            f"{stmt['letter']}) {stmt['text']}",
                            key=f"tf_{i}_{stmt['letter']}"
                        )
                        if is_true:
                            selected_answers.append(stmt['letter'])
                    answer['selected_answers'] = selected_answers
                else:
                    selected = st.radio(
                        "Chọn đáp án:",
                        options=['Đúng', 'Sai'],
                        key=f"tf_simple_{i}",
                        index=None
                    )
                    answer['selected_option'] = selected
            
            elif question['type'] == 'short_answer':
                text_answer = st.text_input(
                    "Câu trả lời:",
                    key=f"sa_{i}",
                    placeholder="Nhập câu trả lời ngắn..."
                )
                answer['answer_text'] = text_answer
            
            elif question['type'] == 'essay':
                text_answer = st.text_area(
                    "Câu trả lời:",
                    key=f"essay_{i}",
                    placeholder="Nhập câu trả lời tự luận...",
                    height=150
                )
                answer['answer_text'] = text_answer
                
                if question.get('requires_image'):
                    uploaded_file = st.file_uploader(
                        "Hoặc chụp ảnh bài làm:",
                        type=['png', 'jpg', 'jpeg'],
                        key=f"essay_img_{i}"
                    )
                    if uploaded_file:
                        image_data = base64.b64encode(uploaded_file.read()).decode()
                        answer['image_data'] = image_data
            
            answers.append(answer)
            st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("📤 Nộp bài", use_container_width=True, type="primary")
            if submitted:
                st.session_state.form_submitted = True
                submit_exam(user['id'], exam_id, answers, time_elapsed_seconds, exam['total_points'])
        
        with col2:
            if st.form_submit_button("❌ Hủy bài thi", use_container_width=True):
                st.session_state.taking_exam = False
                st.rerun()

# ==========================================
# ĐÂY LÀ HÀM ĐƯỢC CẢI THIỆN
# ==========================================
def submit_exam(student_id: str, exam_id: str, answers: list, time_taken: int, max_score: float):
    """
    Nộp bài, chấm trắc nghiệm ngay lập tức và kích hoạt chấm tự luận.
    """
    db = get_database()
    
    try:
        exam = db.get_exam_by_id(exam_id)
        if not exam:
            st.error("Lỗi: Không tìm thấy đề thi để chấm điểm."); return

        trac_nghiem_score = 0
        question_scores_map = {}
        has_essay = False

        for q in exam.get('questions', []):
            q_id_str = str(q.get('question_id'))
            student_answer = next((ans for ans in answers if ans.get('question_id') == q['question_id']), None)
            
            if q.get('type') in ['multiple_choice', 'true_false', 'short_answer']:
                # Dùng hàm calculate_auto_score đã được import
                score = calculate_auto_score(q, student_answer) 
                trac_nghiem_score += score
                question_scores_map[q_id_str] = score
            elif q.get('type') == 'essay':
                has_essay = True
                question_scores_map[q_id_str] = 0

        submission_id = db.create_submission_with_partial_grade(
            exam_id=exam_id, student_id=student_id, answers=answers, 
            time_taken=time_taken, max_score=max_score,
            trac_nghiem_score=trac_nghiem_score,
            question_scores=question_scores_map,
            has_essay=has_essay
        )

        if submission_id:
            if has_essay:
                # Dùng hàm run_essay_auto_grading đã được import
                run_essay_auto_grading(submission_id)

            st.session_state.submission_successful = True
            st.session_state.last_submission_id = submission_id
            st.rerun()
        else:
            st.error("❌ Lỗi khi lưu bài nộp vào hệ thống.")

    except Exception as e:
        st.error(f"❌ Đã xảy ra lỗi nghiêm trọng khi nộp bài: {e}")
        st.exception(e)

def auto_grade_submission(submission_id: str, exam_id: str, answers: list):
    """Tự động chấm điểm các câu trắc nghiệm"""
    db = get_database()
    
    try:
        exam = db.get_exam_by_id(exam_id)
        if not exam:
            return
        
        question_scores = {}
        total_score = 0
        
        for i, question in enumerate(exam['questions']):
            question_id_str = str(question.get('question_id', i+1))
            student_answer = next((a for a in answers if str(a['question_id']) == question_id_str), None)
            
            if not student_answer:
                question_scores[question_id_str] = 0
                continue
            
            score = 0
            
            if question['type'] == 'multiple_choice':
                if student_answer.get('selected_option') == question.get('correct_answer'):
                    score = question['points']
            
            elif question['type'] == 'true_false':
                if question.get('statements'):
                    correct_letters = {stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)}
                    selected_letters = set(student_answer.get('selected_answers', []))
                    if correct_letters == selected_letters:
                        score = question['points']
                else:
                    correct_answer_bool = question.get('correct_answer')
                    correct_answer_str = "Đúng" if correct_answer_bool else "Sai"
                    if student_answer.get('selected_option') == correct_answer_str:
                        score = question['points']
            
            elif question['type'] == 'short_answer':
                student_text = student_answer.get('answer_text', '').strip()
                correct_answers = question.get('sample_answers', [])
                case_sensitive = question.get('case_sensitive', False)
                
                if not case_sensitive:
                    student_text = student_text.lower()
                    correct_answers = [ans.lower() for ans in correct_answers]
                
                if student_text in correct_answers:
                    score = question['points']
            
            question_scores[question_id_str] = score
            total_score += score
        
        # Cập nhật điểm vào DB
        db.update_submission_grade(submission_id, total_score, question_scores)
        
    except Exception as e:
        # Ném lỗi ra để hàm submit_exam có thể bắt và hiển thị
        raise Exception(f"Lỗi trong quá trình tự động chấm điểm: {e}")

