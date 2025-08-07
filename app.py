import streamlit as st
import os
import sys
from datetime import datetime
from admin.manage_users import show_manage_users
from admin.exam_management import show_exam_management
from admin.grading import show_grading
# --- Cấu hình trang và CSS ---
st.set_page_config(
    page_title="Hệ thống Thi Trực tuyến",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem; border-radius: 10px; color: white;
        text-align: center; margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f0f2f6 0%, #e6e9ed 100%);
    }
    .stButton > button {
        border-radius: 20px; border: 1px solid #667eea;
        padding: 0.5rem 1rem; font-weight: 600; transition: all 0.3s;
        background-color: white; color: #667eea;
    }
    .stButton > button:hover {
        transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102,126,234,0.3);
        background-color: #667eea; color: white;
    }
    .info-box {
        background: #e9eafc; border: 1px solid #d6d8fb;
        border-radius: 10px; padding: 1rem; margin: 1rem 0;
    }
    .metric-card {
        background: white; border: 1px solid #e1e5e9;
        border-radius: 10px; padding: 1rem; margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-message {
        background: #d4edda; border: 1px solid #c3e6cb;
        color: #155724; padding: 0.75rem; border-radius: 5px;
    }
    .error-message {
        background: #f8d7da; border: 1px solid #f5c6cb;
        color: #721c24; padding: 0.75rem; border-radius: 5px;
    }
    .warning-message {
        background: #fff3cd; border: 1px solid #ffeaa7;
        color: #856404; padding: 0.75rem; border-radius: 5px;
    }
    .info-message {
        background: #d1ecf1; border: 1px solid #bee5eb;
        color: #0c5460; padding: 0.75rem; border-radius: 5px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        .stButton > button {
            padding: 0.4rem 0.8rem;
            font-size: 0.9rem;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .main-header {
            background: linear-gradient(90deg, #4a5568 0%, #2d3748 100%);
        }
        .info-box {
            background: #2d3748; border: 1px solid #4a5568; color: white;
        }
        .metric-card {
            background: #2d3748; border: 1px solid #4a5568; color: white;
        }
    }
    
    /* Animation for loading */
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 2s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Exam interface styles */
    .exam-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 20px; border-radius: 15px;
        margin-bottom: 20px; text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .question-card {
        background: white; border: 2px solid #e1e5e9;
        border-radius: 15px; padding: 20px; margin: 15px 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .question-card:hover {
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .timer-display {
        background: #ff6b6b; color: white; padding: 10px 20px;
        border-radius: 25px; font-weight: bold; font-size: 1.1rem;
        display: inline-block; margin: 10px 0;
    }
    
    .score-display {
        background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
        color: white; padding: 15px; border-radius: 10px;
        text-align: center; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)
# ==============================================================================
# BỘ KHỞI ĐỘNG DỰ ÁN (Project Bootstrapper)
# Đoạn code này đảm bảo Python có thể tìm thấy các module trong dự án
# một cách chính xác, bất kể bạn chạy lệnh từ đâu.
# ------------------------------------------------------------------------------
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
except Exception as e:
    st.error(f"Lỗi khởi tạo đường dẫn hệ thống: {e}")
    st.stop()
# ==============================================================================

# Import các module của dự án
try:
    from auth.login import show_login_page, is_logged_in, get_current_user, logout_user
    from admin.manage_users import show_manage_users
    from admin.class_management import show_manage_classes
    from admin.student_management import show_manage_students
    # <<< THAY ĐỔI Ở ĐÂY: Import exam_creation.py >>>
    from admin.exam_creation import show_create_exam 
    from admin.exam_management import show_exam_management
    from student.dashboard import student_dashboard 
except ImportError as e:
    st.error(f"❌ Lỗi Import Module Quan Trọng: {e}")
    st.stop()




def initialize_app():
    """
    Hàm này thực hiện các tác vụ khởi tạo cần thiết
    """
    # Tạo thư mục uploads nếu chưa có
    os.makedirs("uploads/images", exist_ok=True)
    os.makedirs("uploads/documents", exist_ok=True)
    
    # Khởi tạo session state mặc định
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.theme = "light"
        st.session_state.language = "vi"

def show_sidebar():
    """Hiển thị sidebar và menu điều hướng."""
    with st.sidebar:
        st.markdown("<h4 style='text-align: center;'>🎓 Hệ thống thi trực tuyến</h4>", unsafe_allow_html=True)
        st.markdown("---")
        
        user = get_current_user()
        if not user: return

        role_map = { "student": "👨‍🎓 Học sinh", "admin": "👨‍💼 Quản trị"}
        role_display = role_map.get(user['role'], "👤 Người dùng")
        
        st.markdown(f"""
            <div class='info-box'>
                <h4>{role_display}</h4>
                <p><strong>{user.get('ho_ten', 'N/A')}</strong> (@{user.get('username', 'N/A')})</p>
            </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        # ĐIỀU HƯỚNG MENU ĐÚNG CÁCH
        if user['role'] == 'student':
            show_student_menu()
        elif user['role'] == 'admin':
            show_admin_menu()

        st.divider()
        if st.button("🚪 Đăng xuất", use_container_width=True):
            logout_user_session() # Hàm logout nên được gọi từ auth.login
            st.rerun()
            
        # Thông tin hệ thống
        st.markdown(f"""
            <div style='text-align: center; color: #555; font-size: 12px; padding-top: 20px;'>
                🕐 {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}<br/>
                📊 Phiên bản: 1.0.0<br/>
                🔗 Powered by Streamlit
            </div>
        """, unsafe_allow_html=True)



def show_student_menu():
    st.markdown("### 👨‍🎓 Menu Học sinh")
    menu_items = [
        ("📚 Lớp học của tôi", "my_classes"),
        ("📝 Làm bài thi", "take_exam"),
        ("📊 Xem kết quả", "view_results")
    ]
    for name, key in menu_items:
        if st.button(name, use_container_width=True, key=f"btn_{key}"):
            if key == "take_exam" and "selected_class_id" in st.session_state:
                del st.session_state.selected_class_id
            st.session_state.current_page = key
            st.rerun()
def show_admin_menu():
    st.markdown("### 👨‍💼 Menu Quản trị")
    menu_items = [
        ("👥 Quản lý Người dùng", "manage_users"),
        ("🏫 Quản lý Lớp học", "manage_classes"),
        ("👥 Quản lý Học sinh", "manage_students"),
        # Thống nhất key là "create_exam"
        ("📝 Tạo/Sửa Đề thi", "create_exam"), 
        ("📚 Quản lý Đề thi", "exam_management"),
        ("✅ Chấm bài", "grading"),
        ("🏫 Quản lý Hệ thống", "system_manage"),
        ("📊 Thống kê Tổng quan", "system_statistics")
    ]
    for name, key in menu_items:
        # Nếu đang ở trang create_exam, xóa các id tạm để bắt đầu đề mới
        if st.button(name, use_container_width=True, key=f"btn_{key}"):
            if key == 'create_exam':
                if 'edit_exam_id' in st.session_state: del st.session_state.edit_exam_id
                if 'clone_exam_id' in st.session_state: del st.session_state.clone_exam_id
                if 'editing_exam_id_value' in st.session_state: del st.session_state.editing_exam_id_value

            st.session_state.current_page = key
            st.rerun()
def logout_user_session():
    """Đăng xuất người dùng"""
    # Xóa tất cả session state liên quan đến user
    keys_to_preserve = ['app_initialized', 'theme', 'language']
    keys_to_remove = [key for key in st.session_state.keys() if key not in keys_to_preserve]
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    st.success("✅ Đã đăng xuất thành công!")
    st.rerun()

def show_loading_screen():
    """Hiển thị màn hình loading"""
    st.markdown("""
        <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh;'>
            <div class='loading-spinner'></div>
            <h3>🔄 Đang tải...</h3>
            <p>Vui lòng chờ trong giây lát</p>
        </div>
    """, unsafe_allow_html=True)

def show_error_page(error_message, error_details=None):
    """Hiển thị trang lỗi"""
    st.markdown("<div class='main-header'><h1>❌ Đã xảy ra lỗi</h1></div>", unsafe_allow_html=True)
    
    st.error(f"**Lỗi:** {error_message}")
    
    if error_details:
        with st.expander("🔍 Chi tiết lỗi"):
            st.code(str(error_details))
    
    st.markdown("### 🔧 Cách khắc phục:")
    st.markdown("""
    1. **Làm mới trang:** Nhấn F5 hoặc Ctrl+R
    2. **Kiểm tra kết nối:** Đảm bảo kết nối internet ổn định
    3. **Đăng nhập lại:** Thử đăng xuất và đăng nhập lại
    4. **Liên hệ hỗ trợ:** Nếu lỗi vẫn tiếp diễn
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Làm mới trang", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🏠 Về trang chủ", use_container_width=True):
            st.session_state.current_page = None
            st.rerun()
    
    with col3:
        if st.button("🚪 Đăng xuất", use_container_width=True):
            logout_user()

def show_maintenance_page():
    """Hiển thị trang bảo trì"""
    st.markdown("<div class='main-header'><h1>🔧 Hệ thống đang bảo trì</h1></div>", unsafe_allow_html=True)
    
    st.info("""
    **Thông báo:** Hệ thống đang được nâng cấp để phục vụ bạn tốt hơn.
    
    **Thời gian dự kiến:** 15-30 phút
    
    **Liên hệ:** admin@examystem.com nếu cần hỗ trợ khẩn cấp
    """)
    
    # Auto refresh every 30 seconds
    st.markdown("""
    <script>
    setTimeout(function(){
        window.location.reload();
    }, 30000);
    </script>
    """, unsafe_allow_html=True)

def handle_navigation():
    """Xử lý điều hướng trang"""
    user = get_current_user()
    current_page = st.session_state.get("current_page")
    
    # Đặt trang mặc định dựa theo role
    if not current_page:
        if user['role'] == 'teacher':
            st.session_state.current_page = "manage_classes"
        else:
            st.session_state.current_page = "my_classes"
        st.rerun()
    
    try:
        if user['role'] == 'admin':
            admin_dashboard()
        
        else:
            student_dashboard()
    except Exception as e:
        show_error_page("Đã xảy ra lỗi khi tải trang", str(e))
def admin_dashboard():
    """Router chính cho tất cả các trang của Admin."""
    # Đặt trang mặc định nếu chưa có
    page = st.session_state.get('current_page', 'manage_users')
    
    if page == "manage_users":
        show_manage_users()
    elif page == "manage_classes":
        show_manage_classes()
    elif page == "manage_students":
        show_manage_students()
    # Thay "manage_exams" bằng "create_exam"
    elif page == "create_exam": 
        show_create_exam()
    elif page == "exam_management":
        show_exam_management()
    # Thêm các trang khác vào đây nếu cần
    elif page == "grading":
        show_grading()
    else:
        # Trang không xác định, quay về trang mặc định
        st.warning(f"Trang '{page}' không tồn tại. Quay về trang chủ.")
        st.session_state.current_page = "manage_users"
        st.rerun()
def main():
    if not is_logged_in():
        show_login_page()
        return

    user = get_current_user()
    if not user:
        st.error("❌ Lỗi phiên đăng nhập!")
        logout_user()
        st.rerun()
        return

    show_sidebar()
    
    # st.markdown("<div class='main-header'><h1>🎓 Hệ thống Thi Trực tuyến</h1></div>", unsafe_allow_html=True)

    # ĐIỀU HƯỚNG DASHBOARD ĐÚNG CÁCH
    try:
        if user['role'] == 'student':
            student_dashboard()
        elif user['role'] == 'admin':
            admin_dashboard()
        else:
            st.error(f"❌ Vai trò '{user['role']}' không được hỗ trợ!")
    except Exception as e:
        st.error(f"❌ Đã xảy ra lỗi nghiêm trọng khi tải trang: {e}")
        st.exception(e)



if __name__ == "__main__":
    main()