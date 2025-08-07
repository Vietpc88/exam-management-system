import streamlit as st
from datetime import datetime
from auth.login import get_current_user
from database.supabase_models import get_database

# =====================================================================
# HÀM GIAO DIỆN CHÍNH (CHO ADMIN)
# =====================================================================

def show_manage_classes():
    """Trang chính Quản lý Lớp học dành cho Admin."""
    st.header("🏫 Quản lý Lớp học")
    
    user = get_current_user()
    db = get_database()
    
    # --- Thanh hành động ---
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        if st.button("➕ Tạo lớp mới", use_container_width=True):
            st.session_state.show_create_class = True
            st.rerun()
    with col2:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.rerun()
    
    # --- Hiển thị các Popups ---
    show_class_popups(user, db)
    
    st.markdown("---")
    
    # --- Danh sách lớp học ---
    # SỬA LỖI: Admin dùng hàm get_all_classes() để xem tất cả lớp
    classes = db.get_all_classes() 
    
    if not classes:
        st.info("📚 Hệ thống chưa có lớp học nào. Hãy tạo một lớp mới để bắt đầu!")
        return
    
    st.subheader(f"📚 Danh sách tất cả lớp học ({len(classes)} lớp)")
    
    for class_info in classes:
        display_class_item(class_info, db)

