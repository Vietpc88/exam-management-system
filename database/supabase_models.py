# Nội dung cuối cùng cho file: database/supabase_models.py

import streamlit as st
from .supabase_wrapper import SupabaseDatabase

_db_instance = None

@st.cache_resource
def get_database() -> SupabaseDatabase:
    """
    Tạo và trả về một instance duy nhất của SupabaseDatabase.
    Được cache bởi Streamlit để đảm bảo chỉ có một kết nối được tạo.
    """
    global _db_instance
    if _db_instance is None:
        try:
            _db_instance = SupabaseDatabase()
        except Exception as e:
            st.error(f"❌ Lỗi nghiêm trọng khi khởi tạo Database: {e}")
            st.info("Vui lòng kiểm tra lại cấu hình trong file .env và kết nối mạng.")
            st.stop()
    return _db_instance

def get_db() -> SupabaseDatabase:
    """Hàm tiện ích để lấy database instance."""
    return get_database()