from typing import List, Dict, Any, Optional, Union
from config.supabase_config import get_supabase_client, get_supabase_admin_client
import bcrypt
import json
from datetime import datetime

class SupabaseDatabase:
    """
    Enhanced Supabase Database class for exam management system (UUID VERSION)
    
    Database Schema:
    - users: User accounts (students, teachers, admins) - UUID primary keys
    - classes: Class/course information - UUID primary keys  
    - class_students: Many-to-many relationship between classes and students
    - exams: Exam/test information
    - submissions: Student exam submissions
    - import_logs: Track student import activities
    """
    
    def __init__(self):
        self.client = get_supabase_client()
        self.admin_client = get_supabase_admin_client()
    
    def hash_password(self, password: str) -> str:
        """Hash password sử dụng bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    # ==================== USER MANAGEMENT ====================
    
    def create_user(self, username: str, password: str, ho_ten: str, 
                   email: str = None, so_dien_thoai: str = None, role: str = 'student') -> bool:
        """Tạo user mới"""
        try:
            password_hash = self.hash_password(password)
            result = self.client.table('users').insert({
                'username': username,
                'password_hash': password_hash,
                'ho_ten': ho_ten,
                'email': email,
                'so_dien_thoai': so_dien_thoai,
                'role': role,
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Xác thực user"""
        try:
            result = self.client.table('users').select('*').eq('username', username).execute()
            if result.data:
                user = result.data[0]
                if user.get('is_active', True) and self.verify_password(password, user['password_hash']):
                    # Remove password_hash from returned data
                    user.pop('password_hash', None)
                    return user
            return None
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Lấy thông tin user theo ID (UUID string)"""
        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            if result.data:
                user = result.data[0]
                user.pop('password_hash', None)
                return user
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user_info(self, user_id: str, **kwargs) -> bool:
        """Cập nhật thông tin user"""
        try:
            # Remove None values and password_hash
            update_data = {k: v for k, v in kwargs.items() if v is not None and k != 'password_hash'}
            update_data['updated_at'] = datetime.now().isoformat()
            
            result = self.client.table('users').update(update_data).eq('id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def toggle_user_status(self, user_id: str) -> bool:
        """Bật/tắt trạng thái user"""
        try:
            # Get current status
            user_result = self.client.table('users').select('is_active').eq('id', user_id).execute()
            if user_result.data:
                current_status = user_result.data[0].get('is_active', True)
                new_status = not current_status
                
                # Update status
                self.client.table('users').update({
                    'is_active': new_status,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', user_id).execute()
                
                return new_status
            return False
        except Exception as e:
            print(f"Error toggling user status: {e}")
            return False
    
    def search_users(self, search_term: str, role: str = None) -> List[Dict]:
        """Tìm kiếm users"""
        try:
            query = self.client.table('users').select('*')
            
            if role:
                query = query.eq('role', role)
            
            # Search in multiple fields
            result = query.or_(
                f'ho_ten.ilike.%{search_term}%,username.ilike.%{search_term}%,email.ilike.%{search_term}%'
            ).execute()
            
            # Remove password_hash from results
            for user in result.data:
                user.pop('password_hash', None)
            
            return result.data
        except Exception as e:
            print(f"Error searching users: {e}")
            return []
    
    def get_all_users_by_role(self, role: str) -> List[Dict]:
        """Lấy tất cả users theo role"""
        try:
            result = self.client.table('users').select('*').eq('role', role).execute()
            
            # Remove password_hash from results
            for user in result.data:
                user.pop('password_hash', None)
            
            return result.data
        except Exception as e:
            print(f"Error getting users by role: {e}")
            return []
    
    # ==================== CLASS MANAGEMENT ====================
    
    def create_class(self, ma_lop: str, ten_lop: str, mo_ta: str, teacher_id: str) -> bool:
        """Tạo lớp học mới"""
        try:
            result = self.client.table('classes').insert({
                'ma_lop': ma_lop,
                'ten_lop': ten_lop,
                'mo_ta': mo_ta,
                'teacher_id': teacher_id,
                'created_at': datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error creating class: {e}")
            return False
    
    def get_classes_by_teacher(self, teacher_id: str) -> List[Dict]:
        """Lấy danh sách lớp của giáo viên"""
        try:
            result = self.client.table('classes').select('*').eq('teacher_id', teacher_id).order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Error getting classes: {e}")
            return []
    
    def update_class_info(self, class_id: str, ma_lop: str, ten_lop: str, mo_ta: str) -> bool:
        """Cập nhật thông tin lớp"""
        try:
            result = self.client.table('classes').update({
                'ma_lop': ma_lop,
                'ten_lop': ten_lop,
                'mo_ta': mo_ta,
                'updated_at': datetime.now().isoformat()
            }).eq('id', class_id).execute()
            return True
        except Exception as e:
            print(f"Error updating class: {e}")
            return False
    
    def delete_class(self, class_id: str) -> bool:
        """Xóa lớp học"""
        try:
            # First delete all class_students relationships
            self.client.table('class_students').delete().eq('class_id', class_id).execute()
            
            # Then delete the class
            result = self.client.table('classes').delete().eq('id', class_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting class: {e}")
            return False
    
    def check_class_code_exists(self, ma_lop: str, teacher_id: str, exclude_class_id: str = None) -> bool:
        """Kiểm tra mã lớp đã tồn tại"""
        try:
            query = self.client.table('classes').select('id').eq('ma_lop', ma_lop).eq('teacher_id', teacher_id)
            
            if exclude_class_id:
                query = query.neq('id', exclude_class_id)
            
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error checking class code: {e}")
            return False
    
    # ==================== CLASS-STUDENT RELATIONSHIPS ====================
    
    def add_student_to_class(self, class_id: str, student_id: str) -> bool:
        """Thêm học sinh vào lớp"""
        try:
            # Check if relationship already exists
            existing = self.client.table('class_students').select('id').eq('class_id', class_id).eq('student_id', student_id).execute()
            
            if existing.data:
                return False  # Already exists
            
            result = self.client.table('class_students').insert({
                'class_id': class_id,
                'student_id': student_id,
                'joined_at': datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error adding student to class: {e}")
            return False
    
    def remove_student_from_class(self, class_id: str, student_id: str) -> bool:
        """Xóa học sinh khỏi lớp"""
        try:
            result = self.client.table('class_students').delete().eq('class_id', class_id).eq('student_id', student_id).execute()
            return True
        except Exception as e:
            print(f"Error removing student from class: {e}")
            return False
    
    def get_students_in_class(self, class_id: str) -> List[Dict]:
        """Lấy danh sách học sinh trong lớp"""
        try:
            result = self.client.table('class_students').select(
                'student_id, joined_at, users(id, username, ho_ten, email, so_dien_thoai, is_active)'
            ).eq('class_id', class_id).execute()
            
            students = []
            for item in result.data:
                if item['users']:
                    student_info = item['users']
                    student_info['joined_at'] = item['joined_at']
                    students.append(student_info)
            return students
        except Exception as e:
            print(f"Error getting students in class: {e}")
            return []
    
    def get_classes_by_student(self, student_id: str) -> List[Dict]:
        """Lấy danh sách lớp của học sinh"""
        try:
            result = self.client.table('class_students').select(
                'class_id, joined_at, classes(id, ma_lop, ten_lop, mo_ta, teacher_id, users(ho_ten))'
            ).eq('student_id', student_id).execute()
            
            classes = []
            for item in result.data:
                if item['classes']:
                    class_info = item['classes']
                    class_info['joined_at'] = item['joined_at']
                    if class_info.get('users'):
                        class_info['teacher_name'] = class_info['users']['ho_ten']
                        class_info.pop('users')
                    classes.append(class_info)
            return classes
        except Exception as e:
            print(f"Error getting classes by student: {e}")
            return []
    
    def get_students_not_in_class(self, class_id: str) -> List[Dict]:
        """Lấy học sinh chưa có trong lớp"""
        try:
            # Get students already in class
            existing_result = self.client.table('class_students').select('student_id').eq('class_id', class_id).execute()
            existing_student_ids = [item['student_id'] for item in existing_result.data]
            
            # Get all students
            all_students_result = self.client.table('users').select('*').eq('role', 'student').eq('is_active', True).execute()
            
            # Filter students not in class
            available_students = []
            for student in all_students_result.data:
                if student['id'] not in existing_student_ids:
                    student.pop('password_hash', None)
                    available_students.append(student)
            
            return available_students
        except Exception as e:
            print(f"Error getting available students: {e}")
            return []
    
    def get_class_student_count(self, class_id: str) -> int:
        """Lấy số lượng học sinh trong lớp"""
        try:
            result = self.client.table('class_students').select('student_id', count='exact').eq('class_id', class_id).execute()
            return result.count or 0
        except Exception as e:
            print(f"Error getting class student count: {e}")
            return 0
    
    # ==================== EXAM MANAGEMENT ====================
    
    def create_exam(self, title: str, description: str, class_id: str, teacher_id: str,
                   questions: List[Dict], time_limit: int = 60, start_time: str = None, 
                   end_time: str = None, instructions: str = None) -> Optional[str]:
        """Tạo đề thi mới - Returns exam UUID"""
        try:
            exam_data = {
                'title': title,
                'description': description,
                'instructions': instructions,
                'class_id': class_id,
                'teacher_id': teacher_id,
                'questions': json.dumps(questions),
                'time_limit': time_limit,
                'start_time': start_time,
                'end_time': end_time,
                'total_questions': len(questions),
                'total_points': sum(q.get('points', 1) for q in questions),
                'is_published': False,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.client.table('exams').insert(exam_data).execute()
            
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"Error creating exam: {e}")
            return None
    
    def update_exam(self, exam_id: str, **kwargs) -> bool:
        """Cập nhật thông tin đề thi"""
        try:
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            update_data['updated_at'] = datetime.now().isoformat()
            
            # Handle questions serialization
            if 'questions' in update_data and isinstance(update_data['questions'], list):
                update_data['questions'] = json.dumps(update_data['questions'])
                update_data['total_questions'] = len(kwargs['questions'])
                update_data['total_points'] = sum(q.get('points', 1) for q in kwargs['questions'])
            
            result = self.client.table('exams').update(update_data).eq('id', exam_id).execute()
            return True
        except Exception as e:
            print(f"Error updating exam: {e}")
            return False
    
    def get_exams_by_class(self, class_id: str) -> List[Dict]:
        """Lấy danh sách đề thi theo lớp"""
        try:
            result = self.client.table('exams').select('*').eq('class_id', class_id).order('created_at', desc=True).execute()
            
            # Parse questions JSON
            for exam in result.data:
                if exam.get('questions'):
                    try:
                        exam['questions'] = json.loads(exam['questions'])
                    except:
                        exam['questions'] = []
            
            return result.data
        except Exception as e:
            print(f"Error getting exams: {e}")
            return []
    
    def get_exams_by_teacher(self, teacher_id: str) -> List[Dict]:
        """Lấy danh sách đề thi theo giáo viên"""
        try:
            result = self.client.table('exams').select(
                '*, classes(ten_lop)'
            ).eq('teacher_id', teacher_id).order('created_at', desc=True).execute()
            
            # Parse questions JSON and add class name
            for exam in result.data:
                if exam.get('questions'):
                    try:
                        exam['questions'] = json.loads(exam['questions'])
                    except:
                        exam['questions'] = []
                
                if exam.get('classes'):
                    exam['class_name'] = exam['classes']['ten_lop']
                    exam.pop('classes')
            
            return result.data
        except Exception as e:
            print(f"Error getting exams by teacher: {e}")
            return []
    
    def get_exam_by_id(self, exam_id: str) -> Optional[Dict]:
        """Lấy thông tin đề thi theo ID"""
        try:
            result = self.client.table('exams').select('*').eq('id', exam_id).execute()
            if result.data:
                exam = result.data[0]
                if exam.get('questions'):
                    try:
                        exam['questions'] = json.loads(exam['questions'])
                    except:
                        exam['questions'] = []
                return exam
            return None
        except Exception as e:
            print(f"Error getting exam: {e}")
            return None
    
    def delete_exam(self, exam_id: str) -> bool:
        """Xóa đề thi"""
        try:
            # First delete all submissions
            self.client.table('submissions').delete().eq('exam_id', exam_id).execute()
            
            # Then delete the exam
            result = self.client.table('exams').delete().eq('id', exam_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting exam: {e}")
            return False
    
    def publish_exam(self, exam_id: str) -> bool:
        """Phát hành đề thi"""
        try:
            result = self.client.table('exams').update({
                'is_published': True,
                'published_at': datetime.now().isoformat()
            }).eq('id', exam_id).execute()
            return True
        except Exception as e:
            print(f"Error publishing exam: {e}")
            return False
    
    # ==================== SUBMISSION MANAGEMENT ====================
    
    def submit_exam(self, exam_id: str, student_id: str, answers: List[Dict], 
                   time_taken: int = None) -> bool:
        """Nộp bài thi"""
        try:
            result = self.client.table('submissions').insert({
                'exam_id': exam_id,
                'student_id': student_id,
                'answers': json.dumps(answers),
                'time_taken': time_taken,
                'submitted_at': datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error submitting exam: {e}")
            return False
    
    def get_submission(self, exam_id: str, student_id: str) -> Optional[Dict]:
        """Lấy bài làm của học sinh"""
        try:
            result = self.client.table('submissions').select('*').eq('exam_id', exam_id).eq('student_id', student_id).execute()
            if result.data:
                submission = result.data[0]
                if submission.get('answers'):
                    try:
                        submission['answers'] = json.loads(submission['answers'])
                    except:
                        submission['answers'] = []
                return submission
            return None
        except Exception as e:
            print(f"Error getting submission: {e}")
            return None
    
    def get_submissions_by_exam(self, exam_id: str) -> List[Dict]:
        """Lấy tất cả bài làm của một đề thi"""
        try:
            result = self.client.table('submissions').select(
                '*, users(ho_ten, username)'
            ).eq('exam_id', exam_id).execute()
            
            submissions = []
            for submission in result.data:
                if submission.get('answers'):
                    try:
                        submission['answers'] = json.loads(submission['answers'])
                    except:
                        submission['answers'] = []
                
                if submission.get('users'):
                    submission['student_name'] = submission['users']['ho_ten']
                    submission['student_username'] = submission['users']['username']
                    submission.pop('users')
                
                submissions.append(submission)
            
            return submissions
        except Exception as e:
            print(f"Error getting submissions by exam: {e}")
            return []
    
    def update_submission_score(self, submission_id: str, total_score: float, 
                              max_score: float, feedback: str = None, 
                              question_scores: List[Dict] = None) -> bool:
        """Cập nhật điểm bài thi"""
        try:
            update_data = {
                'total_score': total_score,
                'max_score': max_score,
                'feedback': feedback,
                'graded_at': datetime.now().isoformat(),
                'is_graded': True
            }
            
            if question_scores:
                update_data['question_scores'] = json.dumps(question_scores)
            
            result = self.client.table('submissions').update(update_data).eq('id', submission_id).execute()
            return True
        except Exception as e:
            print(f"Error updating score: {e}")
            return False
    
    # ==================== IMPORT LOGGING ====================
    
    def log_import_activity(self, teacher_id: str, import_type: str, 
                          success_count: int, total_count: int, details: Dict = None) -> bool:
        """Ghi log hoạt động import"""
        try:
            result = self.client.table('import_logs').insert({
                'teacher_id': teacher_id,
                'import_type': import_type,
                'success_count': success_count,
                'total_count': total_count,
                'details': json.dumps(details) if details else None,
                'created_at': datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Error logging import activity: {e}")
            return False
    
    def get_import_statistics(self, teacher_id: str = None) -> Dict:
        """Lấy thống kê import"""
        try:
            query = self.client.table('import_logs').select('*')
            
            if teacher_id:
                query = query.eq('teacher_id', teacher_id)
            
            result = query.execute()
            
            # Calculate statistics
            today = datetime.now().date()
            stats = {'today': 0, 'week': 0, 'month': 0}
            
            for log in result.data:
                log_date = datetime.fromisoformat(log['created_at']).date()
                days_diff = (today - log_date).days
                
                success_count = log['success_count']
                
                if days_diff == 0:
                    stats['today'] += success_count
                if days_diff <= 7:
                    stats['week'] += success_count
                if days_diff <= 30:
                    stats['month'] += success_count
            
            return stats
        except Exception as e:
            print(f"Error getting import statistics: {e}")
            return {'today': 0, 'week': 0, 'month': 0}
    
    # ==================== UTILITY METHODS ====================
    
    def get_dashboard_stats(self, teacher_id: str) -> Dict:
        """Lấy thống kê cho dashboard giáo viên"""
        try:
            # Get class count
            class_result = self.client.table('classes').select('id', count='exact').eq('teacher_id', teacher_id).execute()
            class_count = class_result.count or 0
            
            # Get student count (across all classes)
            student_result = self.client.table('class_students').select(
                'student_id', count='exact'
            ).in_('class_id', [c['id'] for c in (class_result.data or [])]).execute()
            student_count = student_result.count or 0
            
            # Get exam count
            exam_result = self.client.table('exams').select('id', count='exact').eq('teacher_id', teacher_id).execute()
            exam_count = exam_result.count or 0
            
            # Get submission count
            submission_result = self.client.table('submissions').select(
                'id', count='exact'
            ).in_('exam_id', [e['id'] for e in (exam_result.data or [])]).execute()
            submission_count = submission_result.count or 0
            
            return {
                'class_count': class_count,
                'student_count': student_count,
                'exam_count': exam_count,
                'submission_count': submission_count
            }
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {'class_count': 0, 'student_count': 0, 'exam_count': 0, 'submission_count': 0}
    
    def health_check(self) -> bool:
        """Kiểm tra kết nối database"""
        try:
            result = self.client.table('users').select('id').limit(1).execute()
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False