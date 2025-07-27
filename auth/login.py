import streamlit as st
from database.supabase_models import SupabaseDatabase
from datetime import datetime, timedelta
import hashlib
import time

# Initialize database
@st.cache_resource
def get_db():
    return SupabaseDatabase()

def show_login_page():
    """Hiển thị trang đăng nhập"""
    st.title("🎓 Hệ thống Quản lý Thi Trực tuyến")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Đăng nhập")
        
        # Login form
        with st.form("login_form"):
            username = st.text_input(
                "👤 Tên đăng nhập", 
                placeholder="Nhập username...",
                key="login_username"
            )
            
            password = st.text_input(
                "🔑 Mật khẩu", 
                type="password",
                placeholder="Nhập mật khẩu...",
                key="login_password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                login_button = st.form_submit_button(
                    "🚀 Đăng nhập", 
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                demo_button = st.form_submit_button(
                    "🎯 Demo", 
                    use_container_width=True,
                    help="Đăng nhập với tài khoản demo"
                )
        
        # Handle login
        if login_button:
            if not username or not password:
                st.error("❌ Vui lòng nhập đầy đủ thông tin!")
            else:
                handle_login(username, password)
        
        # Handle demo login
        if demo_button:
            show_demo_accounts()
        
        # Show sample accounts
        with st.expander("📋 Tài khoản mẫu", expanded=False):
            st.info("""
            **🎯 Để test hệ thống, sử dụng các tài khoản sau:**
            
            **👨‍💼 Admin:**
            - Username: `admin`
            - Password: `admin123`
            
            **👨‍🏫 Giáo viên:**
            - Username: `teacher1`
            - Password: `teacher123`
            
            **👨‍🎓 Học sinh:**
            - Username: `student1`
            - Password: `student123`
            """)
        
        # System info
        with st.expander("ℹ️ Thông tin hệ thống", expanded=False):
            st.info("""
            **🔧 Tính năng hiện có:**
            - ✅ Đăng nhập/đăng xuất
            - ✅ Dashboard giáo viên
            - ✅ Quản lý lớp học
            - ✅ Quản lý học sinh
            - ✅ Import học sinh từ Excel
            - ✅ Upload đề thi từ Word (word_parser.py)
            
            **🚧 Đang phát triển:**
            - 📝 Tạo đề thi hoàn chỉnh
            - ✅ Chấm bài tự động
            - 📊 Báo cáo thống kê
            - 👨‍🎓 Giao diện học sinh
            """)

def show_demo_accounts():
    """Hiển thị các tài khoản demo để đăng nhập nhanh"""
    st.markdown("### 🎯 Đăng nhập Demo")
    
    demo_accounts = [
        {"username": "admin", "password": "admin123", "role": "👨‍💼 Admin", "desc": "Quản trị hệ thống"},
        {"username": "teacher1", "password": "teacher123", "role": "👨‍🏫 Giáo viên", "desc": "Tạo đề thi, quản lý lớp"},
        {"username": "student1", "password": "student123", "role": "👨‍🎓 Học sinh", "desc": "Làm bài thi"}
    ]
    
    for account in demo_accounts:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{account['role']}**: {account['desc']}")
            st.caption(f"Username: `{account['username']}` • Password: `{account['password']}`")
        
        with col2:
            if st.button(f"Đăng nhập", key=f"demo_{account['username']}"):
                handle_login(account['username'], account['password'])

def handle_login(username: str, password: str):
    """Xử lý đăng nhập"""
    try:
        db = get_db()
        
        with st.spinner("🔍 Đang xác thực..."):
            user = db.authenticate_user(username, password)
        
        if user:
            # Set session
            st.session_state.user = user
            st.session_state.login_time = datetime.now()
            st.session_state.is_logged_in = True
            
            # Show success and redirect
            st.success(f"✅ Đăng nhập thành công! Xin chào {user['ho_ten']}")
            
            # Log login activity
            log_user_activity(user['id'], 'login', {'ip': get_client_ip()})
            
            time.sleep(1)  # Brief pause for user to see success message
            st.rerun()
        
        else:
            st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác!")
            
            # Log failed login
            log_failed_login(username, get_client_ip())
    
    except Exception as e:
        st.error(f"❌ Lỗi hệ thống: {str(e)}")
        st.error("🔧 Vui lòng kiểm tra kết nối database!")

def get_current_user():
    """Lấy thông tin user hiện tại"""
    return st.session_state.get('user')

def is_logged_in():
    """Kiểm tra trạng thái đăng nhập"""
    if not st.session_state.get('is_logged_in', False):
        return False
    
    # Check session timeout
    login_time = st.session_state.get('login_time')
    if login_time:
        session_timeout = timedelta(hours=1)  # 1 hour timeout
        if datetime.now() - login_time > session_timeout:
            logout_user()
            st.warning("⏰ Phiên đăng nhập đã hết hạn!")
            return False
    
    return True

def logout_user():
    """Đăng xuất user"""
    user = get_current_user()
    
    if user:
        # Log logout activity
        log_user_activity(user['id'], 'logout', {'duration': get_session_duration()})
    
    # Clear session
    for key in ['user', 'login_time', 'is_logged_in']:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear other session data
    keys_to_clear = [key for key in st.session_state.keys() if key.startswith(('show_', 'edit_', 'selected_', 'current_'))]
    for key in keys_to_clear:
        del st.session_state[key]

def require_role(required_roles):
    """Decorator để yêu cầu quyền truy cập"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                st.error("❌ Vui lòng đăng nhập!")
                return
            
            if user['role'] not in required_roles:
                st.error(f"❌ Bạn không có quyền truy cập! Yêu cầu: {', '.join(required_roles)}")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_login(func):
    """Decorator để yêu cầu đăng nhập"""
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            st.error("❌ Vui lòng đăng nhập để tiếp tục!")
            show_login_page()
            return
        return func(*args, **kwargs)
    return wrapper

# Utility functions
def get_client_ip():
    """Lấy IP client (simplified)"""
    try:
        # In production, you might want to get real IP from headers
        return st.session_state.get('client_ip', 'unknown')
    except:
        return 'unknown'

def get_session_duration():
    """Lấy thời gian session"""
    login_time = st.session_state.get('login_time')
    if login_time:
        duration = datetime.now() - login_time
        return int(duration.total_seconds())
    return 0

def log_user_activity(user_id: int, activity: str, details: dict = None):
    """Log hoạt động user (simplified)"""
    try:
        # In a real system, you'd want to log this to database
        # For now, just store in session state
        if 'user_activities' not in st.session_state:
            st.session_state.user_activities = []
        
        activity_log = {
            'user_id': user_id,
            'activity': activity,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        st.session_state.user_activities.append(activity_log)
        
        # Keep only last 100 activities
        if len(st.session_state.user_activities) > 100:
            st.session_state.user_activities = st.session_state.user_activities[-100:]
    
    except Exception as e:
        # Don't fail the main flow if logging fails
        pass

def log_failed_login(username: str, ip: str):
    """Log failed login attempts"""
    try:
        # In a real system, you'd track failed login attempts
        # and implement rate limiting
        if 'failed_logins' not in st.session_state:
            st.session_state.failed_logins = []
        
        failed_login = {
            'username': username,
            'ip': ip,
            'timestamp': datetime.now().isoformat()
        }
        
        st.session_state.failed_logins.append(failed_login)
        
        # Keep only last 50 failed attempts
        if len(st.session_state.failed_logins) > 50:
            st.session_state.failed_logins = st.session_state.failed_logins[-50:]
    
    except Exception as e:
        pass

def hash_session_token(user_id: int, timestamp: str):
    """Generate session token"""
    data = f"{user_id}:{timestamp}:exam_system_secret"
    return hashlib.sha256(data.encode()).hexdigest()[:32]

def check_password_strength(password: str):
    """Kiểm tra độ mạnh mật khẩu"""
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    
    if not any(c.isalpha() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ cái"
    
    if not any(c.isdigit() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ số"
    
    return True, "Mật khẩu hợp lệ"

# Session management
def get_session_info():
    """Lấy thông tin session hiện tại"""
    user = get_current_user()
    login_time = st.session_state.get('login_time')
    
    if not user or not login_time:
        return None
    
    duration = datetime.now() - login_time
    
    return {
        'user': user,
        'login_time': login_time,
        'duration': duration,
        'duration_minutes': int(duration.total_seconds() / 60)
    }

def extend_session():
    """Gia hạn session"""
    if is_logged_in():
        st.session_state.login_time = datetime.now()
        return True
    return False