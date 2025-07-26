import streamlit as st
import json
import pandas as pd
import base64
import io
import random
from datetime import datetime, timedelta
from database.models import *
from auth.login import get_current_user
from teacher.word_parser import show_upload_word_exam, render_mathjax

# Định nghĩa các hàm cơ bản trước
def show_statistics():
    """Thống kê"""
    st.header("📊 Thống kê")
    st.info("Tính năng thống kê đang được phát triển...")

def show_grading():
    """Chấm bài"""
    st.header("✅ Chấm bài")
    st.info("Tính năng chấm bài đang được phát triển...")

def show_exam_creation_guide():
    """Hiển thị hướng dẫn tạo đề thi"""
    with st.expander("📚 Hướng dẫn tạo đề thi", expanded=True):
        st.markdown("""
        ### 🔄 Quy trình tạo đề thi:
        
        1. **📋 Thông tin đề thi**
           - Nhập tiêu đề, chọn lớp
           - Đặt thời gian làm bài
           - Cấu hình thời gian mở đề
        
        2. **❓ Thêm câu hỏi**
           - Chọn loại câu hỏi phù hợp
           - Nhập nội dung và đáp án
           - Đặt điểm cho từng câu
           - Upload từ Word với LaTeX và hình ảnh
        
        3. **📝 Xem trước**
           - Kiểm tra toàn bộ đề thi
           - Xem thống kê và phân bố điểm
           - Preview LaTeX và hình ảnh
        
        4. **🚀 Hoàn thành**
           - Lưu nháp hoặc phát hành
        
        ### 📝 Các loại câu hỏi:
        
        - **🔤 Trắc nghiệm:** 4 lựa chọn, 1 đáp án đúng
        - **✅ Đúng/Sai:** Nhiều phát biểu trong 1 câu
        - **📝 Trả lời ngắn:** Học sinh gõ câu trả lời
        - **📄 Tự luận:** Có thể yêu cầu chụp ảnh bài làm
        
        ### 📄 Upload từ Word:
        
        - **Hỗ trợ LaTeX:** $x^2$, $\\int_0^1 f(x)dx$
        - **Hình ảnh:** Tự động extract và hiển thị chính xác
        - **4 loại câu hỏi:** Trắc nghiệm, Đúng/Sai, Trả lời ngắn, Tự luận
        - **Format chuẩn:** Theo file mẫu đã cung cấp
        """)
        
        if st.button("🎯 Tạo lớp ngay", key="btn_create_class_from_guide"):
            st.session_state.current_page = "manage_classes"
            st.rerun()

def teacher_dashboard():
    """Dashboard chính của giáo viên"""
    current_page = st.session_state.get("current_page", "manage_classes")
    
    if current_page == "manage_classes":
        show_manage_classes()
    elif current_page == "manage_students":
        show_manage_students()
    elif current_page == "create_exam":
        show_create_exam()
    elif current_page == "statistics":
        show_statistics()
    elif current_page == "grading":
        show_grading()

def show_manage_classes():
    """Quản lý lớp học với popup"""
    st.header("📋 Quản lý Lớp học")
    
    user = get_current_user()
    
    # Buttons hành động
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("➕ Tạo lớp mới", use_container_width=True, key="btn_create_class_main"):
            st.session_state.show_create_class = True
    with col2:
        if st.button("🔄 Làm mới", use_container_width=True, key="btn_refresh_classes"):
            # Clear all popups
            for key in list(st.session_state.keys()):
                if key.startswith('show_'):
                    del st.session_state[key]
            st.rerun()
    
    # Popups
    show_popups()
    
    # Danh sách lớp
    classes = get_classes_by_teacher(user['id'])
    
    if not classes:
        st.info("📚 Bạn chưa có lớp học nào. Hãy tạo lớp đầu tiên!")
        return
    
    st.subheader(f"📚 Danh sách lớp học ({len(classes)} lớp)")
    
    for class_info in classes:
        with st.container():
            # Header lớp
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"### 📋 {class_info['name']}")
                if class_info['description']:
                    st.caption(f"📝 {class_info['description']}")
                st.caption(f"👥 {class_info['student_count']} học sinh | 📅 Tạo: {class_info['created_at'][:10]}")
            
            with col2:
                if st.button("👥 Học sinh", key=f"btn_students_{class_info['id']}", use_container_width=True):
                    st.session_state.show_class_students = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col3:
                if st.button("📝 Đề thi", key=f"btn_exams_{class_info['id']}", use_container_width=True):
                    st.session_state.show_class_exams = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col4:
                if st.button("➕ Thêm HS", key=f"btn_add_{class_info['id']}", use_container_width=True):
                    st.session_state.show_add_students = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col5:
                if st.button("⚙️ Quản lý", key=f"btn_manage_{class_info['id']}", use_container_width=True):
                    st.session_state.show_manage_class = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            with col6:
                if st.button("🗑️ Xóa", key=f"btn_delete_{class_info['id']}", use_container_width=True, type="secondary"):
                    st.session_state.show_delete_class = True
                    st.session_state.selected_class = class_info
                    st.rerun()
            
            st.divider()

def show_popups():
    """Hiển thị tất cả popups"""
    # Popup tạo lớp
    if st.session_state.get("show_create_class", False):
        with st.expander("➕ Tạo lớp học mới", expanded=True):
            show_create_class_popup()
    
    # Popup quản lý lớp
    if st.session_state.get("show_manage_class", False):
        with st.expander("⚙️ Quản lý lớp", expanded=True):
            show_manage_class_popup()
    
    # Popup thêm học sinh
    if st.session_state.get("show_add_students", False):
        with st.expander("➕ Thêm học sinh vào lớp", expanded=True):
            show_add_students_popup()
    
    # Popup xem học sinh
    if st.session_state.get("show_class_students", False):
        with st.expander("👥 Học sinh trong lớp", expanded=True):
            show_class_students_popup()
    
    # Popup xem đề thi
    if st.session_state.get("show_class_exams", False):
        with st.expander("📝 Đề thi của lớp", expanded=True):
            show_class_exams_popup()
    
    # Popup xóa lớp
    if st.session_state.get("show_delete_class", False):
        with st.expander("🗑️ Xóa lớp", expanded=True):
            show_delete_class_popup()

def show_create_class_popup():
    """Popup tạo lớp học"""
    user = get_current_user()
    
    st.write("### 📋 Thông tin lớp học")
    
    class_name = st.text_input("Tên lớp *", placeholder="Ví dụ: Lớp 10A1", key="input_new_class_name")
    description = st.text_area("Mô tả", placeholder="Mô tả về lớp học...", key="input_new_class_desc")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Tạo lớp", use_container_width=True, key="btn_create_class_submit"):
            if not class_name.strip():
                st.error("❌ Vui lòng nhập tên lớp!")
                return
            
            # Kiểm tra trùng tên
            if check_class_name_exists(class_name.strip(), user['id']):
                st.error("❌ Tên lớp đã tồn tại! Vui lòng chọn tên khác.")
                return
            
            class_id = create_class(class_name.strip(), description.strip(), user['id'])
            if class_id:
                st.success(f"✅ Tạo lớp '{class_name}' thành công!")
                st.session_state.show_create_class = False
                st.rerun()
            else:
                st.error("❌ Có lỗi xảy ra khi tạo lớp!")
    
    with col2:
        if st.button("❌ Hủy", use_container_width=True, key="btn_cancel_create_class"):
            st.session_state.show_create_class = False
            st.rerun()

