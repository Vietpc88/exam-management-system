import streamlit as st
import pandas as pd
import io
from datetime import datetime
from auth.login import get_current_user
from database.supabase_models import get_database

# --- HÀM HỖ TRỢ ---

def create_excel_template():
    """Tạo một file Excel mẫu trong bộ nhớ để người dùng tải về."""
    sample_data = {
        'ho_ten': ['Nguyễn Văn A', 'Trần Thị B'],
        'username': ['hocsinh_a', 'hocsinh_b'],
        'email': ['a@example.com', 'b@example.com'],
        'password': ['matkhau123', 'matkhau456'],
        'so_dien_thoai': ['0901234567', '0987654321']
    }
    df_sample = pd.DataFrame(sample_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_sample.to_excel(writer, index=False, sheet_name='DanhSachHocSinh')
        # Tự động điều chỉnh độ rộng cột
        for column in df_sample:
            column_length = max(df_sample[column].astype(str).map(len).max(), len(column))
            col_idx = df_sample.columns.get_loc(column)
            writer.sheets['DanhSachHocSinh'].set_column(col_idx, col_idx, column_length + 2)
            
    processed_data = output.getvalue()
    return processed_data

# --- HÀM GIAO DIỆN CHÍNH ---

def show_manage_students():
    """Trang chính Quản lý Học sinh cho Giáo viên."""
    st.header("👥 Quản lý Học sinh")
    
    user = get_current_user()
    db = get_database()

    # --- Thanh hành động ---
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        if st.button("➕ Thêm thủ công", use_container_width=True):
            st.session_state.show_create_student_form = True
    with col2:
        if st.button("📥 Import từ Excel", use_container_width=True):
            st.session_state.show_import_students_form = True

    # --- Hiển thị các Popups (dạng expander) ---
    if st.session_state.get("show_create_student_form"):
        show_manual_create_popup(user, db)
    
    if st.session_state.get("show_import_students_form"):
        show_import_students_popup(user, db)
    if st.session_state.get("editing_student"):
        show_edit_student_popup(user, db)
    st.markdown("---")

    # --- Danh sách học sinh (Cải tiến với nút Sửa) ---
    st.subheader("📋 Danh sách học sinh toàn trường")
    all_students = db.get_all_students()

    if not all_students:
        st.info("Hiện chưa có học sinh nào trong hệ thống.")
        return

    for student in all_students:
        with st.container():
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{student.get('ho_ten', '')}** (@{student.get('username', '')})")
                st.caption(f"📧 {student.get('email', '')} | 📱 {student.get('so_dien_thoai', 'Chưa có SĐT')}")
            with cols[1]:
                if st.button("✏️ Sửa", key=f"edit_student_{student['id']}", use_container_width=True):
                    st.session_state.editing_student = student
                    st.rerun()
            st.divider()

    df = pd.DataFrame(all_students, columns=['ho_ten', 'username', 'email', 'so_dien_thoai', 'created_at'])
    df.rename(columns={
        'ho_ten': 'Họ và Tên',
        'username': 'Tên đăng nhập',
        'email': 'Email',
        'so_dien_thoai': 'Số điện thoại',
        'created_at': 'Ngày tham gia'
    }, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


# --- CÁC HÀM POPUP ---
def show_edit_student_popup(user, db):
    """Popup để giáo viên sửa thông tin của một học sinh."""
    student_info = st.session_state.editing_student
    with st.expander(f"✏️ Sửa thông tin: **{student_info.get('ho_ten', '')}**", expanded=True):
        with st.form("edit_student_form"):
            ho_ten = st.text_input("Họ và tên *", value=student_info.get('ho_ten', ''))
            # Username thường không nên cho sửa, nhưng nếu muốn thì thêm vào đây
            email = st.text_input("Email *", value=student_info.get('email', ''))
            so_dien_thoai = st.text_input("Số điện thoại", value=student_info.get('so_dien_thoai', ''))

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Lưu thay đổi", type="primary"):
                    # Giáo viên dùng hàm admin_update_user để có quyền sửa
                    if db.admin_update_user(
                        student_info['id'], 
                        ho_ten=ho_ten, 
                        email=email, 
                        so_dien_thoai=so_dien_thoai
                    ):
                        del st.session_state.editing_student
                        st.rerun()
            with col2:
                if st.form_submit_button("❌ Hủy"):
                    del st.session_state.editing_student
                    st.rerun()
def show_manual_create_popup(user, db):
    """Popup để giáo viên tạo một tài khoản học sinh thủ công."""
    with st.expander("➕ Thêm học sinh mới (Thủ công)", expanded=True):
        with st.form("manual_create_student_form"):
            st.subheader("📝 Thông tin học sinh")
            
            col1, col2 = st.columns(2)
            with col1:
                ho_ten = st.text_input("Họ và tên *")
                username = st.text_input("Tên đăng nhập *")
                so_dien_thoai = st.text_input("Số điện thoại (Tùy chọn)")
            with col2:
                email = st.text_input("Email *")
                password = st.text_input("Mật khẩu *", type="password")
                confirm_password = st.text_input("Xác nhận mật khẩu *", type="password")

            submitted = st.form_submit_button("✅ Tạo tài khoản học sinh")
            
            if submitted:
                if not all([ho_ten.strip(), username.strip(), email.strip(), password, confirm_password]):
                    st.error("❌ Vui lòng điền đầy đủ các trường bắt buộc.")
                elif password != confirm_password:
                    st.error("❌ Mật khẩu xác nhận không khớp.")
                else:
                    user_id = db.create_user(
                        username=username, password=password, ho_ten=ho_ten,
                        email=email, role='student',
                        so_dien_thoai=so_dien_thoai if so_dien_thoai.strip() else None
                    )
                    if user_id:
                        st.success(f"✅ Tạo tài khoản cho '{ho_ten}' thành công!")
                        del st.session_state.show_create_student_form
                        st.rerun()
                    else:
                        st.error("Tạo tài khoản thất bại. Email hoặc Tên đăng nhập có thể đã tồn tại.")
        
        if st.button("❌ Hủy bỏ"):
            del st.session_state.show_create_student_form
            st.rerun()


def show_import_students_popup(user, db):
    """Popup để import học sinh hàng loạt từ file Excel."""
    with st.expander("📥 Import học sinh từ Excel", expanded=True):
        
        excel_template_data = create_excel_template()
        st.download_button(
            label="📄 Tải file Excel mẫu",
            data=excel_template_data,
            file_name="Mau_Import_Hoc_Sinh.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.info(
            "Tải lên file Excel (.xlsx) có các cột: **ho_ten, username, email, password, so_dien_thoai** (tùy chọn)."
        )
        
        uploaded_file = st.file_uploader("Chọn file Excel của bạn", type=["xlsx"])

        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                df.columns = df.columns.str.strip().str.lower()
                st.write("Dữ liệu 5 dòng đầu:")
                st.dataframe(df.head())

                if st.button("🚀 Bắt đầu Import", type="primary"):
                    required_columns = {'ho_ten', 'username', 'email', 'password'}
                    if not required_columns.issubset(df.columns):
                        st.error(f"❌ File Excel thiếu các cột bắt buộc. Các cột yêu cầu (viết thường): {', '.join(required_columns)}")
                        st.write("Các cột tìm thấy trong file của bạn:", ", ".join(df.columns))
                        return

                    usernames_to_check = df['username'].dropna().tolist()
                    emails_to_check = df['email'].dropna().tolist()
                    
                    with st.spinner("🔍 Đang kiểm tra dữ liệu..."):
                        existing_users = db.check_users_exist(usernames=usernames_to_check, emails=emails_to_check)
                    
                    valid_rows = []
                    skipped_rows = []

                    for index, row in df.iterrows():
                        if row['username'] in existing_users['usernames'] or row['email'] in existing_users['emails']:
                            skipped_rows.append(f"Dòng {index+2}: {row['ho_ten']} ({row['username']}/{row['email']}) - Đã tồn tại.")
                        else:
                            valid_rows.append(row)
                    
                    if skipped_rows:
                        st.warning("⚠️ Một số học sinh đã bị bỏ qua vì đã tồn tại trong hệ thống:")
                        with st.expander("Xem danh sách bị bỏ qua"):
                            for item in skipped_rows:
                                st.write(item)
                    
                    if not valid_rows:
                        st.error("Không có học sinh mới nào hợp lệ để thêm.")
                        return

                    st.info(f"Chuẩn bị tạo {len(valid_rows)} tài khoản học sinh mới...")
                    progress_bar = st.progress(0)
                    success_count = 0
                    failed_accounts = []

                    for i, row in enumerate(valid_rows):
                        try:
                            user_id = db.create_user(
                                username=row['username'],
                                password=str(row['password']),
                                ho_ten=row['ho_ten'],
                                email=row['email'],
                                role='student',
                                so_dien_thoai=str(row['so_dien_thoai']) if 'so_dien_thoai' in row and pd.notna(row['so_dien_thoai']) else None
                            )
                            if user_id:
                                success_count += 1
                            else:
                                failed_accounts.append(f"{row['ho_ten']} - Lỗi không xác định.")
                        except Exception as e:
                            failed_accounts.append(f"{row['ho_ten']} - Lỗi: {e}")
                        
                        progress_bar.progress((i + 1) / len(valid_rows))

                    st.success(f"✅ Hoàn thành! Đã tạo thành công {success_count}/{len(valid_rows)} tài khoản.")
                    if failed_accounts:
                        st.error("Một số tài khoản không thể tạo được:")
                        with st.expander("Xem danh sách lỗi"):
                            for item in failed_accounts:
                                st.write(item)
                    
                    st.button("Hoàn tất")

            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi khi đọc file Excel: {e}")

        if st.button("❌ Đóng"):
            del st.session_state.show_import_students_form
            st.rerun()