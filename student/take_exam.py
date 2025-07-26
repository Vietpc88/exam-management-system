import streamlit as st
import json
import os
from datetime import datetime, timedelta
from database.models import *
from auth.login import get_current_user
from config import Config

def student_dashboard():
    """Dashboard chính của học sinh"""
    current_page = st.session_state.get("current_page", "my_classes")
    
    if current_page == "my_classes":
        show_my_classes()
    elif current_page == "take_exam":
        show_available_exams()
    elif current_page == "view_results":
        show_my_results()

def show_my_classes():
    """Hiển thị lớp học của học sinh"""
    st.header("📚 Lớp học của tôi")
    
    user = get_current_user()
    classes = get_student_classes(user['id'])
    
    if not classes:
        st.info("""
            📚 Bạn chưa tham gia lớp học nào.
            
            **Cách tham gia lớp:**
            1. Liên hệ giáo viên để được thêm vào lớp
            2. Giáo viên sẽ thêm bạn vào lớp học
        """)
        return
    
    for class_info in classes:
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 2])
            
            with col1:
                st.write(f"**📋 {class_info['name']}**")
                if class_info['description']:
                    st.caption(class_info['description'])
                st.caption(f"👨‍🏫 Giáo viên: {class_info['teacher_name']}")
            
            with col2:
                # Thống kê đề thi
                exams = get_exams_by_class(class_info['id'])
                available_exams = [e for e in exams if is_exam_available_for_student(e, user['id'])]
                st.metric("📝 Đề thi khả dụng", len(available_exams))
            
            with col3:
                if st.button(f"👁️ Xem đề thi", key=f"view_class_exams_{class_info['id']}"):
                    show_class_exams_for_student(class_info)
            
            st.divider()

def show_available_exams():
    """Hiển thị đề thi có thể làm"""
    st.header("📝 Đề thi có thể làm")
    
    user = get_current_user()
    exams = get_available_exams_for_student(user['id'])
    
    if not exams:
        st.info("📝 Hiện tại không có đề thi nào để làm.")
        return
    
    # Phân loại đề thi
    available_exams = []
    completed_exams = []
    upcoming_exams = []
    expired_exams = []
    
    for exam in exams:
        if exam['submission_id']:  # Đã làm
            completed_exams.append(exam)
        elif is_exam_available_now(exam):  # Có thể làm ngay
            available_exams.append(exam)
        elif is_exam_upcoming(exam):  # Sắp mở
            upcoming_exams.append(exam)
        else:  # Đã hết hạn
            expired_exams.append(exam)
    
    # Hiển thị đề thi có thể làm ngay
    if available_exams:
        st.subheader("🟢 Có thể làm ngay")
        for exam in available_exams:
            show_exam_card(exam, "available")
    
    # Hiển thị đề thi sắp mở
    if upcoming_exams:
        st.subheader("🟡 Sắp mở")
        for exam in upcoming_exams:
            show_exam_card(exam, "upcoming")
    
    # Hiển thị đề thi đã làm
    if completed_exams:
        st.subheader("✅ Đã hoàn thành")
        for exam in completed_exams:
            show_exam_card(exam, "completed")
    
    # Hiển thị đề thi đã hết hạn
    if expired_exams:
        st.subheader("🔴 Đã hết hạn")
        for exam in expired_exams:
            show_exam_card(exam, "expired")

