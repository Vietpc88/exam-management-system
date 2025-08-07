# --- START OF FILE supabase_wrapper.py ---

print("\n\n>>> 2105 supabase_wrapper.py <<<\n\n")
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any
import streamlit as st

# Import bcrypt for password hashing
try:
    import bcrypt
except ImportError:
    st.error("❌ Vui lòng cài đặt: pip install bcrypt")
    st.stop()

# Import Supabase client từ config
try:
    from config.supabase_config import get_supabase_client, test_connection
except ImportError:
    st.error("❌ Không thể import Supabase config. Kiểm tra file config/supabase_config.py")
    st.stop()

class SupabaseDatabase:
    def __init__(self):
        self.client = get_supabase_client()
        if not self.test_connection():
            st.error("❌ Không thể kết nối database")
            st.stop()

    def test_connection(self) -> bool:
        return test_connection()
    # ==========================================
    # AUTHENTICATION METHODS
    # ==========================================
    
    # Trong database/supabase_wrapper.py

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        try:
            print(f"\n--- DEBUG: Bắt đầu xác thực cho user: {username} ---")
            response = self.client.table('users').select('*').eq('username', username).limit(1).maybe_single().execute()
            user = response.data
            
            if not user:
                print("DEBUG: Không tìm thấy user trong database.")
                return None
            print("DEBUG: Đã tìm thấy user:", user)

            if not user.get('is_active', True): # Sửa lại để mặc định là active
                print("DEBUG: User không hoạt động.")
                st.warning("⚠️ Tài khoản đã bị vô hiệu hóa")
                return None
            
            password_hash_from_db = user.get('password_hash', '')
            print(f"DEBUG: Hash từ DB: {password_hash_from_db}")
            
            # Tạo hash từ mật khẩu người dùng nhập vào để so sánh
            password_hash_from_input = self._hash_password(password)
            print(f"DEBUG: Hash từ input: {password_hash_from_input}")

            if self._verify_password(password, password_hash_from_db):
                print("DEBUG: Xác minh mật khẩu THÀNH CÔNG.")
                self.update_last_login(user['id'])
                user.pop('password_hash', None)
                return user
            else:
                print("DEBUG: Xác minh mật khẩu THẤT BẠI.")
                return None
                
        except Exception as e:
            print(f"DEBUG: Xảy ra lỗi Exception: {e}")
            st.error(f"❌ Lỗi xác thực: {e}")
            return None
    def update_last_login(self, user_id: str) -> bool:
        try:
            self.client.table('users').update({'last_login': datetime.now().isoformat()}).eq('id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error updating last login: {e}")
            return False
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except (ValueError, TypeError):
            return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def _hash_password(self, password: str) -> str:
        """Mã hóa mật khẩu"""
        try:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except:
            # Fallback cho hash đơn giản (chỉ dùng trong development)
            return hashlib.sha256(password.encode()).hexdigest()
    
    # ==========================================
    # USER MANAGEMENT
    # ==========================================
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Lấy thông tin user theo ID"""
        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"❌ Lỗi lấy thông tin user: {str(e)}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Lấy thông tin người dùng bằng username."""
        try:
            response = self.client.table('users').select('*').eq('username', username).single().execute()
            return response.data
        except Exception:
            return None
    
    # Trong database/supabase_wrapper.py

    # Trong file database/supabase_wrapper.py
    # Trong file database/supabase_wrapper.py, class SupabaseDatabase

    # ==========================================
    # ADMIN-ONLY METHODS
    # ==========================================
    
    # ... (các hàm admin_... khác)
    def check_users_exist(self, usernames: list = None, emails: list = None) -> dict:
        """
        Kiểm tra xem một danh sách usernames hoặc emails đã tồn tại trong bảng users chưa.
        Trả về một dictionary chứa các giá trị đã tồn tại.
        """
        existing_users = {'usernames': set(), 'emails': set()}
        try:
            if usernames:
                response = self.client.table('users').select('username').in_('username', usernames).execute()
                for user in response.data:
                    existing_users['usernames'].add(user['username'])
            
            if emails:
                response = self.client.table('users').select('email').in_('email', emails).execute()
                for user in response.data:
                    existing_users['emails'].add(user['email'])
            
            return existing_users
        except Exception as e:
            st.error(f"❌ Lỗi khi kiểm tra người dùng tồn tại: {e}")
            return existing_users
    def admin_update_user(self, user_id: str, **kwargs) -> bool:
        """Admin cập nhật thông tin cho một người dùng bất kỳ."""
        try:
            from config.supabase_config import get_supabase_admin_client
            admin_client = get_supabase_admin_client()
            
            allowed_fields = ['ho_ten', 'email', 'is_active', 'role']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_data:
                st.warning("Không có dữ liệu hợp lệ để cập nhật.")
                return False
            
            # Sử dụng admin_client để bỏ qua RLS
            response = admin_client.table('users').update(update_data).eq('id', user_id).execute()

            if response.data:
                st.success("✅ Cập nhật thông tin người dùng thành công!")
                return True
            else:
                st.error("❌ Cập nhật thất bại. Không có dữ liệu trả về.")
                return False
        except Exception as e:
            st.error(f"❌ Lỗi khi cập nhật người dùng: {e}")
            return False
    # Trong file database/supabase_wrapper.py

    def create_user(self, username: str, password: str, ho_ten: str, email: str, role: str, so_dien_thoai: Optional[str] = None) -> Optional[str]:
        """
        Tạo user mới, đồng bộ Auth và public.users, bao gồm cả số điện thoại.
        """
        try:
            from config.supabase_config import get_supabase_admin_client
            admin_client = get_supabase_admin_client()

            # Bước 1: Tạo user trong Auth. Trigger sẽ tạo dòng cơ bản.
            # Truyền metadata để trigger có thể sử dụng nếu cần
            auth_response = admin_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {'ho_ten': ho_ten, 'role': role}
            })
            new_user = auth_response.user
            if not new_user:
                st.error("❌ Không thể tạo user trong hệ thống xác thực.")
                return None

            new_user_id = new_user.id

            # Bước 2: Chuẩn bị dữ liệu để UPDATE, bao gồm cả số điện thoại
            update_data = {
                'username': username,
                'ho_ten': ho_ten,
                'role': role,
                'password_hash': self._hash_password(password),
                'is_active': True,
                'so_dien_thoai': so_dien_thoai # Thêm số điện thoại vào đây
            }
            
            # Bước 3: Dùng admin_client để UPDATE lại dòng vừa được trigger tạo ra.
            update_response = admin_client.table('users').update(update_data).eq('id', new_user_id).execute()

            if update_response.data:
                st.success(f"✅ Tạo tài khoản thành công cho {ho_ten}")
                return new_user_id
            else:
                # Nếu UPDATE thất bại, rollback
                admin_client.auth.admin.delete_user(new_user_id)
                st.error("❌ Lỗi khi cập nhật thông tin chi tiết cho người dùng mới. Kiểm tra RLS Policy.")
                return None

        except Exception as e:
            # Xử lý rollback an toàn
            if 'new_user_id' in locals() and 'admin_client' in locals():
                try:
                    admin_client.auth.admin.delete_user(new_user_id)
                    st.warning("Đã rollback user vừa tạo trong Auth do có lỗi.")
                except Exception as rollback_error:
                    st.error(f"Lỗi khi rollback: {rollback_error}")

            if 'duplicate key value' in str(e) or 'already exists' in str(e):
                st.error("❌ Email hoặc người dùng đã tồn tại.")
            else:
                st.error(f"❌ Lỗi tạo user: {e}")
            return None
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Cập nhật thông tin user"""
        try:
            # Loại bỏ các field không được phép cập nhật
            allowed_fields = ['ho_ten', 'email', 'is_active']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_data:
                return False
            
            result = self.client.table('users').update(update_data).eq('id', user_id).execute()
            
            if result.data:
                st.success("✅ Cập nhật thông tin thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi cập nhật user: {str(e)}")
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Đổi mật khẩu"""
        try:
            # Lấy thông tin user hiện tại
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Xác minh mật khẩu cũ
            if not self._verify_password(old_password, user['password_hash']):
                st.error("❌ Mật khẩu cũ không đúng")
                return False
            
            # Cập nhật mật khẩu mới
            new_hash = self._hash_password(new_password)
            result = self.client.table('users').update({
                'password_hash': new_hash
            }).eq('id', user_id).execute()
            
            if len(result.data) > 0:
                st.success("✅ Đổi mật khẩu thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi đổi mật khẩu: {str(e)}")
            return False
    
    def get_all_students(self) -> List[Dict]:
        """Lấy danh sách tất cả học sinh"""
        try:
            result = self.client.table('users').select('id, username, ho_ten, email, created_at').eq('role', 'student').eq('is_active', True).execute()
            return result.data or []
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách học sinh: {str(e)}")
            return []
    
    # ==========================================
    # CLASS MANAGEMENT  
    # ==========================================
    
    def get_classes_by_student(self, student_id: str) -> list:
        """
        Lấy các lớp học mà một học sinh đã tham gia.
        PHIÊN BẢN CHUẨN - KHÔNG GÂY LỖI
        """
        try:
            # Bước 1: Lấy danh sách class_id từ bảng class_students
            enrollments = self.client.table('class_students').select('class_id, joined_at').eq('student_id', student_id).execute()
            if not enrollments.data:
                return []
            
            class_ids = [item['class_id'] for item in enrollments.data]
            
            # Bước 2: Lấy thông tin chi tiết các lớp từ danh sách ID đã có
            response = self.client.table('classes').select('*').in_('id', class_ids).execute()
            
            # Bước 3 (Tùy chọn): Gắn ngày tham gia vào thông tin lớp
            classes_data = response.data if response.data else []
            for cls in classes_data:
                for enr in enrollments.data:
                    if cls['id'] == enr['class_id']:
                        cls['joined_at'] = enr['joined_at']
                        break
            return classes_data
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy lớp của học sinh: {e}")
            return []
    def get_class_by_id(self, class_id: str) -> Optional[Dict]:
        """Lấy thông tin lớp theo ID"""
        try:
            result = self.client.table('classes').select('*').eq('id', class_id).execute()
            if result.data:
                cls = result.data[0]
                cls['student_count'] = self.get_class_student_count(class_id)
                return cls
            return None
        except Exception as e:
            st.error(f"❌ Lỗi lấy thông tin lớp: {str(e)}")
            return None
    
    # TÌM VÀ THAY THẾ HÀM NÀY:
    def create_class(self, ma_lop: str, ten_lop: str, mo_ta: str = '') -> Optional[str]:
        """Tạo lớp học mới (không cần teacher_id)"""
        try:
            result = self.client.table('classes').insert({
                'ma_lop': ma_lop,
                'ten_lop': ten_lop,
                'mo_ta': mo_ta,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            if result.data:
                st.success(f"✅ Tạo lớp '{ten_lop}' thành công")
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            st.error(f"❌ Lỗi tạo lớp: {str(e)}")
            return None
    
    def update_class(self, class_id: str, **kwargs) -> bool:
        """Cập nhật thông tin lớp"""
        try:
            allowed_fields = ['ten_lop', 'mo_ta']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_data:
                return False
            
            result = self.client.table('classes').update(update_data).eq('id', class_id).execute()
            
            if result.data:
                st.success("✅ Cập nhật thông tin lớp thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi cập nhật lớp: {str(e)}")
            return False
    
    def delete_class(self, class_id: str) -> bool:
        """Xóa lớp học"""
        try:
            # Xóa học sinh trong lớp trước
            self.client.table('class_students').delete().eq('class_id', class_id).execute()
            
            # Xóa lớp
            result = self.client.table('classes').delete().eq('id', class_id).execute()
            
            if result.data:
                st.success("✅ Xóa lớp thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi xóa lớp: {str(e)}")
            return False
    
    def get_class_student_count(self, class_id: str) -> int:
        """Đếm số học sinh trong lớp"""
        try:
            result = self.client.table('class_students').select('id', count='exact').execute()
            return result.count if result.count is not None else 0
        except Exception as e:
            print(f"Error counting students: {e}")
            return 0
    
    def get_students_in_class(self, class_id: str) -> List[Dict]:
        """Lấy danh sách học sinh trong lớp"""
        try:
            result = self.client.table('class_students').select('''
                *,
                users!class_students_student_id_fkey (
                    id, username, ho_ten, email
                )
            ''').eq('class_id', class_id).execute()
            
            students = []
            for record in result.data or []:
                if record.get('users'):
                    student = record['users'].copy()
                    student['joined_at'] = record['joined_at']
                    students.append(student)
            
            return students
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách học sinh: {str(e)}")
            return []
    
    def add_student_to_class(self, class_id: str, student_id: str) -> bool:
        """Thêm học sinh vào lớp"""
        try:
            # Kiểm tra học sinh đã có trong lớp chưa
            existing = self.client.table('class_students').select('id').eq('class_id', class_id).eq('student_id', student_id).execute()
            
            if existing.data:
                st.warning("⚠️ Học sinh đã có trong lớp")
                return False
            
            result = self.client.table('class_students').insert({
                'class_id': class_id,
                'student_id': student_id,
                'joined_at': datetime.now().isoformat()
            }).execute()
            
            if result.data:
                st.success("✅ Thêm học sinh vào lớp thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi thêm học sinh: {str(e)}")
            return False
    
    def remove_student_from_class(self, class_id: str, student_id: str) -> bool:
        """Xóa học sinh khỏi lớp"""
        try:
            result = self.client.table('class_students').delete().eq('class_id', class_id).eq('student_id', student_id).execute()
            
            if result.data:
                st.success("✅ Xóa học sinh khỏi lớp thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi xóa học sinh: {str(e)}")
            return False
    
    
    
    def get_class_by_code(self, ma_lop: str) -> Optional[Dict]:
        """Lấy lớp theo mã lớp"""
        try:
            result = self.client.table('classes').select('*').eq('ma_lop', ma_lop).limit(1).single().execute()
            return result.data
        except Exception:
            return None
    # ==========================================
    # EXAM MANAGEMENT
    # ==========================================
    # Code để copy

    # Trong file database/supabase_wrapper.py, bên trong class SupabaseDatabase

    # ==========================================
    # ĐÂY LÀ HÀM ĐÃ ĐƯỢC SỬA LỖI
    # ==========================================
    def get_student_submission(self, exam_id: str, student_id: str) -> Optional[Dict]:
        """
        Lấy bài nộp của một học sinh cho một bài thi cụ thể.
        Phiên bản này an toàn hơn, không dùng maybe_single().
        """
        try:
            # Sử dụng .limit(1) thay cho .maybe_single() để đảm bảo kết quả luôn là một danh sách.
            response = self.client.table('submissions').select('*').eq('exam_id', exam_id).eq('student_id', student_id).limit(1).execute()
            
            # Kiểm tra xem danh sách kết quả có rỗng không.
            if not response.data:
                return None
            
            # Lấy phần tử đầu tiên nếu có kết quả.
            submission = response.data[0]

            # Parse các trường JSON an toàn.
            if submission.get('answers') and isinstance(submission['answers'], str):
                try: 
                    submission['answers'] = json.loads(submission['answers'])
                except json.JSONDecodeError: 
                    submission['answers'] = []
            
            if submission.get('question_scores') and isinstance(submission['question_scores'], str):
                try: 
                    submission['question_scores'] = json.loads(submission['question_scores'])
                except json.JSONDecodeError: 
                    submission['question_scores'] = {}
            
            return submission
        except Exception as e:
            print(f"ERROR in get_student_submission: {e}")
            st.error(f"❌ Lỗi khi truy vấn bài nộp: {e}")
            return None

    def get_student_results(self, student_id: str) -> list:
        """
        Lấy danh sách kết quả thi của học sinh.
        Phiên bản đã được sửa để không còn tìm kiếm teacher.
        """
        try:
            # Câu select đã được đơn giản hóa, không còn join với users
            response = self.client.table('submissions').select(
                '*, exams!inner(id, title, total_points, classes!inner(ten_lop))'
            ).eq('student_id', student_id).eq('is_graded', True).execute()
            
            processed_results = []
            for submission in response.data or []:
                exam_info = submission.pop('exams', {})
                if exam_info:
                    submission['exam_id'] = exam_info.get('id')
                    submission['exam_title'] = exam_info.get('title', 'N/A')
                    submission['max_score'] = submission.get('max_score') or exam_info.get('total_points', 0)
                    submission['class_name'] = exam_info.get('classes', {}).get('ten_lop', 'N/A')
                    # Dòng lấy teacher_name đã được xóa
                processed_results.append(submission)
            return processed_results
        except Exception as e:
            st.error(f"❌ Lỗi lấy kết quả thi: {e}")
            print(f"ERROR in get_student_results: {e}")
            return []
    
    def get_exam_by_id(self, exam_id: str) -> Optional[Dict]:
        """Lấy thông tin đề thi theo ID"""
        try:
            result = self.client.table('exams').select('''
                *,
                classes!exams_class_id_fkey (ten_lop)
            ''').eq('id', exam_id).execute()
            
            if result.data:
                exam = result.data[0]
                exam['class_name'] = exam.get('classes', {}).get('ten_lop', 'Unknown')
                
                # Parse questions từ JSON
                if isinstance(exam.get('questions'), str):
                    try:
                        exam['questions'] = json.loads(exam['questions'])
                    except:
                        exam['questions'] = []
                
                return exam
            
            return None
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy thông tin đề thi: {str(e)}")
            return None
    
    # TÌM VÀ THAY THẾ HÀM NÀY:
    def create_exam(self, title: str, description: str, class_id: str,
                    questions: List[Dict], time_limit: int, start_time: str, end_time: str,
                    instructions: str = '') -> Optional[str]:
        """Tạo đề thi mới (không cần teacher_id)"""
        try:
            total_questions = len(questions)
            total_points = sum(q.get('points', 0) for q in questions)
            
            result = self.client.table('exams').insert({
                'title': title,
                'description': description,
                'instructions': instructions,
                'class_id': class_id,
                'questions': json.dumps(questions),
                'time_limit': time_limit,
                'start_time': start_time,
                'end_time': end_time,
                'total_questions': total_questions,
                'total_points': total_points,
                'is_published': False,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            if result.data:
                st.success(f"✅ Tạo đề thi '{title}' thành công")
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            st.error(f"❌ Lỗi tạo đề thi: {str(e)}")
            return None
    # TÌM VÀ THAY THẾ HÀM NÀY:
    def get_all_exams(self) -> List[Dict]:
        """Lấy danh sách TẤT CẢ đề thi trong hệ thống (dành cho Admin)"""
        try:
            result = self.client.table('exams').select('''
                *,
                classes!exams_class_id_fkey (ten_lop)
            ''').execute()
            
            exams = []
            for exam in result.data or []:
                exam['class_name'] = exam.get('classes', {}).get('ten_lop', 'Unknown')
                exam['submission_count'] = len(self.get_submissions_by_exam(exam['id']))
                exams.append(exam)
            
            return exams
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách đề thi: {str(e)}")
            return []
    def update_exam(self, exam_id: str, **kwargs) -> bool:
        """Cập nhật đề thi"""
        try:
            # Loại bỏ các field không được phép cập nhật
            allowed_fields = ['title', 'description', 'instructions', 'questions', 
                            'time_limit', 'start_time', 'end_time', 'is_published']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_data:
                return False
            
            # Nếu cập nhật questions, tính lại total_questions và total_points
            if 'questions' in update_data:
                questions = update_data['questions']
                if isinstance(questions, list):
                    update_data['questions'] = json.dumps(questions)
                    update_data['total_questions'] = len(questions)
                    update_data['total_points'] = sum(q.get('points', 0) for q in questions)
            
            result = self.client.table('exams').update(update_data).eq('id', exam_id).execute()
            
            if result.data:
                st.success("✅ Cập nhật đề thi thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi cập nhật đề thi: {str(e)}")
            return False
    
    def publish_exam(self, exam_id: str) -> bool:
        """Công bố đề thi"""
        try:
            result = self.client.table('exams').update({
                'is_published': True,
                'published_at': datetime.now().isoformat()
            }).eq('id', exam_id).execute()
            
            if result.data:
                st.success("✅ Công bố đề thi thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi công bố đề thi: {str(e)}")
            return False
    
    def delete_exam(self, exam_id: str) -> bool:
        """Xóa đề thi"""
        try:
            # Xóa tất cả submissions trước
            self.client.table('submissions').delete().eq('exam_id', exam_id).execute()
            
            # Xóa đề thi
            result = self.client.table('exams').delete().eq('id', exam_id).execute()
            
            if result.data:
                st.success("✅ Xóa đề thi thành công")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Lỗi xóa đề thi: {str(e)}")
            return False
    
    def get_published_exams_by_class(self, class_id: str) -> List[Dict]:
        """Lấy danh sách đề thi đã publish của một lớp"""
        try:
            result = self.client.table('exams').select('*').eq('class_id', class_id).eq('is_published', True).execute()
            return result.data or []
        except Exception as e:
            st.error(f"❌ Lỗi lấy đề thi: {str(e)}")
            return []
    
    # ==========================================
    # SUBMISSION MANAGEMENT
    # ==========================================
    
    def get_submissions_by_exam(self, exam_id: str) -> List[Dict]:
        """Lấy danh sách bài làm theo đề thi"""
        try:
            result = self.client.table('submissions').select('''
                *,
                users!submissions_student_id_fkey (
                    id, username, ho_ten, email
                )
            ''').eq('exam_id', exam_id).execute()
            
            submissions = []
            for submission in result.data or []:
                submission['student_info'] = submission.get('users', {})
                
                # Parse JSON fields
                for field in ['answers', 'question_scores']:
                    if isinstance(submission.get(field), str):
                        try:
                            submission[field] = json.loads(submission[field])
                        except:
                            submission[field] = [] if field == 'answers' else {}
                
                submissions.append(submission)
            
            return submissions
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách bài làm: {str(e)}")
            return []
    
    def get_submission_by_student_exam(self, student_id: str, exam_id: str) -> Optional[Dict]:
        """Lấy bài làm của học sinh cho một đề thi. Phiên bản an toàn hơn."""
        try:
            response = self.client.table('submissions').select('*').eq('student_id', student_id).eq('exam_id', exam_id).limit(1).execute()
            
            if not response.data:
                return None
            
            submission = response.data[0]
            
            # Parse JSON fields để đảm bảo tính nhất quán
            for field in ['answers', 'question_scores']:
                if isinstance(submission.get(field), str):
                    try:
                        submission[field] = json.loads(submission[field])
                    except json.JSONDecodeError:
                        submission[field] = [] if field == 'answers' else {}
            
            return submission
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy bài làm: {str(e)}")
            return None
    def create_submission(self, exam_id: str, student_id: str, answers: List[Dict],
                     time_taken: int, max_score: float) -> Optional[str]:
        """Tạo bài làm mới (PHIÊN BẢN ĐÃ SỬA)"""
        try:
            # Kiểm tra đã submit chưa
            existing = self.get_submission_by_student_exam(student_id, exam_id)
            
            if existing:
                st.warning("⚠️ Bạn đã nộp bài cho đề thi này rồi")
                return None
            
            # Dữ liệu để chèn vào, bao gồm cả các giá trị mặc định
            submission_data = {
                'exam_id': exam_id,
                'student_id': student_id,
                'answers': json.dumps(answers),
                'time_taken': time_taken,
                'max_score': max_score,
                'is_graded': False,
                'submitted_at': datetime.now().isoformat(),
                'score': 0,  # <-- THÊM DÒNG NÀY: Khởi tạo điểm là 0
                'question_scores': json.dumps({}) # <-- THÊM DÒNG NÀY: Khởi tạo điểm từng câu là JSON rỗng
            }
            
            result = self.client.table('submissions').insert(submission_data).execute()
            
            if result.data:
                st.success("✅ Nộp bài thành công")
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            # Kiểm tra chi tiết lỗi từ Supabase
            if 'violates row-level security policy' in str(e):
                st.error("❌ Lỗi nộp bài: Không có quyền. Vui lòng kiểm tra lại chính sách bảo mật (RLS) trên bảng 'submissions' trong Supabase.")
                st.code(f"Chi tiết: {e}")
            else:
                st.error(f"❌ Lỗi nộp bài: {str(e)}")
            return None
    def create_submission_with_partial_grade(self, exam_id: str, student_id: str, answers: List[Dict], 
                                       time_taken: int, max_score: float, trac_nghiem_score: float, 
                                       question_scores: Dict, has_essay: bool) -> Optional[str]:
        """Tạo bài làm mới và lưu điểm trắc nghiệm đã chấm."""
        try:
            if self.get_submission_by_student_exam(student_id, exam_id):
                st.warning("⚠️ Bạn đã nộp bài cho đề thi này rồi."); return None

            submission_data = {
                'exam_id': exam_id,
                'student_id': student_id,
                'answers': json.dumps(answers),
                'time_taken': time_taken,
                'max_score': max_score,
                'submitted_at': datetime.now().isoformat(),
                'score': trac_nghiem_score,  # Điểm ban đầu là điểm trắc nghiệm
                'trac_nghiem_score': trac_nghiem_score,
                'question_scores': json.dumps(question_scores),
                # Nếu không có tự luận, coi như đã chấm xong hoàn toàn
                'is_graded': not has_essay, 
                'grading_status': 'fully_graded' if not has_essay else 'partially_graded'
            }
            
            result = self.client.table('submissions').insert(submission_data).execute()
            return result.data[0]['id'] if result.data else None
                
        except Exception as e:
            st.error(f"❌ Lỗi tạo bài làm: {str(e)}"); return None
    def update_final_grade(self, submission_id: str, final_score: float, tu_luan_score: float, 
                     question_scores: Dict, feedback: str) -> bool:
        """Cập nhật điểm tự luận và hoàn tất việc chấm bài."""
        try:
            update_data = {
                'score': final_score,
                'tu_luan_score': tu_luan_score,
                'question_scores': json.dumps(question_scores),
                'feedback': feedback,
                'is_graded': True,
                'grading_status': 'fully_graded',
                'graded_at': datetime.now().isoformat()
            }
            result = self.client.table('submissions').update(update_data).eq('id', submission_id).execute()
            return bool(result.data)
        except Exception as e:
            st.error(f"❌ Lỗi cập nhật điểm cuối cùng: {str(e)}"); return False
    def get_submission_by_id(self, submission_id: str) -> Optional[Dict]:
        """
        Lấy thông tin chi tiết một bài nộp bằng ID của chính bài nộp đó.
        """
        try:
            # Sử dụng .single() để đảm bảo chỉ có một kết quả hoặc báo lỗi
            response = self.client.table('submissions').select('*').eq('id', submission_id).single().execute()
            
            submission = response.data
            if not submission:
                return None

            # Parse các trường JSON để đảm bảo chúng là dict/list, không phải string
            # Rất quan trọng cho các bước xử lý sau này
            for field in ['answers', 'question_scores']:
                if submission.get(field) and isinstance(submission[field], str):
                    try: 
                        submission[field] = json.loads(submission[field])
                    except json.JSONDecodeError:
                        # Nếu parse lỗi, trả về giá trị mặc định an toàn
                        submission[field] = [] if field == 'answers' else {}
            
            return submission

        except Exception as e:
            # In lỗi ra console để debug phía server
            print(f"ERROR in get_submission_by_id for ID {submission_id}: {e}")
            # Không cần hiển thị st.error ở đây vì hàm này có thể được gọi ở background
            return None

    def update_submission_grade(self, submission_id: str, total_score: float,
                          question_scores: Dict, feedback: str = '') -> bool:
        """
        Cập nhật điểm cho bài làm sau khi Admin chấm thủ công.
        Hàm này sẽ tính lại điểm thành phần và cập nhật trạng thái.
        PHIÊN BẢN HOÀN CHỈNH CHO KIẾN TRÚC MỚI.
        """
        try:
            # --- BƯỚC 1: Lấy thông tin đề thi để phân loại câu hỏi ---
            exam = self.get_exam_by_submission_id(submission_id)
            if not exam:
                st.error("Lỗi: Không tìm thấy đề thi tương ứng với bài làm.")
                return False

            # --- BƯỚC 2: Tính toán lại điểm thành phần dựa trên kết quả chấm của Admin ---
            trac_nghiem_score = 0
            tu_luan_score = 0
            exam_questions = exam.get('questions', [])

            for q in exam_questions:
                q_id_str = str(q.get('question_id'))
                # Lấy điểm cho câu hỏi này từ `question_scores` do Admin chấm
                score_for_q = question_scores.get(q_id_str, 0)

                if q.get('type') == 'essay':
                    tu_luan_score += score_for_q
                else: # multiple_choice, true_false, short_answer
                    trac_nghiem_score += score_for_q
            
            # --- BƯỚC 3: Chuẩn bị dữ liệu để cập nhật ---
            update_data = {
                'score': total_score, # Điểm tổng kết cuối cùng do Admin quyết định
                'question_scores': json.dumps(question_scores),
                'trac_nghiem_score': trac_nghiem_score, # Cập nhật điểm thành phần đã tính lại
                'tu_luan_score': tu_luan_score,       # Cập nhật điểm thành phần đã tính lại
                'feedback': feedback,
                'is_graded': True, # Đánh dấu là đã chấm xong
                'grading_status': 'fully_graded', # Cập nhật trạng thái cuối cùng
                'graded_at': datetime.now().isoformat()
            }
            
            # --- BƯỚC 4: Thực thi lệnh UPDATE và kiểm tra lỗi ---
            self.client.table('submissions').update(update_data).eq('id', submission_id).execute()
            
            # Nếu không có Exception nào xảy ra, coi như thành công.
            return True
            
        except Exception as e:
            # Bắt lỗi và hiển thị thông báo chi tiết
            # Lỗi RLS (Row-Level Security) cũng sẽ bị bắt ở đây
            if 'violates row-level security policy' in str(e):
                st.error("❌ Lỗi quyền truy cập: Admin không có quyền cập nhật bài nộp. Vui lòng kiểm tra chính sách RLS 'UPDATE' trên bảng 'submissions'.")
            else:
                st.error(f"❌ Lỗi cập nhật điểm trong DB: {str(e)}")
            st.code(e) 
            return False
    def get_exam_by_submission_id(self, submission_id: str) -> Optional[Dict]:
        """
        Lấy thông tin chi tiết của một đề thi từ ID của một bài nộp.
        Hàm này rất hữu ích khi bạn cần thông tin đề thi (như tổng điểm, danh sách câu hỏi)
        trong quá trình chấm một bài làm cụ thể.
        """
        try:
            # Bước 1: Từ submission_id, lấy ra exam_id.
            submission_response = self.client.table('submissions') \
                .select('exam_id') \
                .eq('id', submission_id) \
                .single() \
                .execute()

            if not submission_response.data:
                print(f"Warning: Không tìm thấy submission với ID {submission_id}")
                return None

            exam_id = submission_response.data['exam_id']

            # Bước 2: Từ exam_id, gọi hàm get_exam_by_id đã có sẵn.
            return self.get_exam_by_id(exam_id)

        except Exception as e:
            print(f"ERROR in get_exam_by_submission_id: {e}")
            return None
    def get_submissions_by_student(self, student_id: str) -> List[Dict]:
        """Lấy danh sách bài làm của học sinh"""
        try:
            result = self.client.table('submissions').select('''
                *,
                exams!submissions_exam_id_fkey (
                    title, total_points,
                    classes!exams_class_id_fkey (ten_lop)
                )
            ''').eq('student_id', student_id).execute()
            
            submissions = []
            for submission in result.data or []:
                # Parse JSON fields
                for field in ['answers', 'question_scores']:
                    if isinstance(submission.get(field), str):
                        try:
                            submission[field] = json.loads(submission[field])
                        except:
                            submission[field] = [] if field == 'answers' else {}
                
                # Add exam info
                if submission.get('exams'):
                    exam_info = submission['exams']
                    submission['exam_title'] = exam_info.get('title', 'Unknown')
                    submission['class_name'] = exam_info.get('classes', {}).get('ten_lop', 'Unknown')
                
                submissions.append(submission)
            
            return submissions
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách bài làm: {str(e)}")
            return []
    
    # ==========================================
    # STATISTICS AND DASHBOARD
    # ==========================================
    # Code để copy

    
    # TÌM VÀ THAY THẾ HÀM NÀY:
    def get_dashboard_stats(self) -> Dict:
        """Lấy thống kê dashboard cho toàn hệ thống (dành cho Admin)"""
        try:
            # Số lượng lớp học
            classes = self.get_all_classes()
            class_count = len(classes)
            
            # Tổng số học sinh
            student_count = len(self.get_all_students())
            
            # Số lượng đề thi
            exams = self.get_all_exams()
            exam_count = len(exams)
            
            # Số lượng bài làm
            submission_count = sum(len(self.get_submissions_by_exam(exam['id'])) for exam in exams)
            
            # Số đề thi đã công bố
            published_exams = sum(1 for exam in exams if exam.get('is_published'))
            
            # Số bài chưa chấm
            ungraded_count = 0
            for exam in exams:
                submissions = self.get_submissions_by_exam(exam['id'])
                ungraded_count += sum(1 for sub in submissions if not sub.get('is_graded'))
            
            return {
                'class_count': class_count,
                'student_count': student_count,
                'exam_count': exam_count,
                'submission_count': submission_count,
                'published_exams': published_exams,
                'draft_exams': exam_count - published_exams,
                'ungraded_count': ungraded_count
            }
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy thống kê: {str(e)}")
            return {}
    
    def get_exam_statistics(self, exam_id: str) -> Dict:
        """Lấy thống kê chi tiết cho một đề thi"""
        try:
            submissions = self.get_submissions_by_exam(exam_id)
            
            if not submissions:
                return {
                    'total_submissions': 0,
                    'graded_submissions': 0,
                    'average_score': 0,
                    'highest_score': 0,
                    'lowest_score': 0,
                    'pass_rate': 0
                }
            
            graded_submissions = [s for s in submissions if s.get('is_graded')]
            # SỬA Ở ĐÂY: từ 'total_score' thành 'score'
            scores = [s.get('score', 0) for s in graded_submissions if s.get('score') is not None]
            
            if scores:
                average_score = sum(scores) / len(scores)
                highest_score = max(scores)
                lowest_score = min(scores)
                # Giả sử điểm pass là 50% tổng điểm
                exam = self.get_exam_by_id(exam_id)
                pass_threshold = (exam.get('total_points', 10) * 0.5) if exam else 5
                pass_rate = sum(1 for score in scores if score >= pass_threshold) / len(scores) * 100
            else:
                average_score = highest_score = lowest_score = pass_rate = 0
            
            return {
                'total_submissions': len(submissions),
                'graded_submissions': len(graded_submissions),
                'average_score': round(average_score, 2),
                'highest_score': highest_score,
                'lowest_score': lowest_score,
                'pass_rate': round(pass_rate, 1)
            }
            
        except Exception as e:
            st.error(f"❌ Lỗi lấy thống kê đề thi: {str(e)}")
            return {}
    # ==========================================
    # ADMIN-ONLY METHODS
    # ==========================================
    
    def get_all_users(self) -> List[Dict]:
        """Lấy tất cả người dùng trong hệ thống (chỉ dành cho Admin)."""
        try:
            response = self.client.table('users').select('*').order('created_at', desc=True).execute()
            return response.data or []
        except Exception as e:
            st.error(f"❌ Lỗi lấy danh sách người dùng: {e}")
            return []

    # Trong database/supabase_wrapper.py
    # Trong file database/supabase_wrapper.py, bên trong class SupabaseDatabase

    def get_all_classes(self) -> list:
        """Lấy TẤT CẢ các lớp học, dành cho Admin."""
        try:
            response = self.client.table('classes').select('*').order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            st.error(f"❌ Lỗi khi lấy danh sách tất cả lớp học: {e}")
            return []

    def admin_delete_user(self, user_id: str) -> bool:
        """Admin xóa người dùng ở cả hai nơi."""
        try:
            from config.supabase_config import get_supabase_admin_client
            admin_client = get_supabase_admin_client()
            
            # Bước 1: Xóa user khỏi hệ thống auth.users trước
            # Nếu bước này thất bại, không cần làm gì thêm
            admin_client.auth.admin.delete_user(user_id)
            
            # Bước 2: Xóa user khỏi bảng public.users
            # (Thực tế, bạn có thể thiết lập 'ON DELETE CASCADE' trong DB để bước này tự động)
            self.client.table('users').delete().eq('id', user_id).execute()
            
            st.success("✅ Đã xóa người dùng thành công khỏi hệ thống!")
            return True
        except Exception as e:
            if 'User not found' in str(e):
                st.warning("⚠️ Người dùng không có trong hệ thống xác thực, chỉ xóa khỏi bảng public.")
                # Chỉ xóa khỏi bảng public nếu không tìm thấy trong auth
                self.client.table('users').delete().eq('id', user_id).execute()
                st.success("✅ Đã xóa người dùng (bản ghi cũ) thành công!")
                return True
            else:
                st.error(f"❌ Lỗi xóa người dùng: {e}")
            return False
        # Trong database/supabase_wrapper.py

    def admin_reset_password(self, user_id: str, new_password: str) -> bool:
        """Admin reset mật khẩu cho người dùng."""
        try:
            from config.supabase_config import get_supabase_admin_client
            admin_client = get_supabase_admin_client()

            # Bước 1: Cập nhật trong auth.users
            admin_client.auth.admin.update_user_by_id(user_id, {"password": new_password})
            
            # Bước 2: Cập nhật hash trong public.users bằng admin_client
            new_password_hash = self._hash_password(new_password)
            response = admin_client.table('users').update({
                'password_hash': new_password_hash
            }).eq('id', user_id).execute()

            if response.data:
                st.success("✅ Đã reset mật khẩu thành công!")
                return True
            else:
                st.error("❌ Không thể cập nhật hash mật khẩu trong bảng users.")
                return False
                
        except Exception as e:
            # ... (xử lý lỗi)
            return False
        
    # Database functions using Supabase (UUID VERSION)
    
    # Trong file database/supabase_wrapper.py, bên trong class SupabaseDatabase

    def check_class_code_exists(self, ma_lop: str) -> bool:
        """
        Kiểm tra xem một mã lớp đã tồn tại trong hệ thống chưa.
        Phiên bản đơn giản hóa cho mô hình Admin.
        """
        try:
            # Chỉ cần kiểm tra xem mã lớp đã có trong bảng chưa
            response = self.client.table('classes').select('id').eq('ma_lop', ma_lop).limit(1).execute()
            
            # Nếu có dữ liệu trả về (response.data không rỗng), nghĩa là mã đã tồn tại
            return bool(response.data)
        except Exception as e:
            st.error(f"❌ Lỗi khi kiểm tra mã lớp: {e}")
            # Mặc định trả về True để ngăn tạo trùng lặp nếu có lỗi
            return True
    def update_class_info(class_id: str, ma_lop: str, ten_lop: str, mo_ta: str):
        """Cập nhật thông tin lớp"""
        db = get_database()
        try:
            result = db.client.table('classes').update({
                'ma_lop': ma_lop,
                'ten_lop': ten_lop,
                'mo_ta': mo_ta
            }).eq('id', class_id).execute()
            return True
        except Exception as e:
            st.error(f"Lỗi cập nhật lớp: {e}")
            return False    
    
    def get_class_exam_count(class_id: str):
        """Lấy số lượng đề thi của lớp"""
        db = get_database()
        try:
            result = db.client.table('exams').select('id', count='exact').eq('class_id', class_id).execute()
            return result.count
        except Exception as e:
            return 0
    def get_class_students(class_id: str):
        """Lấy danh sách học sinh trong lớp"""
        db = get_database()
        try:
            # Subquery để lấy thông tin chi tiết học sinh
            result = db.client.table('class_students').select(
                'student_id, users(id, username, ho_ten, email, so_dien_thoai)'
            ).eq('class_id', class_id).execute()
            
            students = []
            for item in result.data:
                student_info = item['users']
                students.append(student_info)
            return students
        except Exception as e:
            st.error(f"Lỗi lấy danh sách học sinh: {e}")
            return []
    # Trong file database/supabase_wrapper.py, bên trong class SupabaseDatabase

    def get_students_not_in_class(self, class_id: str) -> list:
        """
        Lấy danh sách các học sinh trong hệ thống chưa thuộc về một lớp học cụ thể.
        """
        try:
            # Bước 1: Lấy danh sách ID của các học sinh đã có trong lớp.
            existing_students_response = self.client.table('class_students') \
                .select('student_id') \
                .eq('class_id', class_id) \
                .execute()
            
            existing_student_ids = [item['student_id'] for item in existing_students_response.data]

            # Bước 2: Lấy tất cả học sinh trong hệ thống.
            all_students_response = self.client.table('users') \
                .select('id, username, ho_ten, email') \
                .eq('role', 'student') \
                .execute()
            
            if not all_students_response.data:
                return []

            # Bước 3: Lọc ra những học sinh chưa có trong lớp.
            available_students = [
                student for student in all_students_response.data
                if student['id'] not in existing_student_ids
            ]
            
            return available_students

        except Exception as e:
            st.error(f"❌ Lỗi khi lấy danh sách học sinh khả dụng: {e}")
            return []
    def get_exams_by_class(self, class_id: str):
        """Lấy danh sách đề thi theo lớp"""
        # db = get_database()
        try:
            result = self.client.table('exams').select('*').eq('class_id', class_id).execute()
            return result.data or []
        except Exception as e:
            st.error(f"Lỗi lấy danh sách đề thi: {e}")
            return []
            
    def get_exam_status(exam):
        """Lấy trạng thái đề thi"""
        try:
            now = datetime.now(datetime.timezone.utc)
            
            if exam['start_time']:
                start_time = datetime.fromisoformat(exam['start_time'].replace('Z', '+00:00'))
                if now < start_time:
                    return "⏳ Chưa mở"
            
            if exam['end_time']:
                end_time = datetime.fromisoformat(exam['end_time'].replace('Z', '+00:00'))
                if now > end_time:
                    return "🔒 Đã đóng"
            
            return "✅ Đang mở"
        except:
            return "❓ Không xác định"
        
    def remove_student_from_class(self, class_id: str, student_id: str) -> bool:
        """Xóa một học sinh khỏi một lớp học cụ thể."""
        try:
            # Lệnh này sẽ bị kiểm tra bởi RLS Policy
            response = self.client.table('class_students').delete() \
                .eq('class_id', class_id) \
                .eq('student_id', student_id) \
                .execute()
            
            # Kiểm tra xem có dòng nào được xóa không
            if response.data:
                st.success("✅ Đã xóa học sinh khỏi lớp.")
                return True
            else:
                st.warning("⚠️ Không tìm thấy học sinh trong lớp này.")
                return False
        except Exception as e:
            st.error(f"❌ Lỗi khi xóa học sinh khỏi lớp: {e}")
            return False

    def move_student_to_class(self, student_id: str, old_class_id: str, new_class_id: str) -> bool:
        """Chuyển một học sinh từ lớp cũ sang lớp mới."""
        try:
            # Kiểm tra xem học sinh đã ở trong lớp mới chưa
            check_response = self.client.table('class_students') \
                .select('id') \
                .eq('class_id', new_class_id) \
                .eq('student_id', student_id) \
                .execute()
            
            if check_response.data:
                st.warning("⚠️ Học sinh này đã có trong lớp mới.")
                return False

            # Cập nhật bản ghi trong bảng class_students
            response = self.client.table('class_students').update({
                'class_id': new_class_id
            }).eq('student_id', student_id).eq('class_id', old_class_id).execute()

            if response.data:
                st.success("✅ Đã chuyển lớp cho học sinh thành công!")
                return True
            return False
        except Exception as e:
            st.error(f"❌ Lỗi khi chuyển lớp: {e}")
            return False
# Global instance với caching
_db_instance = None

@st.cache_resource
def get_database() -> SupabaseDatabase:
    """Lấy instance database được cache"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDatabase()
    return _db_instance

# Convenience functions
def get_db() -> SupabaseDatabase:
    """Shorthand để lấy database instance"""
    return get_database()