def show_manage_class_popup():
    """Popup quản lý lớp"""
    class_info = st.session_state.get("selected_class", {})
    user = get_current_user()
    
    if not class_info:
        st.error("Không tìm thấy thông tin lớp!")
        return
    
    st.write(f"### ⚙️ Quản lý lớp: {class_info['name']}")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Thống kê", "✏️ Chỉnh sửa", "🗑️ Xóa lớp"])
    
    with tab1:
        # Thống kê chi tiết
        stats = get_class_detail_stats(class_info['id'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Học sinh", stats['student_count'])
        with col2:
            st.metric("📝 Đề thi", stats['exam_count'])
        with col3:
            st.metric("📊 Bài làm", stats['submission_count'])
        with col4:
            st.metric("✅ Đã chấm", stats['graded_count'])
        
        st.info(f"📅 **Ngày tạo:** {class_info['created_at']}")
    
    with tab2:
        # Form chỉnh sửa
        new_name = st.text_input("Tên lớp", value=class_info['name'], key=f"input_edit_class_name_{class_info['id']}")
        new_description = st.text_area("Mô tả", value=class_info.get('description', ''), key=f"input_edit_class_desc_{class_info['id']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Lưu thay đổi", use_container_width=True, key=f"btn_save_class_{class_info['id']}"):
                if not new_name.strip():
                    st.error("❌ Tên lớp không được để trống!")
                    return
                
                # Kiểm tra trùng tên (trừ chính nó)
                if check_class_name_exists(new_name.strip(), user['id'], class_info['id']):
                    st.error("❌ Tên lớp đã tồn tại!")
                    return
                
                if update_class_info(class_info['id'], new_name.strip(), new_description.strip(), user['id']):
                    st.success("✅ Cập nhật thành công!")
                    st.session_state.show_manage_class = False
                    st.rerun()
                else:
                    st.error("❌ Cập nhật thất bại!")
        
        with col2:
            if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_edit_class_{class_info['id']}"):
                st.session_state.show_manage_class = False
                st.rerun()
    
    with tab3:
        st.warning("⚠️ **Cảnh báo:** Xóa lớp sẽ ảnh hưởng đến dữ liệu!")
        
        stats = get_class_detail_stats(class_info['id'])
        
        if stats['exam_count'] > 0:
            st.error(f"❌ Không thể xóa lớp có {stats['exam_count']} đề thi!")
            st.info("💡 **Gợi ý:** Xóa tất cả đề thi trước khi xóa lớp")
            
            if st.checkbox("🔥 Tôi muốn xóa lớp cùng tất cả đề thi và dữ liệu liên quan", key=f"chk_force_delete_{class_info['id']}"):
                st.error("⚠️ **NGUY HIỂM:** Thao tác này không thể hoàn tác!")
                confirm_text = st.text_input("Nhập 'XOA HOAN TOAN' để xác nhận:", key=f"input_confirm_force_delete_{class_info['id']}")
                
                if confirm_text == "XOA HOAN TOAN":
                    if st.button("🔥 XÓA HOÀN TOÀN", type="secondary", key=f"btn_force_delete_{class_info['id']}"):
                        success, message = force_delete_class(class_info['id'], user['id'])
                        if success:
                            st.success(message)
                            st.session_state.show_manage_class = False
                            st.rerun()
                        else:
                            st.error(message)
        else:
            if st.checkbox("Tôi hiểu rủi ro khi xóa lớp", key=f"chk_delete_class_{class_info['id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Xóa lớp", type="secondary", use_container_width=True, key=f"btn_delete_class_confirm_{class_info['id']}"):
                        success, message = delete_class(class_info['id'], user['id'])
                        if success:
                            st.success(message)
                            st.session_state.show_manage_class = False
                            st.rerun()
                        else:
                            st.error(message)
                
                with col2:
                    if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_delete_class_{class_info['id']}"):
                        st.session_state.show_manage_class = False
                        st.rerun()

def show_delete_class_popup():
    """Popup xác nhận xóa lớp"""
    class_info = st.session_state.get("selected_class", {})
    user = get_current_user()
    
    if not class_info:
        return
    
    st.error(f"🗑️ **Xóa lớp: {class_info['name']}?**")
    
    stats = get_class_detail_stats(class_info['id'])
    
    st.write("**Thông tin lớp:**")
    st.write(f"- 👥 Học sinh: {stats['student_count']}")
    st.write(f"- 📝 Đề thi: {stats['exam_count']}")
    st.write(f"- 📊 Bài làm: {stats['submission_count']}")
    
    if stats['exam_count'] > 0:
        st.error("❌ Không thể xóa lớp có đề thi!")
        if st.button("❌ Đóng", key=f"btn_close_delete_popup_{class_info['id']}"):
            st.session_state.show_delete_class = False
            st.rerun()
    else:
        st.warning("⚠️ Thao tác này sẽ xóa lớp và tất cả học sinh trong lớp!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Xác nhận xóa", type="secondary", use_container_width=True, key=f"btn_confirm_delete_popup_{class_info['id']}"):
                success, message = delete_class(class_info['id'], user['id'])
                if success:
                    st.success(message)
                    st.session_state.show_delete_class = False
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_delete_popup_{class_info['id']}"):
                st.session_state.show_delete_class = False
                st.rerun()

def show_class_students_popup():
    """Popup hiển thị học sinh trong lớp"""
    class_info = st.session_state.get("selected_class", {})
    
    if not class_info:
        return
    
    st.write(f"### 👥 Học sinh lớp: {class_info['name']}")
    
    students = get_class_students(class_info['id'])
    
    if not students:
        st.info("📚 Lớp này chưa có học sinh nào.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Thêm học sinh ngay", key=f"btn_add_students_from_empty_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.session_state.show_add_students = True
                st.rerun()
        with col2:
            if st.button("❌ Đóng", key=f"btn_close_empty_students_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.rerun()
    else:
        st.info(f"👥 **Tổng cộng:** {len(students)} học sinh")
        
        # Danh sách học sinh
        for i, student in enumerate(students, 1):
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
            
            with col1:
                st.write(f"**{i}**")
            
            with col2:
                st.write(f"**{student['full_name']}**")
                st.caption(f"@{student['username']}")
            
            with col3:
                st.caption(f"📅 Tham gia: {student['joined_at'][:10]}")
                if student.get('email'):
                    st.caption(f"📧 {student['email']}")
            
            with col4:
                if st.button("❌", key=f"btn_remove_popup_{class_info['id']}_{student['id']}", help="Xóa khỏi lớp"):
                    if remove_student_from_class(class_info['id'], student['id']):
                        st.success(f"✅ Đã xóa {student['full_name']} khỏi lớp")
                        st.rerun()
                    else:
                        st.error("❌ Lỗi khi xóa học sinh")
        
        # Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Thêm học sinh", use_container_width=True, key=f"btn_add_more_students_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.session_state.show_add_students = True
                st.rerun()
        
        with col2:
            if st.button("❌ Đóng", use_container_width=True, key=f"btn_close_students_popup_{class_info['id']}"):
                st.session_state.show_class_students = False
                st.rerun()

def show_add_students_popup():
    """Popup thêm học sinh vào lớp"""
    class_info = st.session_state.get("selected_class", {})
    
    if not class_info:
        return
    
    st.write(f"### ➕ Thêm học sinh vào lớp: {class_info['name']}")
    
    # Tab thêm từng học sinh và thêm hàng loạt
    tab1, tab2 = st.tabs(["👤 Thêm từng học sinh", "👥 Thêm hàng loạt"])
    
    with tab1:
        available_students = get_students_not_in_class(class_info['id'])
        
        if not available_students:
            st.info("✅ Tất cả học sinh đã có trong lớp hoặc không có học sinh nào.")
        else:
            st.info(f"📋 Có {len(available_students)} học sinh có thể thêm vào lớp")
            
            student_options = {f"{s['full_name']} (@{s['username']})": s['id'] for s in available_students}
            selected_student = st.selectbox("Chọn học sinh", options=list(student_options.keys()), key=f"select_single_student_{class_info['id']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Thêm vào lớp", use_container_width=True, key=f"btn_add_single_student_{class_info['id']}"):
                    student_id = student_options[selected_student]
                    if add_student_to_class(class_info['id'], student_id):
                        st.success(f"✅ Đã thêm {selected_student.split(' (@')[0]} vào lớp!")
                        st.rerun()
                    else:
                        st.error("❌ Không thể thêm học sinh vào lớp! Có thể học sinh đã có trong lớp.")
            
            with col2:
                if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_add_single_{class_info['id']}"):
                    st.session_state.show_add_students = False
                    st.rerun()
    
    with tab2:
        available_students = get_students_not_in_class(class_info['id'])
        
        if not available_students:
            st.info("✅ Tất cả học sinh đã có trong lớp.")
        else:
            st.write("**Chọn nhiều học sinh để thêm cùng lúc:**")
            
            selected_students = []
            
            # Checkbox chọn tất cả
            select_all = st.checkbox("🔘 Chọn tất cả", key=f"chk_select_all_students_{class_info['id']}")
            
            for student in available_students:
                checked = select_all or st.checkbox(
                    f"{student['full_name']} (@{student['username']})", 
                    key=f"chk_bulk_student_{class_info['id']}_{student['id']}"
                )
                
                if checked:
                    selected_students.append(student['id'])
            
            if selected_students:
                st.info(f"✅ Đã chọn {len(selected_students)} học sinh")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"➕ Thêm {len(selected_students)} học sinh", use_container_width=True, key=f"btn_add_bulk_students_{class_info['id']}"):
                        success_count = bulk_add_students_to_class(class_info['id'], selected_students)
                        st.success(f"✅ Đã thêm {success_count}/{len(selected_students)} học sinh vào lớp!")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_add_bulk_{class_info['id']}"):
                        st.session_state.show_add_students = False
                        st.rerun()
            else:
                if st.button("❌ Đóng", use_container_width=True, key=f"btn_close_add_bulk_{class_info['id']}"):
                    st.session_state.show_add_students = False
                    st.rerun()

def show_class_exams_popup():
    """Popup hiển thị đề thi của lớp"""
    class_info = st.session_state.get("selected_class", {})
    
    if not class_info:
        return
    
    st.write(f"### 📝 Đề thi lớp: {class_info['name']}")
    
    exams = get_exams_by_class(class_info['id'])
    
    if not exams:
        st.info("📝 Lớp này chưa có đề thi nào.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Tạo đề thi ngay", key=f"btn_create_exam_from_class_{class_info['id']}"):
                st.session_state.show_class_exams = False
                st.session_state.current_page = "create_exam"
                # Tự động chọn lớp này
                st.session_state.exam_class_id = class_info['id']
                st.session_state.exam_class_name = class_info['name']
                st.rerun()
        with col2:
            if st.button("❌ Đóng", key=f"btn_close_empty_exams_{class_info['id']}"):
                st.session_state.show_class_exams = False
                st.rerun()
    else:
        st.info(f"📊 **Tổng cộng:** {len(exams)} đề thi")
        
        for exam in exams:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**📝 {exam['title']}**")
                    if exam['description']:
                        st.caption(exam['description'])
                
                with col2:
                    status = get_exam_status(exam)
                    st.write(status)
                    st.caption(f"📊 {exam['submission_count']} bài nộp")
                
                with col3:
                    if st.button("👁️", key=f"btn_view_exam_popup_{exam['id']}", help="Xem chi tiết"):
                        st.info("Tính năng đang phát triển...")
                
                st.divider()
        
        if st.button("❌ Đóng", use_container_width=True, key=f"btn_close_exams_popup_{class_info['id']}"):
            st.session_state.show_class_exams = False
            st.rerun()

def get_exam_status(exam):
    """Lấy trạng thái đề thi"""
    now = datetime.now()
    start_time = datetime.fromisoformat(exam['start_time']) if exam['start_time'] else None
    end_time = datetime.fromisoformat(exam['end_time']) if exam['end_time'] else None
    
    if start_time and now < start_time:
        return "⏳ Chưa mở"
    elif end_time and now > end_time:
        return "🔒 Đã đóng"
    else:
        return "✅ Đang mở"

def show_manage_students():
    """Quản lý học sinh toàn hệ thống"""
    st.header("👥 Quản lý Học sinh")
    
    # Buttons hành động
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("📥 Import Excel", use_container_width=True, key="btn_import_excel_main"):
            st.session_state.show_import_students = True
    with col2:
        if st.button("📊 Thống kê", use_container_width=True, key="btn_stats_main"):
            st.session_state.show_import_stats = True
    with col3:
        if st.button("🔄 Làm mới", use_container_width=True, key="btn_refresh_students"):
            # Clear search results
            if hasattr(st.session_state, 'search_results'):
                del st.session_state.search_results
            st.rerun()
    
    # Popup import học sinh
    if st.session_state.get("show_import_students", False):
        with st.expander("📥 Import học sinh từ Excel", expanded=True):
            show_import_students_popup()
    
    # Popup thống kê import
    if st.session_state.get("show_import_stats", False):
        with st.expander("📊 Thống kê Import", expanded=True):
            show_import_stats_popup()
    
    # Tìm kiếm học sinh
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Tìm kiếm học sinh", placeholder="Nhập tên, username hoặc email...", key="input_search_students")
    with col2:
        if st.button("🔍 Tìm kiếm", use_container_width=True, key="btn_search_students"):
            if search_term:
                st.session_state.search_results = search_students(search_term)
            else:
                st.session_state.search_results = None
    
    # Hiển thị kết quả tìm kiếm hoặc tất cả học sinh
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results is not None:
        students = st.session_state.search_results
        st.subheader(f"🔍 Kết quả tìm kiếm ({len(students)} học sinh)")
    else:
        students = get_all_students_detailed()
        st.subheader(f"👥 Tất cả học sinh ({len(students)} học sinh)")
    
    if not students:
        st.info("👥 Không tìm thấy học sinh nào.")
        return
    
    # Thống kê nhanh
    active_students = len([s for s in students if s['is_active']])
    inactive_students = len(students) - active_students
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Tổng số", len(students))
    with col2:
        st.metric("✅ Đang hoạt động", active_students)
    with col3:
        st.metric("🔒 Đã khóa", inactive_students)
    
    st.divider()
    
    # Danh sách học sinh
    for student in students:
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 1, 1, 1])
            
            with col1:
                status_icon = "✅" if student['is_active'] else "🔒"
                st.write(f"{status_icon} **{student['full_name']}**")
                st.caption(f"@{student['username']} | {student.get('email', 'Chưa có email')}")
            
            with col2:
                classes_text = student['classes'] if student['classes'] else "Chưa vào lớp nào"
                st.caption(f"📚 {classes_text}")
                
                # Thống kê học sinh
                stats = get_student_statistics(student['id'])
                st.caption(f"📊 {stats['class_count']} lớp | {stats['exam_count']} bài thi | TB: {stats['avg_score']}%")
            
            with col3:
                status_text = "Hoạt động" if student['is_active'] else "Đã khóa"
                status_color = "success" if student['is_active'] else "error"
                st.write(f":{status_color}[{status_text}]")
            
            with col4:
                action_text = "🔒 Khóa" if student['is_active'] else "✅ Mở khóa"
                if st.button(action_text, key=f"btn_toggle_{student['id']}"):
                    new_status = toggle_user_status(student['id'])
                    action = "mở khóa" if new_status else "khóa"
                    st.success(f"✅ Đã {action} tài khoản {student['full_name']}")
                    st.rerun()
            
            with col5:
                if st.button("📝 Sửa", key=f"btn_edit_{student['id']}"):
                    st.session_state.edit_student = student
                    st.rerun()
            
            with col6:
                if st.button("🏫 Lớp", key=f"btn_class_{student['id']}"):
                    st.session_state.manage_student_class = student
                    st.rerun()
            
            st.divider()
    
    # Popup chỉnh sửa học sinh
    if st.session_state.get("edit_student"):
        with st.expander("📝 Chỉnh sửa học sinh", expanded=True):
            show_edit_student_popup()
    
    # Popup quản lý lớp của học sinh
    if st.session_state.get("manage_student_class"):
        with st.expander("🏫 Quản lý lớp học sinh", expanded=True):
            show_student_class_popup()

def show_edit_student_popup():
    """Popup chỉnh sửa thông tin học sinh"""
    student = st.session_state.get("edit_student", {})
    
    if not student:
        return
    
    st.write(f"### 📝 Chỉnh sửa: {student['full_name']}")
    
    full_name = st.text_input("Họ và tên", value=student['full_name'], key=f"input_edit_student_name_{student['id']}")
    email = st.text_input("Email", value=student.get('email', ''), key=f"input_edit_student_email_{student['id']}")
    phone = st.text_input("Số điện thoại", value=student.get('phone', ''), key=f"input_edit_student_phone_{student['id']}")
    
    st.info(f"**Username:** {student['username']} (không thể thay đổi)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Lưu thay đổi", use_container_width=True, key=f"btn_save_student_{student['id']}"):
            if update_student_info(student['id'], full_name, email, phone):
                st.success("✅ Cập nhật thông tin thành công!")
                st.session_state.edit_student = None
                st.rerun()
            else:
                st.error("❌ Có lỗi xảy ra!")
    
    with col2:
        if st.button("❌ Hủy", use_container_width=True, key=f"btn_cancel_edit_student_{student['id']}"):
            st.session_state.edit_student = None
            st.rerun()

def show_student_class_popup():
    """Popup quản lý lớp học của học sinh"""
    student = st.session_state.get("manage_student_class", {})
    
    if not student:
        return
    
    st.write(f"### 🏫 Quản lý lớp: {student['full_name']}")
    
    user = get_current_user()
    current_classes = get_student_classes(student['id'])
    teacher_classes = get_classes_by_teacher(user['id'])
    
    # Hiển thị lớp hiện tại
    st.write("**📚 Lớp hiện tại:**")
    if current_classes:
        for class_info in current_classes:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {class_info['name']} (GV: {class_info['teacher_name']})")
            with col2:
                if st.button(f"❌", key=f"btn_remove_class_{student['id']}_{class_info['id']}", help="Xóa khỏi lớp"):
                    if remove_student_from_class(class_info['id'], student['id']):
                        st.success(f"✅ Đã xóa {student['full_name']} khỏi lớp {class_info['name']}")
                        st.rerun()
    else:
        st.info("Học sinh chưa tham gia lớp nào")
    
    st.divider()
    
    # Thêm vào lớp mới
    st.write("**➕ Thêm vào lớp:**")
    available_classes = [c for c in teacher_classes if c['id'] not in [cc['id'] for cc in current_classes]]
    
    if available_classes:
        class_options = {f"{c['name']} ({c['student_count']} HS)": c['id'] for c in available_classes}
        selected_class = st.selectbox("Chọn lớp", options=list(class_options.keys()), key=f"select_add_to_class_{student['id']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Thêm vào lớp", use_container_width=True, key=f"btn_add_to_class_{student['id']}"):
                class_id = class_options[selected_class]
                if add_student_to_class(class_id, student['id']):
                    st.success(f"✅ Đã thêm {student['full_name']} vào lớp!")
                    st.rerun()
                else:
                    st.error("❌ Không thể thêm vào lớp!")
        
        with col2:
            if st.button("❌ Đóng", use_container_width=True, key=f"btn_close_student_class_{student['id']}"):
                st.session_state.manage_student_class = None
                st.rerun()
    else:
        st.info("Không có lớp nào để thêm")
        if st.button("❌ Đóng", use_container_width=True, key=f"btn_close_student_class_empty_{student['id']}"):
            st.session_state.manage_student_class = None
            st.rerun()

def show_import_students_popup():
    """Popup import học sinh từ Excel"""
    st.write("### 📥 Import học sinh từ Excel")
    
    # Tab download template và upload file
    tab1, tab2, tab3 = st.tabs(["📋 Template", "📤 Upload", "📊 Kết quả"])
    
    with tab1:
        st.write("**📋 Tải template Excel mẫu:**")
        st.info("""
        📝 **Template bao gồm:**
        - **ho_ten** (bắt buộc): Họ và tên học sinh
        - **username** (bắt buộc): Tên đăng nhập (chỉ chữ, số, dấu gạch dưới)
        - **mat_khau** (bắt buộc): Mật khẩu (ít nhất 6 ký tự)
        - **email** (tùy chọn): Địa chỉ email
        - **so_dien_thoai** (tùy chọn): Số điện thoại
        """)
        
        # Tạo template Excel
        try:
            excel_data = create_excel_template()
            st.download_button(
                label="📥 Tải Template Excel",
                data=excel_data,
                file_name=f"template_hoc_sinh_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_download_template"
            )
        except Exception as e:
            st.error(f"❌ Lỗi tạo template: {str(e)}")
    
    with tab2:
        st.write("**📤 Upload file Excel:**")
        
        uploaded_file = st.file_uploader(
            "Chọn file Excel",
            type=['xlsx', 'xls'],
            help="Chọn file Excel có định dạng theo template",
            key="uploader_students_excel"
        )
        
        if uploaded_file is not None:
            try:
                # Đọc file Excel
                df = pd.read_excel(uploaded_file, sheet_name=0)
                
                st.success(f"✅ Đã đọc file: {uploaded_file.name}")
                st.info(f"📊 Tìm thấy {len(df)} dòng dữ liệu")
                
                # Hiển thị preview
                st.write("**👀 Preview dữ liệu:**")
                st.dataframe(df.head(10), use_container_width=True)
                
                if len(df) > 10:
                    st.caption(f"... và {len(df) - 10} dòng khác")
                
                # Validate dữ liệu
                st.write("**🔍 Kiểm tra dữ liệu:**")
                
                with st.spinner("Đang kiểm tra..."):
                    errors, warnings, valid_students = validate_excel_data(df)
                
                # Hiển thị kết quả validation
                if errors:
                    st.error(f"❌ Tìm thấy {len(errors)} lỗi:")
                    for error in errors[:10]:  # Hiển thị tối đa 10 lỗi
                        st.error(f"• {error}")
                    if len(errors) > 10:
                        st.error(f"... và {len(errors) - 10} lỗi khác")
                
                if warnings:
                    st.warning(f"⚠️ Tìm thấy {len(warnings)} cảnh báo:")
                    for warning in warnings[:5]:  # Hiển thị tối đa 5 cảnh báo
                        st.warning(f"• {warning}")
                    if len(warnings) > 5:
                        st.warning(f"... và {len(warnings) - 5} cảnh báo khác")
                
                if not errors and valid_students:
                    st.success(f"✅ Dữ liệu hợp lệ! Sẵn sàng import {len(valid_students)} học sinh")
                    
                    # Tùy chọn import
                    st.write("**⚙️ Tùy chọn import:**")
                    
                    auto_resolve = st.checkbox(
                        "🔧 Tự động giải quyết username trùng lặp",
                        help="Hệ thống sẽ tự động thêm số vào username bị trùng",
                        value=True,
                        key="chk_auto_resolve"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🚀 Bắt đầu Import", use_container_width=True, type="primary", key="btn_start_import"):
                            # Lưu dữ liệu vào session để import
                            st.session_state.import_data = valid_students
                            st.session_state.auto_resolve = auto_resolve
                            st.session_state.start_import = True
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ Hủy", use_container_width=True, key="btn_cancel_import"):
                            st.session_state.show_import_students = False
                            st.rerun()
                
                elif not errors:
                    st.info("ℹ️ Không có dữ liệu hợp lệ để import")
            
            except Exception as e:
                st.error(f"❌ Lỗi đọc file Excel: {str(e)}")
                st.info("💡 Hãy đảm bảo file Excel đúng định dạng template")
    
    with tab3:
        st.write("**📊 Kết quả import:**")
        
        # Xử lý import
        if st.session_state.get("start_import", False):
            import_data = st.session_state.get("import_data", [])
            auto_resolve = st.session_state.get("auto_resolve", True)
            
            if import_data:
                with st.spinner("Đang import học sinh..."):
                    result = bulk_create_students(import_data, auto_resolve)
                
                # Hiển thị kết quả
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("✅ Thành công", result['success_count'])
                
                with col2:
                    st.metric("❌ Thất bại", len(result['failed_students']))
                
                with col3:
                    st.metric("⚠️ Trùng lặp", len(result['conflict_students']))
                
                # Chi tiết kết quả
                if result['success_count'] > 0:
                    st.success(f"🎉 Đã tạo thành công {result['success_count']} học sinh!")
                
                # Hiển thị username đã được thay đổi
                if result['resolved_conflicts']:
                    st.info("🔧 **Username đã được tự động thay đổi:**")
                    for student in result['resolved_conflicts']:
                        st.write(f"• {student['ho_ten']}: `{student['original_username']}` → `{student['new_username']}`")
                
                # Hiển thị lỗi
                if result['failed_students']:
                    st.error("❌ **Không thể tạo:**")
                    for student in result['failed_students']:
                        st.write(f"• Dòng {student['row_num']}: {student['ho_ten']} - {student['error']}")
                
                # Hiển thị trùng lặp
                if result['conflict_students']:
                    st.warning("⚠️ **Username bị trùng lặp:**")
                    for student in result['conflict_students']:
                        st.write(f"• Dòng {student['row_num']}: {student['ho_ten']} (username: {student['username']})")
                    
                    st.info("💡 Bật tùy chọn 'Tự động giải quyết username trùng lặp' để xử lý tự động")
                
                # Reset import state
                st.session_state.start_import = False
                st.session_state.import_data = None
                
                # Button đóng
                if st.button("✅ Hoàn thành", use_container_width=True, key="btn_complete_import"):
                    st.session_state.show_import_students = False
                    st.rerun()
            
            else:
                st.error("❌ Không có dữ liệu để import")
        
        else:
            st.info("📤 Upload file Excel ở tab 'Upload' để bắt đầu import")
    
    # Nút đóng popup
    if not st.session_state.get("start_import", False):
        if st.button("❌ Đóng", use_container_width=True, key="btn_close_import_popup"):
            st.session_state.show_import_students = False
            st.rerun()

def show_import_stats_popup():
    """Popup thống kê import"""
    st.write("### 📊 Thống kê Import Học sinh")
    
    try:
        stats = get_import_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📅 Hôm nay", stats['today'])
        
        with col2:
            st.metric("📆 Tuần này", stats['week'])
        
        with col3:
            st.metric("🗓️ Tháng này", stats['month'])
        
        # Thêm thống kê khác
        st.divider()
        
        # Lấy thống kê tổng
        all_students = get_all_students_detailed()
        active_count = len([s for s in all_students if s['is_active']])
        inactive_count = len(all_students) - active_count
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Tổng học sinh", len(all_students))
        
        with col2:
            st.metric("✅ Đang hoạt động", active_count)
        
        with col3:
            st.metric("🔒 Đã khóa", inactive_count)
        
        st.info("📈 Thống kê được cập nhật theo thời gian thực")
    
    except Exception as e:
        st.error(f"❌ Lỗi lấy thống kê: {str(e)}")
    
    if st.button("❌ Đóng", use_container_width=True, key="btn_close_stats_popup"):
        st.session_state.show_import_stats = False
        st.rerun()

def show_create_exam():
    """Giao diện tạo đề thi hoàn chỉnh với tích hợp word parser"""
    st.header("📝 Tạo đề thi mới")
    
    user = get_current_user()
    classes = get_classes_by_teacher(user['id'])
    
    if not classes:
        st.warning("⚠️ Bạn cần tạo lớp học trước khi tạo đề thi!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Tạo lớp ngay", use_container_width=True):
                st.session_state.current_page = "manage_classes"
                st.rerun()
        with col2:
            if st.button("📚 Xem hướng dẫn", use_container_width=True):
                show_exam_creation_guide()
        return
    
    # Khởi tạo session state cho questions
    if "exam_questions" not in st.session_state:
        st.session_state.exam_questions = []
    if "current_question" not in st.session_state:
        st.session_state.current_question = {}
    
    # Tabs chính
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Thông tin đề thi", 
        "❓ Thêm câu hỏi", 
        "📝 Xem trước đề", 
        "🚀 Hoàn thành"
    ])
    
    with tab1:
        show_exam_info_tab(classes)
    
    with tab2:
        show_add_questions_tab()
    
    with tab3:
        show_preview_tab()
    
    with tab4:
        show_complete_tab(user)

def show_exam_info_tab(classes):
    """Tab thông tin đề thi"""
    st.subheader("📋 Thông tin cơ bản")
    
    with st.form("exam_basic_info"):
        col1, col2 = st.columns(2)
        
        with col1:
            exam_title = st.text_input(
                "Tiêu đề đề thi *", 
                placeholder="Ví dụ: Kiểm tra 15 phút - Toán học",
                value=st.session_state.get("exam_title", "")
            )
            
            class_options = {f"{c['name']} ({c['student_count']} HS)": c['id'] for c in classes}
            
            # Nếu đã có lớp được chọn từ popup lớp học, tự động chọn
            if st.session_state.get("exam_class_id"):
                for display_name, class_id in class_options.items():
                    if class_id == st.session_state.exam_class_id:
                        selected_index = list(class_options.keys()).index(display_name)
                        break
                else:
                    selected_index = 0
            else:
                selected_index = 0
                
            selected_class_display = st.selectbox(
                "Chọn lớp *", 
                options=list(class_options.keys()),
                index=selected_index
            )
            
            time_limit = st.number_input(
                "Thời gian làm bài (phút) *", 
                min_value=5, max_value=300, 
                value=st.session_state.get("exam_time_limit", 60)
            )
        
        with col2:
            description = st.text_area(
                "Mô tả đề thi", 
                placeholder="Ghi chú về đề thi, yêu cầu đặc biệt...",
                value=st.session_state.get("exam_description", "")
            )
            
            instructions = st.text_area(
                "Hướng dẫn làm bài",
                placeholder="Hướng dẫn chi tiết cho học sinh...",
                value=st.session_state.get("exam_instructions", "")
            )
        
        st.subheader("⏰ Thời gian mở đề")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            start_date = st.date_input(
                "Ngày bắt đầu", 
                value=st.session_state.get("exam_start_date", datetime.now().date())
            )
        with col2:
            start_time = st.time_input(
                "Giờ bắt đầu", 
                value=st.session_state.get("exam_start_time", datetime.now().time())
            )
        with col3:
            end_date = st.date_input(
                "Ngày kết thúc", 
                value=st.session_state.get("exam_end_date", (datetime.now() + timedelta(days=7)).date())
            )
        with col4:
            end_time = st.time_input(
                "Giờ kết thúc", 
                value=st.session_state.get("exam_end_time", datetime.now().time())
            )
        
        if st.form_submit_button("💾 Lưu thông tin đề thi", use_container_width=True):
            if not exam_title or not selected_class_display:
                st.error("❌ Vui lòng nhập đầy đủ thông tin bắt buộc!")
                return
            
            # Lưu vào session state
            st.session_state.exam_title = exam_title
            st.session_state.exam_description = description
            st.session_state.exam_instructions = instructions
            st.session_state.exam_class_id = class_options[selected_class_display]
            st.session_state.exam_class_name = selected_class_display.split(" (")[0]
            st.session_state.exam_time_limit = time_limit
            st.session_state.exam_start_date = start_date
            st.session_state.exam_start_time = start_time
            st.session_state.exam_end_date = end_date
            st.session_state.exam_end_time = end_time
            
            st.success("✅ Đã lưu thông tin đề thi! Chuyển sang tab 'Thêm câu hỏi'")
    
    # Hiển thị thông tin đã lưu
    if st.session_state.get("exam_title"):
        with st.expander("📄 Thông tin đã lưu", expanded=False):
            st.write(f"**Tiêu đề:** {st.session_state.exam_title}")
            st.write(f"**Lớp:** {st.session_state.get('exam_class_name', 'Chưa chọn')}")
            st.write(f"**Thời gian:** {st.session_state.exam_time_limit} phút")
            st.write(f"**Từ:** {st.session_state.exam_start_date} {st.session_state.exam_start_time}")
            st.write(f"**Đến:** {st.session_state.exam_end_date} {st.session_state.exam_end_time}")

def show_add_questions_tab():
    """Tab thêm câu hỏi với point distribution và consistency"""
    st.subheader("❓ Thêm câu hỏi")
    
    if not st.session_state.get("exam_title"):
        st.warning("⚠️ Vui lòng hoàn thành thông tin đề thi ở tab đầu tiên!")
        return
    
    # Kích hoạt MathJax
    render_mathjax()
    
    # Tabs con cho các cách thêm câu hỏi
    subtab1, subtab2, subtab3, subtab4 = st.tabs(["✍️ Thêm thủ công", "📄 Upload từ Word", "📊 Quản lý", "⚖️ Phân phối điểm"])
    
    with subtab1:
        show_manual_question_input()
    
    with subtab2:
        try:
            show_upload_word_exam()
        except Exception as e:
            st.error("❌ Lỗi tải word parser!")
            st.code(str(e))
            st.info("💡 Cần cài đặt: `pip install mammoth pandas openpyxl`")
    
    with subtab3:
        show_questions_management()
    
    with subtab4:
        show_point_distribution()

def import_questions_to_exam(questions: list, parser):
    """Import câu hỏi vào session_state - SỬA: Giữ nguyên cấu trúc ban đầu"""
    try:
        # KHÔNG CHUYỂN ĐỔI - Giữ nguyên cấu trúc từ parser
        if "exam_questions" not in st.session_state:
            st.session_state.exam_questions = []
        
        # Import trực tiếp without conversion để giữ nguyên cấu trúc
        imported_count = 0
        for q in questions:
            # Đảm bảo có các trường cần thiết cho exam format
            exam_question = {
                'type': q['type'],
                'question': q['question'],
                'points': q.get('points', 1.0),
                'difficulty': q.get('difficulty', 'Trung bình'),
                'solution': q.get('solution', ''),
                'image_data': q.get('image_base64') or None  # Đổi tên field
            }
            
            if q['type'] == 'multiple_choice':
                exam_question.update({
                    'options': [q['option_a'], q['option_b'], q['option_c'], q['option_d']],
                    'correct_answer': q['correct_answer']
                })
            elif q['type'] == 'true_false':
                # QUAN TRỌNG: Giữ nguyên cấu trúc statements
                exam_question.update({
                    'statements': q['statements'],
                    'correct_answers': q['correct_answers']
                })
            elif q['type'] == 'short_answer':
                exam_question.update({
                    'sample_answers': q.get('sample_answers', [q.get('correct_answer', '')]),
                    'case_sensitive': q.get('case_sensitive', False)
                })
            elif q['type'] == 'essay':
                exam_question.update({
                    'grading_criteria': q.get('grading_criteria', 'Chấm bằng hình ảnh do học sinh nộp'),
                    'submission_type': q.get('submission_type', 'image_upload'),
                    'requires_image': True
                })
            
            st.session_state.exam_questions.append(exam_question)
            imported_count += 1
        
        st.success(f"✅ Đã import thành công {imported_count} câu hỏi vào đề thi!")
        st.info("💡 Chuyển sang tab 'Quản lý' để xem danh sách câu hỏi đã import")
        
    except Exception as e:
        st.error(f"❌ Lỗi khi import: {str(e)}")
        st.code(str(e))  # Debug info

