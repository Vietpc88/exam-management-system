import streamlit as st
from database.supabase_models import get_database
from datetime import datetime
import pytz
import os

LOCAL_TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"))

def show_exam_management():
    """Giao diện quản lý toàn bộ đề thi cho Admin."""
    st.header("📚 Quản lý Đề thi")
    st.write("Xem, sửa, nhân bản hoặc xóa các đề thi đã có trong hệ thống.")

    db = get_database()

    try:
        # Lấy tất cả các đề thi mà không phân biệt người tạo (vì là Admin)
        all_exams = db.get_all_exams()
    except Exception as e:
        st.error(f"❌ Lỗi tải danh sách đề thi: {e}")
        return

    if not all_exams:
        st.info("ℹ️ Chưa có đề thi nào trong hệ thống.")
        if st.button("➕ Tạo đề thi ngay"):
            st.session_state.current_page = "create_exam" # Giả sử bạn dùng key này để chuyển trang
            st.rerun()
        return

    # Sắp xếp đề thi, mới nhất lên đầu
    all_exams.sort(key=lambda x: x['created_at'], reverse=True)

    # Hiển thị danh sách đề thi
    for exam in all_exams:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 2])

            with col1:
                st.subheader(exam['title'])
                st.caption(f"ID: `{exam['id']}`")
                st.write(f"**Lớp:** {exam.get('class_name', 'N/A')}")
                
                # Hiển thị trạng thái
                status_text = "Bản nháp"
                status_color = "orange"
                if exam.get('is_published'):
                    status_text = "Đã phát hành"
                    status_color = "green"
                st.markdown(f"**Trạng thái:** <span style='color:{status_color};'>● {status_text}</span>", unsafe_allow_html=True)


            with col2:
                st.write(f"**Số câu:** {exam.get('total_questions', 'N/A')}")
                st.write(f"**Tổng điểm:** {exam.get('total_points', 'N/A')}")
                created_at_local = datetime.fromisoformat(exam['created_at']).astimezone(LOCAL_TIMEZONE)
                st.write(f"**Ngày tạo:** {created_at_local.strftime('%d/%m/%Y %H:%M')}")

            with col3:
                # Nút Sửa
                if st.button("✏️ Sửa", key=f"edit_{exam['id']}", use_container_width=True):
                    # Đặt session state để báo cho trang "create_exam" biết cần tải dữ liệu để sửa
                    st.session_state.edit_exam_id = exam['id']
                    st.session_state.current_page = "create_exam"
                    st.rerun()

                # Nút Nhân bản
                if st.button("🔄 Nhân bản", key=f"clone_{exam['id']}", use_container_width=True):
                    # Đặt session state để báo cho trang "create_exam" biết cần tải dữ liệu để nhân bản
                    st.session_state.clone_exam_id = exam['id']
                    st.session_state.current_page = "create_exam"
                    st.rerun()

                # Nút Xóa
                if st.button("🗑️ Xóa", key=f"delete_{exam['id']}", use_container_width=True, type="secondary"):
                    st.session_state.delete_exam_id_confirm = exam['id']
                    st.rerun()

            # Hộp thoại xác nhận xóa
            if st.session_state.get('delete_exam_id_confirm') == exam['id']:
                 with st.expander("Bạn có chắc chắn muốn xóa đề thi này không?", expanded=True):
                    st.warning(f"⚠️ Hành động này sẽ xóa vĩnh viễn đề thi **'{exam['title']}'** và tất cả bài làm liên quan. Không thể hoàn tác.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("❌ Hủy", key=f"cancel_delete_{exam['id']}", use_container_width=True):
                            del st.session_state.delete_exam_id_confirm
                            st.rerun()
                    with c2:
                        if st.button("🗑️ Vẫn xóa", key=f"confirm_delete_{exam['id']}", type="primary", use_container_width=True):
                            if db.delete_exam(exam['id']):
                                st.success(f"Đã xóa thành công đề thi '{exam['title']}'.")
                                del st.session_state.delete_exam_id_confirm
                                st.rerun()
                            else:
                                st.error("Có lỗi xảy ra khi xóa.")