from typing import List, Dict, Any, Optional
from config.supabase_config import get_supabase_client, get_supabase_admin_client
import bcrypt
import json

class SupabaseDatabase:
    def __init__(self):
        self.client = get_supabase_client()
        self.admin_client = get_supabase_admin_client()
    
    def hash_password(self, password: str) -> str:
        """Hash password sử dụng bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    # User management
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
                'role': role
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
                if self.verify_password(password, user['password_hash']):
                    return user
            return None
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin user theo ID"""
        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    # Class management
    def create_class(self, ma_lop: str, ten_lop: str, mo_ta: str, teacher_id: int) -> bool:
        """Tạo lớp học mới"""
        try:
            result = self.client.table('classes').insert({
                'ma_lop': ma_lop,
                'ten_lop': ten_lop,
                'mo_ta': mo_ta,
                'teacher_id': teacher_id
            }).execute()
            return True
        except Exception as e:
            print(f"Error creating class: {e}")
            return False
    
    def get_classes_by_teacher(self, teacher_id: int) -> List[Dict]:
        """Lấy danh sách lớp của giáo viên"""
        try:
            result = self.client.table('classes').select('*').eq('teacher_id', teacher_id).execute()
            return result.data
        except Exception as e:
            print(f"Error getting classes: {e}")
            return []
    
    def add_student_to_class(self, class_id: int, student_id: int) -> bool:
        """Thêm học sinh vào lớp"""
        try:
            result = self.client.table('class_students').insert({
                'class_id': class_id,
                'student_id': student_id
            }).execute()
            return True
        except Exception as e:
            print(f"Error adding student to class: {e}")
            return False
    
    def get_students_in_class(self, class_id: int) -> List[Dict]:
        """Lấy danh sách học sinh trong lớp"""
        try:
            result = self.client.table('class_students').select(
                'student_id, users(id, username, ho_ten, email, so_dien_thoai)'
            ).eq('class_id', class_id).execute()
            
            students = []
            for item in result.data:
                student_info = item['users']
                students.append(student_info)
            return students
        except Exception as e:
            print(f"Error getting students: {e}")
            return []
    
    # Exam management
    def create_exam(self, title: str, description: str, class_id: int, teacher_id: int,
                   questions: List[Dict], time_limit: int = 60, start_time: str = None, 
                   end_time: str = None) -> bool:
        """Tạo đề thi mới"""
        try:
            result = self.client.table('exams').insert({
                'title': title,
                'description': description,
                'class_id': class_id,
                'teacher_id': teacher_id,
                'questions': json.dumps(questions),
                'time_limit': time_limit,
                'start_time': start_time,
                'end_time': end_time
            }).execute()
            return True
        except Exception as e:
            print(f"Error creating exam: {e}")
            return False
    
    def get_exams_by_class(self, class_id: int) -> List[Dict]:
        """Lấy danh sách đề thi theo lớp"""
        try:
            result = self.client.table('exams').select('*').eq('class_id', class_id).execute()
            return result.data
        except Exception as e:
            print(f"Error getting exams: {e}")
            return []
    
    def get_exam_by_id(self, exam_id: int) -> Optional[Dict]:
        """Lấy thông tin đề thi theo ID"""
        try:
            result = self.client.table('exams').select('*').eq('id', exam_id).execute()
            if result.data:
                exam = result.data[0]
                exam['questions'] = json.loads(exam['questions'])
                return exam
            return None
        except Exception as e:
            print(f"Error getting exam: {e}")
            return None
    
    # Submission management
    def submit_exam(self, exam_id: int, student_id: int, answers: List[Dict]) -> bool:
        """Nộp bài thi"""
        try:
            result = self.client.table('submissions').insert({
                'exam_id': exam_id,
                'student_id': student_id,
                'answers': json.dumps(answers)
            }).execute()
            return True
        except Exception as e:
            print(f"Error submitting exam: {e}")
            return False
    
    def get_submission(self, exam_id: int, student_id: int) -> Optional[Dict]:
        """Lấy bài làm của học sinh"""
        try:
            result = self.client.table('submissions').select('*').eq('exam_id', exam_id).eq('student_id', student_id).execute()
            if result.data:
                submission = result.data[0]
                submission['answers'] = json.loads(submission['answers'])
                return submission
            return None
        except Exception as e:
            print(f"Error getting submission: {e}")
            return None
    
    def update_submission_score(self, submission_id: int, total_score: float, max_score: float, feedback: str = None) -> bool:
        """Cập nhật điểm bài thi"""
        try:
            result = self.client.table('submissions').update({
                'total_score': total_score,
                'max_score': max_score,
                'feedback': feedback,
                'graded_at': 'now()'
            }).eq('id', submission_id).execute()
            return True
        except Exception as e:
            print(f"Error updating score: {e}")
            return False