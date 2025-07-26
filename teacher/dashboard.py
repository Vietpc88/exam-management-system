import os
from supabase import create_client, Client
import streamlit as st

def get_supabase_client() -> Client:
    """
    Khởi tạo Supabase client với thông tin từ Streamlit secrets hoặc environment variables
    
    Cấu hình trong .streamlit/secrets.toml:
    [supabase]
    url = "your-supabase-url"
    key = "your-supabase-anon-key"
    """
    try:
        # Try to get from Streamlit secrets first
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            supabase_config = st.secrets.supabase
            url = supabase_config.get('url')
            key = supabase_config.get('key')
        else:
            # Fallback to environment variables
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            st.error("❌ **Thiếu cấu hình Supabase!**")
            st.error("🔧 **Hướng dẫn khắc phục:**")
            st.code("""
# Tạo file .streamlit/secrets.toml với nội dung:

[supabase]
url = "https://your-project.supabase.co"
key = "eyJhbGciOiJIUzI1NiIs..."

# Lấy thông tin tại: Supabase Dashboard > Settings > API
            """)
            raise ValueError("Supabase URL and key must be provided in .streamlit/secrets.toml")
        
        supabase: Client = create_client(url, key)
        return supabase
    
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Supabase: {str(e)}")
        st.error("🔧 Vui lòng kiểm tra cấu hình Supabase trong .streamlit/secrets.toml")
        
        # Show detailed error for debugging
        with st.expander("🐛 Chi tiết lỗi", expanded=False):
            st.error(f"**Chi tiết:** {str(e)}")
            st.info("**Kiểm tra:**")
            st.write("1. File `.streamlit/secrets.toml` có tồn tại?")
            st.write("2. Cấu trúc `[supabase]` section đúng chưa?")
            st.write("3. URL và key có chính xác không?")
        
        st.stop()

def get_supabase_admin_client() -> Client:
    """
    Khởi tạo Supabase admin client với service role key (cho các thao tác admin)
    
    Cấu hình trong .streamlit/secrets.toml:
    [supabase]
    url = "your-supabase-url"
    service_role_key = "your-supabase-service-role-key"
    """
    try:
        # Try to get from Streamlit secrets first
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            supabase_config = st.secrets.supabase
            url = supabase_config.get('url')
            service_key = supabase_config.get('service_role_key', supabase_config.get('key'))
        else:
            # Fallback to environment variables
            url = os.getenv('SUPABASE_URL')
            service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_ANON_KEY'))
        
        if not url or not service_key:
            # For admin operations, fall back to regular client
            return get_supabase_client()
        
        supabase: Client = create_client(url, service_key)
        return supabase
    
    except Exception as e:
        # For admin operations, we can fall back to regular client
        return get_supabase_client()

def test_connection():
    """Test kết nối Supabase"""
    try:
        client = get_supabase_client()
        
        # Test simple query
        result = client.table('users').select('id').limit(1).execute()
        
        return True, "Kết nối Supabase thành công!"
    
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"

def validate_secrets():
    """Validate Supabase configuration"""
    try:
        if not hasattr(st, 'secrets'):
            return False, "Streamlit secrets không được cấu hình"
        
        if 'supabase' not in st.secrets:
            return False, "Thiếu section [supabase] trong secrets.toml"
        
        supabase_config = st.secrets.supabase
        
        required_keys = ['url', 'key']
        missing_keys = [key for key in required_keys if not supabase_config.get(key)]
        
        if missing_keys:
            return False, f"Thiếu các key: {', '.join(missing_keys)}"
        
        # Validate URL format
        url = supabase_config.get('url')
        if not url.startswith('https://') or '.supabase.co' not in url:
            return False, "URL Supabase không đúng định dạng"
        
        # Validate key format (should be JWT)
        key = supabase_config.get('key')
        if not key.startswith('eyJ'):
            return False, "API key không đúng định dạng JWT"
        
        return True, "Cấu hình hợp lệ"
    
    except Exception as e:
        return False, f"Lỗi validate: {str(e)}"

# Constants
DATABASE_TABLES = {
    'users': 'Bảng người dùng (giáo viên, học sinh)',
    'classes': 'Bảng lớp học',
    'class_students': 'Bảng quan hệ lớp-học sinh',
    'exams': 'Bảng đề thi',
    'submissions': 'Bảng bài làm',
    'import_logs': 'Bảng log import'
}

def get_database_info():
    """Lấy thông tin database"""
    return {
        'tables': DATABASE_TABLES,
        'connection_status': test_connection(),
        'config_status': validate_secrets()
    }