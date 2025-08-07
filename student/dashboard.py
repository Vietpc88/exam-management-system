# Nội dung cuối cùng và chính xác cho file: student/dashboard.py

import streamlit as st

def student_dashboard():
    
    # Di chuyển import vào trong hàm
    from .my_classes import show_my_classes
    from .take_exam import show_take_exam
    from .view_results import show_view_results

    page = st.session_state.get('current_page', 'my_classes')
    
    try:
        if page == "my_classes":
            show_my_classes()
        elif page == "take_exam":
            show_take_exam()
        elif page == "view_results":
            show_view_results()
        else:
            st.warning(f"Trang '{page}' không hợp lệ. Đang quay về trang chính.")
            st.session_state.current_page = "my_classes"
            show_my_classes()
            
    except Exception as e:
        st.error(f"❌ Đã xảy ra lỗi khi tải trang của học sinh: {e}")
        st.exception(e) # In traceback để debug