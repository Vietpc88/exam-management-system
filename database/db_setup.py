import sqlite3
import hashlib
import bcrypt
import sys
import os
from datetime import datetime

# Thêm thư mục gốc vào Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_database():
    """Khởi tạo database và các bảng"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Bảng users (giáo viên và học sinh)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Bảng classes (lớp học)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            teacher_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    ''')
    
    # Bảng class_students (học sinh trong lớp)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS class_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            UNIQUE(class_id, student_id)
        )
    ''')
    
    # Bảng exams (đề thi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            class_id INTEGER NOT NULL,
            questions TEXT NOT NULL, -- JSON string
            time_limit INTEGER DEFAULT 60, -- phút
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (class_id) REFERENCES classes (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Bảng submissions (bài làm của học sinh)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            answers TEXT NOT NULL, -- JSON string
            images TEXT, -- JSON string chứa đường dẫn ảnh
            total_score REAL DEFAULT 0,
            max_score REAL DEFAULT 0,
            feedback TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            graded_at TIMESTAMP,
            graded_by INTEGER,
            is_graded BOOLEAN DEFAULT 0,
            FOREIGN KEY (exam_id) REFERENCES exams (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (graded_by) REFERENCES users (id),
            UNIQUE(exam_id, student_id)
        )
    ''')
    
    # Bảng question_scores (điểm từng câu)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            question_index INTEGER NOT NULL,
            score REAL DEFAULT 0,
            max_score REAL DEFAULT 0,
            feedback TEXT,
            is_correct BOOLEAN,
            FOREIGN KEY (submission_id) REFERENCES submissions (id)
        )
    ''')
    
    conn.commit()
    
    # Tạo tài khoản admin mặc định
    create_default_admin(cursor)
    
    conn.commit()
    conn.close()
    
    print("✅ Database đã được khởi tạo thành công!")

def create_default_admin(cursor):
    """Tạo tài khoản admin mặc định"""
    admin_password_hash = hash_password(Config.DEFAULT_ADMIN_PASSWORD)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, 'teacher', 'Administrator', 'admin@school.edu.vn')
        ''', (Config.DEFAULT_ADMIN_USERNAME, admin_password_hash))
        print(f"✅ Tạo tài khoản admin: {Config.DEFAULT_ADMIN_USERNAME}/{Config.DEFAULT_ADMIN_PASSWORD}")
    except sqlite3.IntegrityError:
        print("ℹ️ Tài khoản admin đã tồn tại")

def reset_database():
    """Reset toàn bộ database (Cẩn thận!)"""
    import os
    if os.path.exists(Config.DATABASE_PATH):
        os.remove(Config.DATABASE_PATH)
        print("🗑️ Đã xóa database cũ")
    init_database()

if __name__ == "__main__":
    # Chạy file này để khởi tạo database
    init_database()