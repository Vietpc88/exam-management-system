import streamlit as st
from datetime import datetime, timedelta
from database.models import authenticate_user, create_user, get_students

def show_login_page():
    """Hiển thị trang đăng nhập"""
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1>🎓 Hệ thống Thi Trực tuyến</h1>
            <p style='font-size: 18px; color: #666;'>Đăng nhập để bắt đầu</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký học sinh"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()

def show_login_form():
    """Form đăng nhập"""
    st.subheader("Đăng nhập hệ thống")
    
    with st.form("login_form", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
        
        with col2:
            role = st.selectbox("Vai trò", ["student", "teacher"], 
                              format_func=lambda x: "👨‍🎓 Học sinh" if x == "student" else "👨‍🏫 Giáo viên")
        
        submit_button = st.form_submit_button("🚀 Đăng nhập", use_container_width=True)
        
        if submit_button:
            if not username or not password:
                st.error("❌ Vui lòng nhập đầy đủ thông tin!")
                return
            
            user = authenticate_user(username, password, role)
            if user:
                # Lưu thông tin user vào session
                st.session_state.user = user
                st.session_state.login_time = datetime.now()
                
                st.success(f"✅ Đăng nhập thành công! Chào mừng {user['full_name']}")
                st.rerun()
            else:
                st.error("❌ Sai tên đăng nhập, mật khẩu hoặc vai trò!")
    
    # Thông tin tài khoản mặc định
    st.info("""
        **Tài khoản mặc định:**
        - Giáo viên: `admin` / `admin123`
        - Học sinh: Đăng ký tài khoản mới ở tab bên cạnh
    """)

def show_register_form():
    """Form đăng ký học sinh"""
    st.subheader("Đăng ký tài khoản học sinh")
    
    with st.form("register_form", clear_on_submit=True):
        username = st.text_input("Tên đăng nhập", placeholder="Ví dụ: nguyenvana")
        password = st.text_input("Mật khẩu", type="password", placeholder="Tối thiểu 6 ký tự")
        confirm_password = st.text_input("Xác nhận mật khẩu", type="password")
        full_name = st.text_input("Họ và tên", placeholder="Ví dụ: Nguyễn Văn A")
        email = st.text_input("Email (tùy chọn)", placeholder="example@email.com")
        phone = st.text_input("Số điện thoại (tùy chọn)", placeholder="0123456789")
        
        submit_button = st.form_submit_button("📝 Đăng ký", use_container_width=True)
        
        if submit_button:
            # Validate form
            if not username or not password or not full_name:
                st.error("❌ Vui lòng nhập đầy đủ thông tin bắt buộc!")
                return
            
            if len(password) < 6:
                st.error("❌ Mật khẩu phải có ít nhất 6 ký tự!")
                return
            
            if password != confirm_password:
                st.error("❌ Mật khẩu xác nhận không khớp!")
                return
            
            # Tạo tài khoản mới
            user_id = create_user(username, password, "student", full_name, email, phone)
            
            if user_id:
                st.success("✅ Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.")
                st.balloons()
            else:
                st.error("❌ Tên đăng nhập đã tồn tại! Vui lòng chọn tên khác.")

def check_authentication():
    """Kiểm tra trạng thái đăng nhập"""
    if "user" not in st.session_state or st.session_state.user is None:
        return False
    
    # Kiểm tra session timeout
    if "login_time" in st.session_state:
        session_duration = datetime.now() - st.session_state.login_time
        if session_duration > timedelta(hours=8):  # Session timeout 8 giờ
            logout()
            return False
    
    return True

def logout():
    """Đăng xuất"""
    if "user" in st.session_state:
        del st.session_state.user
    if "login_time" in st.session_state:
        del st.session_state.login_time
    st.rerun()

def require_role(required_role):
    """Decorator kiểm tra quyền truy cập"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication():
                st.error("❌ Vui lòng đăng nhập để tiếp tục!")
                show_login_page()
                return
            
            if st.session_state.user['role'] != required_role:
                st.error(f"❌ Bạn không có quyền truy cập trang này! (Yêu cầu: {required_role})")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user():
    """Lấy thông tin user hiện tại"""
    return st.session_state.get('user', None)

def show_user_info():
    """Hiển thị thông tin user và nút logout"""
    user = get_current_user()
    if user:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            role_emoji = "👨‍🏫" if user['role'] == 'teacher' else "👨‍🎓"
            st.write(f"{role_emoji} **{user['full_name']}** ({user['username']})")
        
        with col2:
            if st.button("👤 Thông tin"):
                show_user_profile()
        
        with col3:
            if st.button("🚪 Đăng xuất"):
                logout()

def show_user_profile():
    """Hiển thị thông tin chi tiết user"""
    user = get_current_user()
    if user:
        with st.expander("👤 Thông tin tài khoản", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Tên đăng nhập:** {user['username']}")
                st.write(f"**Họ tên:** {user['full_name']}")
                st.write(f"**Vai trò:** {'Giáo viên' if user['role'] == 'teacher' else 'Học sinh'}")
            
            with col2:
                st.write(f"**Email:** {user.get('email', 'Chưa cập nhật')}")
                st.write(f"**Điện thoại:** {user.get('phone', 'Chưa cập nhật')}")
                st.write(f"**Ngày tạo:** {user['created_at']}")