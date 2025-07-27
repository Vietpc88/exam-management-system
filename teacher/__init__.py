import streamlit as st
import os
import sys
from datetime import datetime

# ==============================================================================
# BỘ KHỞI ĐỘNG DỰ ÁN (Project Bootstrapper)
# ==============================================================================
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
except Exception as e:
    st.error(f"Lỗi khởi tạo đường dẫn hệ thống: {e}")
    st.stop()

# ==============================================================================
# IMPORT CÁC MODULE CHÍNH
# ==============================================================================
try:
    # Authentication
    from auth.login import (
        show_login_page, 
        is_logged_in, 
        get_current_user, 
        logout_user,
        get_session_info
    )
    
    # Database
    from database.supabase_models import get_database
    
    # Teacher modules - Main features
    from teacher.exam_creation import show_create_exam
    from teacher.grading import show_grading
    from teacher.statistics import show_statistics
    
except ImportError as e:
    st.error(f"❌ Lỗi Import Module: {e}")
    st.error("Vui lòng kiểm tra cấu trúc thư mục và các file cần thiết.")
    st.stop()

# ==============================================================================
# IMPORT CÁC MODULE PHỤ (Với fallback nếu chưa có)
# ==============================================================================
try:
    from teacher.manage_classes import show_manage_classes
except ImportError:
    def show_manage_classes():
        st.header("🏫 Quản lý Lớp học")
        st.info("📚 Module quản lý lớp học đang được phát triển...")
        
        # Basic class management placeholder
        user = get_current_user()
        db = get_database()
        
        try:
            classes = db.get_classes_by_teacher(user['id'])
            if classes:
                st.write("### 📋 Danh sách lớp hiện có:")
                for cls in classes:
                    with st.expander(f"📚 {cls['ten_lop']}", expanded=False):
                        st.write(f"**Mô tả:** {cls.get('mo_ta', 'Không có mô tả')}")
                        st.write(f"**Số học sinh:** {db.get_class_student_count(cls['id'])}")
                        st.write(f"**Tạo lúc:** {cls.get('created_at', 'N/A')}")
            else:
                st.info("📝 Chưa có lớp học nào. Tính năng tạo lớp sẽ được bổ sung.")
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách lớp: {str(e)}")

try:
    from teacher.manage_students import show_manage_students
except ImportError:
    def show_manage_students():
        st.header("👥 Quản lý Học sinh")
        st.info("👨‍🎓 Module quản lý học sinh đang được phát triển...")
        
        # Basic student management placeholder
        user = get_current_user()
        db = get_database()
        
        try:
            classes = db.get_classes_by_teacher(user['id'])
            if classes:
                st.write("### 📋 Học sinh theo lớp:")
                for cls in classes:
                    with st.expander(f"📚 {cls['ten_lop']}", expanded=False):
                        students = db.get_students_in_class(cls['id'])
                        if students:
                            for student in students:
                                st.write(f"👤 **{student['ho_ten']}** (@{student['username']})")
                        else:
                            st.info("Chưa có học sinh nào trong lớp này")
            else:
                st.info("📝 Chưa có lớp học nào.")
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách học sinh: {str(e)}")

# Student modules (placeholders)
def show_my_classes():
    st.header("📚 Lớp học của tôi")
    st.info("👨‍🎓 Module lớp học học sinh đang được phát triển...")

def show_take_exam():
    st.header("📝 Làm bài thi")
    st.info("✍️ Module làm bài thi đang được phát triển...")

def show_view_results():
    st.header("📊 Xem kết quả")
    st.info("📈 Module xem kết quả đang được phát triển...")

