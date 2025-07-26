import streamlit as st
from datetime import datetime
from auth.login import get_current_user
from database.supabase_models import SupabaseDatabase

# Initialize database
db = SupabaseDatabase()

def show_manage_classes():
    """Quản lý lớp học với popup"""
    st.header("📋 Quản lý Lớp học")
    
    user = get_current_user()
    
    # Buttons hành động
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("➕ Tạo lớp mới", use_container_width=True, key="btn_create_class_main"):
            st.session_state.show_create_class = True
    with col2:
        if st.button("🔄 Làm mới", use_container_width=True, key="btn_refresh_classes"):
            # Clear all popups
            for key in list(st.session_state.keys()):
                if key.startswith('show_'):
                    del st.session_state[key]
            st.rerun()
    
    # Popups
    show_class_popups()
    
    # Danh sách lớp
    classes = get_classes_by_teacher(user['id'])
    
    if not classes:
        st.info("📚 Bạn chưa có lớp học nào. Hãy tạo lớp đầu tiên!")
        return
    
    st.subheader(f"📚 Danh sách lớp học ({len(classes)} lớp)")
    
    for class_info in classes:
        with st.container():
            # Header lớp
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"### 📋 {class_info['ten_lop']}")
                if class_info['mo_ta']:
                    st.caption(f"📝 {class_info['mo_ta']}")
                student_count = get_class_student_count(class_info['id'])
                st.caption(f"👥 {student_count} học sinh | 📅 Tạo: {class_info['created_at'][:10]}")
            
            with col2:
                if st.button("👥 Học sinh", key=f"btn_students_{class_info['id']}", use_container_width=True):
                    st.session_state.show_class_students = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col3:
                if st.button("📝 Đề thi", key=f"btn_exams_{class_info['id']}", use_container_width=True):
                    st.session_state.show_class_exams = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col4:
                if st.button("➕ Thêm HS", key=f"btn_add_{class_info['id']}", use_container_width=True):
                    st.session_state.show_add_students = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col5:
                if st.button("⚙️ Sửa", key=f"btn_edit_{class_info['id']}", use_container_width=True):
                    st.session_state.show_edit_class = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col6:
                if st.button("🗑️ Xóa", key=f"btn_delete_{class_info['id']}", use_container_width=True, type="secondary"):
                    st.session_state.show_delete_class = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            st.divider()

def show_class_popups():
    """Hiển thị tất cả popups cho quản lý lớp"""
    # Popup tạo lớp
    if st.session_state.get("show_create_class", False):
        with st.expander("➕ Tạo lớp học mới", expanded=True):
            show_create_class_popup()
    
    # Popup sửa lớp
    if st.session_state.get("show_edit_class", False):
        with st.expander("⚙️ Sửa thông tin lớp", expanded=True):
            show_edit_class_popup()
    
    # Popup thêm học sinh
    if st.session_state.get("show_add_students", False):
        with st.expander("➕ Thêm học sinh vào lớp", expanded=True):
            show_add_students_popup()
    
    # Popup xem học sinh
    if st.session_state.get("show_class_students", False):
        with st.expander("👥 Học sinh trong lớp", expanded=True):
            show_class_students_popup()
    
    # Popup xem đề thi
    if st.session_state.get("show_class_exams", False):
        with st.expander("📝 Đề thi của lớp", expanded=True):
            show_class_exams_popup()
    
    # Popup xóa lớp
    if st.session_state.get("show_delete_class", False):
        with st.expander("🗑️ Xóa lớp", expanded=True):
            show_delete_class_popup()

