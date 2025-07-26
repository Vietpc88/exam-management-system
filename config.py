import os
import streamlit as st

class Config:
    # Database settings
    DATABASE_PATH = "exam_system.db"
    
    # Gemini API settings - ưu tiên Streamlit secrets
    try:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    except:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
    
    # File upload settings
    UPLOAD_FOLDER = "uploads/images"
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session settings
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    
    # Default admin credentials - ưu tiên Streamlit secrets
    try:
        DEFAULT_ADMIN_USERNAME = st.secrets.get("DEFAULT_ADMIN_USERNAME", "admin")
        DEFAULT_ADMIN_PASSWORD = st.secrets.get("DEFAULT_ADMIN_PASSWORD", "admin123")
    except:
        DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS