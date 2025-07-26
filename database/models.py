import sqlite3
import json
import bcrypt
from datetime import datetime, timedelta
from config import Config

def get_db_connection():
    """Tạo kết nối database"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Trả về dict thay vì tuple
    return conn

def verify_password(password, hashed):
    """Xác thực mật khẩu"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def hash_password(password):
    """Hash mật khẩu"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# === USER FUNCTIONS ===
def create_user(username, password, role, full_name, email=None, phone=None):
    """Tạo user mới"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, full_name, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, role, full_name, email, phone))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def authenticate_user(username, password, role):
    """Xác thực đăng nhập"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users 
        WHERE username = ? AND role = ? AND is_active = 1
    ''', (username, role))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(password, user['password_hash']):
        return dict(user)
    return None

def get_user_by_id(user_id):
    """Lấy thông tin user theo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None

def get_students():
    """Lấy danh sách tất cả học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, full_name, email, created_at
        FROM users 
        WHERE role = 'student' AND is_active = 1
        ORDER BY full_name
    ''')
    
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

# === CLASS FUNCTIONS ===
def create_class(name, description, teacher_id):
    """Tạo lớp học mới"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO classes (name, description, teacher_id)
        VALUES (?, ?, ?)
    ''', (name, description, teacher_id))
    
    class_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return class_id

def get_classes_by_teacher(teacher_id):
    """Lấy danh sách lớp của giáo viên"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, COUNT(cs.student_id) as student_count
        FROM classes c
        LEFT JOIN class_students cs ON c.id = cs.class_id
        WHERE c.teacher_id = ? AND c.is_active = 1
        GROUP BY c.id
        ORDER BY c.created_at DESC
    ''', (teacher_id,))
    
    classes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return classes

def add_student_to_class(class_id, student_id):
    """Thêm học sinh vào lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO class_students (class_id, student_id)
            VALUES (?, ?)
        ''', (class_id, student_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_class_students(class_id):
    """Lấy danh sách học sinh trong lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.username, u.full_name, u.email, cs.joined_at
        FROM users u
        JOIN class_students cs ON u.id = cs.student_id
        WHERE cs.class_id = ?
        ORDER BY u.full_name
    ''', (class_id,))
    
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

def get_student_classes(student_id):
    """Lấy danh sách lớp của học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, u.full_name as teacher_name
        FROM classes c
        JOIN class_students cs ON c.id = cs.class_id
        JOIN users u ON c.teacher_id = u.id
        WHERE cs.student_id = ? AND c.is_active = 1
        ORDER BY c.name
    ''', (student_id,))
    
    classes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return classes

# === EXAM FUNCTIONS ===
def create_exam(title, description, class_id, questions, time_limit, start_time, end_time, created_by):
    """Tạo đề thi mới"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    questions_json = json.dumps(questions, ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO exams (title, description, class_id, questions, time_limit, 
                          start_time, end_time, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, class_id, questions_json, time_limit, 
          start_time, end_time, created_by))
    
    exam_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return exam_id

def get_exams_by_class(class_id):
    """Lấy danh sách đề thi của lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.*, u.full_name as teacher_name,
               COUNT(s.id) as submission_count
        FROM exams e
        JOIN users u ON e.created_by = u.id
        LEFT JOIN submissions s ON e.id = s.exam_id
        WHERE e.class_id = ? AND e.is_active = 1
        GROUP BY e.id
        ORDER BY e.created_at DESC
    ''', (class_id,))
    
    exams = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return exams

def get_exam_by_id(exam_id):
    """Lấy thông tin đề thi theo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
    exam = cursor.fetchone()
    conn.close()
    
    if exam:
        exam_dict = dict(exam)
        exam_dict['questions'] = json.loads(exam_dict['questions'])
        return exam_dict
    return None

def get_available_exams_for_student(student_id):
    """Lấy danh sách đề thi có thể làm của học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    
    cursor.execute('''
        SELECT e.*, c.name as class_name, u.full_name as teacher_name,
               s.id as submission_id, s.submitted_at, s.total_score, s.max_score
        FROM exams e
        JOIN classes c ON e.class_id = c.id
        JOIN class_students cs ON c.id = cs.class_id
        JOIN users u ON e.created_by = u.id
        LEFT JOIN submissions s ON e.id = s.exam_id AND s.student_id = ?
        WHERE cs.student_id = ? AND e.is_active = 1
        AND (e.start_time IS NULL OR e.start_time <= ?)
        AND (e.end_time IS NULL OR e.end_time >= ?)
        ORDER BY e.created_at DESC
    ''', (student_id, student_id, now, now))
    
    exams = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return exams

# === SUBMISSION FUNCTIONS ===
def create_submission(exam_id, student_id, answers, images=None):
    """Tạo bài làm mới"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    answers_json = json.dumps(answers, ensure_ascii=False)
    images_json = json.dumps(images, ensure_ascii=False) if images else None
    
    cursor.execute('''
        INSERT INTO submissions (exam_id, student_id, answers, images)
        VALUES (?, ?, ?, ?)
    ''', (exam_id, student_id, answers_json, images_json))
    
    submission_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return submission_id

def get_submission(exam_id, student_id):
    """Lấy bài làm của học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM submissions 
        WHERE exam_id = ? AND student_id = ?
    ''', (exam_id, student_id))
    
    submission = cursor.fetchone()
    conn.close()
    
    if submission:
        submission_dict = dict(submission)
        submission_dict['answers'] = json.loads(submission_dict['answers'])
        if submission_dict['images']:
            submission_dict['images'] = json.loads(submission_dict['images'])
        return submission_dict
    return None

