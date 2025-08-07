import streamlit as st
from database.supabase_models import get_database
from datetime import datetime, timedelta
import time

def show_login_page():
    """Hiển thị giao diện đăng nhập."""
    st.title("🎓 Hệ thống Quản lý Thi Trực tuyến")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Đăng nhập")
        with st.form("login_form"):
            username = st.text_input("👤 Tên đăng nhập", placeholder="Nhập username...")
            password = st.text_input("🔑 Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
            login_button = st.form_submit_button("🚀 Đăng nhập", use_container_width=True, type="primary")
        
        if login_button:
            if not username or not password:
                st.error("❌ Vui lòng nhập đầy đủ thông tin!")
            else:
                handle_login(username, password)

def handle_login(username: str, password: str):
    """Xử lý đăng nhập, đồng bộ hóa session với Supabase client."""
    db = get_database()
    try:
        with st.spinner("🔍 Đang kiểm tra thông tin..."):
            user_profile = db.get_user_by_username(username)
        
        if not user_profile or not user_profile.get('email'):
            st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác!")
            return

        with st.spinner("🔐 Đang xác thực..."):
            supabase_client = db.client 
            auth_response = supabase_client.auth.sign_in_with_password({
                "email": user_profile['email'], 
                "password": password
            })
        
        st.session_state.is_logged_in = True
        st.session_state.user = user_profile
        st.session_state.login_time = datetime.now()
        
        st.success(f"✅ Đăng nhập thành công! Xin chào {user_profile.get('ho_ten', 'bạn')}")
        time.sleep(1)
        st.rerun()
            
    except Exception as e:
        if 'Invalid login credentials' in str(e):
            st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác!")
        else:
            st.error(f"❌ Lỗi hệ thống khi đăng nhập: Vui lòng thử lại.")
        print(f"LOGIN EXCEPTION: {e}")

def is_logged_in():
    """Kiểm tra trạng thái đăng nhập."""
    return st.session_state.get('is_logged_in', False)

def get_current_user():
    """Lấy thông tin của người dùng đang đăng nhập."""
    return st.session_state.get('user')

def logout_user():
    """Đăng xuất người dùng."""
    try:
        db = get_database()
        db.client.auth.sign_out()
    except Exception as e:
        print(f"Error during Supabase sign out: {e}")

    keys_to_clear = list(st.session_state.keys())
    for key in keys_to_clear:
        del st.session_state[key]
    st.rerun()