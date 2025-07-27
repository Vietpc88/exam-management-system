import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_models import SupabaseDatabase

def create_admin_user():
    """Tạo tài khoản admin"""
    db = SupabaseDatabase()
    
    print("🔄 Creating admin user...")
    
    # Tạo admin với mật khẩu admin123
    result = db.create_user(
        username="admin",
        password="admin123",  # Sẽ được hash tự động
        ho_ten="Quản trị viên",
        email="admin@example.com",
        role="admin"
    )
    
    if result:
        print("✅ Admin user created successfully!")
        
        # Test đăng nhập
        print("🔄 Testing admin login...")
        user = db.authenticate_user("admin", "admin123")
        
        if user:
            print("✅ Admin login test successful!")
            print(f"User info: {user['ho_ten']} ({user['role']})")
        else:
            print("❌ Admin login test failed!")
            
    else:
        print("❌ Failed to create admin user (may already exist)")
        
        # Thử đăng nhập để kiểm tra
        print("🔄 Testing existing admin...")
        user = db.authenticate_user("admin", "admin123")
        
        if user:
            print("✅ Existing admin login successful!")
        else:
            print("❌ Admin login failed - wrong password?")

if __name__ == "__main__":
    create_admin_user()