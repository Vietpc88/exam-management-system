import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    print("🔍 Testing Supabase connection...")
    
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    print(f"URL: {url}")
    print(f"Anon Key: {anon_key[:30]}...")
    print(f"Service Key: {service_key[:30]}...")
    
    try:
        # Test với anon key
        print("\n🔄 Testing anon client...")
        anon_client = create_client(url, anon_key)
        
        # Test simple query
        result = anon_client.table('users').select('count').execute()
        print("✅ Anon client connection successful!")
        
        # Test với service key
        print("\n🔄 Testing service client...")
        service_client = create_client(url, service_key)
        
        result2 = service_client.table('users').select('count').execute()
        print("✅ Service client connection successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase_connection()