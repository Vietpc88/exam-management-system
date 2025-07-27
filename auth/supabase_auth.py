import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
import streamlit as st

class SupabaseDatabase:
    def __init__(self):
        """Initialize Supabase client"""
        try:
            # Get credentials from Streamlit secrets or environment
            if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                url = st.secrets.supabase.url
                key = st.secrets.supabase.key
            else:
                url = os.getenv('SUPABASE_URL')
                key = os.getenv('SUPABASE_KEY')
            
            if not url or not key:
                raise ValueError("Supabase URL and Key must be provided")
            
            self.supabase: Client = create_client(url, key)
        except Exception as e:
            st.error(f"❌ Lỗi kết nối Supabase: {str(e)}")
            raise

    # ==================== USER MANAGEMENT ====================
    
    def create_user(self, username: str, password_hash: str, ho_ten: str, 
                   email: str = None, role: str = 'student') -> Optional[str]:
        """Tạo user mới"""
        try:
            data = {
                'username': username,
                'password_hash': password_hash,
                'ho_ten': ho_ten,
                'email': email,
                'role': role,
                'is_active': True
            }
            
            result = self.supabase.table('users').insert(data).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            st.error(f"Lỗi tạo user: {str(e)}")
            return None

    def get_user_by_credentials(self, username: str, password_hash: str) -> Optional[Dict]:
        """Lấy user theo username và password"""
        try:
            result = self.supabase.table('users').select('*').eq('username', username).eq('password_hash', password_hash).eq('is_active', True).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Lỗi xác thực: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Lấy user theo ID"""
        try:
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Lỗi lấy user: {str(e)}")
            return None

    # ==================== CLASS MANAGEMENT ====================
    
    def create_class(self, ma_lop: str, ten_lop: str, teacher_id: str, mo_ta: str = None) -> Optional[str]:
        """Tạo lớp học mới"""
        try:
            data = {
                'ma_lop': ma_lop,
                'ten_lop': ten_lop,
                'teacher_id': teacher_id,
                'mo_ta': mo_ta
            }
            
            result = self.supabase.table('classes').insert(data).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            st.error(f"Lỗi tạo lớp: {str(e)}")
            return None

    def get_classes_by_teacher(self, teacher_id: str) -> List[Dict]:
        """Lấy danh sách lớp của giáo viên"""
        try:
            result = self.supabase.from_('class_summary').select('*').eq('teacher_id', teacher_id).execute()
            return result.data or []
        except Exception as e:
            st.error(f"Lỗi lấy danh sách lớp: {str(e)}")
            return []

    def get_class_student_count(self, class_id: str) -> int:
        """Lấy số lượng học sinh trong lớp"""
        try:
            result = self.supabase.table('class_students').select('id', count='exact').eq('class_id', class_id).execute()
            return result.count or 0
        except Exception as e:
            return 0

    def add_student_to_class(self, class_id: str, student_id: str) -> bool:
        """Thêm học sinh vào lớp"""
        try:
            data = {
                'class_id': class_id,
                'student_id': student_id
            }
            
            result = self.supabase.table('class_students').insert(data).execute()
            return bool(result.data)
        except Exception as e:
            st.error(f"Lỗi thêm học sinh: {str(e)}")
            return False

    def get_students_in_class(self, class_id: str) -> List[Dict]:
        """Lấy danh sách học sinh trong lớp"""
        try:
            result = self.supabase.table('class_students').select('''
                student_id,
                joined_at,
                users:student_id (id, username, ho_ten, email)
            ''').eq('class_id', class_id).execute()
            
            students = []
            for item in result.data or []:
                if item.get('users'):
                    student = item['users']
                    student['joined_at'] = item['joined_at']
                    students.append(student)
            
            return students
        except Exception as e:
            st.error(f"Lỗi lấy danh sách học sinh: {str(e)}")
            return []

    def get_student_classes(self, student_id: str) -> List[Dict]:
        """Lấy danh sách lớp của học sinh"""
        try:
            result = self.supabase.table('class_students').select('''
                class_id,
                joined_at,
                classes:class_id (id, ma_lop, ten_lop, mo_ta, teacher_id,
                    users:teacher_id (ho_ten))
            ''').eq('student_id', student_id).execute()
            
            classes = []
            for item in result.data or []:
                if item.get('classes'):
                    class_info = item['classes']
                    class_info['joined_at'] = item['joined_at']
                    classes.append(class_info)
            
            return classes
        except Exception as e:
            st.error(f"Lỗi lấy danh sách lớp học sinh: {str(e)}")
            return []

    # ==================== EXAM MANAGEMENT ====================
    
    def create_exam(self, title: str, description: str, class_id: str, teacher_id: str,
                   questions: List[Dict], time_limit: int, start_time: str, end_time: str,
                   instructions: str = None) -> Optional[str]:
        """Tạo đề thi mới"""
        try:
            total_questions = len(questions)
            total_points = sum(q.get('points', 0) for q in questions)
            
            data = {
                'title': title,
                'description': description,
                'instructions': instructions,
                'class_id': class_id,
                'teacher_id': teacher_id,
                'questions': json.dumps(questions),
                'time_limit': time_limit,
                'start_time': start_time,
                'end_time': end_time,
                'total_questions': total_questions,
                'total_points': total_points,
                'is_published': False
            }
            
            result = self.supabase.table('exams').insert(data).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            st.error(f"Lỗi tạo đề thi: {str(e)}")
            return None

    def publish_exam(self, exam_id: str) -> bool:
        """Phát hành đề thi"""
        try:
            data = {
                'is_published': True,
                'published_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('exams').update(data).eq('id', exam_id).execute()
            return bool(result.data)
        except Exception as e:
            st.error(f"Lỗi phát hành đề thi: {str(e)}")
            return False

    def get_exams_by_teacher(self, teacher_id: str) -> List[Dict]:
        """Lấy danh sách đề thi của giáo viên"""
        try:
            result = self.supabase.from_('exam_stats').select('*').eq('teacher_id', teacher_id).execute()
            return result.data or []
        except Exception as e:
            st.error(f"Lỗi lấy danh sách đề thi: {str(e)}")
            return []

    def get_exam_by_id(self, exam_id: str) -> Optional[Dict]:
        """Lấy thông tin đề thi theo ID"""
        try:
            result = self.supabase.table('exams').select('*').eq('id', exam_id).execute()
            if result.data:
                exam = result.data[0]
                if exam.get('questions'):
                    exam['questions'] = json.loads(exam['questions'])
                return exam
            return None
        except Exception as e:
            st.error(f"Lỗi lấy đề thi: {str(e)}")
            return None

    def get_published_exams_for_student(self, student_id: str) -> List[Dict]:
        """Lấy đề thi đã phát hành cho học sinh"""
        try:
            # Get classes that student is in
            student_classes = self.get_student_classes(student_id)
            class_ids = [c['id'] for c in student_classes]
            
            if not class_ids:
                return []
            
            result = self.supabase.table('exams').select('''
                *,
                classes:class_id (ten_lop),
                users:teacher_id (ho_ten)
            ''').eq('is_published', True).in_('class_id', class_ids).execute()
            
            return result.data or []
        except Exception as e:
            st.error(f"Lỗi lấy đề thi cho học sinh: {str(e)}")
            return []

    # ==================== SUBMISSION MANAGEMENT ====================
    
    def create_submission(self, exam_id: str, student_id: str, answers: List[Dict],
                         time_taken: int, max_score: float) -> Optional[str]:
        """Tạo bài nộp mới"""
        try:
            data = {
                'exam_id': exam_id,
                'student_id': student_id,
                'answers': json.dumps(answers),
                'time_taken': time_taken,
                'max_score': max_score,
                'is_graded': False
            }
            
            result = self.supabase.table('submissions').insert(data).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            st.error(f"Lỗi nộp bài: {str(e)}")
            return None

    def get_submissions_by_exam(self, exam_id: str) -> List[Dict]:
        """Lấy danh sách bài nộp theo đề thi"""
        try:
            result = self.supabase.table('submissions').select('''
                *,
                users:student_id (id, username, ho_ten)
            ''').eq('exam_id', exam_id).execute()
            
            submissions = []
            for item in result.data or []:
                if item.get('users'):
                    submission = item.copy()
                    submission['student_info'] = item['users']
                    if submission.get('answers'):
                        submission['answers'] = json.loads(submission['answers'])
                    submissions.append(submission)
            
            return submissions
        except Exception as e:
            st.error(f"Lỗi lấy danh sách bài nộp: {str(e)}")
            return []

    def get_student_submission(self, exam_id: str, student_id: str) -> Optional[Dict]:
        """Lấy bài nộp của học sinh cho đề thi cụ thể"""
        try:
            result = self.supabase.table('submissions').select('*').eq('exam_id', exam_id).eq('student_id', student_id).execute()
            if result.data:
                submission = result.data[0]
                if submission.get('answers'):
                    submission['answers'] = json.loads(submission['answers'])
                return submission
            return None
        except Exception as e:
            st.error(f"Lỗi lấy bài nộp: {str(e)}")
            return None

    def update_submission_grade(self, submission_id: str, total_score: float,
                              question_scores: Dict, feedback: str = None) -> bool:
        """Cập nhật điểm bài nộp"""
        try:
            data = {
                'total_score': total_score,
                'question_scores': json.dumps(question_scores),
                'feedback': feedback,
                'is_graded': True,
                'graded_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('submissions').update(data).eq('id', submission_id).execute()
            return bool(result.data)
        except Exception as e:
            st.error(f"Lỗi cập nhật điểm: {str(e)}")
            return False

    def get_student_results(self, student_id: str) -> List[Dict]:
        """Lấy kết quả thi của học sinh"""
        try:
            result = self.supabase.table('submissions').select('''
                *,
                exams:exam_id (id, title, total_points, time_limit,
                    classes:class_id (ten_lop),
                    users:teacher_id (ho_ten))
            ''').eq('student_id', student_id).eq('is_graded', True).execute()
            
            return result.data or []
        except Exception as e:
            st.error(f"Lỗi lấy kết quả thi: {str(e)}")
            return []

    # ==================== STATISTICS ====================
    
    def get_dashboard_stats(self, teacher_id: str) -> Dict:
        """Lấy thống kê dashboard cho giáo viên"""
        try:
            # Count classes
            class_count = self.supabase.table('classes').select('id', count='exact').eq('teacher_id', teacher_id).execute().count or 0
            
            # Count students
            classes_result = self.supabase.table('classes').select('id').eq('teacher_id', teacher_id).execute()
            class_ids = [c['id'] for c in classes_result.data or []]
            
            student_count = 0
            if class_ids:
                student_count = self.supabase.table('class_students').select('student_id', count='exact').in_('class_id', class_ids).execute().count or 0
            
            # Count exams
            exam_count = self.supabase.table('exams').select('id', count='exact').eq('teacher_id', teacher_id).execute().count or 0
            
            # Count submissions
            submission_count = 0
            if class_ids:
                exam_ids_result = self.supabase.table('exams').select('id').eq('teacher_id', teacher_id).execute()
                exam_ids = [e['id'] for e in exam_ids_result.data or []]
                if exam_ids:
                    submission_count = self.supabase.table('submissions').select('id', count='exact').in_('exam_id', exam_ids).execute().count or 0
            
            return {
                'class_count': class_count,
                'student_count': student_count,
                'exam_count': exam_count,
                'submission_count': submission_count
            }
        except Exception as e:
            st.error(f"Lỗi lấy thống kê: {str(e)}")
            return {'class_count': 0, 'student_count': 0, 'exam_count': 0, 'submission_count': 0}

    # ==================== UTILITY FUNCTIONS ====================
    
    def search_users(self, query: str, role: str = None) -> List[Dict]:
        """Tìm kiếm users"""
        try:
            select_query = self.supabase.table('users').select('id, username, ho_ten, email, role')
            
            # Add role filter if specified
            if role:
                select_query = select_query.eq('role', role)
            
            # Search in username or ho_ten
            result = select_query.or_(f'username.ilike.%{query}%,ho_ten.ilike.%{query}%').eq('is_active', True).execute()
            
            return result.data or []
        except Exception as e:
            st.error(f"Lỗi tìm kiếm user: {str(e)}")
            return []

    def get_class_by_code(self, ma_lop: str) -> Optional[Dict]:
        """Lấy lớp theo mã lớp"""
        try:
            result = self.supabase.table('classes').select('*').eq('ma_lop', ma_lop).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Lỗi lấy lớp theo mã: {str(e)}")
            return None

# Singleton instance
_db_instance = None

def get_database() -> SupabaseDatabase:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDatabase()
    return _db_instance