def display_class_item(class_info, db):
    """Hiển thị thông tin của một lớp trong danh sách."""
    with st.container():
        cols = st.columns([3, 1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(f"**{class_info.get('ten_lop', 'Chưa có tên')}**")
            student_count = db.get_class_student_count(class_info['id'])
            st.caption(f"👥 {student_count} học sinh | Mã lớp: {class_info.get('ma_lop', 'N/A')}")
        
        action_buttons = {
            "Học sinh": "show_class_students", "Đề thi": "show_class_exams",
            "Thêm HS": "show_add_students", "Sửa": "show_edit_class", "Xóa": "show_delete_class"
        }
        
        for i, (label, state_key) in enumerate(action_buttons.items()):
            with cols[i+1]:
                if st.button(label, key=f"btn_{state_key}_{class_info['id']}", use_container_width=True):
                    st.session_state[state_key] = True
                    st.session_state.selected_class = class_info
                    st.rerun()
        st.divider()

# =====================================================================
# CÁC HÀM XỬ LÝ POPUP
# =====================================================================

def show_class_popups(user, db):
    """Kiểm tra session_state và gọi các hàm popup tương ứng."""
    if st.session_state.get("show_create_class"):
        show_create_class_popup(user, db)
    if st.session_state.get("show_edit_class"):
        show_edit_class_popup(user, db)
    if st.session_state.get("show_add_students"):
        show_add_students_popup(user, db)
    if st.session_state.get("show_class_students"):
        show_class_students_popup(user, db)
    if st.session_state.get("show_class_exams"):
        show_class_exams_popup(user, db)
    if st.session_state.get("show_delete_class"):
        show_delete_class_popup(user, db)

def show_create_class_popup(user, db):
    """Popup để tạo một lớp học mới."""
    with st.expander("➕ Tạo lớp học mới", expanded=True):
        with st.form("create_class_form"):
            st.subheader("📋 Thông tin lớp học")
            ma_lop = st.text_input("Mã lớp *", placeholder="Ví dụ: 10A1")
            ten_lop = st.text_input("Tên lớp *", placeholder="Ví dụ: Lớp 10 Chuyên Toán")
            mo_ta = st.text_area("Mô tả (Tùy chọn)")
            
            submitted = st.form_submit_button("🎯 Tạo lớp", type="primary")

            if submitted:
                if not ma_lop.strip() or not ten_lop.strip():
                    st.error("❌ Vui lòng điền Mã lớp và Tên lớp.")
                # SỬA LỖI: Chỉ truyền vào 1 tham số là ma_lop
                elif db.check_class_code_exists(ma_lop.strip()):
                    st.error("❌ Mã lớp này đã tồn tại trong hệ thống. Vui lòng chọn mã khác.")
                else:
                    # SỬA LỖI: Lời gọi không cần user['id'] nữa
                    success = db.create_class(ma_lop.strip(), ten_lop.strip(), mo_ta.strip())
                    if success:
                        st.success(f"✅ Đã tạo lớp '{ten_lop}' thành công!")
                        if "show_create_class" in st.session_state:
                            del st.session_state.show_create_class
                        st.rerun()
        
        if st.button("❌ Hủy", key="cancel_create_class"):
            if "show_create_class" in st.session_state:
                del st.session_state.show_create_class
            st.rerun()

def show_edit_class_popup(user, db):
    """Popup để chỉnh sửa thông tin lớp học."""
    class_info = st.session_state.selected_class
    with st.expander(f"⚙️ Chỉnh sửa lớp: {class_info.get('ten_lop', '')}", expanded=True):
        with st.form("edit_class_form"):
            new_ma_lop = st.text_input("Mã lớp", value=class_info.get('ma_lop', ''))
            new_ten_lop = st.text_input("Tên lớp", value=class_info.get('ten_lop', ''))
            new_mo_ta = st.text_area("Mô tả", value=class_info.get('mo_ta', ''))

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Lưu thay đổi", type="primary"):
                    if db.update_class(class_info['id'], ten_lop=new_ten_lop, mo_ta=new_mo_ta, ma_lop=new_ma_lop):
                        del st.session_state.show_edit_class
                        st.rerun()
            with col2:
                if st.form_submit_button("❌ Hủy"):
                    del st.session_state.show_edit_class
                    st.rerun()

def show_add_students_popup(user, db):
    """Popup để thêm học sinh vào một lớp."""
    class_info = st.session_state.selected_class
    with st.expander(f"➕ Thêm học sinh vào lớp '{class_info.get('ten_lop', '')}'", expanded=True):
        available_students = db.get_students_not_in_class(class_info['id'])
        
        if not available_students:
            st.info("✅ Tất cả học sinh trong hệ thống đã có trong lớp này.")
            if st.button("Đóng"):
                del st.session_state.show_add_students
                st.rerun()
            return

        student_options = {f"{s['ho_ten']} (@{s['username']})": s['id'] for s in available_students}
        selected_students_display = st.multiselect("Chọn học sinh để thêm:", student_options.keys())
        
        if st.button("➕ Thêm học sinh đã chọn", type="primary"):
            student_ids_to_add = [student_options[name] for name in selected_students_display]
            if student_ids_to_add:
                success_count = 0
                for student_id in student_ids_to_add:
                    if db.add_student_to_class(class_info['id'], student_id):
                        success_count += 1
                st.success(f"✅ Đã thêm thành công {success_count}/{len(student_ids_to_add)} học sinh.")
                del st.session_state.show_add_students
                st.rerun()

def show_class_students_popup(user, db):
    """Popup để xem danh sách học sinh trong lớp."""
    class_info = st.session_state.selected_class
    with st.expander(f"👥 Danh sách học sinh lớp '{class_info.get('ten_lop', '')}'", expanded=True):
        students = db.get_students_in_class(class_info['id'])
        if not students:
            st.info("Lớp này chưa có học sinh nào.")
        else:
            for student in students:
                st.write(f"- {student.get('ho_ten', '')} (@{student.get('username', '')})")
        if st.button("Đóng", key=f"close_students_{class_info['id']}"):
            del st.session_state.show_class_students
            st.rerun()

def show_class_exams_popup(user, db):
    """Popup để xem danh sách đề thi của lớp."""
    class_info = st.session_state.selected_class
    with st.expander(f"📝 Đề thi của lớp '{class_info.get('ten_lop', '')}'", expanded=True):
        exams = db.get_exams_by_class(class_info['id'])
        if not exams:
            st.info("Lớp này chưa có đề thi nào.")
        else:
            for exam in exams:
                st.write(f"- {exam.get('title', '')}")
        if st.button("Đóng", key=f"close_exams_{class_info['id']}"):
            del st.session_state.show_class_exams
            st.rerun()

def show_delete_class_popup(user, db):
    """Popup để xác nhận xóa lớp."""
    class_info = st.session_state.selected_class
    with st.expander(f"🗑️ Xóa lớp: {class_info.get('ten_lop', '')}?", expanded=True):
        st.warning("⚠️ Hành động này không thể hoàn tác. Toàn bộ liên kết học sinh, đề thi của lớp này sẽ bị xóa.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Vâng, xóa lớp này", type="primary"):
                if db.delete_class(class_info['id']):
                    st.success("✅ Đã xóa lớp thành công.")
                    del st.session_state.show_delete_class
                    st.rerun()
        with col2:
            if st.button("❌ Hủy"):
                del st.session_state.show_delete_class
                st.rerun()