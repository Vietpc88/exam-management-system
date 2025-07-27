import os
import streamlit as st
from typing import Optional

# Supabase imports
try:
    from supabase import create_client, Client
except ImportError:
    st.error("❌ Vui lòng cài đặt: pip install supabase")
    st.stop()

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

class SupabaseConfig:
    """
    Cấu hình Supabase cho hệ thống thi trực tuyến
    """
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        # Kiểm tra biến môi trường
        if not self.supabase_url:
            st.error("❌ Thiếu SUPABASE_URL trong file .env")
            st.info("Vui lòng tạo file .env và thêm: SUPABASE_URL=your_url")
            st.stop()
            
        if not self.supabase_key:
            st.error("❌ Thiếu SUPABASE_KEY trong file .env") 
            st.info("Vui lòng tạo file .env và thêm: SUPABASE_KEY=your_key")
            st.stop()
    
    def get_client(self) -> Client:
        """Tạo và trả về Supabase client"""
        try:
            return create_client(self.supabase_url, self.supabase_key)
        except Exception as e:
            st.error(f"❌ Lỗi kết nối Supabase: {str(e)}")
            st.stop()

# Global instance
_supabase_config = None

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Lấy Supabase client được cache
    Function này được cache để tránh tạo nhiều kết nối
    """
    global _supabase_config
    if _supabase_config is None:
        _supabase_config = SupabaseConfig()
    
    return _supabase_config.get_client()

def test_connection() -> bool:
    """
    Kiểm tra kết nối với Supabase
    Returns: True nếu kết nối thành công, False nếu thất bại
    """
    try:
        client = get_supabase_client()
        # Thử query đơn giản để test kết nối
        result = client.table('users').select('id').limit(1).execute()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi test kết nối database: {str(e)}")
        return False

def get_database_info() -> dict:
    """
    Lấy thông tin về database
    """
    try:
        client = get_supabase_client()
        return {
            "url": client.supabase_url,
            "connected": True
        }
    except Exception as e:
        return {
            "url": None,
            "connected": False,
            "error": str(e)
        }

# Utility functions for common database operations
def execute_query(table: str, operation: str, **kwargs):
    """
    Thực hiện query database một cách an toàn
    
    Args:
        table: Tên bảng
        operation: Loại operation (select, insert, update, delete)
        **kwargs: Các tham số khác
    """
    try:
        client = get_supabase_client()
        table_ref = client.table(table)
        
        if operation == "select":
            columns = kwargs.get("columns", "*")
            query = table_ref.select(columns)
            
            # Thêm filters nếu có
            if "eq" in kwargs:
                for field, value in kwargs["eq"].items():
                    query = query.eq(field, value)
            
            if "limit" in kwargs:
                query = query.limit(kwargs["limit"])
                
            return query.execute()
            
        elif operation == "insert":
            data = kwargs.get("data", {})
            return table_ref.insert(data).execute()
            
        elif operation == "update":
            data = kwargs.get("data", {})
            query = table_ref.update(data)
            
            if "eq" in kwargs:
                for field, value in kwargs["eq"].items():
                    query = query.eq(field, value)
                    
            return query.execute()
            
        elif operation == "delete":
            query = table_ref.delete()
            
            if "eq" in kwargs:
                for field, value in kwargs["eq"].items():
                    query = query.eq(field, value)
                    
            return query.execute()
            
    except Exception as e:
        st.error(f"❌ Lỗi thực hiện query: {str(e)}")
        return None