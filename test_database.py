import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config.supabase_config import get_supabase_client
    from database.supabase_models import SupabaseDatabase
    
    print("✅ Import successful!")
    
    # Test database connection
    db = SupabaseDatabase()
    print("✅ Database connection successful!")
    
    # Test create user
    result = db.create_user(
        username="testuser",
        password="testpass",
        ho_ten="Test User",
        email="test@example.com",
        role="student"
    )
    
    if result:
        print("✅ User creation successful!")
    else:
        print("⚠️ User creation failed (may already exist)")
    
    # Test authentication
    user = db.authenticate_user("testuser", "testpass")
    if user:
        print("✅ Authentication successful!")
        print(f"User: {user['ho_ten']} ({user['role']})")
    else:
        print("❌ Authentication failed!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()