def show_manual_question_input():
    """Giao diện thêm câu hỏi thủ công - NHẤT QUÁN cho đúng/sai"""
    # Hiển thị danh sách câu hỏi hiện có
    questions = st.session_state.get("exam_questions", [])
    
    if questions:
        st.write(f"**📝 Đã có {len(questions)} câu hỏi:**")
        
        total_points = sum(q['points'] for q in questions)
        st.info(f"📊 Tổng điểm: {total_points:.1f} điểm")
        
        # Hiển thị từng câu hỏi với format NHẤT QUÁN
        for i, question in enumerate(questions):
            with st.expander(f"Câu {i+1}: {question['question'][:50]}...", expanded=False):
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    type_names = {
                        "multiple_choice": "🔤 Trắc nghiệm 4 lựa chọn",
                        "true_false": "✅ Đúng/Sai",
                        "short_answer": "📝 Trả lời ngắn",
                        "essay": "📄 Tự luận"
                    }
                    st.write(f"**Loại:** {type_names[question['type']]}")
                    st.write(f"**Câu hỏi:** {question['question']}")
                    st.write(f"**Điểm:** {question['points']}")
                    
                    if question['type'] == 'multiple_choice':
                        st.write("**Các lựa chọn:**")
                        for j, option in enumerate(question.get('options', [])):
                            prefix = "✅" if chr(65+j) == question.get('correct_answer') else "  "
                            st.write(f"  {prefix} {chr(65+j)}. {option}")
                    
                    elif question['type'] == 'true_false':
                        # NHẤT QUÁN: Hiển thị đúng cấu trúc đúng/sai
                        if 'statements' in question and question['statements']:
                            st.write("**📝 Các phát biểu:**")
                            for stmt in question['statements']:
                                icon = "✅" if stmt.get('is_correct', False) else "❌"
                                status = "Đúng" if stmt.get('is_correct', False) else "Sai"
                                st.write(f"  {icon} **{stmt['letter']})** {stmt['text']} ({status})")
                            
                            correct_letters = [stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)]
                            st.info(f"**🎯 Phát biểu đúng:** {', '.join(correct_letters)}")
                        else:
                            # Fallback cho format cũ hoặc bị lỗi
                            st.warning("⚠️ Câu hỏi này thiếu cấu trúc phát biểu!")
                            if 'correct_answers' in question:
                                st.write(f"**Đáp án:** {', '.join(question['correct_answers'])}")
                            else:
                                st.write(f"**Đáp án:** {question.get('correct_answer', 'N/A')}")
                    
                    elif question['type'] == 'short_answer':
                        answers = question.get('sample_answers', [])
                        if answers:
                            st.write(f"**Đáp án mẫu:** {', '.join(answers)}")
                        else:
                            st.write("**Đáp án:** Chưa có")
                    
                    elif question['type'] == 'essay':
                        st.write("**📄 Loại:** Tự luận")
                        if question.get('requires_image'):
                            st.write("**📷 Yêu cầu chụp ảnh bài làm**")
                        if question.get('grading_criteria'):
                            st.write(f"**📋 Tiêu chí:** {question['grading_criteria'][:50]}...")
                    
                    # Hiển thị hình ảnh nếu có
                    if question.get('image_data'):
                        st.write("**🖼️ Có hình ảnh đính kèm**")
                    
                    # Hiển thị lời giải nếu có
                    if question.get('solution'):
                        st.write("**💡 Lời giải:**")
                        st.markdown(question['solution'][:100] + "..." if len(question['solution']) > 100 else question['solution'])
                
                with col2:
                    if st.button("✏️ Sửa", key=f"edit_q_{i}"):
                        st.session_state.edit_question_index = i
                        st.session_state.current_question = question.copy()
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Xóa", key=f"delete_q_{i}"):
                        st.session_state.exam_questions.pop(i)
                        st.success(f"✅ Đã xóa câu {i+1}")
                        st.rerun()
        
        st.divider()
    
    # Form thêm câu hỏi mới hoặc chỉnh sửa
    is_editing = "edit_question_index" in st.session_state
    form_title = "✏️ Chỉnh sửa câu hỏi" if is_editing else "➕ Thêm câu hỏi mới"
    
    st.write(f"**{form_title}:**")
    
    # Lấy dữ liệu từ câu hỏi đang edit (nếu có)
    current_question = st.session_state.get("current_question", {}) if is_editing else {}
    
    question_type = st.selectbox(
        "Loại câu hỏi",
        ["multiple_choice", "true_false", "short_answer", "essay"],
        format_func=lambda x: {
            "multiple_choice": "🔤 Trắc nghiệm 4 lựa chọn",
            "true_false": "✅ Đúng/Sai",
            "short_answer": "📝 Trả lời ngắn",
            "essay": "📄 Tự luận"
        }[x],
        index=["multiple_choice", "true_false", "short_answer", "essay"].index(current_question.get('type', 'multiple_choice')),
        key="new_question_type"
    )
    
    with st.form("add_question_form"):
        question_text = st.text_area(
            "Nội dung câu hỏi *", 
            value=current_question.get('question', ''),
            placeholder="Nhập câu hỏi... (Hỗ trợ LaTeX: $x^2$ hoặc $\\int_0^1 f(x)dx$)",
            height=100,
            help="Có thể sử dụng công thức LaTeX với $...$ cho inline hoặc $$...$$ cho block"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            points = st.number_input(
                "Điểm", 
                min_value=0.25, max_value=20.0, 
                value=current_question.get('points', 1.0), 
                step=0.25
            )
        
        with col2:
            difficulty = st.selectbox(
                "Độ khó", 
                ["Dễ", "Trung bình", "Khó"],
                index=["Dễ", "Trung bình", "Khó"].index(current_question.get('difficulty', 'Trung bình'))
            )
        
        # Trường lời giải chung
        solution = st.text_area(
            "Lời giải (tùy chọn)",
            value=current_question.get('solution', ''),
            placeholder="Nhập lời giải chi tiết... (Hỗ trợ LaTeX)",
            height=80
        )
        
        # Các trường cụ thể theo loại câu hỏi
        question_data = {
            "type": question_type,
            "question": question_text,
            "points": points,
            "difficulty": difficulty,
            "solution": solution
        }
        
        if question_type == "multiple_choice":
            st.write("**Các lựa chọn:**")
            current_options = current_question.get('options', ['', '', '', ''])
            options = []
            
            for i in range(4):
                option = st.text_input(
                    f"Lựa chọn {chr(65+i)}", 
                    value=current_options[i] if i < len(current_options) else '',
                    key=f"option_{i}",
                    placeholder="Có thể dùng LaTeX: $x^2$"
                )
                options.append(option)
            
            current_correct = current_question.get('correct_answer', 'A')
            correct_answer = st.selectbox(
                "Đáp án đúng", 
                ["A", "B", "C", "D"],
                index=["A", "B", "C", "D"].index(current_correct) if current_correct in ["A", "B", "C", "D"] else 0
            )
            
            question_data.update({
                "options": options,
                "correct_answer": correct_answer
            })
        
        elif question_type == "true_false":
            # XỬ LÝ NHẤT QUÁN cho đúng/sai
            st.write("**📝 Các phát biểu đúng/sai:**")
            st.caption("Nhập từng phát biểu và đánh dấu đúng/sai")
            
            # Lấy dữ liệu hiện tại nếu đang edit
            current_statements = current_question.get('statements', [])
            statements = []
            correct_answers = []
            
            # Đảm bảo có ít nhất 4 phát biểu để nhập
            for i in range(4):
                col1, col2 = st.columns([3, 1])
                
                # Lấy dữ liệu hiện tại cho phát biểu này
                current_stmt = None
                if i < len(current_statements):
                    current_stmt = current_statements[i]
                
                with col1:
                    statement_text = st.text_input(
                        f"Phát biểu {chr(ord('a') + i)}", 
                        value=current_stmt['text'] if current_stmt else '',
                        key=f"statement_{i}",
                        placeholder="Nhập nội dung phát biểu..."
                    )
                
                with col2:
                    is_correct = st.checkbox(
                        "Đúng", 
                        value=current_stmt['is_correct'] if current_stmt else False,
                        key=f"correct_{i}",
                        help=f"Đánh dấu nếu phát biểu {chr(ord('a') + i)} đúng"
                    )
                
                if statement_text.strip():  # Chỉ thêm nếu có nội dung
                    statements.append({
                        'letter': chr(ord('a') + i),
                        'text': statement_text.strip(),
                        'is_correct': is_correct
                    })
                    
                    if is_correct:
                        correct_answers.append(chr(ord('a') + i))
            
            question_data.update({
                "statements": statements,
                "correct_answers": correct_answers
            })
        
        elif question_type == "short_answer":
            current_answers = current_question.get('sample_answers', [])
            sample_answers_text = '; '.join(current_answers) if current_answers else ''
            
            sample_answers = st.text_area(
                "Câu trả lời mẫu", 
                value=sample_answers_text,
                placeholder="Nhập các câu trả lời đúng, cách nhau bằng dấu ;"
            )
            
            case_sensitive = st.checkbox(
                "Phân biệt hoa thường",
                value=current_question.get('case_sensitive', False)
            )
            
            question_data.update({
                "sample_answers": [ans.strip() for ans in sample_answers.split(";") if ans.strip()],
                "case_sensitive": case_sensitive
            })
        
        elif question_type == "essay":
            requires_image = st.checkbox(
                "Yêu cầu chụp ảnh bài làm",
                value=current_question.get('requires_image', False)
            )
            
            grading_rubric = st.text_area(
                "Tiêu chí chấm điểm", 
                value=current_question.get('grading_criteria', ''),
                placeholder="Mô tả tiêu chí chấm điểm cho câu tự luận..."
            )
            
            question_data.update({
                "requires_image": requires_image,
                "grading_criteria": grading_rubric
            })
        
        # Copy image data nếu đang edit
        if is_editing and current_question.get('image_data'):
            question_data['image_data'] = current_question['image_data']
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_text = "💾 Cập nhật câu hỏi" if is_editing else "✅ Thêm câu hỏi"
            if st.form_submit_button(submit_text, use_container_width=True):
                # Validation
                if not question_text.strip():
                    st.error("❌ Vui lòng nhập nội dung câu hỏi!")
                elif question_type == "multiple_choice" and not all(options):
                    st.error("❌ Vui lòng nhập đầy đủ 4 lựa chọn!")
                elif question_type == "true_false" and len(question_data["statements"]) == 0:
                    st.error("❌ Vui lòng nhập ít nhất 1 phát biểu!")
                elif question_type == "true_false" and len(question_data["correct_answers"]) == 0:
                    st.warning("⚠️ Chưa có phát biểu nào được đánh dấu đúng!")
                elif question_type == "short_answer" and not question_data["sample_answers"]:
                    st.error("❌ Vui lòng nhập ít nhất 1 câu trả lời mẫu!")
                else:
                    # Lưu câu hỏi
                    if is_editing:
                        # Cập nhật câu hỏi
                        st.session_state.exam_questions[st.session_state.edit_question_index] = question_data
                        del st.session_state.edit_question_index
                        del st.session_state.current_question
                        st.success("✅ Đã cập nhật câu hỏi!")
                    else:
                        # Thêm câu hỏi mới
                        st.session_state.exam_questions.append(question_data)
                        st.success("✅ Đã thêm câu hỏi!")
                    
                    st.rerun()
        
        with col2:
            cancel_text = "❌ Hủy chỉnh sửa" if is_editing else "🔄 Làm mới"
            if st.form_submit_button(cancel_text, use_container_width=True):
                if is_editing:
                    del st.session_state.edit_question_index
                    del st.session_state.current_question
                st.rerun()
    
    # Hiển thị thông báo nếu đang edit
    if is_editing:
        edit_index = st.session_state.edit_question_index
        st.info(f"✏️ Đang chỉnh sửa câu {edit_index + 1}. Dữ liệu đã được load vào form phía trên.")

def show_questions_management():
    """Tab quản lý câu hỏi với hiển thị NHẤT QUÁN"""
    st.subheader("📊 Quản lý câu hỏi")
    
    questions = st.session_state.get("exam_questions", [])
    
    if not questions:
        st.info("📝 Chưa có câu hỏi nào. Hãy thêm câu hỏi ở các tab khác!")
        return
    
    # Thống kê tổng quan
    total_questions = len(questions)
    total_points = sum(q['points'] for q in questions)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Tổng câu", total_questions)
    with col2:
        st.metric("📊 Tổng điểm", f"{total_points:.1f}")
    with col3:
        avg_points = total_points / total_questions if total_questions > 0 else 0
        st.metric("📈 TB điểm/câu", f"{avg_points:.1f}")
    with col4:
        image_count = len([q for q in questions if q.get('image_data')])
        st.metric("🖼️ Có hình ảnh", image_count)
    
    # Bảng quản lý câu hỏi với hiển thị CHÍNH XÁC
    st.write("### 📋 Danh sách câu hỏi")
    
    # Tạo DataFrame với hiển thị đúng cho câu đúng/sai
    questions_data = []
    for i, q in enumerate(questions):
        row_data = {
            'STT': i + 1,
            'Loại': get_question_type_display(q['type']),
            'Câu hỏi': truncate_text(q['question'], 60),
            'Điểm': q['points'],
            'Độ khó': q.get('difficulty', 'Trung bình'),
            'Hình ảnh': '✅' if q.get('image_data') else '❌'
        }
        
        # Xử lý đáp án theo từng loại - NHẤT QUÁN
        if q['type'] == 'multiple_choice':
            row_data['Đáp án'] = f"Đáp án: {q.get('correct_answer', 'N/A')}"
        elif q['type'] == 'true_false':
            if 'statements' in q and q['statements']:
                correct_letters = [stmt['letter'] for stmt in q['statements'] if stmt.get('is_correct', False)]
                row_data['Đáp án'] = f"Đúng: {', '.join(correct_letters)}" if correct_letters else "Chưa có đáp án"
                row_data['Số phát biểu'] = len(q['statements'])
            elif 'correct_answers' in q:
                row_data['Đáp án'] = f"Đúng: {', '.join(q['correct_answers'])}"
            else:
                row_data['Đáp án'] = "Chưa xác định"
        elif q['type'] == 'short_answer':
            answers = q.get('sample_answers', [])
            row_data['Đáp án'] = f"Mẫu: {answers[0][:20]}..." if answers else "Chưa có"
        elif q['type'] == 'essay':
            submission_type = "Hình ảnh" if q.get('requires_image') else "Text"
            row_data['Đáp án'] = f"Tự luận ({submission_type})"
        
        questions_data.append(row_data)
    
    if questions_data:
        df = pd.DataFrame(questions_data)
        st.dataframe(df, use_container_width=True)
        
        # Thao tác với câu hỏi
        st.write("**🔧 Thao tác:**")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_indices = st.multiselect(
                "Chọn câu hỏi (theo STT):",
                options=list(range(1, len(questions) + 1)),
                format_func=lambda x: f"Câu {x}",
                key="selected_questions"
            )
        
        with col2:
            if selected_indices:
                st.write(f"**Đã chọn {len(selected_indices)} câu hỏi**")
        
        # Buttons hành động
        if selected_indices:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✏️ Sửa câu đầu tiên", disabled=len(selected_indices) != 1):
                    if len(selected_indices) == 1:
                        idx = selected_indices[0] - 1
                        st.session_state.edit_question_index = idx
                        st.session_state.current_question = questions[idx].copy()
                        st.info("💡 Chuyển sang tab 'Thêm thủ công' để chỉnh sửa")
            
            with col2:
                if st.button("📋 Sao chép"):
                    for idx in selected_indices:
                        new_question = questions[idx - 1].copy()
                        new_question['question'] = f"[Sao chép] {new_question['question']}"
                        st.session_state.exam_questions.append(new_question)
                    st.success(f"✅ Đã sao chép {len(selected_indices)} câu hỏi!")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Đổi thứ tự"):
                    st.info("💡 Chuyển sang tab 'Phân phối điểm' để sắp xếp")
            
            with col4:
                if st.button("🗑️ Xóa", type="secondary"):
                    for idx in sorted(selected_indices, reverse=True):
                        st.session_state.exam_questions.pop(idx - 1)
                    st.success(f"✅ Đã xóa {len(selected_indices)} câu hỏi!")
                    st.rerun()
    
    # Buttons quản lý chung
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📤 Xuất Excel", use_container_width=True):
            export_questions_to_excel(questions)
    
    with col2:
        if st.button("📊 Thống kê chi tiết", use_container_width=True):
            show_detailed_statistics(questions)
    
    with col3:
        if st.button("🔀 Trộn câu hỏi", use_container_width=True):
            shuffle_questions()
    
    with col4:
        if st.button("🗑️ Xóa tất cả", type="secondary", use_container_width=True):
            if st.button("⚠️ Xác nhận xóa tất cả", type="secondary"):
                st.session_state.exam_questions = []
                st.success("✅ Đã xóa tất cả câu hỏi!")
                st.rerun()
    
    # Preview chi tiết một số câu hỏi đúng/sai để kiểm tra
    with st.expander("👁️ Preview chi tiết câu đúng/sai (kiểm tra tính nhất quán)", expanded=False):
        true_false_questions = [q for q in questions if q['type'] == 'true_false']
        
        if true_false_questions:
            for i, q in enumerate(true_false_questions[:2]):  # Chỉ hiển thị 2 câu đầu
                st.write(f"**Câu đúng/sai {i+1}:**")
                st.write(f"Câu hỏi: {q['question']}")
                
                if 'statements' in q and q['statements']:
                    st.write("Các phát biểu:")
                    for stmt in q['statements']:
                        icon = "✅" if stmt.get('is_correct', False) else "❌"
                        st.write(f"  {icon} {stmt['letter']}) {stmt['text']}")
                    
                    correct_letters = [stmt['letter'] for stmt in q['statements'] if stmt.get('is_correct', False)]
                    st.success(f"Đáp án đúng: {', '.join(correct_letters)}")
                else:
                    st.warning("⚠️ Câu hỏi này thiếu cấu trúc statements!")
                
                st.write(f"Điểm: {q['points']}")
                st.divider()
        else:
            st.info("Không có câu hỏi đúng/sai nào")

def show_point_distribution():
    """Tab phân phối điểm tự động và thủ công"""
    st.subheader("⚖️ Phân phối điểm")
    
    questions = st.session_state.get("exam_questions", [])
    if not questions:
        st.info("📝 Chưa có câu hỏi nào để phân phối điểm!")
        return
    
    current_total = sum(q['points'] for q in questions)
    st.info(f"📊 **Tổng điểm hiện tại:** {current_total:.1f} điểm từ {len(questions)} câu hỏi")
    
    # Tab phân phối
    tab1, tab2, tab3 = st.tabs(["🤖 Tự động theo loại", "📋 Theo phần", "✏️ Thủ công từng câu"])
    
    with tab1:
        show_auto_point_distribution()
    
    with tab2:
        show_section_point_distribution()
    
    with tab3:
        show_manual_point_distribution()

def show_auto_point_distribution():
    """Phân phối điểm tự động theo loại câu hỏi"""
    st.write("### 🤖 Phân phối tự động theo loại câu hỏi")
    
    questions = st.session_state.exam_questions
    
    # Đếm số câu theo loại
    type_counts = {}
    for q in questions:
        q_type = q['type']
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
    
    # Hiển thị thống kê hiện tại
    st.write("**📊 Thống kê câu hỏi:**")
    type_names = {
        "multiple_choice": "🔤 Trắc nghiệm",
        "true_false": "✅ Đúng/Sai", 
        "short_answer": "📝 Trả lời ngắn",
        "essay": "📄 Tự luận"
    }
    
    for q_type, count in type_counts.items():
        current_points = sum(q['points'] for q in questions if q['type'] == q_type)
        st.write(f"- {type_names[q_type]}: {count} câu, {current_points:.1f} điểm")
    
    st.divider()
    
    # Cài đặt điểm theo loại
    st.write("**⚖️ Thiết lập điểm cho từng loại:**")
    
    with st.form("auto_point_distribution"):
        total_target = st.number_input("🎯 Tổng điểm mục tiêu", min_value=1.0, max_value=100.0, value=10.0, step=0.5)
        
        point_settings = {}
        for q_type, count in type_counts.items():
            if count > 0:
                default_points = {
                    "multiple_choice": 1.0,
                    "true_false": 1.0,
                    "short_answer": 1.5,
                    "essay": 2.0
                }.get(q_type, 1.0)
                
                point_settings[q_type] = st.number_input(
                    f"Điểm cho {type_names[q_type]} ({count} câu)",
                    min_value=0.25, max_value=20.0, value=default_points, step=0.25,
                    key=f"auto_points_{q_type}"
                )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("🎯 Áp dụng theo điểm cố định", use_container_width=True):
                apply_fixed_points(point_settings)
        
        with col2:
            if st.form_submit_button("⚖️ Áp dụng theo tỷ lệ mục tiêu", use_container_width=True):
                apply_proportional_points(point_settings, total_target, type_counts)

def show_section_point_distribution():
    """Phân phối điểm theo phần (từ Word upload)"""
    st.write("### 📋 Phân phối theo phần")
    
    questions = st.session_state.exam_questions
    
    # Phân loại câu hỏi theo phần (dựa trên vị trí và loại)
    sections = {
        "Phần 1 - Trắc nghiệm": [q for q in questions if q['type'] == 'multiple_choice'],
        "Phần 2 - Đúng/Sai": [q for q in questions if q['type'] == 'true_false'],
        "Phần 3 - Trả lời ngắn": [q for q in questions if q['type'] == 'short_answer'],
        "Phần 4 - Tự luận": [q for q in questions if q['type'] == 'essay']
    }
    
    # Hiển thị thống kê từng phần
    for section_name, section_questions in sections.items():
        if section_questions:
            current_points = sum(q['points'] for q in section_questions)
            st.write(f"**{section_name}:** {len(section_questions)} câu, {current_points:.1f} điểm")
    
    st.divider()
    
    with st.form("section_point_distribution"):
        st.write("**⚖️ Thiết lập điểm cho từng phần:**")
        
        section_points = {}
        total_questions_in_sections = 0
        
        for section_name, section_questions in sections.items():
            if section_questions:
                total_questions_in_sections += len(section_questions)
                default_total = len(section_questions) * {
                    "Phần 1 - Trắc nghiệm": 1.0,
                    "Phần 2 - Đúng/Sai": 1.0,
                    "Phần 3 - Trả lời ngắn": 1.5,
                    "Phần 4 - Tự luận": 2.0
                }.get(section_name, 1.0)
                
                section_points[section_name] = st.number_input(
                    f"Tổng điểm {section_name} ({len(section_questions)} câu)",
                    min_value=0.5, max_value=50.0, value=default_total, step=0.5,
                    key=f"section_points_{section_name}"
                )
        
        distribution_method = st.radio(
            "Phương pháp phân phối trong phần:",
            ["Chia đều cho tất cả câu", "Theo độ khó (Dễ=0.8x, TB=1x, Khó=1.2x)"],
            key="section_distribution_method"
        )
        
        if st.form_submit_button("📋 Áp dụng phân phối theo phần", use_container_width=True):
            apply_section_points(sections, section_points, distribution_method)

def show_manual_point_distribution():
    """Chỉnh sửa điểm thủ công từng câu"""
    st.write("### ✏️ Chỉnh sửa thủ công từng câu")
    
    questions = st.session_state.exam_questions
    
    if not questions:
        st.info("📝 Chưa có câu hỏi nào!")
        return
    
    st.write("**📝 Danh sách câu hỏi và điểm:**")
    
    # Tạo form để edit từng câu
    with st.form("manual_points"):
        total_new_points = 0
        point_changes = {}
        
        for i, q in enumerate(questions):
            col1, col2, col3, col4 = st.columns([1, 4, 1, 1])
            
            with col1:
                st.write(f"**Câu {i+1}**")
            
            with col2:
                st.write(f"{q['question'][:50]}...")
                st.caption(f"Loại: {get_question_type_display(q['type'])}")
            
            with col3:
                st.write(f"Hiện tại: {q['points']}")
            
            with col4:
                new_points = st.number_input(
                    "Điểm mới",
                    min_value=0.25, max_value=20.0, value=q['points'], step=0.25,
                    key=f"manual_points_{i}"
                )
                point_changes[i] = new_points
                total_new_points += new_points
        
        st.divider()
        current_total = sum(q['points'] for q in questions)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tổng điểm hiện tại", f"{current_total:.1f}")
        with col2:
            st.metric("Tổng điểm mới", f"{total_new_points:.1f}")
        with col3:
            change = total_new_points - current_total
            st.metric("Thay đổi", f"{change:+.1f}")
        
        if st.form_submit_button("💾 Lưu thay đổi điểm", use_container_width=True):
            apply_manual_points(point_changes)

def apply_fixed_points(point_settings):
    """Áp dụng điểm cố định theo loại"""
    questions = st.session_state.exam_questions
    
    for i, q in enumerate(questions):
        if q['type'] in point_settings:
            questions[i]['points'] = point_settings[q['type']]
    
    new_total = sum(q['points'] for q in questions)
    st.success(f"✅ Đã áp dụng điểm cố định! Tổng điểm mới: {new_total:.1f}")
    st.rerun()

def apply_proportional_points(point_settings, total_target, type_counts):
    """Áp dụng điểm theo tỷ lệ để đạt tổng mục tiêu"""
    # Tính tổng điểm theo cài đặt
    calculated_total = sum(point_settings[q_type] * count for q_type, count in type_counts.items() if q_type in point_settings)
    
    if calculated_total == 0:
        st.error("❌ Tổng điểm tính toán bằng 0!")
        return
    
    # Tính tỷ lệ điều chỉnh
    adjustment_ratio = total_target / calculated_total
    
    questions = st.session_state.exam_questions
    
    for i, q in enumerate(questions):
        if q['type'] in point_settings:
            adjusted_points = point_settings[q['type']] * adjustment_ratio
            questions[i]['points'] = round(adjusted_points, 2)
    
    final_total = sum(q['points'] for q in questions)
    st.success(f"✅ Đã áp dụng điểm theo tỷ lệ! Tổng điểm: {final_total:.1f} (mục tiêu: {total_target})")
    st.rerun()

def apply_section_points(sections, section_points, distribution_method):
    """Áp dụng điểm theo phần"""
    questions = st.session_state.exam_questions
    
    for section_name, section_questions in sections.items():
        if section_name in section_points and section_questions:
            total_section_points = section_points[section_name]
            
            if distribution_method == "Chia đều cho tất cả câu":
                points_per_question = total_section_points / len(section_questions)
                for q in section_questions:
                    # Tìm index trong danh sách chính để update
                    for i, main_q in enumerate(questions):
                        if main_q is q:  # So sánh object reference
                            questions[i]['points'] = round(points_per_question, 2)
                            break
            
            else:  # Theo độ khó
                difficulty_weights = {"Dễ": 0.8, "Trung bình": 1.0, "Khó": 1.2}
                total_weight = sum(difficulty_weights.get(q.get('difficulty', 'Trung bình'), 1.0) for q in section_questions)
                
                for q in section_questions:
                    weight = difficulty_weights.get(q.get('difficulty', 'Trung bình'), 1.0)
                    q_points = (total_section_points * weight) / total_weight
                    
                    # Tìm index để update
                    for i, main_q in enumerate(questions):
                        if main_q is q:
                            questions[i]['points'] = round(q_points, 2)
                            break
    
    new_total = sum(q['points'] for q in questions)
    st.success(f"✅ Đã áp dụng phân phối theo phần! Tổng điểm: {new_total:.1f}")
    st.rerun()

def apply_manual_points(point_changes):
    """Áp dụng thay đổi điểm thủ công"""
    questions = st.session_state.exam_questions
    
    for i, new_points in point_changes.items():
        if i < len(questions):
            questions[i]['points'] = new_points
    
    new_total = sum(q['points'] for q in questions)
    st.success(f"✅ Đã cập nhật điểm thủ công! Tổng điểm: {new_total:.1f}")
    st.rerun()

def get_question_type_display(question_type: str) -> str:
    """Lấy tên hiển thị cho loại câu hỏi"""
    type_map = {
        'multiple_choice': '🔤 Trắc nghiệm',
        'true_false': '✅ Đúng/Sai',
        'short_answer': '📝 Trả lời ngắn',
        'essay': '📄 Tự luận'
    }
    return type_map.get(question_type, question_type)

def get_answer_display(question: dict) -> str:
    """Lấy text hiển thị đáp án - NHẤT QUÁN cho mọi nơi"""
    if question['type'] == 'multiple_choice':
        return f"Đáp án: {question.get('correct_answer', 'N/A')}"
    elif question['type'] == 'true_false':
        # Xử lý thống nhất cho cả 2 format
        if 'statements' in question and question['statements']:
            correct_letters = [stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)]
            if correct_letters:
                return f"Phát biểu đúng: {', '.join(correct_letters)}"
            else:
                return "Chưa có đáp án đúng"
        elif 'correct_answers' in question and question['correct_answers']:
            return f"Phát biểu đúng: {', '.join(question['correct_answers'])}"
        else:
            return f"Đáp án: {question.get('correct_answer', 'N/A')}"
    elif question['type'] == 'short_answer':
        answers = question.get('sample_answers', [])
        if answers:
            return f"Đáp án: {answers[0][:30]}..."
        return "Chưa có đáp án"
    elif question['type'] == 'essay':
        return "Tự luận (học sinh nộp bài)"
    return "N/A"