def show_create_class_popup():
    """Popup tạo lớp học"""
    user = get_current_user()
    
    st.write("### 📋 Thông tin lớp học")
    
    with st.form("create_class_form"):
        ma_lop = st.text_input("Mã lớp *", placeholder="Ví dụ: 10A1", key="input_new_class_code")
        ten_lop = st.text_input("Tên lớp *", placeholder="Ví dụ: Lớp 10A1", key="input_new_class_name")
        mo_ta = st.text_area("Mô tả", placeholder="Mô tả về lớp học...", key="input_new_class_desc")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("🎯 Tạo lớp", use_container_width=True)
        
        with col2:
            cancelled = st.form_submit_button("❌ Hủy", use_container_width=True)
        
        if submitted:
            if not ma_lop.strip() or not ten_lop.strip():
                st.error("❌ Vui lòng nhập đầy đủ thông tin bắt buộc!")
                return
            
            # Kiểm tra trùng mã lớp
            if check_class_code_exists(ma_lop.strip(), user['id']):
                st.error("❌ Mã lớp đã tồn tại! Vui lòng chọn mã khác.")
                return
            
            success = create_class(ma_lop.strip(), ten_lop.strip(), mo_ta.strip(), user['id'])
            if success:
                st.success(f"✅ Tạo lớp '{ten_lop}' thành công!")
                st.session_state.show_create_class = False
                st.rerun()
            else:
                st.error("❌ Có lỗi xảy ra khi tạo lớp!")
        
        if cancelled:
            st.session_state.show_create_class = False
            st.rerun()

def show_edit_class_popup():
    """Popup sửa thông tin lớp"""
    class_info = st.session_state.get("selected_class", {})
    user = get_current_user()
    
    if not class_info:
        st.error("Không tìm thấy thông tin lớp!")
        return
    
    st.write(f"### ⚙️ Sửa lớp: {class_info['ten_lop']}")
    
    with st.form("edit_class_form"):
        new_ma_lop = st.text_input("Mã lớp", value=class_info['ma_lop'], key=f"input_edit_ma_lop_{class_info['id']}")
        new_ten_lop = st.text_input("Tên lớp", value=class_info['ten_lop'], key=f"input_edit_ten_lop_{class_info['id']}")
        new_mo_ta = st.text_area("Mô tả", value=class_info.get('mo_ta', ''), key=f"input_edit_mo_ta_{class_info['id']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("💾 Lưu thay đổi", use_container_width=True)
        
        with col2:
            cancelled = st.form_submit_button("❌ Hủy", use_container_width=True)
        
        if submitted:
            if not new_ma_lop.strip() or not new_ten_lop.strip():
                st.error("❌ Mã lớp và tên lớp không được để trống!")
                return
            
            # Kiểm tra trùng mã lớp (trừ chính nó)
            if new_ma_lop != class_info['ma_lop'] and check_class_code_exists(new_ma_lop.strip(), user['id']):
                st.error("❌ Mã lớp đã tồn tại!")
                return
            
            success = update_class_info(class_info['id'], new_ma_lop.strip(), new_ten_lop.strip(), new_mo_ta.strip())
            if success:
                st.success("✅ Cập nhật thành công!")
                st.session_state.show_edit_class = False
                st.rerun()
            else:
                st.error("❌ Cập nhật thất bại!")
        
        if cancelled:
            st.session_state.show_edit_class = False
            st.rerun()

def show_add_students_popup():
    """Popup thêm học sinh vào lớp"""
    class_info = st.session_state.get("selected_class", {})
    
    if not class_info:
        return
    
    st.write(f"### ➕ Thêm học sinh vào lớp: {class_info['ten_lop']}")
    
    # Tab thêm từng học sinh và thêm hàng loạt
    tab1, tab2 = st.tabs(["👤 Thêm từng học sinh", "👥 Thêm hàng loạt"])
    
    with tab1:
        available_students = get_students_not_in_class(class_info['id'])
        
        if not available_students:
            st.info("✅ Tất cả học sinh đã có trong lớp hoặc không có học sinh nào.")
        else:
            st.info(f"📋 Có {len(available_students)} học sinh có thể thêm vào lớp")
            
            student_options = {f"{s['ho_ten']} (@{s['username']})": s['id'] for s in available_students}
            selected_student = st.selectbox("Chọn học sinh", options=list(student_options.keys()), key=f"select_single_student_{class_info['id']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Thêm vào lớp", use_container_width=True, key=f"btn_add_single_student_{class_info['id']}"):
                    student_id = student_options[selected_student]
                    if add_student_to_class(class_info['id'], student_id):
                        st.success(f"✅ Đã thêm {selected_student.split(' (@')[0]} vào lớp!")
                        st.rerun()
                    else:
                        st.error("❌ Không thể thêm học sinh vào lớp!")
            
            with col2:
                if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_add_single_{class_info['id']}"):
                    st.session_state.show_add_students = False
                    st.rerun()
    
    with tab2:
        available_students = get_students_not_in_class(class_info['id'])
        
        if not available_students:
            st.info("✅ Tất cả học sinh đã có trong lớp.")
        else:
            st.write("**Chọn nhiều học sinh để thêm cùng lúc:**")
            
            selected_students = []
            
            # Checkbox chọn tất cả
            select_all = st.checkbox("🔘 Chọn tất cả", key=f"chk_select_all_students_{class_info['id']}")
            
            for student in available_students:
                checked = select_all or st.checkbox(
                    f"{student['ho_ten']} (@{student['username']})", 
                    key=f"chk_bulk_student_{class_info['id']}_{student['id']}"
                )
                
                if checked:
                    selected_students.append(student['id'])
            
            if selected_students:
                st.info(f"✅ Đã chọn {len(selected_students)} học sinh")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"➕ Thêm {len(selected_students)} học sinh", use_container_width=True, key=f"btn_add_bulk_students_{class_info['id']}"):
                        success_count = bulk_add_students_to_class(class_info['id'], selected_students)
                        st.success(f"✅ Đã thêm {success_count}/{len(selected_students)} học sinh vào lớp!")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_add_bulk_{class_info['id']}"):
                        st.session_state.show_add_students = False
                        st.rerun()