# ==============================================================================
# CẤU HÌNH TRANG
# ==============================================================================
st.set_page_config(
    page_title="Hệ thống Thi Trực tuyến",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem; border-radius: 15px; color: white;
        text-align: center; margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f0f2f6 0%, #e6e9ed 100%);
    }
    .stButton > button {
        border-radius: 25px; border: 2px solid #667eea;
        padding: 0.75rem 1.5rem; font-weight: 600; 
        transition: all 0.3s ease;
        background-color: white; color: #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px); 
        box-shadow: 0 6px 20px rgba(102,126,234,0.3);
        background-color: #667eea; color: white;
    }
    .info-box {
        background: linear-gradient(135deg, #e9eafc 0%, #f0f2f6 100%);
        border: 2px solid #d6d8fb; border-radius: 15px; 
        padding: 1.5rem; margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .metric-container {
        background: white; border-radius: 15px; padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 0.5rem 0;
        border: 1px solid #f0f0f0;
    }
    .success-alert {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #b8daff; color: #155724;
        padding: 1rem; border-radius: 10px; margin: 1rem 0;
    }
    .error-alert {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 2px solid #f1b0b7; color: #721c24;
        padding: 1rem; border-radius: 10px; margin: 1rem 0;
    }
    .status-indicator {
        display: inline-block;
        width: 10px; height: 10px; border-radius: 50%;
        margin-right: 8px;
    }
    .status-online { background-color: #28a745; }
    .status-offline { background-color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# KHỞI TẠO DATABASE
# ==============================================================================
@st.cache_resource
def init_database():
    """Khởi tạo database connection"""
    try:
        db = get_database()
        # Test connection
        if hasattr(db, 'test_connection'):
            if db.test_connection():
                return db, True
        return db, False
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Database: {e}")
        return None, False

# ==============================================================================
# SIDEBAR VÀ NAVIGATION
# ==============================================================================
def show_sidebar():
    """Hiển thị sidebar với navigation"""
    with st.sidebar:
        # Header
        st.markdown("""
            <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 15px; margin-bottom: 1rem;'>
                <h2 style='color: white; margin: 0;'>🎓 Exam System</h2>
            </div>
        """, unsafe_allow_html=True)
        
        user = get_current_user()
        if not user:
            return

        # User info
        role_emoji = {"teacher": "👨‍🏫", "student": "👨‍🎓", "admin": "👨‍💼"}.get(user['role'], "👤")
        role_name = {"teacher": "Giáo viên", "student": "Học sinh", "admin": "Quản trị"}.get(user['role'], "Người dùng")
        
        st.markdown(f"""
            <div class='info-box'>
                <h4>{role_emoji} {role_name}</h4>
                <p><strong>{user.get('ho_ten', 'N/A')}</strong></p>
                <p>@{user.get('username', 'N/A')}</p>
                <small>📧 {user.get('email', 'N/A')}</small>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation menu
        if user['role'] == 'teacher':
            show_teacher_menu()
        elif user['role'] == 'student':
            show_student_menu()
        elif user['role'] == 'admin':
            show_admin_menu()
        
        st.divider()
        
        # System status
        show_system_status()
        
        # Session info
        show_session_info()
        
        # Logout button
        if st.button("🚪 Đăng xuất", use_container_width=True, type="secondary"):
            logout_user()
            st.success("✅ Đã đăng xuất thành công!")
            st.rerun()

def show_teacher_menu():
    """Menu cho giáo viên"""
    st.markdown("### 👨‍🏫 Menu Giáo viên")
    
    menu_items = [
        ("🏫 Quản lý Lớp học", "manage_classes", "Tạo và quản lý các lớp học"),
        ("👥 Quản lý Học sinh", "manage_students", "Quản lý danh sách học sinh"),
        ("📝 Tạo Đề thi", "create_exam", "Tạo đề thi mới với nhiều loại câu hỏi"),
        ("✅ Chấm bài", "grading", "Chấm bài và quản lý điểm số"),
        ("📊 Thống kê", "statistics", "Xem báo cáo và thống kê chi tiết")
    ]
    
    for icon_name, page_key, description in menu_items:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button(icon_name, use_container_width=True, key=f"btn_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()
        
        with col2:
            st.markdown(f"<small>{description}</small>", unsafe_allow_html=True)

def show_student_menu():
    """Menu cho học sinh"""
    st.markdown("### 👨‍🎓 Menu Học sinh")
    
    menu_items = [
        ("📚 Lớp học của tôi", "my_classes", "Xem các lớp đã tham gia"),
        ("📝 Làm bài thi", "take_exam", "Thi trực tuyến"),
        ("📊 Xem kết quả", "view_results", "Kết quả và nhận xét")
    ]
    
    for icon_name, page_key, description in menu_items:
        if st.button(icon_name, use_container_width=True, key=f"btn_{page_key}"):
            st.session_state.current_page = page_key
            st.rerun()
        st.caption(description)

def show_admin_menu():
    """Menu cho admin"""
    st.markdown("### 👨‍💼 Menu Quản trị")
    
    menu_items = [
        ("👥 Quản lý Người dùng", "manage_users"),
        ("🏫 Quản lý Hệ thống", "system_manage"), 
        ("📊 Thống kê Tổng quan", "system_statistics"),
        ("🔧 Cài đặt", "system_settings")
    ]
    
    for icon_name, page_key in menu_items:
        if st.button(icon_name, use_container_width=True, key=f"btn_{page_key}"):
            st.session_state.current_page = page_key
            st.rerun()

def show_system_status():
    """Hiển thị trạng thái hệ thống"""
    st.markdown("### 🔧 Trạng thái hệ thống")
    
    # Database status
    db, db_status = init_database()
    db_color = "status-online" if db_status else "status-offline"
    db_text = "Kết nối OK" if db_status else "Lỗi kết nối"
    
    st.markdown(f"""
        <div style='font-size: 14px;'>
            <span class='status-indicator {db_color}'></span>
            Database: {db_text}
        </div>
    """, unsafe_allow_html=True)

def show_session_info():
    """Hiển thị thông tin session"""
    session_info = get_session_info()
    
    if session_info:
        st.markdown("### ⏱️ Thông tin phiên")
        st.caption(f"🕐 Đăng nhập: {session_info['login_time'].strftime('%H:%M:%S')}")
        st.caption(f"⏲️ Thời gian: {session_info['duration_minutes']} phút")
    
    # Current time
    st.markdown(f"""
        <div style='text-align: center; color: #666; font-size: 12px; margin-top: 10px;'>
            🕐 {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# MAIN DASHBOARD FUNCTIONS
# ==============================================================================
def teacher_dashboard():
    """Dashboard chính cho giáo viên"""
    page = st.session_state.get('current_page', 'manage_classes')
    
    try:
        if page == "manage_classes":
            show_manage_classes()
        elif page == "manage_students":
            show_manage_students()
        elif page == "create_exam":
            show_create_exam()
        elif page == "grading":
            show_grading()
        elif page == "statistics":
            show_statistics()
        else:
            st.error(f"❌ Trang '{page}' không tồn tại!")
            st.session_state.current_page = "manage_classes"
            st.rerun()
            
    except Exception as e:
        show_error_page(f"Lỗi tải trang '{page}'", str(e))

def student_dashboard():
    """Dashboard chính cho học sinh"""
    page = st.session_state.get('current_page', 'my_classes')
    
    try:
        if page == "my_classes":
            show_my_classes()
        elif page == "take_exam":
            show_take_exam()
        elif page == "view_results":
            show_view_results()
        else:
            st.error(f"❌ Trang '{page}' không tồn tại!")
            st.session_state.current_page = "my_classes"
            st.rerun()
            
    except Exception as e:
        show_error_page(f"Lỗi tải trang '{page}'", str(e))

def admin_dashboard():
    """Dashboard chính cho admin"""
    page = st.session_state.get('current_page', 'manage_users')
    
    st.header("👨‍💼 Quản trị Hệ thống")
    st.info("🔧 Các chức năng quản trị đang được phát triển...")
    
    # Basic admin info
    user = get_current_user()
    db, db_status = init_database()
    
    if db_status and db:
        try:
            # System statistics
            st.write("### 📊 Thống kê hệ thống")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Get basic stats (simplified)
            try:
                # This would need proper admin methods in SupabaseDatabase
                with col1:
                    st.metric("👥 Tổng người dùng", "N/A")
                
                with col2:
                    st.metric("🏫 Tổng lớp học", "N/A")
                
                with col3:
                    st.metric("📝 Tổng đề thi", "N/A")
                
                with col4:
                    st.metric("📊 Bài làm hôm nay", "N/A")
                    
            except Exception as e:
                st.warning(f"⚠️ Chưa thể lấy thống kê: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Lỗi admin dashboard: {str(e)}")

def show_error_page(title: str, error_msg: str):
    """Hiển thị trang lỗi"""
    st.error(f"❌ {title}")
    
    with st.expander("🔍 Chi tiết lỗi", expanded=False):
        st.code(error_msg)
        
        # Debug info
        st.write("**Session State Debug:**")
        debug_info = {k: str(v)[:100] + "..." if len(str(v)) > 100 else str(v) 
                     for k, v in st.session_state.items()}
        st.json(debug_info)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Tải lại trang", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("🏠 Về trang chủ"):
            user = get_current_user()
            if user:
                if user['role'] == 'teacher':
                    st.session_state.current_page = "manage_classes"
                elif user['role'] == 'student':
                    st.session_state.current_page = "my_classes"
                elif user['role'] == 'admin':
                    st.session_state.current_page = "manage_users"
            st.rerun()

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================
def main():
    """Hàm chính của ứng dụng"""
    
    # Initialize database
    db, db_status = init_database()
    
    if not db_status:
        st.error("❌ Không thể kết nối Database! Vui lòng kiểm tra cấu hình Supabase.")
        st.info("🔧 Kiểm tra file .env và đảm bảo Supabase đang hoạt động.")
        st.stop()
    
    # Check authentication
    if not is_logged_in():
        show_login_page()
        return
    
    # Get current user
    user = get_current_user()
    if not user:
        st.error("❌ Lỗi phiên đăng nhập!")
        logout_user()
        st.rerun()
        return
    
    # Show main interface
    show_sidebar()
    
    # Main header
    st.markdown(f"""
        <div class='main-header'>
            <h1>🎓 Hệ thống Thi Trực tuyến</h1>
            <p>Chào mừng <strong>{user.get('ho_ten', 'User')}</strong> ({user.get('role', 'unknown').title()})</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Set default page
    if "current_page" not in st.session_state:
        if user['role'] == 'teacher':
            st.session_state.current_page = "manage_classes"
        elif user['role'] == 'student':
            st.session_state.current_page = "my_classes"
        elif user['role'] == 'admin':
            st.session_state.current_page = "manage_users"
    
    # Route to appropriate dashboard
    try:
        if user['role'] == 'teacher':
            teacher_dashboard()
        elif user['role'] == 'student':
            student_dashboard()
        elif user['role'] == 'admin':
            admin_dashboard()
        else:
            st.error(f"❌ Role '{user['role']}' không được hỗ trợ!")
            
    except Exception as e:
        show_error_page("Lỗi hệ thống nghiêm trọng", str(e))

# ==============================================================================
# APPLICATION ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Lỗi khởi động ứng dụng: {e}")
        st.code(str(e))
        
        if st.button("🔄 Khởi động lại"):
            st.rerun()