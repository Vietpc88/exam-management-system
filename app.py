import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from auth.login import show_login_page, get_current_user, logout_user, is_logged_in
from teacher.dashboard import teacher_dashboard
from config.supabase_config import test_connection, get_database_info
from database.supabase_models import SupabaseDatabase

# Page config
st.set_page_config(
    page_title="Hệ thống Quản lý Thi Trực tuyến",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    """Initialize database connection"""
    return SupabaseDatabase()

def show_system_status():
    """Hiển thị trạng thái hệ thống"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔧 Trạng thái Hệ thống")
        
        # Test database connection
        is_connected, message = test_connection()
        
        if is_connected:
            st.success("✅ Database: Kết nối OK")
        else:
            st.error("❌ Database: Lỗi kết nối")
            st.error(message)
        
        # Show database info
        if st.checkbox("📊 Thông tin Database", key="show_db_info"):
            db_info = get_database_info()
            st.write("**Bảng dữ liệu:**")
            for table, desc in db_info['tables'].items():
                st.caption(f"• {table}: {desc}")

def show_admin_panel():
    """Panel admin cơ bản"""
    st.header("👨‍💼 Admin Panel")
    
    st.info("🚧 Tính năng Admin đang được phát triển...")
    
    # Quick stats
    db = init_database()
    
    try:
        # Get basic stats
        users_result = db.client.table('users').select('role', count='exact').execute()
        classes_result = db.client.table('classes').select('id', count='exact').execute()
        exams_result = db.client.table('exams').select('id', count='exact').execute()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Tổng Users", users_result.count or 0)
        
        with col2:
            st.metric("📚 Tổng Lớp", classes_result.count or 0)
        
        with col3:
            st.metric("📝 Tổng Đề thi", exams_result.count or 0)
        
        # User breakdown
        st.subheader("📊 Phân bố Users")
        users_by_role = db.client.table('users').select('role').execute()
        
        role_counts = {}
        for user in users_by_role.data:
            role = user['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👨‍💼 Admin", role_counts.get('admin', 0))
        with col2:
            st.metric("👨‍🏫 Teacher", role_counts.get('teacher', 0))
        with col3:
            st.metric("👨‍🎓 Student", role_counts.get('student', 0))
        
        # Recent users
        st.subheader("👥 Users gần đây")
        recent_users = db.client.table('users').select('ho_ten, username, role, created_at').order('created_at', desc=True).limit(5).execute()
        
        if recent_users.data:
            for user in recent_users.data:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        role_icon = {"admin": "👨‍💼", "teacher": "👨‍🏫", "student": "👨‍🎓"}[user['role']]
                        st.write(f"{role_icon} **{user['ho_ten']}** (@{user['username']})")
                    with col2:
                        st.caption(user['role'].title())
                    with col3:
                        st.caption(user['created_at'][:10])
                    st.divider()
    
    except Exception as e:
        st.error(f"Lỗi lấy thống kê: {e}")

def show_student_panel():
    """Panel học sinh cơ bản"""
    st.header("👨‍🎓 Student Dashboard")
    
    user = get_current_user()
    st.info(f"Xin chào {user['ho_ten']}!")
    
    st.info("🚧 Tính năng Student đang được phát triển...")
    
    # Quick info
    db = init_database()
    
    try:
        # Get student's classes (UUID version)
        classes = db.get_classes_by_student(user['id'])  # user['id'] is UUID string
        
        st.subheader("📚 Lớp học của bạn")
        
        if classes:
            for class_info in classes:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**📋 {class_info['ten_lop']}** ({class_info['ma_lop']})")
                        if class_info.get('mo_ta'):
                            st.caption(class_info['mo_ta'])
                        st.caption(f"👨‍🏫 GV: {class_info.get('teacher_name', 'N/A')}")
                    
                    with col2:
                        st.caption(f"Tham gia: {class_info['joined_at'][:10]}")
                    
                    st.divider()
                    
            # Student stats
            st.subheader("📊 Thống kê của bạn")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📚 Lớp tham gia", len(classes))
            
            with col2:
                # TODO: Đếm đề thi available
                st.metric("📝 Đề thi khả dụng", "0")
            
            with col3:
                # TODO: Đếm bài đã nộp
                st.metric("📊 Bài đã nộp", "0")
                
        else:
            st.info("📚 Bạn chưa tham gia lớp học nào.")
            st.caption("Liên hệ giáo viên để được thêm vào lớp.")
    
    except Exception as e:
        st.error(f"Lỗi lấy thông tin lớp: {e}")
        
        # Show user ID for debugging
        with st.expander("🐛 Debug Info", expanded=False):
            st.code(f"User ID: {user['id']}")
            st.code(f"Error: {str(e)}")

def main():
    """Main application function - Entry point for app.py"""
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Show system status in sidebar
    show_system_status()
    
    # Check if user is logged in
    if not is_logged_in():
        show_login_page()
        return
    
    # Get current user
    user = get_current_user()
    
    if not user:
        st.error("❌ Phiên đăng nhập không hợp lệ!")
        logout_user()
        st.rerun()
        return
    
    # Sidebar user info and logout
    with st.sidebar:
        st.markdown("---")
        st.subheader(f"👋 Xin chào, {user['ho_ten']}")
        st.caption(f"@{user['username']} • {user['role'].title()}")
        
        if st.button("🚪 Đăng xuất", use_container_width=True):
            logout_user()
            st.rerun()
    
    # Route based on user role
    if user['role'] == 'admin':
        show_admin_panel()
    
    elif user['role'] == 'teacher':
        teacher_dashboard()
    
    elif user['role'] == 'student':
        show_student_panel()
    
    else:
        st.error("❌ Vai trò người dùng không hợp lệ!")
        logout_user()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Lỗi ứng dụng: {str(e)}")
        st.error("🔧 Vui lòng kiểm tra cấu hình và thử lại!")
        
        # Show debug info in development
        if st.checkbox("🐛 Hiển thị thông tin debug"):
            st.exception(e)