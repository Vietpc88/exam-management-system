import os
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

def get_supabase_config():
    """Lấy config từ Streamlit secrets hoặc environment variables"""
    try:
        # Thử lấy từ Streamlit secrets trước
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["anon_key"]
        supabase_service_key = st.secrets["supabase"]["service_key"]
    except:
        # Fallback sang environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    return supabase_url, supabase_key, supabase_service_key

def get_supabase_client() -> Client:
    """Tạo Supabase client"""
    url, key, _ = get_supabase_config()
    if not url or not key:
        raise ValueError("Missing Supabase URL or API Key")
    return create_client(url, key)

def get_supabase_admin_client() -> Client:
    """Tạo Supabase admin client với service role key"""
    url, _, service_key = get_supabase_config()
    if not url or not service_key:
        raise ValueError("Missing Supabase URL or Service Key")
    return create_client(url, service_key)