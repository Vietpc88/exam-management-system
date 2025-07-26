import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
from auth.login import get_current_user
from database.supabase_models import SupabaseDatabase

# Initialize database
db = SupabaseDatabase()

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
    active_students = len([s for s in students if s.get('is_active', True)])
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
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                status_icon = "✅" if student.get('is_active', True) else "🔒"
                st.write(f"{status_icon} **{student['ho_ten']}**")
                st.caption(f"@{student['username']} | {student.get('email', 'Chưa có email')}")
            
            with col2:
                classes = get_student_classes_names(student['id'])
                classes_text = ", ".join(classes) if classes else "Chưa vào lớp nào"
                st.caption(f"📚 {classes_text}")
                
                # Thống kê học sinh
                stats = get_student_statistics(student['id'])
                st.caption(f"📊 {stats['class_count']} lớp | {stats['exam_count']} bài thi")
            
            with col3:
                status_text = "Hoạt động" if student.get('is_active', True) else "Đã khóa"
                status_color = "success" if student.get('is_active', True) else "error"
                st.write(f":{status_color}[{status_text}]")
            
            with col4:
                action_text = "🔒 Khóa" if student.get('is_active', True) else "✅ Mở khóa"
                if st.button(action_text, key=f"btn_toggle_{student['id']}"):
                    new_status = toggle_user_status(student['id'])
                    action = "mở khóa" if new_status else "khóa"
                    st.success(f"✅ Đã {action} tài khoản {student['ho_ten']}")
                    st.rerun()
            
            with col5:
                if st.button("📝 Sửa", key=f"btn_edit_{student['id']}"):
                    st.session_state.edit_student = student
                    st.rerun()
            
            st.divider()
    
    # Popup chỉnh sửa học sinh
    if st.session_state.get("edit_student"):
        with st.expander("📝 Chỉnh sửa học sinh", expanded=True):
            show_edit_student_popup()

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
        active_count = len([s for s in all_students if s.get('is_active', True)])
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

def show_edit_student_popup():
    """Popup chỉnh sửa thông tin học sinh"""
    student = st.session_state.get("edit_student", {})
    
    if not student:
        return
    
    st.write(f"### 📝 Chỉnh sửa: {student['ho_ten']}")
    
    with st.form("edit_student_form"):
        ho_ten = st.text_input("Họ và tên", value=student['ho_ten'], key=f"input_edit_student_name_{student['id']}")
        email = st.text_input("Email", value=student.get('email', ''), key=f"input_edit_student_email_{student['id']}")
        so_dien_thoai = st.text_input("Số điện thoại", value=student.get('so_dien_thoai', ''), key=f"input_edit_student_phone_{student['id']}")
        
        st.info(f"**Username:** {student['username']} (không thể thay đổi)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("💾 Lưu thay đổi", use_container_width=True)
        
        with col2:
            cancelled = st.form_submit_button("❌ Hủy", use_container_width=True)
        
        if submitted:
            if update_student_info(student['id'], ho_ten, email, so_dien_thoai):
                st.success("✅ Cập nhật thông tin thành công!")
                st.session_state.edit_student = None
                st.rerun()
            else:
                st.error("❌ Có lỗi xảy ra!")
        
        if cancelled:
            st.session_state.edit_student = None
            st.rerun()

# Helper functions
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
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
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

# Database functions using Supabase (UUID VERSION)
def get_all_students_detailed():
    """Lấy tất cả học sinh với thông tin chi tiết"""
    try:
        result = db.client.table('users').select('*').eq('role', 'student').execute()
        return result.data
    except Exception as e:
        st.error(f"Lỗi lấy danh sách học sinh: {e}")
        return []

def search_students(search_term: str):
    """Tìm kiếm học sinh"""
    try:
        # Search in multiple fields
        result = db.client.table('users').select('*').eq('role', 'student').or_(
            f'ho_ten.ilike.%{search_term}%,username.ilike.%{search_term}%,email.ilike.%{search_term}%'
        ).execute()
        return result.data
    except Exception as e:
        st.error(f"Lỗi tìm kiếm: {e}")
        return []

def get_student_classes_names(student_id: str):
    """Lấy tên các lớp của học sinh"""
    try:
        result = db.client.table('class_students').select(
            'classes(ten_lop)'
        ).eq('student_id', student_id).execute()
        
        class_names = []
        for item in result.data:
            if item['classes']:
                class_names.append(item['classes']['ten_lop'])
        return class_names
    except Exception as e:
        return []

def get_student_statistics(student_id: str):
    """Thống kê học sinh"""
    try:
        # Đếm số lớp
        class_result = db.client.table('class_students').select('class_id').eq('student_id', student_id).execute()
        class_count = len(class_result.data)
        
        # Đếm số bài thi (sẽ implement sau)
        exam_count = 0  # TODO: Implement khi có bảng submissions
        
        return {
            'class_count': class_count,
            'exam_count': exam_count
        }
    except Exception as e:
        return {'class_count': 0, 'exam_count': 0}

def toggle_user_status(user_id: str):
    """Bật/tắt trạng thái user"""
    try:
        # Lấy trạng thái hiện tại
        user_result = db.client.table('users').select('is_active').eq('id', user_id).execute()
        if user_result.data:
            current_status = user_result.data[0].get('is_active', True)
            new_status = not current_status
            
            # Cập nhật trạng thái
            db.client.table('users').update({'is_active': new_status}).eq('id', user_id).execute()
            return new_status
        return False
    except Exception as e:
        st.error(f"Lỗi thay đổi trạng thái: {e}")
        return False

def update_student_info(student_id: str, ho_ten: str, email: str, so_dien_thoai: str):
    """Cập nhật thông tin học sinh"""
    try:
        result = db.client.table('users').update({
            'ho_ten': ho_ten,
            'email': email if email else None,
            'so_dien_thoai': so_dien_thoai if so_dien_thoai else None
        }).eq('id', student_id).execute()
        return True
    except Exception as e:
        st.error(f"Lỗi cập nhật thông tin: {e}")
        return False

def bulk_create_students(students_data: list, auto_resolve: bool = True):
    """Tạo học sinh hàng loạt"""
    result = {
        'success_count': 0,
        'failed_students': [],
        'conflict_students': [],
        'resolved_conflicts': []
    }
    
    # Lấy danh sách username đã tồn tại
    existing_users = db.client.table('users').select('username').execute()
    existing_usernames = {user['username'] for user in existing_users.data}
    
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
                    existing_usernames.add(final_username)
                    
                    result['resolved_conflicts'].append({
                        'ho_ten': student['ho_ten'],
                        'original_username': original_username,
                        'new_username': final_username,
                        'row_num': student['row_num']
                    })
                else:
                    result['conflict_students'].append(student)
                    continue
            
            # Tạo user mới
            success = db.create_user(
                username=final_username,
                password=student['mat_khau'],
                ho_ten=student['ho_ten'],
                email=student.get('email'),
                so_dien_thoai=student.get('so_dien_thoai'),
                role='student'
            )
            
            if success:
                existing_usernames.add(final_username)
                result['success_count'] += 1
            else:
                result['failed_students'].append({
                    **student,
                    'error': 'Lỗi tạo tài khoản'
                })
                
        except Exception as e:
            result['failed_students'].append({
                **student,
                'error': str(e)
            })
    
    return result

def get_import_statistics():
    """Thống kê import"""
    try:
        # TODO: Implement thống kê thực từ database
        # Hiện tại trả về mock data
        return {
            'today': 0,
            'week': 0,
            'month': 0
        }
    except Exception as e:
        return {'today': 0, 'week': 0, 'month': 0}