def truncate_text(text: str, max_length: int) -> str:
    """Cắt ngắn text"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def export_questions_to_excel(questions: list):
    """Xuất câu hỏi ra Excel"""
    try:
        # Tạo data cho Excel
        excel_data = []
        for i, q in enumerate(questions):
            row = {
                'STT': i + 1,
                'Loại câu hỏi': get_question_type_display(q['type']),
                'Câu hỏi': q['question'],
                'Điểm': q['points'],
                'Độ khó': q.get('difficulty', 'Trung bình'),
                'Lời giải': q.get('solution', '')
            }
            
            # Thêm thông tin specific cho từng loại
            if q['type'] == 'multiple_choice':
                row.update({
                    'Đáp án A': q.get('options', [''])[0] if len(q.get('options', [])) > 0 else '',
                    'Đáp án B': q.get('options', ['', ''])[1] if len(q.get('options', [])) > 1 else '',
                    'Đáp án C': q.get('options', ['', '', ''])[2] if len(q.get('options', [])) > 2 else '',
                    'Đáp án D': q.get('options', ['', '', '', ''])[3] if len(q.get('options', [])) > 3 else '',
                    'Đáp án đúng': q.get('correct_answer', '')
                })
            elif q['type'] == 'true_false':
                if 'statements' in q and q['statements']:
                    correct_letters = [stmt['letter'] for stmt in q['statements'] if stmt.get('is_correct', False)]
                    row['Đáp án đúng'] = ', '.join(correct_letters)
                    # Thêm các phát biểu
                    for j, stmt in enumerate(q['statements'][:4]):  # Tối đa 4 phát biểu
                        row[f'Phát biểu {stmt["letter"]}'] = stmt['text']
                        row[f'Phát biểu {stmt["letter"]} - Đúng/Sai'] = 'Đúng' if stmt.get('is_correct', False) else 'Sai'
                else:
                    row['Đáp án đúng'] = q.get('correct_answer', '')
            elif q['type'] == 'short_answer':
                answers = q.get('sample_answers', [])
                row['Đáp án mẫu'] = '; '.join(answers)
            elif q['type'] == 'essay':
                row['Yêu cầu hình ảnh'] = 'Có' if q.get('requires_image') else 'Không'
                row['Tiêu chí chấm'] = q.get('grading_criteria', '')
            
            excel_data.append(row)
        
        # Tạo Excel file
        df = pd.DataFrame(excel_data)
        
        # Convert to Excel bytes
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Questions')
        
        excel_bytes = excel_buffer.getvalue()
        
        # Download button
        exam_title = st.session_state.get('exam_title', 'exam')
        safe_title = "".join(c for c in exam_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"questions_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        st.download_button(
            label="📥 Tải file Excel",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success(f"✅ Sẵn sàng tải {len(questions)} câu hỏi!")
        
    except Exception as e:
        st.error(f"❌ Lỗi xuất Excel: {str(e)}")

def show_detailed_statistics(questions: list):
    """Hiển thị thống kê chi tiết"""
    with st.expander("📊 Thống kê chi tiết", expanded=True):
        
        # Thống kê theo loại câu hỏi
        type_counts = {}
        type_points = {}
        
        for q in questions:
            q_type = q['type']
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
            type_points[q_type] = type_points.get(q_type, 0) + q['points']
        
        st.write("### 📈 Phân bố theo loại câu hỏi")
        
        for q_type, count in type_counts.items():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**{get_question_type_display(q_type)}**")
            with col2:
                st.write(f"{count} câu ({count/len(questions)*100:.1f}%)")
            with col3:
                st.write(f"{type_points[q_type]:.1f} điểm")
        
        # Thống kê theo độ khó
        st.write("### 📊 Phân bố theo độ khó")
        difficulty_counts = {}
        for q in questions:
            diff = q.get('difficulty', 'Trung bình')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        for diff, count in difficulty_counts.items():
            st.write(f"**{diff}:** {count} câu ({count/len(questions)*100:.1f}%)")
        
        # Thống kê điểm
        st.write("### 🎯 Phân bố điểm")
        points_list = [q['points'] for q in questions]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Điểm tối thiểu", min(points_list))
        with col2:
            st.metric("Điểm tối đa", max(points_list))
        with col3:
            st.metric("Điểm trung bình", f"{sum(points_list)/len(points_list):.1f}")

def shuffle_questions():
    """Trộn thứ tự câu hỏi"""
    if st.session_state.get("exam_questions"):
        random.shuffle(st.session_state.exam_questions)
        st.success("🔀 Đã trộn thứ tự câu hỏi!")
        st.rerun()
    else:
        st.warning("⚠️ Không có câu hỏi để trộn!")

def show_preview_tab():
    """Tab xem trước đề thi với hỗ trợ MathJax và hình ảnh - NHẤT QUÁN hiển thị đúng/sai"""
    st.subheader("📝 Xem trước đề thi")
    
    if not st.session_state.get("exam_title") or not st.session_state.exam_questions:
        st.warning("⚠️ Vui lòng hoàn thành thông tin đề thi và thêm câu hỏi!")
        return
    
    # Load MathJax
    render_mathjax()
    
    # Header đề thi
    st.markdown(f"""
    <div style='text-align: center; border: 2px solid #667eea; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h2>📝 {st.session_state.exam_title}</h2>
        <p><strong>Lớp:</strong> {st.session_state.get('exam_class_name', '')}</p>
        <p><strong>Thời gian:</strong> {st.session_state.exam_time_limit} phút</p>
        <p><strong>Tổng điểm:</strong> {sum(q['points'] for q in st.session_state.exam_questions):.1f} điểm</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mô tả và hướng dẫn
    if st.session_state.get("exam_description"):
        st.info(f"📄 **Mô tả:** {st.session_state.exam_description}")
    
    if st.session_state.get("exam_instructions"):
        st.info(f"📋 **Hướng dẫn:** {st.session_state.exam_instructions}")
    
    st.divider()
    
    # Danh sách câu hỏi với hỗ trợ LaTeX và hình ảnh
    for i, question in enumerate(st.session_state.exam_questions):
        st.markdown(f"### Câu {i+1}: ({question['points']} điểm)")
        
        # Hiển thị câu hỏi với MathJax
        st.markdown(question['question'])
        
        # Hiển thị hình ảnh nếu có
        if question.get('image_data'):
            try:
                # Hiển thị hình ảnh từ base64
                image_bytes = base64.b64decode(question['image_data'])
                st.image(image_bytes, caption=f"Hình ảnh câu {i+1}", use_column_width=True)
            except Exception as e:
                st.error(f"Lỗi hiển thị hình ảnh câu {i+1}: {e}")
        
        if question['type'] == 'multiple_choice':
            for j, option in enumerate(question.get('options', [])):
                st.markdown(f"  **{chr(65+j)}.** {option}")
            st.caption(f"✅ Đáp án đúng: {question.get('correct_answer', 'N/A')}")
        
        elif question['type'] == 'true_false':
            # NHẤT QUÁN: Hiển thị đúng cấu trúc đúng/sai trong preview
            if 'statements' in question and question['statements']:
                st.markdown("**📝 Đánh dấu Đúng (✓) hoặc Sai (✗) cho mỗi phát biểu:**")
                for stmt in question['statements']:
                    st.markdown(f"  **{stmt['letter']})** {stmt['text']} **[ ]** Đúng **[ ]** Sai")
                
                correct_letters = [stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)]
                st.caption(f"✅ Đáp án đúng: {', '.join(correct_letters)}")
            else:
                # Fallback cho format cũ
                st.markdown("**□ Đúng    □ Sai**")
                st.caption(f"✅ Đáp án đúng: {question.get('correct_answer', 'N/A')}")
        
        elif question['type'] == 'short_answer':
            st.markdown("📝 *Câu trả lời ngắn*")
            if question.get('sample_answers'):
                st.caption(f"✅ Đáp án mẫu: {', '.join(question['sample_answers'])}")
        
        elif question['type'] == 'essay':
            st.markdown("📄 *Trả lời tự luận*")
            if question.get('requires_image'):
                st.markdown("📷 *Yêu cầu chụp ảnh bài làm*")
            if question.get('grading_criteria'):
                st.caption(f"📋 Tiêu chí: {question['grading_criteria']}")
        
        # Hiển thị lời giải nếu có
        if question.get('solution'):
            with st.expander(f"💡 Lời giải câu {i+1}", expanded=False):
                st.markdown(question['solution'])
        
        st.divider()
    
    # Thống kê đề thi
    with st.expander("📊 Thống kê đề thi", expanded=False):
        total_questions = len(st.session_state.exam_questions)
        total_points = sum(q['points'] for q in st.session_state.exam_questions)
        
        question_types = {}
        for q in st.session_state.exam_questions:
            q_type = q['type']
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📈 Tổng quan:**")
            st.write(f"- Tổng câu hỏi: {total_questions}")
            st.write(f"- Tổng điểm: {total_points:.1f}")
            st.write(f"- Thời gian: {st.session_state.exam_time_limit} phút")
            st.write(f"- Điểm trung bình/câu: {total_points/total_questions:.1f}")
        
        with col2:
            st.write("**📊 Phân loại câu hỏi:**")
            type_names = {
                "multiple_choice": "🔤 Trắc nghiệm",
                "true_false": "✅ Đúng/Sai",
                "short_answer": "📝 Trả lời ngắn",
                "essay": "📄 Tự luận"
            }
            for q_type, count in question_types.items():
                st.write(f"- {type_names[q_type]}: {count} câu")
    
    # Button xuất Word hoặc PDF
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Xuất đề thi (Word)", use_container_width=True):
            st.info("🚧 Tính năng đang phát triển...")
    with col2:
        if st.button("🖨️ In đề thi (PDF)", use_container_width=True):
            st.info("🚧 Tính năng đang phát triển...")

