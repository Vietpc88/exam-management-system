import os
import streamlit as st
from typing import Optional

# Supabase imports
try:
    from supabase import create_client, Client
except ImportError:
    st.error("❌ Vui lòng cài đặt: pip install supabase")
    st.info("Chạy lệnh: `pip install supabase>=2.0.0`")
    st.stop()

class SupabaseConfig:
    """
    Cấu hình Supabase cho hệ thống thi trực tuyến
    Hỗ trợ cả local development và cloud deployment
    """
    
    def __init__(self):
        # Ưu tiên Streamlit secrets (cho cloud), fallback về environment variables (cho local)
        self.supabase_url = self._get_config("SUPABASE_URL")
        self.supabase_key = self._get_config("SUPABASE_KEY")
        
        # Validate configuration
        if not self.supabase_url:
            self._show_config_error("SUPABASE_URL")
            
        if not self.supabase_key:
            self._show_config_error("SUPABASE_KEY")
    
    def _get_config(self, key: str) -> Optional[str]:
        """Lấy config từ Streamlit secrets hoặc environment variables"""
        # Thử Streamlit secrets trước (cho deployment)
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except:
            pass
        
        # Fallback về environment variables (cho local development)
        return os.getenv(key)
    
    def _show_config_error(self, missing_key: str):
        """Hiển thị lỗi cấu hình với hướng dẫn chi tiết"""
        st.error(f"❌ Thiếu cấu hình: {missing_key}")
        
        st.markdown("### 🔧 Cách khắc phục:")
        
        # Hướng dẫn cho local development
        with st.expander("💻 Chạy Local (Development)"):
            st.markdown("""
            **Tạo file `.env` trong thư mục gốc:**
            ```env
            SUPABASE_URL=https://your-project.supabase.co
            SUPABASE_KEY=your-anon-key-here
            SUPABASE_SERVICE_KEY=your-service-role-key-here
            ```
            
            **Sau đó cài đặt python-dotenv:**
            ```bash
            pip install python-dotenv
            ```
            """)
        
        # Hướng dẫn cho Streamlit Cloud
        with st.expander("☁️ Deploy Streamlit Cloud"):
            st.markdown("""
            **Thêm vào `.streamlit/secrets.toml`:**
            ```toml
            SUPABASE_URL = "https://your-project.supabase.co"
            SUPABASE_KEY = "your-anon-key-here"
            SUPABASE_SERVICE_KEY = "your-service-role-key-here"
            ```
            
            **Hoặc cấu hình trong Streamlit Cloud Dashboard:**
            1. Vào App settings
            2. Secrets tab
            3. Thêm secrets theo format TOML
            """)
        
        # Hướng dẫn lấy thông tin Supabase
        with st.expander("📋 Lấy thông tin Supabase"):
            st.markdown("""
            1. Đăng nhập vào [https://supabase.com](https://supabase.com)
            2. Chọn dự án của bạn
            3. Vào **Settings** → **API**
            4. Copy **URL**, **anon/public key**, và **service_role key**
            5. Dán vào cấu hình theo hướng dẫn trên
            """)
        
        st.stop()
    
    def get_client(self) -> Client:
        """Tạo và trả về Supabase client"""
        try:
            client = create_client(self.supabase_url, self.supabase_key)
            return client
        except Exception as e:
            st.error(f"❌ Lỗi kết nối Supabase: {str(e)}")
            st.info("Kiểm tra lại URL và KEY trong cấu hình")
            st.stop()

# Global instance
_supabase_config = None

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Lấy Supabase client được cache
    Function này được cache để tránh tạo nhiều kết nối
    
    Returns:
        Client: Supabase client instance
    """
    global _supabase_config
    if _supabase_config is None:
        _supabase_config = SupabaseConfig()
    
    return _supabase_config.get_client()

# =======================================================
# =========== THÊM HÀM MỚI VÀO ĐÂY ======================
# =======================================================
@st.cache_resource
def get_supabase_admin_client() -> Client:
    """
    Lấy Supabase client với quyền admin (service_role key).
    Dùng cho các tác vụ backend, bỏ qua RLS.
    
    Returns:
        Client: Supabase client instance với quyền admin.
    """
    global _supabase_config
    if _supabase_config is None:
        _supabase_config = SupabaseConfig()

    # Lấy service key từ config
    service_key = _supabase_config._get_config("SUPABASE_SERVICE_KEY")

    if not service_key:
        _supabase_config._show_config_error("SUPABASE_SERVICE_KEY")

    # Tạo client với service key
    try:
        admin_client = create_client(_supabase_config.supabase_url, service_key)
        return admin_client
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Supabase với quyền Admin: {str(e)}")
        st.info("Kiểm tra lại SUPABASE_SERVICE_KEY trong cấu hình của bạn.")
        st.stop()
# =======================================================
# =======================================================

def test_connection() -> bool:
    """
    Kiểm tra kết nối với Supabase
    
    Returns:
        bool: True nếu kết nối thành công, False nếu thất bại
    """
    try:
        client = get_supabase_client()
        # Thử query đơn giản để test kết nối
        result = client.table('users').select('id').limit(1).execute()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi test kết nối database: {str(e)}")
        
        # Gợi ý debug
        with st.expander("🔍 Debug Info"):
            st.write("**Lỗi chi tiết:**", str(e))
            st.write("**Có thể do:**")
            st.write("- URL hoặc KEY không đúng")
            st.write("- Bảng 'users' chưa được tạo")
            st.write("- Quyền truy cập database bị hạn chế")
            st.write("- Kết nối mạng không ổn định")
        
        return False

def get_database_info() -> dict:
    """
    Lấy thông tin về database connection
    
    Returns:
        dict: Thông tin database
    """
    try:
        client = get_supabase_client()
        return {
            "url": client.supabase_url,
            "connected": True,
            "status": "✅ Kết nối thành công"
        }
    except Exception as e:
        return {
            "url": None,
            "connected": False,
            "status": f"❌ Lỗi: {str(e)}"
        }

# Load environment variables nếu chạy local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv không bắt buộc, chỉ cần cho local development
    pass