def show_class_students_popup():
    """Popup hiển thị học sinh trong lớp"""
    class_info = st.session_state.get("selected_class", {})
    
    if not class_info:
        return
    
    st.write(f"### 👥 Học sinh lớp: {class_info['ten_lop']}")
    
    students = get_class_students(class_info['id'])
    
    if not students:
        st.info("📚 Lớp này chưa có học sinh nào.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Thêm học sinh ngay", key=f"btn_add_students_from_empty_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.session_state.show_add_students = True
                st.rerun()
        with col2:
            if st.button("❌ Đóng", key=f"btn_close_empty_students_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.rerun()
    else:
        st.info(f"👥 **Tổng cộng:** {len(students)} học sinh")
        
        # Danh sách học sinh
        for i, student in enumerate(students, 1):
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
            
            with col1:
                st.write(f"**{i}**")
            
            with col2:
                st.write(f"**{student['ho_ten']}**")
                st.caption(f"@{student['username']}")
            
            with col3:
                if student.get('email'):
                    st.caption(f"📧 {student['email']}")
                if student.get('so_dien_thoai'):
                    st.caption(f"📱 {student['so_dien_thoai']}")
            
            with col4:
                if st.button("❌", key=f"btn_remove_popup_{class_info['id']}_{student['id']}", help="Xóa khỏi lớp"):
                    if remove_student_from_class(class_info['id'], student['id']):
                        st.success(f"✅ Đã xóa {student['ho_ten']} khỏi lớp")
                        st.rerun()
                    else:
                        st.error("❌ Lỗi khi xóa học sinh")
        
        # Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Thêm học sinh", use_container_width=True, key=f"btn_add_more_students_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.session_state.show_add_students = True
                st.rerun()
        
        with col2:
            if st.button("❌ Đóng", use_container_width=True, key=f"btn_close_students_popup_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.rerun()

def show_class_exams_popup():
    """Popup hiển thị đề thi của lớp"""
    class_info = st.session_state.get("selected_class", {})
    
    if not class_info:
        return
    
    st.write(f"### 📝 Đề thi lớp: {class_info['ten_lop']}")
    
    exams = get_exams_by_class(class_info['id'])
    
    if not exams:
        st.info("📝 Lớp này chưa có đề thi nào.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Tạo đề thi ngay", key=f"btn_create_exam_from_class_{class_info['id']}"):
                st.session_state.show_class_exams = False
                st.session_state.current_page = "create_exam"
                # Tự động chọn lớp này
                st.session_state.exam_class_id = class_info['id']
                st.session_state.exam_class_name = class_info['ten_lop']
                st.rerun()
        with col2:
            if st.button("❌ Đóng", key=f"btn_close_empty_exams_{class_info['id']}"):
                st.session_state.show_class_exams = False
                st.rerun()
    else:
        st.info(f"📊 **Tổng cộng:** {len(exams)} đề thi")
        
        for exam in exams:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**📝 {exam['title']}**")
                    if exam['description']:
                        st.caption(exam['description'])
                
                with col2:
                    status = get_exam_status(exam)
                    st.write(status)
                    # TODO: Thêm số bài nộp từ database
                    st.caption("📊 Bài nộp: 0")
                
                with col3:
                    if st.button("👁️", key=f"btn_view_exam_popup_{exam['id']}", help="Xem chi tiết"):
                        st.info("Tính năng đang phát triển...")
                
                st.divider()
        
        if st.button("❌ Đóng", use_container_width=True, key=f"btn_close_exams_popup_{class_info['id']}"):
            st.session_state.show_class_exams = False
            st.rerun()

def show_delete_class_popup():
    """Popup xác nhận xóa lớp"""
    class_info = st.session_state.get("selected_class", {})
    
    if not class_info:
        return
    
    st.error(f"🗑️ **Xóa lớp: {class_info['ten_lop']}?**")
    
    student_count = get_class_student_count(class_info['id'])
    exam_count = get_class_exam_count(class_info['id'])
    
    st.write("**Thông tin lớp:**")
    st.write(f"- 👥 Học sinh: {student_count}")
    st.write(f"- 📝 Đề thi: {exam_count}")
    
    if exam_count > 0:
        st.error("❌ Không thể xóa lớp có đề thi!")
        if st.button("❌ Đóng", key=f"btn_close_delete_popup_{class_info['id']}"):
            st.session_state.show_delete_class = False
            st.rerun()
    else:
        st.warning("⚠️ Thao tác này sẽ xóa lớp và tất cả học sinh trong lớp!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Xác nhận xóa", type="secondary", use_container_width=True, key=f"btn_confirm_delete_popup_{class_info['id']}"):
                success = delete_class(class_info['id'])
                if success:
                    st.success("✅ Đã xóa lớp thành công!")
                    st.session_state.show_delete_class = False
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi xóa lớp!")
        
        with col2:
            if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_delete_popup_{class_info['id']}"):
                st.session_state.show_delete_class = False
                st.rerun()

# Database functions using Supabase (UUID VERSION)
def get_classes_by_teacher(teacher_id: str):
    """Lấy danh sách lớp của giáo viên"""
    try:
        result = db.client.table('classes').select('*').eq('teacher_id', teacher_id).execute()
        return result.data
    except Exception as e:
        st.error(f"Lỗi lấy danh sách lớp: {e}")
        return []

def check_class_code_exists(ma_lop: str, teacher_id: str):
    """Kiểm tra mã lớp đã tồn tại"""
    try:
        result = db.client.table('classes').select('id').eq('ma_lop', ma_lop).eq('teacher_id', teacher_id).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Lỗi kiểm tra mã lớp: {e}")
        return False

def create_class(ma_lop: str, ten_lop: str, mo_ta: str, teacher_id: str):
    """Tạo lớp mới"""
    try:
        result = db.client.table('classes').insert({
            'ma_lop': ma_lop,
            'ten_lop': ten_lop,
            'mo_ta': mo_ta,
            'teacher_id': teacher_id
        }).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi tạo lớp: {e}")
        return False

def update_class_info(class_id: str, ma_lop: str, ten_lop: str, mo_ta: str):
    """Cập nhật thông tin lớp"""
    try:
        result = db.client.table('classes').update({
            'ma_lop': ma_lop,
            'ten_lop': ten_lop,
            'mo_ta': mo_ta
        }).eq('id', class_id).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi cập nhật lớp: {e}")
        return False

def delete_class(class_id: str):
    """Xóa lớp"""
    try:
        # Xóa học sinh trong lớp trước
        db.client.table('class_students').delete().eq('class_id', class_id).execute()
        # Xóa lớp
        result = db.client.table('classes').delete().eq('id', class_id).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi xóa lớp: {e}")
        return False

def get_class_student_count(class_id: str):
    """Lấy số lượng học sinh trong lớp"""
    try:
        result = db.client.table('class_students').select('student_id').eq('class_id', class_id).execute()
        return len(result.data)
    except Exception as e:
        return 0

def get_class_exam_count(class_id: str):
    """Lấy số lượng đề thi của lớp"""
    try:
        result = db.client.table('exams').select('id').eq('class_id', class_id).execute()
        return len(result.data)
    except Exception as e:
        return 0

def get_class_students(class_id: str):
    """Lấy danh sách học sinh trong lớp"""
    try:
        # Subquery để lấy thông tin chi tiết học sinh
        result = db.client.table('class_students').select(
            'student_id, users(id, username, ho_ten, email, so_dien_thoai)'
        ).eq('class_id', class_id).execute()
        
        students = []
        for item in result.data:
            student_info = item['users']
            students.append(student_info)
        return students
    except Exception as e:
        st.error(f"Lỗi lấy danh sách học sinh: {e}")
        return []

def get_students_not_in_class(class_id: str):
    """Lấy học sinh chưa có trong lớp"""
    try:
        # Lấy danh sách ID học sinh đã có trong lớp
        existing_result = db.client.table('class_students').select('student_id').eq('class_id', class_id).execute()
        existing_student_ids = [item['student_id'] for item in existing_result.data]
        
        # Lấy tất cả học sinh
        all_students_result = db.client.table('users').select('*').eq('role', 'student').execute()
        
        # Filter những học sinh chưa có trong lớp
        available_students = [
            student for student in all_students_result.data 
            if student['id'] not in existing_student_ids
        ]
        
        return available_students
    except Exception as e:
        st.error(f"Lỗi lấy học sinh khả dụng: {e}")
        return []

def add_student_to_class(class_id: str, student_id: str):
    """Thêm học sinh vào lớp"""
    try:
        result = db.client.table('class_students').insert({
            'class_id': class_id,
            'student_id': student_id
        }).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi thêm học sinh vào lớp: {e}")
        return False

def bulk_add_students_to_class(class_id: str, student_ids: list):
    """Thêm nhiều học sinh vào lớp"""
    success_count = 0
    for student_id in student_ids:
        if add_student_to_class(class_id, student_id):
            success_count += 1
    return success_count

def remove_student_from_class(class_id: str, student_id: str):
    """Xóa học sinh khỏi lớp"""
    try:
        result = db.client.table('class_students').delete().eq('class_id', class_id).eq('student_id', student_id).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi xóa học sinh khỏi lớp: {e}")
        return False

def get_exams_by_class(class_id: str):
    """Lấy danh sách đề thi theo lớp"""
    try:
        result = db.client.table('exams').select('*').eq('class_id', class_id).execute()
        return result.data
    except Exception as e:
        st.error(f"Lỗi lấy danh sách đề thi: {e}")
        return []

def get_exam_status(exam):
    """Lấy trạng thái đề thi"""
    try:
        now = datetime.now()
        
        if exam['start_time']:
            start_time = datetime.fromisoformat(exam['start_time'].replace('Z', '+00:00'))
            if now < start_time:
                return "⏳ Chưa mở"
        
        if exam['end_time']:
            end_time = datetime.fromisoformat(exam['end_time'].replace('Z', '+00:00'))
            if now > end_time:
                return "🔒 Đã đóng"
        
        return "✅ Đang mở"
    except:
        return "❓ Không xác định"