def update_submission_score(submission_id, total_score, max_score, feedback, graded_by):
    """Cập nhật điểm và nhận xét bài làm"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE submissions 
        SET total_score = ?, max_score = ?, feedback = ?, 
            graded_by = ?, graded_at = ?, is_graded = 1
        WHERE id = ?
    ''', (total_score, max_score, feedback, graded_by, datetime.now(), submission_id))
    
    conn.commit()
    conn.close()

def get_class_submissions(class_id, exam_id=None):
    """Lấy danh sách bài làm của lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT s.*, e.title as exam_title, u.full_name as student_name, u.username
        FROM submissions s
        JOIN exams e ON s.exam_id = e.id
        JOIN users u ON s.student_id = u.id
        WHERE e.class_id = ?
    '''
    params = [class_id]
    
    if exam_id:
        query += ' AND s.exam_id = ?'
        params.append(exam_id)
    
    query += ' ORDER BY s.submitted_at DESC'
    
    cursor.execute(query, params)
    submissions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return submissions
# === STUDENT MANAGEMENT FUNCTIONS ===

def get_all_students_detailed():
    """Lấy danh sách chi tiết tất cả học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.*, 
               GROUP_CONCAT(c.name || ' (ID: ' || c.id || ')') as classes
        FROM users u
        LEFT JOIN class_students cs ON u.id = cs.student_id
        LEFT JOIN classes c ON cs.class_id = c.id AND c.is_active = 1
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY u.full_name
    ''')
    
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

def toggle_user_status(user_id):
    """Kích hoạt/khóa tài khoản học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Lấy trạng thái hiện tại
    cursor.execute('SELECT is_active FROM users WHERE id = ?', (user_id,))
    current_status = cursor.fetchone()
    
    if current_status:
        new_status = 0 if current_status[0] else 1
        cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        conn.close()
        return new_status
    
    conn.close()
    return None

def remove_student_from_class(class_id, student_id):
    """Xóa học sinh khỏi lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM class_students 
        WHERE class_id = ? AND student_id = ?
    ''', (class_id, student_id))
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0

def transfer_student_to_class(student_id, old_class_id, new_class_id):
    """Chuyển học sinh sang lớp khác"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Xóa khỏi lớp cũ
        if old_class_id:
            cursor.execute('''
                DELETE FROM class_students 
                WHERE class_id = ? AND student_id = ?
            ''', (old_class_id, student_id))
        
        # Thêm vào lớp mới
        cursor.execute('''
            INSERT INTO class_students (class_id, student_id)
            VALUES (?, ?)
        ''', (new_class_id, student_id))
        
        conn.commit()
        conn.close()
        return True
    
    except sqlite3.IntegrityError:
        conn.close()
        return False

def update_student_info(student_id, full_name, email, phone):
    """Cập nhật thông tin học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET full_name = ?, email = ?, phone = ?
        WHERE id = ? AND role = 'student'
    ''', (full_name, email, phone, student_id))
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0

