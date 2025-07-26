import streamlit as st
from database.supabase_models import SupabaseDatabase

class SupabaseAuth:
    def __init__(self):
        self.db = SupabaseDatabase()
    
    def login(self, username: str, password: str) -> bool:
        """Đăng nhập user"""
        user = self.db.authenticate_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user['id']
            st.session_state.username = user['username']
            st.session_state.user_role = user['role']
            st.session_state.user_info = user
            return True
        return False
    
    def logout(self):
        """Đăng xuất"""
        for key in ['logged_in', 'user_id', 'username', 'user_role', 'user_info']:
            if key in st.session_state:
                del st.session_state[key]
    
    def register(self, username: str, password: str, ho_ten: str, email: str = None, so_dien_thoai: str = None) -> bool:
        """Đăng ký user mới"""
        return self.db.create_user(username, password, ho_ten, email, so_dien_thoai)
    
    def is_logged_in(self) -> bool:
        """Kiểm tra đã đăng nhập chưa"""
        return st.session_state.get('logged_in', False)
    
    def get_current_user(self) -> dict:
        """Lấy thông tin user hiện tại"""
        return st.session_state.get('user_info', {})
    
    def require_login(self):
        """Decorator yêu cầu đăng nhập"""
        if not self.is_logged_in():
            st.error("Vui lòng đăng nhập để tiếp tục!")
            st.stop()