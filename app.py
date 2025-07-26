import streamlit as st
from auth.supabase_auth import SupabaseAuth

# Import các module hiện có
try:
    from teacher.create_exam import show_teacher_interface
except ImportError:
    def show_teacher_interface():
        st.error("Module teacher.create_exam chưa được cập nhật để sử dụng Supabase!")

try:
    from student.take_exam import show_student_interface
except ImportError:
    def show_student_interface():
        st.error("Module student.take_exam chưa được cập nhật để sử dụng Supabase!")

# Cấu hình page
st.set_page_config(
    page_title="Hệ thống Thi Trực tuyến",
    page_icon="📚",
    layout="wide"
)

# Khởi tạo auth
auth = SupabaseAuth()

def main():
    st.title("🎓 Hệ thống Thi Trực tuyến")
    
    # Sidebar cho authentication
    with st.sidebar:
        if not auth.is_logged_in():
            st.subheader("🔐 Đăng nhập")
            
            tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Tên đăng nhập")
                    password = st.text_input("Mật khẩu", type="password")
                    submitted = st.form_submit_button("Đăng nhập")
                    
                    if submitted:
                        if auth.login(username, password):
                            st.success("Đăng nhập thành công!")
                            st.rerun()
                        else:
                            st.error("Sai tên đăng nhập hoặc mật khẩu!")
            
            with tab2:
                with st.form("register_form"):
                    reg_username = st.text_input("Tên đăng nhập", key="reg_username")
                    reg_password = st.text_input("Mật khẩu", type="password", key="reg_password")
                    reg_ho_ten = st.text_input("Họ và tên")
                    reg_email = st.text_input("Email (không bắt buộc)")
                    reg_phone = st.text_input("Số điện thoại (không bắt buộc)")
                    reg_submitted = st.form_submit_button("Đăng ký")
                    
                    if reg_submitted:
                        if auth.register(reg_username, reg_password, reg_ho_ten, reg_email, reg_phone):
                            st.success("Đăng ký thành công! Vui lòng đăng nhập.")
                        else:
                            st.error("Đăng ký thất bại! Tên đăng nhập có thể đã tồn tại.")
        else:
            user_info = auth.get_current_user()
            st.write(f"Xin chào, **{user_info['ho_ten']}**")
            st.write(f"Vai trò: **{user_info['role']}**")
            
            if st.button("Đăng xuất"):
                auth.logout()
                st.rerun()
    
    # Main content
    if auth.is_logged_in():
        user_info = auth.get_current_user()
        
        if user_info['role'] in ['admin', 'teacher']:
            show_teacher_interface()
        else:
            show_student_interface()
    else:
        st.info("Vui lòng đăng nhập để sử dụng hệ thống.")
        
        # Demo login info
        st.subheader("🔍 Tài khoản demo:")
        st.code("""
Admin/Teacher: 
- Username: admin
- Password: aLy5hQjER37KAE9u

Student:
- Username: testuser  
- Password: testpass
        """)

if __name__ == "__main__":
    main()