def get_student_statistics(student_id):
    """Lấy thống kê của học sinh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Số lớp tham gia
    cursor.execute('''
        SELECT COUNT(*) FROM class_students cs
        JOIN classes c ON cs.class_id = c.id
        WHERE cs.student_id = ? AND c.is_active = 1
    ''', (student_id,))
    class_count = cursor.fetchone()[0]
    
    # Số bài thi đã làm
    cursor.execute('''
        SELECT COUNT(*) FROM submissions WHERE student_id = ?
    ''', (student_id,))
    exam_count = cursor.fetchone()[0]
    
    # Điểm trung bình
    cursor.execute('''
        SELECT AVG(total_score * 100.0 / max_score) 
        FROM submissions 
        WHERE student_id = ? AND is_graded = 1 AND max_score > 0
    ''', (student_id,))
    avg_score = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'class_count': class_count,
        'exam_count': exam_count,
        'avg_score': round(avg_score, 1)
    }

def search_students(search_term):
    """Tìm kiếm học sinh theo tên hoặc username"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.*, 
               GROUP_CONCAT(c.name) as classes
        FROM users u
        LEFT JOIN class_students cs ON u.id = cs.student_id
        LEFT JOIN classes c ON cs.class_id = c.id AND c.is_active = 1
        WHERE u.role = 'student' 
        AND (u.full_name LIKE ? OR u.username LIKE ? OR u.email LIKE ?)
        GROUP BY u.id
        ORDER BY u.full_name
    ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

def get_students_not_in_class(class_id):
    """Lấy danh sách học sinh chưa có trong lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users u
        WHERE u.role = 'student' AND u.is_active = 1
        AND u.id NOT IN (
            SELECT student_id FROM class_students WHERE class_id = ?
        )
        ORDER BY u.full_name
    ''', (class_id,))
    
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

def bulk_add_students_to_class(class_id, student_ids):
    """Thêm nhiều học sinh vào lớp cùng lúc"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    for student_id in student_ids:
        try:
            cursor.execute('''
                INSERT INTO class_students (class_id, student_id)
                VALUES (?, ?)
            ''', (class_id, student_id))
            success_count += 1
        except sqlite3.IntegrityError:
            # Học sinh đã có trong lớp
            continue
    
    conn.commit()
    conn.close()
    return success_count
# === ADDITIONAL CLASS MANAGEMENT FUNCTIONS ===

