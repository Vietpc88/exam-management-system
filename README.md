# 🎓 Hệ thống Thi Trực tuyến

Hệ thống quản lý thi trực tuyến được xây dựng bằng Streamlit, hỗ trợ tạo đề thi, quản lý học sinh và chấm bài tự động.

## ✨ Tính năng chính

### 👨‍🏫 Dành cho Giáo viên
- 📋 Quản lý lớp học
- 👥 Quản lý học sinh (tạo từng cái hoặc import Excel hàng loạt)
- 📝 Tạo đề thi đa dạng (trắc nghiệm, đúng/sai, tự luận)
- ✅ Chấm bài tự động bằng AI
- 📊 Thống kê và báo cáo chi tiết

### 👨‍🎓 Dành cho Học sinh
- 📚 Xem lớp học đã tham gia
- 📝 Làm bài thi trực tuyến
- 📊 Xem kết quả và nhận xét
- 🔒 Bảo mật thông tin cá nhân

### 🤖 Tính năng AI
- Chấm bài tự luận tự động bằng Google Gemini
- Đưa ra nhận xét và gợi ý cải thiện
- Hỗ trợ chấm ảnh bài viết tay

## 🚀 Demo

🌐 **Live Demo**: [https://exam-system.streamlit.app](https://exam-system.streamlit.app)

**Tài khoản demo:**
- Giáo viên: `admin` / `admin123`
- Học sinh: Đăng ký tại giao diện

## 🛠️ Cài đặt Local

### Yêu cầu
- Python 3.8+
- pip

### Cài đặt
```bash
# Clone repository
git clone https://github.com/[username]/exam-management-system.git
cd exam-management-system

# Cài đặt dependencies
pip install -r requirements.txt

# Khởi tạo database
python database/db_setup.py

# Chạy ứng dụng
streamlit run app.py
```

### Cấu hình
1. Copy file `.streamlit/secrets.toml.example` thành `.streamlit/secrets.toml`
2. Điền các API keys cần thiết:
```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "your_secure_password"
```

## 📁 Cấu trúc dự án

```
exam_system/
├── app.py                 # Ứng dụng chính
├── config.py              # Cấu hình
├── requirements.txt       # Dependencies
├── README.md             # Tài liệu
├── .gitignore            # Git ignore
├── database/             # Quản lý database
│   ├── db_setup.py      # Khởi tạo database
│   ├── models.py        # Models và queries
│   └── production_setup.py # Setup production
├── auth/                 # Xác thực
│   └── login.py         # Đăng nhập
├── teacher/              # Giao diện giáo viên
│   └── create_exam.py   # Dashboard giáo viên
├── student/              # Giao diện học sinh
│   └── take_exam.py     # Dashboard học sinh
├── grading/              # Chấm bài
│   ├── auto_grade.py    # Chấm tự động
│   └── gemini_api.py    # Tích hợp Gemini
├── uploads/              # File uploads
├── .streamlit/           # Cấu hình Streamlit
│   ├── config.toml      # UI config
│   └── secrets.toml     # API keys (không commit)
```

## 🔧 Deploy Production

### Streamlit Cloud (Miễn phí)
1. Push code lên GitHub
2. Truy cập [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repo
4. Cấu hình secrets trong App settings
5. Deploy!

### Railway
```bash
npm install -g @railway/cli
railway login
railway init
railway add --service postgresql
railway deploy
```

### Heroku
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

## 📊 API Documentation

### Database Schema
- **users**: Thông tin người dùng
- **classes**: Lớp học
- **class_students**: Học sinh trong lớp
- **exams**: Đề thi
- **submissions**: Bài làm
- **question_scores**: Điểm từng câu

### Import Excel Format
| ho_ten | username | mat_khau | email | so_dien_thoai |
|--------|----------|----------|-------|---------------|
| Nguyễn Văn A | nguyenvana | 123456 | email@domain.com | 0123456789 |

## 🛡️ Bảo mật

- ✅ Hash password bằng bcrypt
- ✅ Session timeout
- ✅ Input validation
- ✅ SQL injection protection
- ✅ File upload restrictions

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Tạo Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 👨‍💻 Tác giả

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@domain.com

## 🙏 Cảm ơn

- [Streamlit](https://streamlit.io/) - Framework web app
- [Google Gemini](https://ai.google.dev/) - AI chấm bài
- [SQLite](https://sqlite.org/) - Database
- [bcrypt](https://github.com/pyca/bcrypt/) - Password hashing

---

⭐ **Nếu project hữu ích, hãy cho một star nhé!** ⭐