def show_exam_card(exam, status):
    """Hiển thị card đề thi"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            st.write(f"**📝 {exam['title']}**")
            if exam['description']:
                st.caption(exam['description'])
            st.caption(f"📚 Lớp: {exam['class_name']} | 👨‍🏫 GV: {exam['teacher_name']}")
        
        with col2:
            # Thời gian
            if exam['start_time']:
                start_time = datetime.fromisoformat(exam['start_time'])
                st.caption(f"⏰ Bắt đầu: {start_time.strftime('%d/%m/%Y %H:%M')}")
            if exam['end_time']:
                end_time = datetime.fromisoformat(exam['end_time'])
                st.caption(f"🔚 Kết thúc: {end_time.strftime('%d/%m/%Y %H:%M')}")
            st.caption(f"⏱️ Thời gian: {exam['time_limit']} phút")
        
        with col3:
            # Trạng thái
            if status == "available":
                st.success("🟢 Có thể làm")
            elif status == "upcoming":
                st.warning("🟡 Sắp mở")
            elif status == "completed":
                if exam['total_score'] is not None:
                    st.info(f"✅ {exam['total_score']:.1f}/{exam['max_score']:.1f}")
                else:
                    st.info("✅ Đã nộp")
            else:
                st.error("🔴 Hết hạn")
        
        with col4:
            # Nút hành động
            if status == "available":
                if st.button("🚀 Làm bài", key=f"take_exam_{exam['id']}"):
                    st.session_state.current_exam_id = exam['id']
                    st.session_state.current_page = "taking_exam"
                    st.rerun()
            elif status == "completed":
                if st.button("👁️ Xem kết quả", key=f"view_result_{exam['id']}"):
                    show_exam_result(exam)
            elif status == "upcoming":
                time_until_start = datetime.fromisoformat(exam['start_time']) - datetime.now()
                st.caption(f"Còn {format_timedelta(time_until_start)}")
        
        st.divider()

def is_exam_available_now(exam):
    """Kiểm tra đề thi có thể làm ngay không"""
    now = datetime.now()
    start_time = datetime.fromisoformat(exam['start_time']) if exam['start_time'] else datetime.min
    end_time = datetime.fromisoformat(exam['end_time']) if exam['end_time'] else datetime.max
    
    return start_time <= now <= end_time

def is_exam_upcoming(exam):
    """Kiểm tra đề thi sắp mở không"""
    if not exam['start_time']:
        return False
    
    now = datetime.now()
    start_time = datetime.fromisoformat(exam['start_time'])
    
    return now < start_time

def is_exam_available_for_student(exam, student_id):
    """Kiểm tra đề thi có khả dụng cho học sinh không"""
    # Kiểm tra xem học sinh đã làm chưa
    submission = get_submission(exam['id'], student_id)
    if submission:
        return False
    
    # Kiểm tra thời gian
    return is_exam_available_now(exam) or is_exam_upcoming(exam)

def format_timedelta(td):
    """Format timedelta thành chuỗi dễ đọc"""
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 0:
        return "Đã qua"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    if days > 0:
        return f"{days} ngày {hours} giờ"
    elif hours > 0:
        return f"{hours} giờ {minutes} phút"
    else:
        return f"{minutes} phút"

def show_class_exams_for_student(class_info):
    """Hiển thị đề thi của lớp cho học sinh"""
    st.subheader(f"📝 Đề thi lớp {class_info['name']}")
    
    user = get_current_user()
    exams = get_exams_by_class(class_info['id'])
    
    if not exams:
        st.info("Lớp này chưa có đề thi nào.")
        return
    
    for exam in exams:
        submission = get_submission(exam['id'], user['id'])
        
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 2])
            
            with col1:
                st.write(f"**{exam['title']}**")
                if exam['description']:
                    st.caption(exam['description'])
            
            with col2:
                # Thời gian
                if exam['start_time']:
                    start_time = datetime.fromisoformat(exam['start_time'])
                    st.caption(f"📅 {start_time.strftime('%d/%m/%Y %H:%M')}")
                st.caption(f"⏱️ {exam['time_limit']} phút")
            
            with col3:
                # Trạng thái
                if submission:
                    if submission['is_graded']:
                        st.success(f"✅ {submission['total_score']:.1f}/{submission['max_score']:.1f}")
                    else:
                        st.info("📝 Đã nộp, chờ chấm")
                elif is_exam_available_now(exam):
                    st.success("🟢 Có thể làm")
                elif is_exam_upcoming(exam):
                    st.warning("🟡 Sắp mở")
                else:
                    st.error("🔴 Hết hạn")
            
            st.divider()

def show_taking_exam():
    """Giao diện làm bài thi"""
    if "current_exam_id" not in st.session_state:
        st.error("❌ Không tìm thấy đề thi!")
        return
    
    exam_id = st.session_state.current_exam_id
    exam = get_exam_by_id(exam_id)
    user = get_current_user()
    
    if not exam:
        st.error("❌ Đề thi không tồn tại!")
        return
    
    # Kiểm tra quyền làm bài
    if not is_exam_available_now(exam):
        st.error("❌ Đề thi hiện không thể làm!")
        return
    
    # Kiểm tra đã làm chưa
    submission = get_submission(exam_id, user['id'])
    if submission:
        st.error("❌ Bạn đã làm bài thi này rồi!")
        return
    
    # Header
    st.header(f"📝 {exam['title']}")
    
    # Thông tin đề thi
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"⏱️ Thời gian: {exam['time_limit']} phút")
    with col2:
        st.info(f"❓ Số câu: {len(exam['questions'])}")
    with col3:
        total_points = sum(q['points'] for q in exam['questions'])
        st.info(f"📊 Tổng điểm: {total_points}")
    
    # Timer (đếm ngược)
    if "exam_start_time" not in st.session_state:
        st.session_state.exam_start_time = datetime.now()
    
    start_time = st.session_state.exam_start_time
    elapsed_seconds = (datetime.now() - start_time).total_seconds()
    remaining_seconds = max(0, exam['time_limit'] * 60 - elapsed_seconds)
    
    if remaining_seconds > 0:
        remaining_minutes = int(remaining_seconds // 60)
        remaining_secs = int(remaining_seconds % 60)
        
        # Hiển thị timer
        timer_col1, timer_col2 = st.columns([1, 4])
        with timer_col1:
            if remaining_minutes < 5:
                st.error(f"⏰ {remaining_minutes:02d}:{remaining_secs:02d}")
            else:
                st.success(f"⏰ {remaining_minutes:02d}:{remaining_secs:02d}")
        
        # Form làm bài
        with st.form("exam_form"):
            answers = {}
            uploaded_images = {}
            
            for i, question in enumerate(exam['questions']):
                st.markdown(f"### Câu {i+1}: ({question['points']} điểm)")
                st.write(question['question'])
                
                if question['type'] == 'multiple_choice':
                    answer = st.radio(
                        "Chọn đáp án:",
                        options=question['options'],
                        format_func=lambda x, idx=question['options'].index(x): f"{chr(65+idx)}. {x}",
                        key=f"answer_{i}"
                    )
                    answers[i] = chr(65 + question['options'].index(answer)) if answer else None
                
                elif question['type'] == 'true_false':
                    answer = st.radio(
                        "Chọn đáp án:",
                        options=["Đúng", "Sai"],
                        key=f"answer_{i}"
                    )
                    answers[i] = answer
                
                elif question['type'] == 'short_answer':
                    answer = st.text_input(
                        "Câu trả lời:",
                        key=f"answer_{i}",
                        placeholder="Nhập câu trả lời ngắn..."
                    )
                    answers[i] = answer
                
                elif question['type'] == 'essay':
                    answer = st.text_area(
                        "Câu trả lời:",
                        key=f"answer_{i}",
                        placeholder="Nhập câu trả lời tự luận...",
                        height=150
                    )
                    answers[i] = answer
                    
                    # Upload ảnh nếu yêu cầu
                    if question.get('requires_image', False):
                        uploaded_file = st.file_uploader(
                            f"Chụp ảnh bài làm câu {i+1}:",
                            type=['png', 'jpg', 'jpeg'],
                            key=f"image_{i}"
                        )
                        
                        if uploaded_file:
                            # Lưu file
                            filename = f"exam_{exam_id}_student_{user['id']}_q{i+1}_{uploaded_file.name}"
                            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            uploaded_images[i] = filepath
                            st.success(f"✅ Đã tải lên ảnh cho câu {i+1}")
                
                st.divider()
            
            # Nút nộp bài
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.form_submit_button("📤 Nộp bài", use_container_width=True):
                    # Kiểm tra thời gian
                    if remaining_seconds <= 0:
                        st.error("❌ Hết thời gian làm bài!")
                        return
                    
                    # Tạo submission
                    submission_id = create_submission(
                        exam_id=exam_id,
                        student_id=user['id'],
                        answers=answers,
                        images=uploaded_images
                    )
                    
                    if submission_id:
                        st.success("✅ Nộp bài thành công!")
                        st.balloons()
                        
                        # Chuyển về trang kết quả
                        del st.session_state.current_exam_id
                        del st.session_state.exam_start_time
                        st.session_state.current_page = "view_results"
                        st.rerun()
                    else:
                        st.error("❌ Có lỗi xảy ra khi nộp bài!")
            
            with col2:
                if st.form_submit_button("💾 Lưu nháp", use_container_width=True):
                    st.info("💾 Đã lưu nháp (tính năng đang phát triển)")
    
    else:
        # Hết thời gian
        st.error("⏰ Hết thời gian làm bài!")
        st.info("Bài thi sẽ được nộp tự động...")
        
        # Tự động nộp bài (có thể implement sau)
        # auto_submit_exam(exam_id, user['id'])

def show_my_results():
    """Hiển thị kết quả bài thi của học sinh"""
    st.header("📊 Kết quả bài thi")
    
    user = get_current_user()
    exams = get_available_exams_for_student(user['id'])
    
    completed_exams = [e for e in exams if e['submission_id']]
    
    if not completed_exams:
        st.info("📝 Bạn chưa hoàn thành bài thi nào.")
        return
    
    # Thống kê tổng quan
    total_exams = len(completed_exams)
    graded_exams = len([e for e in completed_exams if e['total_score'] is not None])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 Tổng bài thi", total_exams)
    with col2:
        st.metric("✅ Đã chấm", graded_exams)
    with col3:
        st.metric("⏳ Chờ chấm", total_exams - graded_exams)
    
    st.divider()
    
    # Danh sách kết quả
    for exam in completed_exams:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.write(f"**📝 {exam['title']}**")
                st.caption(f"📚 Lớp: {exam['class_name']}")
                st.caption(f"📅 Nộp: {exam['submitted_at'][:16]}")
            
            with col2:
                if exam['total_score'] is not None:
                    percentage = (exam['total_score'] / exam['max_score']) * 100
                    st.metric("Điểm", f"{exam['total_score']:.1f}/{exam['max_score']:.1f}")
                    st.caption(f"({percentage:.1f}%)")
                else:
                    st.warning("⏳ Chờ chấm")
            
            with col3:
                if exam['total_score'] is not None:
                    percentage = (exam['total_score'] / exam['max_score']) * 100
                    if percentage >= 80:
                        st.success("🏆 Giỏi")
                    elif percentage >= 65:
                        st.info("👍 Khá")
                    elif percentage >= 50:
                        st.warning("📈 TB")
                    else:
                        st.error("📉 Yếu")
            
            with col4:
                if st.button("👁️ Chi tiết", key=f"detail_{exam['id']}"):
                    show_exam_result_detail(exam)
            
            st.divider()

def show_exam_result_detail(exam):
    """Hiển thị chi tiết kết quả bài thi"""
    st.subheader(f"📊 Chi tiết: {exam['title']}")
    
    user = get_current_user()
    submission = get_submission(exam['id'], user['id'])
    
    if not submission:
        st.error("❌ Không tìm thấy bài làm!")
        return
    
    exam_data = get_exam_by_id(exam['id'])
    
    # Thông tin tổng quan
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Điểm tổng", f"{submission['total_score']:.1f}/{submission['max_score']:.1f}")
    with col2:
        percentage = (submission['total_score'] / submission['max_score']) * 100
        st.metric("📈 Phần trăm", f"{percentage:.1f}%")
    with col3:
        st.metric("📅 Ngày nộp", submission['submitted_at'][:10])
    
    # Nhận xét từ giáo viên
    if submission['feedback']:
        st.subheader("💬 Nhận xét từ giáo viên")
        st.info(submission['feedback'])
    
    # Chi tiết từng câu (nếu đã chấm)
    if submission['is_graded']:
        st.subheader("📋 Chi tiết từng câu")
        
        answers = submission['answers']
        questions = exam_data['questions']
        
        for i, (question, answer) in enumerate(zip(questions, answers.values())):
            with st.expander(f"Câu {i+1}: {question['question'][:50]}...", expanded=False):
                st.write(f"**Câu hỏi:** {question['question']}")
                st.write(f"**Điểm:** {question['points']}")
                st.write(f"**Câu trả lời của bạn:** {answer}")
                
                if question['type'] == 'multiple_choice':
                    correct_option = question['options'][ord(question['correct_answer']) - ord('A')]
                    st.write(f"**Đáp án đúng:** {question['correct_answer']}. {correct_option}")
                    
                    if answer == question['correct_answer']:
                        st.success("✅ Đúng")
                    else:
                        st.error("❌ Sai")

# Kiểm tra trang hiện tại
if st.session_state.get("current_page") == "taking_exam":
    show_taking_exam()
elif st.session_state.get("current_page") == "take_exam":
    show_available_exams()