def check_class_name_exists(class_name, teacher_id, exclude_id=None):
    """Kiểm tra tên lớp có trùng không"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT COUNT(*) FROM classes 
        WHERE name = ? AND teacher_id = ? AND is_active = 1
    '''
    params = [class_name, teacher_id]
    
    if exclude_id:
        query += ' AND id != ?'
        params.append(exclude_id)
    
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

def update_class_info(class_id, name, description, teacher_id):
    """Cập nhật thông tin lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE classes 
        SET name = ?, description = ?
        WHERE id = ? AND teacher_id = ?
    ''', (name, description, class_id, teacher_id))
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0

def delete_class(class_id, teacher_id):
    """Xóa lớp (soft delete)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra có đề thi nào không
        cursor.execute('SELECT COUNT(*) FROM exams WHERE class_id = ? AND is_active = 1', (class_id,))
        exam_count = cursor.fetchone()[0]
        
        if exam_count > 0:
            conn.close()
            return False, "Không thể xóa lớp có đề thi!"
        
        # Xóa học sinh khỏi lớp
        cursor.execute('DELETE FROM class_students WHERE class_id = ?', (class_id,))
        
        # Soft delete lớp
        cursor.execute('''
            UPDATE classes 
            SET is_active = 0 
            WHERE id = ? AND teacher_id = ?
        ''', (class_id, teacher_id))
        
        conn.commit()
        conn.close()
        return True, "Xóa lớp thành công!"
    
    except Exception as e:
        conn.close()
        return False, f"Lỗi: {str(e)}"

def force_delete_class(class_id, teacher_id):
    """Xóa lớp hoàn toàn (bao gồm cả đề thi)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Xóa submissions trước
        cursor.execute('''
            DELETE FROM submissions 
            WHERE exam_id IN (SELECT id FROM exams WHERE class_id = ?)
        ''', (class_id,))
        
        # Xóa question_scores
        cursor.execute('''
            DELETE FROM question_scores 
            WHERE submission_id IN (
                SELECT s.id FROM submissions s
                JOIN exams e ON s.exam_id = e.id
                WHERE e.class_id = ?
            )
        ''', (class_id,))
        
        # Xóa exams
        cursor.execute('DELETE FROM exams WHERE class_id = ?', (class_id,))
        
        # Xóa class_students
        cursor.execute('DELETE FROM class_students WHERE class_id = ?', (class_id,))
        
        # Xóa class
        cursor.execute('DELETE FROM classes WHERE id = ? AND teacher_id = ?', (class_id, teacher_id))
        
        conn.commit()
        conn.close()
        return True, "Xóa lớp hoàn toàn thành công!"
    
    except Exception as e:
        conn.close()
        return False, f"Lỗi: {str(e)}"

def get_class_detail_stats(class_id):
    """Lấy thống kê chi tiết của lớp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Số học sinh
    cursor.execute('SELECT COUNT(*) FROM class_students WHERE class_id = ?', (class_id,))
    student_count = cursor.fetchone()[0]
    
    # Số đề thi
    cursor.execute('SELECT COUNT(*) FROM exams WHERE class_id = ? AND is_active = 1', (class_id,))
    exam_count = cursor.fetchone()[0]
    
    # Số bài làm
    cursor.execute('''
        SELECT COUNT(*) FROM submissions s
        JOIN exams e ON s.exam_id = e.id
        WHERE e.class_id = ?
    ''', (class_id,))
    submission_count = cursor.fetchone()[0]
    
    # Số bài đã chấm
    cursor.execute('''
        SELECT COUNT(*) FROM submissions s
        JOIN exams e ON s.exam_id = e.id
        WHERE e.class_id = ? AND s.is_graded = 1
    ''', (class_id,))
    graded_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'student_count': student_count,
        'exam_count': exam_count,
        'submission_count': submission_count,
        'graded_count': graded_count
    }
# === BULK IMPORT FUNCTIONS ===
import pandas as pd
import re

def validate_excel_data(df):
    """Validate dữ liệu Excel"""
    errors = []
    warnings = []
    
    # Kiểm tra các cột bắt buộc
    required_columns = ['ho_ten', 'username', 'mat_khau']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f"Thiếu cột bắt buộc: {', '.join(missing_columns)}")
        return errors, warnings, []
    
    # Chuẩn hóa dữ liệu
    df = df.fillna('')  # Thay NaN bằng chuỗi rỗng
    
    valid_students = []
    
    for index, row in df.iterrows():
        row_num = index + 2  # +2 vì Excel bắt đầu từ 1 và có header
        student_errors = []
        
        # Validate họ tên
        ho_ten = str(row['ho_ten']).strip()
        if not ho_ten or ho_ten == 'nan':
            student_errors.append(f"Dòng {row_num}: Thiếu họ tên")
        
        # Validate username
        username = str(row['username']).strip()
        if not username or username == 'nan':
            student_errors.append(f"Dòng {row_num}: Thiếu username")
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            student_errors.append(f"Dòng {row_num}: Username chỉ được chứa chữ, số và dấu gạch dưới")
        elif len(username) < 3:
            student_errors.append(f"Dòng {row_num}: Username phải có ít nhất 3 ký tự")
        
        # Validate mật khẩu
        mat_khau = str(row['mat_khau']).strip()
        if not mat_khau or mat_khau == 'nan':
            student_errors.append(f"Dòng {row_num}: Thiếu mật khẩu")
        elif len(mat_khau) < 6:
            student_errors.append(f"Dòng {row_num}: Mật khẩu phải có ít nhất 6 ký tự")
        
        # Validate email (optional)
        email = str(row.get('email', '')).strip()
        if email and email != 'nan':
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                student_errors.append(f"Dòng {row_num}: Email không hợp lệ")
        
        # Validate số điện thoại (optional)
        sdt = str(row.get('so_dien_thoai', '')).strip()
        if sdt and sdt != 'nan':
            if not re.match(r'^[0-9+\-\s\(\)]{10,15}$', sdt):
                warnings.append(f"Dòng {row_num}: Số điện thoại có thể không hợp lệ")
        
        if student_errors:
            errors.extend(student_errors)
        else:
            valid_students.append({
                'ho_ten': ho_ten,
                'username': username,
                'mat_khau': mat_khau,
                'email': email if email and email != 'nan' else None,
                'so_dien_thoai': sdt if sdt and sdt != 'nan' else None,
                'row_num': row_num
            })
    
    return errors, warnings, valid_students

def check_existing_usernames(usernames):
    """Kiểm tra username đã tồn tại"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join('?' * len(usernames))
    cursor.execute(f'''
        SELECT username FROM users 
        WHERE username IN ({placeholders})
    ''', usernames)
    
    existing = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return existing

def bulk_create_students(students_data, auto_resolve_conflicts=False):
    """Tạo học sinh hàng loạt"""
    success_count = 0
    failed_students = []
    conflict_students = []
    
    # Kiểm tra username trùng
    usernames = [s['username'] for s in students_data]
    existing_usernames = check_existing_usernames(usernames)
    
    for student in students_data:
        try:
            username = student['username']
            
            # Nếu username đã tồn tại
            if username in existing_usernames:
                if auto_resolve_conflicts:
                    # Tự động thêm số vào username
                    original_username = username
                    counter = 1
                    while username in existing_usernames:
                        username = f"{original_username}{counter}"
                        counter += 1
                    
                    student['username'] = username
                    student['original_username'] = original_username
                else:
                    conflict_students.append(student)
                    continue
            
            # Tạo user
            user_id = create_user(
                username=username,
                password=student['mat_khau'],
                role='student',
                full_name=student['ho_ten'],
                email=student['email'],
                phone=student['so_dien_thoai']
            )
            
            if user_id:
                success_count += 1
                if 'original_username' in student:
                    student['new_username'] = username
            else:
                failed_students.append({
                    **student,
                    'error': 'Không thể tạo tài khoản'
                })
        
        except Exception as e:
            failed_students.append({
                **student,
                'error': str(e)
            })
    
    return {
        'success_count': success_count,
        'failed_students': failed_students,
        'conflict_students': conflict_students,
        'resolved_conflicts': [s for s in students_data if 'new_username' in s]
    }

def create_excel_template():
    """Tạo file Excel template"""
    import io
    from datetime import datetime
    
    # Dữ liệu mẫu
    sample_data = [
        {
            'ho_ten': 'Nguyễn Văn A',
            'username': 'nguyenvana',
            'mat_khau': '123456',
            'email': 'nguyenvana@email.com',
            'so_dien_thoai': '0123456789'
        },
        {
            'ho_ten': 'Trần Thị B',
            'username': 'tranthib',
            'mat_khau': 'password123',
            'email': 'tranthib@email.com',
            'so_dien_thoai': '0987654321'
        },
        {
            'ho_ten': 'Lê Văn C',
            'username': 'levanc',
            'mat_khau': 'abc123',
            'email': '',  # Email có thể để trống
            'so_dien_thoai': ''  # SĐT có thể để trống
        }
    ]
    
    # Tạo DataFrame
    df = pd.DataFrame(sample_data)
    
    # Tạo file Excel trong memory
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet dữ liệu
        df.to_excel(writer, sheet_name='Danh_sach_hoc_sinh', index=False)
        
        # Sheet hướng dẫn
        instructions = pd.DataFrame([
            ['HƯỚNG DẪN SỬ DỤNG'],
            [''],
            ['1. Các cột bắt buộc:'],
            ['   - ho_ten: Họ và tên học sinh'],
            ['   - username: Tên đăng nhập (chỉ chứa chữ, số, dấu gạch dưới)'],
            ['   - mat_khau: Mật khẩu (ít nhất 6 ký tự)'],
            [''],
            ['2. Các cột tùy chọn:'],
            ['   - email: Địa chỉ email (có thể để trống)'],
            ['   - so_dien_thoai: Số điện thoại (có thể để trống)'],
            [''],
            ['3. Lưu ý:'],
            ['   - Username phải duy nhất'],
            ['   - Không được để trống các cột bắt buộc'],
            ['   - Hệ thống sẽ tự động kiểm tra và báo lỗi'],
            [''],
            ['4. Sau khi điền đầy đủ thông tin:'],
            ['   - Lưu file Excel'],
            ['   - Upload vào hệ thống'],
            ['   - Kiểm tra kết quả import']
        ])
        
        instructions.to_excel(writer, sheet_name='Huong_dan', index=False, header=False)
        
        # Format worksheet
        workbook = writer.book
        worksheet = writer.sheets['Danh_sach_hoc_sinh']
        
        # Định dạng header
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Định dạng cells
        cell_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1
        })
        
        # Áp dụng format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 20)
        
        # Format dữ liệu
        for row_num in range(1, len(df) + 1):
            for col_num in range(len(df.columns)):
                worksheet.write(row_num, col_num, df.iloc[row_num-1, col_num], cell_format)
    
    output.seek(0)
    return output.getvalue()

def get_import_statistics():
    """Lấy thống kê import"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Số học sinh tạo hôm nay
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE role = 'student' 
        AND DATE(created_at) = DATE('now')
    ''')
    today_count = cursor.fetchone()[0]
    
    # Số học sinh tạo tuần này
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE role = 'student' 
        AND DATE(created_at) >= DATE('now', '-7 days')
    ''')
    week_count = cursor.fetchone()[0]
    
    # Số học sinh tạo tháng này
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE role = 'student' 
        AND DATE(created_at) >= DATE('now', 'start of month')
    ''')
    month_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'today': today_count,
        'week': week_count,
        'month': month_count
    }
