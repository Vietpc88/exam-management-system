import streamlit as st
import pandas as pd
from database.supabase_models import SupabaseDatabase
from datetime import datetime, timedelta
import json

def show_teacher_interface():
    """Giao diện chính cho giáo viên"""
    # Khởi tạo database
    db = SupabaseDatabase()
    
    # Lấy thông tin user hiện tại
    if 'user_info' not in st.session_state:
        st.error("Vui lòng đăng nhập lại!")
        return
    
    user_info = st.session_state.user_info
    teacher_id = user_info['id']
    teacher_name = user_info['ho_ten']
    
    st.header(f"🎓 Giao diện Giáo viên - {teacher_name}")
    
    # Tabs cho các chức năng
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Quản lý lớp học", 
        "📝 Tạo đề thi", 
        "👥 Quản lý học sinh",
        "📊 Xem kết quả",
        "⚙️ Cài đặt"
    ])
    
    with tab1:
        manage_classes(db, teacher_id)
    
    with tab2:
        create_exam(db, teacher_id)
    
    with tab3:
        manage_students(db, teacher_id)
    
    with tab4:
        view_results(db, teacher_id)
        
    with tab5:
        teacher_settings(db, teacher_id)

def manage_classes(db, teacher_id):
    """Quản lý lớp học"""
    st.subheader("📚 Quản lý lớp học")
    
    # Tạo lớp học mới
    with st.expander("➕ Tạo lớp học mới", expanded=False):
        with st.form("create_class_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                ma_lop = st.text_input("Mã lớp học *", placeholder="VD: PYTHON101")
                ten_lop = st.text_input("Tên lớp học *", placeholder="VD: Python cơ bản")
            
            with col2:
                mo_ta = st.text_area("Mô tả lớp học", placeholder="Mô tả ngắn về lớp học...")
            
            submitted = st.form_submit_button("🆕 Tạo lớp học", use_container_width=True)
            
            if submitted:
                if ma_lop and ten_lop:
                    if db.create_class(ma_lop, ten_lop, mo_ta, teacher_id):
                        st.success(f"✅ Tạo lớp học '{ten_lop}' thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Tạo lớp học thất bại! Mã lớp có thể đã tồn tại.")
                else:
                    st.error("⚠️ Vui lòng nhập đầy đủ mã lớp và tên lớp!")
    
    # Danh sách lớp học
    st.subheader("📋 Danh sách lớp học của bạn")
    classes = db.get_classes_by_teacher(teacher_id)
    
    if classes:
        for cls in classes:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**{cls['ten_lop']}**")
                    st.caption(f"Mã lớp: {cls['ma_lop']}")
                    if cls['mo_ta']:
                        st.caption(f"📝 {cls['mo_ta']}")
                
                with col2:
                    students = db.get_students_in_class(cls['id'])
                    st.metric("👥 Học sinh", len(students))
                
                with col3:
                    exams = db.get_exams_by_class(cls['id'])
                    st.metric("📝 Đề thi", len(exams))
                
                with col4:
                    if st.button("🔍 Chi tiết", key=f"detail_{cls['id']}"):
                        st.session_state.selected_class = cls
                        st.session_state.show_class_detail = True
                
                st.divider()
                
        # Hiển thị chi tiết lớp nếu được chọn
        if st.session_state.get('show_class_detail', False) and 'selected_class' in st.session_state:
            show_class_detail(db, st.session_state.selected_class)
            
    else:
        st.info("📚 Bạn chưa có lớp học nào. Tạo lớp học đầu tiên để bắt đầu!")

def show_class_detail(db, selected_class):
    """Hiển thị chi tiết lớp học"""
    st.subheader(f"🔍 Chi tiết lớp: {selected_class['ten_lop']}")
    
    if st.button("⬅️ Quay lại danh sách"):
        st.session_state.show_class_detail = False
        st.rerun()
    
    # Thống kê
    col1, col2, col3 = st.columns(3)
    
    students = db.get_students_in_class(selected_class['id'])
    exams = db.get_exams_by_class(selected_class['id'])
    
    with col1:
        st.metric("👥 Tổng học sinh", len(students))
    with col2:
        st.metric("📝 Tổng đề thi", len(exams))
    with col3:
        active_exams = [e for e in exams if e.get('is_active', True)]
        st.metric("✅ Đề thi đang hoạt động", len(active_exams))
    
    # Danh sách học sinh
    st.write("**👥 Danh sách học sinh:**")
    if students:
        df_students = pd.DataFrame(students)
        st.dataframe(df_students[['ho_ten', 'username', 'email']], use_container_width=True)
    else:
        st.info("Chưa có học sinh nào trong lớp.")
    
    # Danh sách đề thi
    st.write("**📝 Danh sách đề thi:**")
    if exams:
        exam_data = []
        for exam in exams:
            exam_data.append({
                'Tiêu đề': exam['title'],
                'Thời gian': f"{exam.get('time_limit', 0)} phút",
                'Trạng thái': '✅ Hoạt động' if exam.get('is_active', True) else '❌ Không hoạt động',
                'Ngày tạo': exam.get('created_at', '')[:10] if exam.get('created_at') else ''
            })
        df_exams = pd.DataFrame(exam_data)
        st.dataframe(df_exams, use_container_width=True)
    else:
        st.info("Chưa có đề thi nào trong lớp.")

def create_exam(db, teacher_id):
    """Tạo đề thi"""
    st.subheader("📝 Tạo đề thi")
    
    # Lấy danh sách lớp học
    classes = db.get_classes_by_teacher(teacher_id)
    
    if not classes:
        st.warning("⚠️ Bạn cần tạo lớp học trước khi tạo đề thi!")
        if st.button("➕ Tạo lớp học ngay"):
            st.session_state.active_tab = 0  # Chuyển về tab quản lý lớp
            st.rerun()
        return
    
    # Form tạo đề thi
    with st.form("create_exam_form"):
        st.subheader("ℹ️ Thông tin cơ bản")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Tiêu đề đề thi *", placeholder="VD: Kiểm tra Python Cơ bản")
            class_options = {cls['id']: f"{cls['ten_lop']} ({cls['ma_lop']})" for cls in classes}
            selected_class_id = st.selectbox(
                "Chọn lớp học *",
                options=list(class_options.keys()),
                format_func=lambda x: class_options[x]
            )
        
        with col2:
            time_limit = st.number_input("Thời gian làm bài (phút) *", min_value=1, max_value=300, value=60)
            description = st.text_area("Mô tả đề thi", placeholder="Mô tả ngắn về đề thi...")
        
        # Thời gian thi
        st.subheader("⏰ Thời gian thi")
        col3, col4 = st.columns(2)
        
        with col3:
            start_date = st.date_input("Ngày bắt đầu", value=datetime.now().date())
            start_time = st.time_input("Giờ bắt đầu", value=datetime.now().time())
        
        with col4:
            end_date = st.date_input("Ngày kết thúc", value=(datetime.now() + timedelta(days=7)).date())
            end_time = st.time_input("Giờ kết thúc", value=datetime.now().time())
        
        # Quản lý câu hỏi
        st.subheader("❓ Quản lý câu hỏi")
        
        # Initialize questions trong session state
        if 'exam_questions' not in st.session_state:
            st.session_state.exam_questions = []
        
        # Hiển thị câu hỏi đã thêm
        if st.session_state.exam_questions:
            st.write(f"**📋 Đã có {len(st.session_state.exam_questions)} câu hỏi:**")
            
            for i, q in enumerate(st.session_state.exam_questions):
                with st.expander(f"Câu {i+1}: {q['question'][:50]}{'...' if len(q['question']) > 50 else ''}"):
                    display_question_preview(q, i)
        
        # Nút để thêm câu hỏi mới (ngoài form)
        st.write("---")
        
        # Submit form
        col_submit1, col_submit2 = st.columns(2)
        
        with col_submit1:
            submitted = st.form_submit_button("🚀 Tạo đề thi", use_container_width=True)
        
        with col_submit2:
            if st.form_submit_button("🗑️ Xóa tất cả câu hỏi", use_container_width=True):
                st.session_state.exam_questions = []
                st.rerun()
        
        if submitted:
            if title and st.session_state.exam_questions:
                # Tạo datetime objects
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(end_date, end_time)
                
                # Validate thời gian
                if end_datetime <= start_datetime:
                    st.error("⚠️ Thời gian kết thúc phải sau thời gian bắt đầu!")
                    st.stop()
                
                # Tạo đề thi
                if db.create_exam(
                    title=title,
                    description=description,
                    class_id=selected_class_id,
                    teacher_id=teacher_id,
                    questions=st.session_state.exam_questions,
                    time_limit=time_limit,
                    start_time=start_datetime.isoformat(),
                    end_time=end_datetime.isoformat()
                ):
                    st.success("🎉 Tạo đề thi thành công!")
                    st.session_state.exam_questions = []  # Reset questions
                    st.rerun()
                else:
                    st.error("❌ Tạo đề thi thất bại!")
            else:
                if not title:
                    st.error("⚠️ Vui lòng nhập tiêu đề đề thi!")
                if not st.session_state.exam_questions:
                    st.error("⚠️ Vui lòng thêm ít nhất 1 câu hỏi!")
    
    # Phần thêm câu hỏi (ngoài form để tránh conflict)
    st.write("---")
    add_question_interface()

def add_question_interface():
    """Giao diện thêm câu hỏi"""
    st.subheader("➕ Thêm câu hỏi mới")
    
    question_type = st.selectbox(
        "Loại câu hỏi",
        ["Trắc nghiệm", "Đúng/Sai", "Tự luận"],
        key="question_type_selector"
    )
    
    if question_type == "Trắc nghiệm":
        add_multiple_choice_question()
    elif question_type == "Đúng/Sai":
        add_true_false_question()
    elif question_type == "Tự luận":
        add_essay_question()

def add_multiple_choice_question():
    """Thêm câu hỏi trắc nghiệm"""
    with st.container():
        question_text = st.text_area("Câu hỏi *", key="mc_question", placeholder="Nhập nội dung câu hỏi...")
        
        col1, col2 = st.columns(2)
        with col1:
            option_a = st.text_input("Đáp án A *", key="mc_a", placeholder="Nhập đáp án A")
            option_b = st.text_input("Đáp án B *", key="mc_b", placeholder="Nhập đáp án B")
        with col2:
            option_c = st.text_input("Đáp án C *", key="mc_c", placeholder="Nhập đáp án C")
            option_d = st.text_input("Đáp án D *", key="mc_d", placeholder="Nhập đáp án D")
        
        col3, col4 = st.columns(2)
        with col3:
            correct_answer = st.selectbox("Đáp án đúng *", ["A", "B", "C", "D"], key="mc_correct")
        with col4:
            points = st.number_input("Điểm *", min_value=0.1, max_value=10.0, value=1.0, key="mc_points")
        
        if st.button("➕ Thêm câu hỏi trắc nghiệm", key="add_mc"):
            if question_text and option_a and option_b and option_c and option_d:
                question = {
                    "type": "multiple_choice",
                    "question": question_text,
                    "options": {
                        "A": option_a,
                        "B": option_b,
                        "C": option_c,
                        "D": option_d
                    },
                    "correct_answer": correct_answer,
                    "points": points
                }
                st.session_state.exam_questions.append(question)
                st.success("✅ Đã thêm câu hỏi trắc nghiệm!")
                # Clear inputs bằng cách rerun
                st.rerun()
            else:
                st.error("⚠️ Vui lòng nhập đầy đủ thông tin câu hỏi và tất cả đáp án!")

def add_true_false_question():
    """Thêm câu hỏi đúng/sai"""
    with st.container():
        question_text = st.text_area("Câu hỏi *", key="tf_question", placeholder="Nhập nội dung câu hỏi...")
        
        col1, col2 = st.columns(2)
        with col1:
            correct_answer = st.selectbox("Đáp án đúng *", ["Đúng", "Sai"], key="tf_correct")
        with col2:
            points = st.number_input("Điểm *", min_value=0.1, max_value=10.0, value=1.0, key="tf_points")
        
        if st.button("➕ Thêm câu hỏi đúng/sai", key="add_tf"):
            if question_text:
                question = {
                    "type": "true_false",
                    "question": question_text,
                    "correct_answer": correct_answer,
                    "points": points
                }
                st.session_state.exam_questions.append(question)
                st.success("✅ Đã thêm câu hỏi đúng/sai!")
                st.rerun()
            else:
                st.error("⚠️ Vui lòng nhập nội dung câu hỏi!")

def add_essay_question():
    """Thêm câu hỏi tự luận"""
    with st.container():
        question_text = st.text_area("Câu hỏi *", key="essay_question", placeholder="Nhập nội dung câu hỏi...")
        sample_answer = st.text_area("Đáp án mẫu (cho AI chấm điểm) *", key="essay_sample", 
                                   placeholder="Nhập đáp án mẫu để AI có thể chấm điểm...")
        
        col1, col2 = st.columns(2)
        with col1:
            points = st.number_input("Điểm *", min_value=0.1, max_value=10.0, value=5.0, key="essay_points")
        with col2:
            min_words = st.number_input("Số từ tối thiểu", min_value=0, value=50, key="essay_min_words")
        
        if st.button("➕ Thêm câu hỏi tự luận", key="add_essay"):
            if question_text and sample_answer:
                question = {
                    "type": "essay",
                    "question": question_text,
                    "sample_answer": sample_answer,
                    "points": points,
                    "min_words": min_words
                }
                st.session_state.exam_questions.append(question)
                st.success("✅ Đã thêm câu hỏi tự luận!")
                st.rerun()
            else:
                st.error("⚠️ Vui lòng nhập đầy đủ câu hỏi và đáp án mẫu!")

def display_question_preview(question, index):
    """Hiển thị preview câu hỏi"""
    st.write(f"**Loại:** {question['type']}")
    st.write(f"**Câu hỏi:** {question['question']}")
    
    if question['type'] == 'multiple_choice':
        st.write("**Các đáp án:**")
        for key, value in question['options'].items():
            marker = "✅" if key == question['correct_answer'] else "⭕"
            st.write(f"{marker} {key}. {value}")
    
    elif question['type'] == 'true_false':
        st.write(f"**Đáp án đúng:** {question['correct_answer']}")
    
    elif question['type'] == 'essay':
        st.write(f"**Đáp án mẫu:** {question['sample_answer'][:100]}...")
        if question.get('min_words'):
            st.write(f"**Số từ tối thiểu:** {question['min_words']}")
    
    st.write(f"**Điểm:** {question['points']}")
    
    if st.button(f"🗑️ Xóa câu {index+1}", key=f"delete_q_{index}"):
        st.session_state.exam_questions.pop(index)
        st.rerun()

def manage_students(db, teacher_id):
    """Quản lý học sinh"""
    st.subheader("👥 Quản lý học sinh")
    
    # Chọn lớp học
    classes = db.get_classes_by_teacher(teacher_id)
    
    if not classes:
        st.warning("⚠️ Bạn cần tạo lớp học trước!")
        return
    
    class_options = {cls['id']: f"{cls['ten_lop']} ({cls['ma_lop']})" for cls in classes}
    selected_class_id = st.selectbox(
        "Chọn lớp học",
        options=list(class_options.keys()),
        format_func=lambda x: class_options[x],
        key="manage_students_class"
    )
    
    if selected_class_id:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Thêm học sinh vào lớp
            with st.expander("➕ Thêm học sinh vào lớp"):
                add_method = st.radio(
                    "Phương thức thêm:",
                    ["Thêm theo username", "Upload file Excel"],
                    key="add_method"
                )
                
                if add_method == "Thêm theo username":
                    with st.form("add_student_form"):
                        student_username = st.text_input("Tên đăng nhập học sinh")
                        add_submitted = st.form_submit_button("➕ Thêm học sinh")
                        
                        if add_submitted and student_username:
                            # Tạm thời hiển thị thông báo
                            st.info("🚧 Chức năng này đang được phát triển")
                
                elif add_method == "Upload file Excel":
                    st.info("🚧 Chức năng upload Excel đang được phát triển")
                    uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'])
                    if uploaded_file:
                        st.write("Preview file sẽ hiển thị ở đây...")
        
        with col2:
            # Danh sách học sinh trong lớp
            st.subheader("📋 Danh sách học sinh trong lớp")
            students = db.get_students_in_class(selected_class_id)
            
            if students:
                for student in students:
                    with st.container():
                        col_info, col_action = st.columns([4, 1])
                        
                        with col_info:
                            st.write(f"**{student['ho_ten']}**")
                            st.caption(f"👤 {student['username']}")
                            if student.get('email'):
                                st.caption(f"📧 {student['email']}")
                        
                        with col_action:
                            if st.button("🗑️", key=f"remove_{student['id']}", help="Xóa khỏi lớp"):
                                st.info("🚧 Chức năng xóa đang được phát triển")
                        
                        st.divider()
            else:
                st.info("📚 Lớp học chưa có học sinh nào.")

def view_results(db, teacher_id):
    """Xem kết quả thi"""
    st.subheader("📊 Kết quả thi")
    
    # Chọn lớp học
    classes = db.get_classes_by_teacher(teacher_id)
    
    if not classes:
        st.warning("⚠️ Bạn cần tạo lớp học trước!")
        return
    
    class_options = {cls['id']: f"{cls['ten_lop']} ({cls['ma_lop']})" for cls in classes}
    selected_class_id = st.selectbox(
        "Chọn lớp học",
        options=list(class_options.keys()),
        format_func=lambda x: class_options[x],
        key="view_results_class"
    )
    
    if selected_class_id:
        # Lấy danh sách đề thi của lớp
        exams = db.get_exams_by_class(selected_class_id)
        
        if exams:
            exam_options = {exam['id']: exam['title'] for exam in exams}
            selected_exam_id = st.selectbox(
                "Chọn đề thi",
                options=list(exam_options.keys()),
                format_func=lambda x: exam_options[x]
            )
            
            if selected_exam_id:
                st.subheader(f"📈 Kết quả: {exam_options[selected_exam_id]}")
                
                # Thống kê tổng quan
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("👥 Tổng học sinh", "25")  # Demo data
                with col2:
                    st.metric("✅ Đã làm bài", "20")
                with col3:
                    st.metric("⏳ Chưa làm", "5")
                with col4:
                    st.metric("📊 Điểm trung bình", "7.8")
                
                # Bảng kết quả chi tiết
                st.subheader("📋 Kết quả chi tiết")
                
                # Demo data - cần implement thực tế
                demo_results = [
                    {"STT": 1, "Học sinh": "Nguyễn Văn A", "Điểm": 8.5, "Thời gian": "45 phút", "Trạng thái": "Hoàn thành"},
                    {"STT": 2, "Học sinh": "Trần Thị B", "Điểm": 7.2, "Thời gian": "50 phút", "Trạng thái": "Hoàn thành"},
                    {"STT": 3, "Học sinh": "Lê Văn C", "Điểm": 9.1, "Thời gian": "38 phút", "Trạng thái": "Hoàn thành"},
                ]
                
                df_results = pd.DataFrame(demo_results)
                st.dataframe(df_results, use_container_width=True)
                
                # Nút export
                if st.button("📥 Xuất kết quả ra Excel"):
                    st.info("🚧 Chức năng xuất Excel đang được phát triển")
                
        else:
            st.info("📝 Lớp học chưa có đề thi nào.")

def teacher_settings(db, teacher_id):
    """Cài đặt dành cho giáo viên"""
    st.subheader("⚙️ Cài đặt")
    
    # Thông tin cá nhân
    user_info = st.session_state.get('user_info', {})
    
    with st.expander("👤 Thông tin cá nhân"):
        with st.form("profile_form"):
            ho_ten = st.text_input("Họ và tên", value=user_info.get('ho_ten', ''))
            email = st.text_input("Email", value=user_info.get('email', ''))
            so_dien_thoai = st.text_input("Số điện thoại", value=user_info.get('so_dien_thoai', ''))
            
            if st.form_submit_button("💾 Cập nhật thông tin"):
                st.info("🚧 Chức năng cập nhật thông tin đang được phát triển")
    
    # Đổi mật khẩu
    with st.expander("🔒 Đổi mật khẩu"):
        with st.form("password_form"):
            current_password = st.text_input("Mật khẩu hiện tại", type="password")
            new_password = st.text_input("Mật khẩu mới", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu mới", type="password")
            
            if st.form_submit_button("🔄 Đổi mật khẩu"):
                if new_password == confirm_password:
                    st.info("🚧 Chức năng đổi mật khẩu đang được phát triển")
                else:
                    st.error("❌ Mật khẩu xác nhận không khớp!")
    
    # Cài đặt hệ thống
    with st.expander("🔧 Cài đặt hệ thống"):
        st.info("🚧 Các cài đặt hệ thống sẽ được thêm vào sau")
        
        # Demo settings
        auto_grade = st.checkbox("🤖 Tự động chấm bài tự luận bằng AI", value=True)
        email_notification = st.checkbox("📧 Nhận thông báo qua email", value=False)
        
        if st.button("💾 Lưu cài đặt"):
            st.success("✅ Đã lưu cài đặt!")

# Main function để test riêng biệt
if __name__ == "__main__":
    # Test function
    st.set_page_config(page_title="Test Teacher Interface", layout="wide")
    
    # Mock session state for testing
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {
            'id': 1,
            'username': 'teacher_test',
            'ho_ten': 'Giáo viên Test',
            'role': 'teacher'
        }
    
    show_teacher_interface()