def show_complete_tab(user):
    """Tab hoàn thành và lưu đề thi - HOÀN THIỆN"""
    st.subheader("🚀 Hoàn thành đề thi")
    
    if not st.session_state.get("exam_title") or not st.session_state.exam_questions:
        st.error("❌ Chưa đủ thông tin để tạo đề thi!")
        
        missing_items = []
        if not st.session_state.get("exam_title"):
            missing_items.append("❌ Thông tin đề thi")
        else:
            missing_items.append("✅ Thông tin đề thi")
            
        if not st.session_state.exam_questions:
            missing_items.append("❌ Câu hỏi")
        else:
            missing_items.append(f"✅ Câu hỏi ({len(st.session_state.exam_questions)} câu)")
        
        st.write("**Checklist:**")
        for item in missing_items:
            st.write(item)
        return
    
    # Tóm tắt đề thi
    total_questions = len(st.session_state.exam_questions)
    total_points = sum(q['points'] for q in st.session_state.exam_questions)
    
    st.success("✅ Đề thi đã sẵn sàng!")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Câu hỏi", total_questions)
    with col2:
        st.metric("📊 Tổng điểm", f"{total_points:.1f}")
    with col3:
        st.metric("⏱️ Thời gian", f"{st.session_state.exam_time_limit} phút")
    with col4:
        avg_points = total_points / total_questions if total_questions > 0 else 0
        st.metric("📈 TB điểm/câu", f"{avg_points:.1f}")
    
    # Tóm tắt thông tin đề thi
    with st.expander("📋 Tóm tắt đề thi", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📝 Thông tin cơ bản:**")
            st.write(f"• **Tiêu đề:** {st.session_state.exam_title}")
            st.write(f"• **Lớp:** {st.session_state.get('exam_class_name', 'Chưa chọn')}")
            st.write(f"• **Thời gian làm bài:** {st.session_state.exam_time_limit} phút")
            
            if st.session_state.get("exam_description"):
                st.write(f"• **Mô tả:** {st.session_state.exam_description}")
        
        with col2:
            st.write("**📅 Thời gian mở đề:**")
            st.write(f"• **Bắt đầu:** {st.session_state.exam_start_date} {st.session_state.exam_start_time}")
            st.write(f"• **Kết thúc:** {st.session_state.exam_end_date} {st.session_state.exam_end_time}")
            
            # Tính thời gian từ bây giờ
            start_datetime = datetime.combine(st.session_state.exam_start_date, st.session_state.exam_start_time)
            time_until_start = start_datetime - datetime.now()
            
            if time_until_start.total_seconds() > 0:
                st.info(f"⏳ Còn {time_until_start.days} ngày đến khi mở đề")
            else:
                st.success("🚀 Đề thi có thể mở ngay")
        
        # Thống kê câu hỏi chi tiết
        st.write("**📊 Phân tích câu hỏi:**")
        question_types = {}
        type_points = {}
        
        for q in st.session_state.exam_questions:
            q_type = q['type']
            question_types[q_type] = question_types.get(q_type, 0) + 1
            type_points[q_type] = type_points.get(q_type, 0) + q['points']
        
        type_names = {
            "multiple_choice": "🔤 Trắc nghiệm",
            "true_false": "✅ Đúng/Sai",
            "short_answer": "📝 Trả lời ngắn",
            "essay": "📄 Tự luận"
        }
        
        for q_type, count in question_types.items():
            percentage = (type_points[q_type] / total_points) * 100
            st.write(f"• {type_names[q_type]}: {count} câu, {type_points[q_type]:.1f} điểm ({percentage:.1f}%)")
    
    st.divider()
    
    # Kiểm tra validation
    validation_issues = []
    
    # Kiểm tra thời gian
    start_datetime = datetime.combine(st.session_state.exam_start_date, st.session_state.exam_start_time)
    end_datetime = datetime.combine(st.session_state.exam_end_date, st.session_state.exam_end_time)
    
    if start_datetime >= end_datetime:
        validation_issues.append("⚠️ Thời gian kết thúc phải sau thời gian bắt đầu")
    
    # Kiểm tra câu hỏi
    for i, q in enumerate(st.session_state.exam_questions):
        if q['type'] == 'true_false' and 'statements' in q:
            if not any(stmt.get('is_correct', False) for stmt in q['statements']):
                validation_issues.append(f"⚠️ Câu {i+1} (đúng/sai) không có phát biểu nào đúng")
        elif q['type'] == 'multiple_choice' and not q.get('correct_answer'):
            validation_issues.append(f"⚠️ Câu {i+1} (trắc nghiệm) chưa có đáp án đúng")
    
    if validation_issues:
        st.error("❌ **Phát hiện vấn đề cần sửa:**")
        for issue in validation_issues:
            st.write(issue)
        st.info("💡 Vui lòng quay lại các tab trước để sửa các vấn đề này")
        return
    
    # Tùy chọn lưu và phát hành
    st.write("### 💾 Lưu đề thi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📝 Lưu nháp**")
        st.caption("Lưu đề thi để chỉnh sửa sau, học sinh chưa thể thấy")
        
        if st.button("💾 Lưu nháp", use_container_width=True, type="secondary"):
            save_exam_as_draft(user)
    
    with col2:
        st.write("**🚀 Phát hành ngay**")
        st.caption("Lưu và cho phép học sinh truy cập theo thời gian đã đặt")
        
        if st.button("🚀 Phát hành đề thi", use_container_width=True, type="primary"):
            publish_exam(user)
    
    # Buttons bổ sung
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Xem thống kê cuối", use_container_width=True):
            show_final_statistics()
    
    with col2:
        if st.button("📄 Preview lần cuối", use_container_width=True):
            st.session_state.show_final_preview = True
            st.rerun()
    
    with col3:
        if st.button("🗑️ Hủy đề thi", use_container_width=True, type="secondary"):
            show_cancel_exam_confirmation()

def save_exam_as_draft(user):
    """Lưu đề thi dưới dạng nháp"""
    try:
        exam_data = prepare_exam_data(user, is_published=False)
        
        # Mock save function - thay bằng database call thực
        exam_id = f"DRAFT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user['id']}"
        
        # TODO: Thay thế bằng database call thực
        # exam_id = database.create_exam(exam_data)
        
        st.success("✅ Đã lưu đề thi dưới dạng nháp!")
        st.info(f"📋 **Mã đề thi:** {exam_id}")
        st.info("💡 Bạn có thể chỉnh sửa và phát hành sau trong mục 'Quản lý đề thi'")
        
        # Option để tiếp tục
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Tạo đề thi mới", type="primary"):
                clear_exam_data()
                st.rerun()
        with col2:
            if st.button("📊 Xem danh sách đề thi"):
                st.session_state.current_page = "statistics"
                clear_exam_data()
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Lỗi lưu đề thi: {str(e)}")

def publish_exam(user):
    """Phát hành đề thi"""
    try:
        exam_data = prepare_exam_data(user, is_published=True)
        
        # Mock publish function - thay bằng database call thực
        exam_id = f"EXAM_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user['id']}"
        
        # TODO: Thay thế bằng database call thực
        # exam_id = database.create_exam(exam_data)
        # database.notify_students(exam_data['class_id'], exam_id)
        
        st.success("🎉 Đã phát hành đề thi thành công!")
        
        start_datetime = datetime.combine(st.session_state.exam_start_date, st.session_state.exam_start_time)
        end_datetime = datetime.combine(st.session_state.exam_end_date, st.session_state.exam_end_time)
        
        st.info(f"📅 Học sinh có thể làm bài từ {start_datetime.strftime('%d/%m/%Y %H:%M')} đến {end_datetime.strftime('%d/%m/%Y %H:%M')}")
        
        # Hiển thị thông tin đề thi
        class_name = st.session_state.get('exam_class_name', '')
        st.success(f"🔗 **Mã đề thi:** {exam_id}")
        st.success(f"🏫 **Lớp:** {class_name}")
        st.info("💡 Học sinh sẽ thấy đề thi trong danh sách 'Đề thi của tôi'")
        
        # Option để tiếp tục
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Theo dõi kết quả", type="primary"):
                st.session_state.current_page = "grading"
                st.session_state.current_exam_id = exam_id
                clear_exam_data()
                st.rerun()
        
        with col2:
            if st.button("➕ Tạo đề thi mới"):
                clear_exam_data()
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Lỗi phát hành đề thi: {str(e)}")

def prepare_exam_data(user, is_published=True):
    """Chuẩn bị dữ liệu đề thi để lưu - ĐẢM BẢO TÍNH NHẤT QUÁN"""
    start_datetime = datetime.combine(st.session_state.exam_start_date, st.session_state.exam_start_time)
    end_datetime = datetime.combine(st.session_state.exam_end_date, st.session_state.exam_end_time)
    
    # Xử lý câu hỏi - GIỮ NGUYÊN cấu trúc, đặc biệt là đúng/sai
    processed_questions = []
    for i, q in enumerate(st.session_state.exam_questions):
        question_data = {
            'question_id': i + 1,
            'type': q['type'],
            'question': q['question'],
            'points': q['points'],
            'difficulty': q.get('difficulty', 'Trung bình'),
            'solution': q.get('solution', ''),
            'image_data': q.get('image_data')
        }
        
        if q['type'] == 'multiple_choice':
            question_data.update({
                'options': q['options'],
                'correct_answer': q['correct_answer']
            })
        elif q['type'] == 'true_false':
            # QUAN TRỌNG: Giữ NGUYÊN cấu trúc đúng/sai
            question_data.update({
                'statements': q['statements'],
                'correct_answers': q.get('correct_answers', [])
            })
        elif q['type'] == 'short_answer':
            question_data.update({
                'sample_answers': q['sample_answers'],
                'case_sensitive': q.get('case_sensitive', False)
            })
        elif q['type'] == 'essay':
            question_data.update({
                'grading_criteria': q.get('grading_criteria', ''),
                'submission_type': q.get('submission_type', 'text'),
                'requires_image': q.get('requires_image', False)
            })
        
        processed_questions.append(question_data)
    
    exam_data = {
        'title': st.session_state.exam_title,
        'description': st.session_state.get('exam_description', ''),
        'instructions': st.session_state.get('exam_instructions', ''),
        'class_id': st.session_state.exam_class_id,
        'teacher_id': user['id'],
        'time_limit': st.session_state.exam_time_limit,
        'start_time': start_datetime.isoformat(),
        'end_time': end_datetime.isoformat(),
        'is_published': is_published,
        'questions': processed_questions,
        'total_points': sum(q['points'] for q in processed_questions),
        'total_questions': len(processed_questions),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return exam_data

def show_final_statistics():
    """Hiển thị thống kê cuối cùng"""
    with st.expander("📊 Thống kê chi tiết cuối cùng", expanded=True):
        questions = st.session_state.exam_questions
        
        # Thống kê tổng quan
        total_questions = len(questions)
        total_points = sum(q['points'] for q in questions)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Tổng câu hỏi", total_questions)
        with col2:
            st.metric("📊 Tổng điểm", f"{total_points:.1f}")
        with col3:
            avg_time = st.session_state.exam_time_limit / total_questions
            st.metric("⏱️ TB thời gian/câu", f"{avg_time:.1f} phút")
        with col4:
            difficulty_dist = {}
            for q in questions:
                diff = q.get('difficulty', 'Trung bình')
                difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
            most_common_diff = max(difficulty_dist, key=difficulty_dist.get) if difficulty_dist else "Trung bình"
            st.metric("🎯 Độ khó chủ đạo", most_common_diff)
        
        # Phân tích chi tiết
        st.write("### 📈 Phân tích theo loại câu hỏi")
        
        type_analysis = {}
        for q in questions:
            q_type = q['type']
            if q_type not in type_analysis:
                type_analysis[q_type] = {'count': 0, 'points': 0, 'difficulties': {}}
            
            type_analysis[q_type]['count'] += 1
            type_analysis[q_type]['points'] += q['points']
            
            diff = q.get('difficulty', 'Trung bình')
            type_analysis[q_type]['difficulties'][diff] = type_analysis[q_type]['difficulties'].get(diff, 0) + 1
        
        type_names = {
            "multiple_choice": "🔤 Trắc nghiệm",
            "true_false": "✅ Đúng/Sai",
            "short_answer": "📝 Trả lời ngắn",
            "essay": "📄 Tự luận"
        }
        
        for q_type, analysis in type_analysis.items():
            st.write(f"**{type_names[q_type]}:**")
            
            percentage = (analysis['points'] / total_points) * 100
            avg_points = analysis['points'] / analysis['count']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"• Số lượng: {analysis['count']} câu")
            with col2:
                st.write(f"• Tổng điểm: {analysis['points']:.1f} ({percentage:.1f}%)")
            with col3:
                st.write(f"• TB điểm/câu: {avg_points:.1f}")
            
            # Phân bố độ khó
            diff_text = ", ".join([f"{diff}: {count}" for diff, count in analysis['difficulties'].items()])
            st.caption(f"  Độ khó: {diff_text}")

def clear_exam_data():
    """Xóa tất cả dữ liệu đề thi trong session"""
    keys_to_clear = [
        'exam_title', 'exam_description', 'exam_instructions',
        'exam_class_id', 'exam_class_name', 'exam_time_limit',
        'exam_start_date', 'exam_start_time', 'exam_end_date', 'exam_end_time',
        'exam_questions', 'current_question', 'edit_question_index',
        'show_final_preview', 'selected_questions'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def show_cancel_exam_confirmation():
    """Hiển thị xác nhận hủy đề thi"""
    if st.button("⚠️ XÁC NHẬN HỦY ĐỀ THI", type="secondary"):
        clear_exam_data()
        st.success("✅ Đã hủy đề thi. Tất cả dữ liệu đã được xóa.")
        st.info("🔄 Trang sẽ tự động làm mới...")
        st.rerun()

# Các helper functions cho database operations - MOCK IMPLEMENTATIONS

def create_excel_template():
    """Tạo template Excel cho import học sinh"""
    data = {
        'ho_ten': ['Nguyễn Văn A', 'Trần Thị B', 'Lê Văn C'],
        'username': ['nguyenvana', 'tranthib', 'levanc'],
        'mat_khau': ['123456', '123456', '123456'],
        'email': ['nguyenvana@example.com', 'tranthib@example.com', 'levanc@example.com'],
        'so_dien_thoai': ['0123456789', '0987654321', '0369258147']
    }
    
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='DanhSachHocSinh')
        
        # Add instruction sheet
        instructions = pd.DataFrame({
            'Cột': ['ho_ten', 'username', 'mat_khau', 'email', 'so_dien_thoai'],
            'Mô tả': [
                'Họ và tên đầy đủ (bắt buộc)',
                'Tên đăng nhập - chỉ chữ, số, gạch dưới (bắt buộc)',
                'Mật khẩu - tối thiểu 6 ký tự (bắt buộc)',
                'Địa chỉ email (tùy chọn)',
                'Số điện thoại (tùy chọn)'
            ],
            'Ví dụ': [
                'Nguyễn Văn A',
                'nguyenvana',
                '123456',
                'email@example.com',
                '0123456789'
            ]
        })
        instructions.to_excel(writer, index=False, sheet_name='HuongDan')
    
    return excel_buffer.getvalue()

def validate_excel_data(df):
    """Validate dữ liệu Excel"""
    errors = []
    warnings = []
    valid_students = []
    
    required_columns = ['ho_ten', 'username', 'mat_khau']
    
    # Kiểm tra cột bắt buộc
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Thiếu cột bắt buộc: {col}")
    
    if errors:
        return errors, warnings, []
    
    # Validate từng dòng
    for idx, row in df.iterrows():
        row_errors = []
        
        # Kiểm tra họ tên
        if pd.isna(row['ho_ten']) or not str(row['ho_ten']).strip():
            row_errors.append(f"Dòng {idx+2}: Thiếu họ tên")
        
        # Kiểm tra username
        username = str(row['username']).strip() if not pd.isna(row['username']) else ''
        if not username:
            row_errors.append(f"Dòng {idx+2}: Thiếu username")
        elif not username.replace('_', '').isalnum():
            row_errors.append(f"Dòng {idx+2}: Username chỉ được chứa chữ, số và dấu gạch dưới")
        
        # Kiểm tra mật khẩu
        password = str(row['mat_khau']).strip() if not pd.isna(row['mat_khau']) else ''
        if not password:
            row_errors.append(f"Dòng {idx+2}: Thiếu mật khẩu")
        elif len(password) < 6:
            row_errors.append(f"Dòng {idx+2}: Mật khẩu phải ít nhất 6 ký tự")
        
        # Kiểm tra email (optional)
        email = str(row['email']).strip() if not pd.isna(row['email']) else ''
        if email and '@' not in email:
            warnings.append(f"Dòng {idx+2}: Email có thể không hợp lệ")
        
        if not row_errors:
            valid_students.append({
                'row_num': idx+2,
                'ho_ten': str(row['ho_ten']).strip(),
                'username': username,
                'mat_khau': password,
                'email': email if email else None,
                'so_dien_thoai': str(row['so_dien_thoai']).strip() if not pd.isna(row['so_dien_thoai']) else None
            })
        else:
            errors.extend(row_errors)
    
    return errors, warnings, valid_students

def bulk_create_students(students_data, auto_resolve=True):
    """Mock function - tạo học sinh hàng loạt"""
    result = {
        'success_count': 0,
        'failed_students': [],
        'conflict_students': [],
        'resolved_conflicts': []
    }
    
    # Mock existing usernames
    existing_usernames = ['admin', 'teacher1', 'student1']
    
    for student in students_data:
        try:
            original_username = student['username']
            final_username = original_username
            
            # Check for conflicts
            if original_username in existing_usernames:
                if auto_resolve:
                    # Auto-resolve conflict
                    counter = 1
                    while f"{original_username}{counter}" in existing_usernames:
                        counter += 1
                    final_username = f"{original_username}{counter}"
                    
                    result['resolved_conflicts'].append({
                        'ho_ten': student['ho_ten'],
                        'original_username': original_username,
                        'new_username': final_username,
                        'row_num': student['row_num']
                    })
                else:
                    result['conflict_students'].append(student)
                    continue
            
            # Mock successful creation
            existing_usernames.append(final_username)
            result['success_count'] += 1
            
        except Exception as e:
            result['failed_students'].append({
                **student,
                'error': str(e)
            })
    
    return result

def get_import_statistics():
    """Mock function - thống kê import"""
    return {
        'today': random.randint(0, 10),
        'week': random.randint(5, 50),
        'month': random.randint(20, 200)
    }

# Mock database functions - THay thế bằng implementation thực tế

def get_classes_by_teacher(teacher_id):
    """Mock function - lấy danh sách lớp của giáo viên"""
    return [
        {
            'id': 1,
            'name': 'Lớp 10A1',
            'description': 'Lớp chuyên Toán',
            'student_count': 30,
            'created_at': '2024-01-15T08:00:00'
        },
        {
            'id': 2,
            'name': 'Lớp 10B2', 
            'description': 'Lớp chuyên Lý',
            'student_count': 25,
            'created_at': '2024-01-20T08:00:00'
        }
    ]

def check_class_name_exists(name, teacher_id, exclude_id=None):
    """Mock function - kiểm tra tên lớp đã tồn tại"""
    return False  # Mock: tên chưa tồn tại

def create_class(name, description, teacher_id):
    """Mock function - tạo lớp mới"""
    return random.randint(100, 999)  # Mock: trả về ID mới

def get_class_detail_stats(class_id):
    """Mock function - thống kê chi tiết lớp"""
    return {
        'student_count': random.randint(20, 35),
        'exam_count': random.randint(0, 5),
        'submission_count': random.randint(0, 100),
        'graded_count': random.randint(0, 50)
    }

def update_class_info(class_id, name, description, teacher_id):
    """Mock function - cập nhật thông tin lớp"""
    return True

def delete_class(class_id, teacher_id):
    """Mock function - xóa lớp"""
    return True, "Đã xóa lớp thành công"

def force_delete_class(class_id, teacher_id):
    """Mock function - xóa lớp cùng tất cả dữ liệu"""
    return True, "Đã xóa lớp và tất cả dữ liệu liên quan"

def get_class_students(class_id):
    """Mock function - lấy danh sách học sinh trong lớp"""
    return [
        {
            'id': 1,
            'full_name': 'Nguyễn Văn A',
            'username': 'nguyenvana',
            'email': 'a@example.com',
            'joined_at': '2024-01-15T08:00:00'
        }
    ]

def get_students_not_in_class(class_id):
    """Mock function - lấy học sinh chưa có trong lớp"""
    return [
        {
            'id': 2,
            'full_name': 'Trần Thị B',
            'username': 'tranthib'
        }
    ]

def add_student_to_class(class_id, student_id):
    """Mock function - thêm học sinh vào lớp"""
    return True

def remove_student_from_class(class_id, student_id):
    """Mock function - xóa học sinh khỏi lớp"""
    return True

def bulk_add_students_to_class(class_id, student_ids):
    """Mock function - thêm nhiều học sinh vào lớp"""
    return len(student_ids)  # Trả về số lượng thành công

def get_exams_by_class(class_id):
    """Mock function - lấy đề thi của lớp"""
    return [
        {
            'id': 1,
            'title': 'Kiểm tra 15 phút',
            'description': 'Bài kiểm tra chương 1',
            'start_time': '2024-02-01T08:00:00',
            'end_time': '2024-02-01T09:00:00',
            'submission_count': 25
        }
    ]

def get_all_students_detailed():
    """Mock function - lấy tất cả học sinh với thông tin chi tiết"""
    return [
        {
            'id': 1,
            'full_name': 'Nguyễn Văn A',
            'username': 'nguyenvana',
            'email': 'a@example.com',
            'is_active': True,
            'classes': 'Lớp 10A1, Lớp 10B2'
        }
    ]

def search_students(search_term):
    """Mock function - tìm kiếm học sinh"""
    return [
        {
            'id': 1,
            'full_name': 'Nguyễn Văn A',
            'username': 'nguyenvana',
            'email': 'a@example.com',
            'is_active': True,
            'classes': 'Lớp 10A1'
        }
    ]

def get_student_statistics(student_id):
    """Mock function - thống kê học sinh"""
    return {
        'class_count': random.randint(1, 3),
        'exam_count': random.randint(0, 10),
        'avg_score': round(random.uniform(6.0, 9.5), 1)
    }

def toggle_user_status(user_id):
    """Mock function - bật/tắt trạng thái user"""
    return random.choice([True, False])

def update_student_info(student_id, full_name, email, phone):
    """Mock function - cập nhật thông tin học sinh"""
    return True

def get_student_classes(student_id):
    """Mock function - lấy danh sách lớp của học sinh"""
    return [
        {
            'id': 1,
            'name': 'Lớp 10A1',
            'teacher_name': 'Nguyễn Thị C'
        }
    ]