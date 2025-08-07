import streamlit as st
from datetime import datetime
from database.supabase_models import get_database
from auth.login import get_current_user

def show_my_classes():
    """Hiển thị danh sách lớp học của học sinh (phiên bản đã sửa lỗi)."""
    st.header("📚 Lớp học của tôi")
    
    user = get_current_user()
    db = get_database()
    
    try:
        classes = db.get_classes_by_student(user['id'])
        
        if not classes:
            st.info("📚 Bạn chưa tham gia lớp học nào!")
            # (Phần form tham gia lớp giữ nguyên)
            return
        
        for class_info in classes:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### 📚 {class_info['ten_lop']}")
                    st.write(f"**Mã lớp:** {class_info['ma_lop']}")
                    # **DÒNG ĐÃ XÓA:** Không còn hiển thị tên giáo viên
                    if class_info.get('mo_ta'):
                        st.caption(class_info['mo_ta'])
                
                with col2:
                    st.write("") # Thêm khoảng trống cho đẹp
                    if st.button("📝 Xem đề thi", key=f"view_exams_{class_info['id']}", use_container_width=True):
                        st.session_state.selected_class_id = class_info['id']
                        st.session_state.current_page = "take_exam"
                        st.rerun()
                st.divider()
        
        
        with st.expander("➕ Tham gia lớp học khác"):
            with st.form("join_another_class_form"):
                ma_lop = st.text_input("Mã lớp mới", placeholder="Nhập mã lớp")
                if st.form_submit_button("📝 Tham gia", use_container_width=True):
                    if ma_lop.strip():
                        join_class_by_code(user['id'], ma_lop.strip())
                    else:
                        st.error("❌ Vui lòng nhập mã lớp!")
    except Exception as e:
        st.error(f"❌ Lỗi lấy danh sách lớp: {str(e)}")

def join_class_by_code(student_id: str, ma_lop: str):
    """Tham gia lớp bằng mã lớp"""
    db = get_database()
    try:
        class_info = db.get_class_by_code(ma_lop) # Giả sử bạn có hàm này
        if not class_info:
            st.error("❌ Không tìm thấy lớp với mã này!")
            return
        
        # LỜI GỌI ĐÃ ĐƯỢC SỬA THÀNH get_classes_by_student
        existing_classes = db.get_classes_by_student(student_id)
        if any(c['id'] == class_info['id'] for c in existing_classes):
            st.warning("⚠️ Bạn đã tham gia lớp này rồi!")
            return
        
        if db.add_student_to_class(class_info['id'], student_id):
            st.success(f"✅ Đã tham gia lớp {class_info['ten_lop']} thành công!")
            st.rerun()
        else:
            st.error("❌ Lỗi khi tham gia lớp!")
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")

def get_class_exam_count(class_id: str) -> int:
    """Lấy số lượng đề thi trong lớp"""
    db = get_database()
    try:
        result = db.client.table('exams').select('id', count='exact').eq('class_id', class_id).eq('is_published', True).execute()
        return result.count or 0
    except:
        return 0