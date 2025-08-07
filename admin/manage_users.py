import streamlit as st
from datetime import datetime
from database.supabase_models import get_database
from auth.login import get_current_user

def show_manage_users():
    """Giao diện chính cho trang Quản lý Người dùng của Admin."""
    st.header("👥 Quản lý Người dùng")
    db = get_database()
    
    # Nút tạo người dùng mới
    if st.button("➕ Tạo người dùng mới", type="primary"):
        st.session_state.show_create_user_form = True
    
    # --- FORM TẠO NGƯỜI DÙNG MỚI (POPUP) ---
    if st.session_state.get("show_create_user_form", False):
        with st.form("create_user_form"):
            st.subheader("📝 Biểu mẫu tạo người dùng")
            col1, col2 = st.columns(2)
            with col1:
                ho_ten = st.text_input("Họ và tên *")
                username = st.text_input("Tên đăng nhập *")
            with col2:
                email = st.text_input("Email *")
                role = st.selectbox("Vai trò *", ["student", "teacher"])
            so_dien_thoai = st.text_input("Số điện thoại (Tùy chọn)")
            password = st.text_input("Mật khẩu *", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu *", type="password")

            submitted = st.form_submit_button("✅ Tạo người dùng")
            if submitted:
                if not all([ho_ten, username, email, password, confirm_password]):
                    st.error("❌ Vui lòng điền đầy đủ các trường bắt buộc.")
                elif password != confirm_password:
                    st.error("❌ Mật khẩu xác nhận không khớp.")
                else:
                    user_id = db.create_user(
                    username=username, 
                    password=password, 
                    ho_ten=ho_ten, 
                    email=email, 
                    role=role, 
                    so_dien_thoai=so_dien_thoai if so_dien_thoai.strip() else None
                )
                    if user_id:
                        st.session_state.show_create_user_form = False
                        st.rerun()
    
    st.markdown("---")

    # --- DANH SÁCH NGƯỜI DÙNG ---
    st.subheader("📋 Danh sách toàn bộ người dùng")
    
    users = db.get_all_users()
    if not users:
        st.info("Hiện chưa có người dùng nào trong hệ thống.")
        return

    # Bộ lọc
    role_filter = st.selectbox("Lọc theo vai trò:", ["Tất cả", "teacher", "student"], key="role_filter")
    
    if role_filter != "Tất cả":
        users = [user for user in users if user['role'] == role_filter]

    # Hiển thị người dùng
    for user in users:
        role_icon = "👨‍🏫" if user['role'] == 'teacher' else "👨‍🎓"
        with st.container():
            # Điều chỉnh lại số cột để có thêm không gian
            col1, col2, col3 = st.columns([3, 2, 1]) 
            
            with col1:
                st.markdown(f"**{role_icon} {user.get('ho_ten', 'Chưa có tên')}**")
                
                # --- BẮT ĐẦU THAY ĐỔI ---
                # Lấy thông tin email và số điện thoại
                email = user.get('email', 'N/A')
                phone = user.get('so_dien_thoai') # Lấy sđt

                # Xây dựng chuỗi caption một cách linh hoạt
                caption_parts = [f"@{user.get('username', 'N/A')}", f"📧 {email}"]
                if phone:
                    caption_parts.append(f"📱 {phone}")
                
                st.caption(" | ".join(caption_parts))
                # --- KẾT THÚC THAY ĐỔI ---

            with col2:
                status = "✅ Hoạt động" if user.get('is_active', True) else "🔒 Bị khóa"
                st.write(status)
                
                created_at_str = user.get('created_at', '')
                if created_at_str:
                    created_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).strftime('%d/%m/%Y')
                    st.caption(f"Tham gia: {created_date}")
            
            with col3:
                # Menu hành động dạng Popover
                with st.popover("Hành động", use_container_width=True):
                    if st.button("✏️ Sửa", key=f"edit_{user['id']}", use_container_width=True):
                        st.session_state.editing_user = user
                        st.rerun()

                    if st.button("🔑 Reset Mật khẩu", key=f"reset_pw_{user['id']}", use_container_width=True):
                        st.session_state.resetting_password_for_user = user
                        st.rerun()
                    
                    if st.button("🗑️ Xóa", type="secondary", key=f"delete_{user['id']}", use_container_width=True):
                        if db.admin_delete_user(user['id']):
                            st.rerun()

            st.divider()

    # --- FORM SỬA THÔNG TIN (POPUP) ---
    if st.session_state.get("editing_user"):
        editing_user = st.session_state.editing_user
        with st.form(key=f"edit_form_{editing_user['id']}"):
            st.subheader(f"✏️ Chỉnh sửa: {editing_user['ho_ten']}")
            new_ho_ten = st.text_input("Họ và tên", value=editing_user['ho_ten'])
            new_email = st.text_input("Email", value=editing_user['email'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Lưu thay đổi"):
                    if db.admin_update_user(editing_user['id'], ho_ten=new_ho_ten, email=new_email):
                        del st.session_state.editing_user
                        st.rerun()
            with col2:
                 if st.form_submit_button("❌ Hủy"):
                     del st.session_state.editing_user
                     st.rerun()

    # --- FORM RESET MẬT KHẨU (POPUP) ---
    if st.session_state.get("resetting_password_for_user"):
        reset_user = st.session_state.resetting_password_for_user
        with st.form(key=f"reset_form_{reset_user['id']}"):
            st.subheader(f"🔑 Reset mật khẩu cho: {reset_user['ho_ten']}")
            new_password = st.text_input("Mật khẩu mới", type="password")
            confirm_new_password = st.text_input("Xác nhận mật khẩu mới", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🔑 Reset"):
                    if not new_password:
                        st.error("Mật khẩu không được để trống.")
                    elif new_password != confirm_new_password:
                        st.error("Mật khẩu xác nhận không khớp.")
                    else:
                        if db.admin_reset_password(reset_user['id'], new_password):
                            del st.session_state.resetting_password_for_user
                            st.rerun()
            with col2:
                if st.form_submit_button("❌ Hủy"):
                    del st.session_state.resetting_password_for_user
                    st.rerun()