# File: create_first_admin.py
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_wrapper import SupabaseDatabase

def run():
    """Tạo tài khoản Admin đầu tiên một cách hoàn chỉnh."""
    print("Đang khởi tạo kết nối database...")
    db = SupabaseDatabase()
    print("Kết nối thành công.")
    
    ADMIN_EMAIL = "vietboy113@gmail.com"
    ADMIN_PASSWORD = "Khang@12" # <-- ĐẶT MỘT MẬT KHẨU MỚI Ở ĐÂY
    ADMIN_USERNAME = "admin"
    ADMIN_HO_TEN = "Quản trị viên"

    print(f"Đang thử tạo admin với email: {ADMIN_EMAIL}")

    # Bước 1: Tạo user trong hệ thống auth và kích hoạt trigger
    from config.supabase_config import get_supabase_admin_client
    admin_client = get_supabase_admin_client()
    
    try:
        auth_response = admin_client.auth.admin.create_user({
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "email_confirm": True,
        })
        new_user = auth_response.user
        if not new_user:
            print("❌ Lỗi: Không nhận được thông tin user sau khi tạo trong auth.")
            return
        
        print(f"✅ Đã tạo user trong AUTH thành công. User ID: {new_user.id}")
        print("Trigger المفروض أن يتم تفعيله الآن...")

    except Exception as e:
        if "already exists" in str(e):
            print("⚠️ User đã tồn tại trong Auth. Đang thử lấy thông tin...")
            response = admin_client.auth.admin.list_users()
            found_user = next((u for u in response.users if u.email == ADMIN_EMAIL), None)
            if not found_user:
                print(f"❌ Không tìm thấy user với email {ADMIN_EMAIL} trong Auth.")
                return
            new_user = found_user
            print(f"✅ Đã tìm thấy User trong Auth. User ID: {new_user.id}")
        else:
            print(f"❌ Lỗi khi tạo user trong Auth: {e}")
            return

    # Bước 2: Cập nhật thông tin chi tiết vào bảng public.users
    print("Đang cập nhật thông tin chi tiết trong bảng public.users...")
    try:
        # SỬ DỤNG admin_client ĐỂ CÓ QUYỀN UPDATE
        update_response = admin_client.table('users').update({
            "username": ADMIN_USERNAME,
            "ho_ten": ADMIN_HO_TEN,
            "role": "admin", # <-- ĐỔI ROLE THÀNH ADMIN
            "is_active": True,
            "password_hash": db._hash_password(ADMIN_PASSWORD)
        }).eq('id', new_user.id).execute()

        # Dữ liệu trả về từ lệnh update có thể khác nhau, kiểm tra cẩn thận hơn
        if update_response.data or getattr(update_response, 'count', 0) > 0:
            print("✅✅✅ TẠO ADMIN HOÀN CHỈNH THÀNH CÔNG! ✅✅✅")
            print("Bây giờ bạn có thể đăng nhập bằng tài khoản này.")
        else:
            print("❌ Lỗi: Cập nhật bảng public.users thất bại.")
            print("Hãy kiểm tra lại RLS Policy và quyền của service_role.")
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật bảng public.users: {e}")
if __name__ == "__main__":
    run()