# === SOLUTION STORAGE FUNCTIONS ===

def update_database_for_solutions():
    """Cập nhật database để hỗ trợ lưu lời giải"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Kiểm tra xem có cột solution trong bảng exams chưa
        cursor.execute("PRAGMA table_info(exams)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'solution_data' not in columns:
            # Thêm cột để lưu lời giải
            cursor.execute('''
                ALTER TABLE exams 
                ADD COLUMN solution_data TEXT
            ''')
            print("✅ Đã thêm cột solution_data vào bảng exams")
        
        conn.commit()
        
    except Exception as e:
        print(f"⚠️ Cập nhật database: {str(e)}")
    finally:
        conn.close()

def save_exam_with_solutions(title, description, class_id, questions, time_limit, start_time, end_time, created_by):
    """Lưu đề thi với lời giải"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tách questions và solutions
    questions_data = []
    solutions_data = {}
    
    for i, q in enumerate(questions):
        # Lưu solution riêng
        if q.get('solution'):
            solutions_data[str(i)] = {
                'solution': q['solution'],
                'explanation': q.get('explanation', ''),
                'grading_rubric': q.get('grading_rubric', '')
            }
        
        # Question data không có solution
        q_copy = q.copy()
        q_copy.pop('solution', None)
        questions_data.append(q_copy)
    
    questions_json = json.dumps(questions_data, ensure_ascii=False)
    solutions_json = json.dumps(solutions_data, ensure_ascii=False) if solutions_data else None
    
    cursor.execute('''
        INSERT INTO exams (title, description, class_id, questions, solution_data,
                          time_limit, start_time, end_time, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, class_id, questions_json, solutions_json,
          time_limit, start_time, end_time, created_by))
    
    exam_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return exam_id

def get_exam_solutions(exam_id):
    """Lấy lời giải của đề thi"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT solution_data FROM exams WHERE id = ?', (exam_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return json.loads(result[0])
    return {}

def get_exam_with_solutions(exam_id):
    """Lấy đề thi kèm lời giải"""
    exam = get_exam_by_id(exam_id)
    if not exam:
        return None
    
    solutions = get_exam_solutions(exam_id)
    
    # Gắn solution vào từng câu hỏi
    for i, question in enumerate(exam['questions']):
        solution_key = str(i)
        if solution_key in solutions:
            question.update(solutions[solution_key])
    
    return exam