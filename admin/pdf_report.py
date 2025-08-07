# File: admin/pdf_report.py

import streamlit as st
from fpdf import FPDF
import base64
import io
from datetime import datetime
from PIL import Image
import os

# --- Class PDF tùy chỉnh ---
class PDFReport(FPDF):
    def __init__(self, exam_title, student_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam_title = exam_title
        self.student_name = student_name
        self.font_path = "assets/fonts/DejaVuSans.ttf"
        
        if not os.path.exists(self.font_path):
            st.error(f"Lỗi: Không tìm thấy font '{self.font_path}'.")
            raise FileNotFoundError("Font file not found for PDF generation.")

        self.add_font("DejaVu", "", self.font_path, uni=True)
        self.add_font("DejaVu", "B", self.font_path, uni=True)
        self.add_font("DejaVu", "I", self.font_path, uni=True)
        
        self.set_font("DejaVu", "", 12)
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
    
    def header(self):
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, 'KẾT QUẢ BÀI LÀM CHI TIẾT', 0, 1, 'C')
        self.set_font("DejaVu", "", 11)
        self.cell(0, 8, f"Đề thi: {self.exam_title}", 0, 1, 'C')
        self.cell(0, 8, f"Học sinh: {self.student_name}", 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f'Trang {self.page_no()}', 0, 0, 'C')
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.set_x(10)
        self.cell(0, 10, f'Xuất lúc: {now}', 0, 0, 'L')

    # <<< HÀM MỚI: Thay thế hoàn toàn multi_cell >>>
    def write_html_like(self, text, h=7):
        """
        In văn bản với khả năng tự động xuống dòng và xử lý từ dài.
        """
        text = str(text) # Đảm bảo đầu vào là string
        
        # Tính toán chiều rộng khả dụng
        available_width = self.w - self.r_margin - self.l_margin
        
        lines = text.split('\n')
        
        for line in lines:
            words = line.split(' ')
            current_line = ''
            for word in words:
                # Xử lý từ quá dài
                word_width = self.get_string_width(word)
                if word_width > available_width:
                    # Chèn ZWSP để giúp ngắt từ
                    temp_word = ""
                    for char in word:
                        if self.get_string_width(temp_word + char) > available_width:
                            self.multi_cell(0, h, temp_word)
                            temp_word = char
                        else:
                            temp_word += char
                    word = temp_word

                # Kiểm tra xem có cần xuống dòng không
                if self.get_string_width(current_line + ' ' + word) < available_width:
                    if current_line:
                        current_line += ' '
                    current_line += word
                else:
                    self.multi_cell(0, h, current_line)
                    current_line = word
            
            # In dòng cuối cùng còn lại
            if current_line:
                self.multi_cell(0, h, current_line)
        self.ln(h / 2) # Thêm một khoảng trống nhỏ sau đoạn văn


    def write_title(self, text):
        self.set_font("DejaVu", "B", 14)
        self.write_html_like(text)
        self.ln(2)

    def write_body(self, text, indent=False):
        self.set_font("DejaVu", "", 11)
        prefix = "    " if indent else ""
        self.write_html_like(f"{prefix}{text}")

    def add_score_summary(self, submission, exam):
        self.write_title("I. Bảng điểm tổng kết")
        tn_score = submission.get('trac_nghiem_score', 0)
        tl_score = submission.get('tu_luan_score', 0)
        total_score = submission.get('score', 0)
        max_score = exam.get('total_points', 0)
        summary_text = (
            f"- Điểm trắc nghiệm: {tn_score or 0:.2f}\n"
            f"- Điểm tự luận: {tl_score or 0:.2f}\n"
            f"- Tổng điểm: {total_score or 0:.2f} / {max_score or 0:.2f}"
        )
        self.write_html_like(summary_text) # Dùng hàm mới
        if submission.get('feedback'):
            self.set_font("DejaVu", "B", 11)
            self.cell(0, 8, "Nhận xét chung:", 0, 1)
            self.write_body(submission['feedback'])
        self.ln(5)
    
    def add_question_detail(self, index, q, student_answer, question_scores):
        q_id_str = str(q.get('question_id'))
        score = question_scores.get(q_id_str, 0)
        points = q.get('points', 0)

        # In câu hỏi
        self.set_font("DejaVu", "B", 12)
        self.write_html_like(f"Câu {index + 1}: ({points} điểm) - Đạt: {score or 0:.2f} điểm")
        self.set_font("DejaVu", "", 11)
        self.write_html_like(q.get('question', ''))
        self.ln(3)

        # In bài làm của học sinh
        self.set_font("DejaVu", "B", 11)
        self.cell(0, 8, "Bài làm của học sinh:", 0, 1)
        if not student_answer:
            self.write_body("Học sinh không trả lời câu này.", indent=True)
        else:
            q_type = q.get('type')
            if q_type == 'multiple_choice': self.write_body(f"Lựa chọn: {student_answer.get('selected_option', 'N/A')}", indent=True)
            elif q_type == 'true_false': self.write_body(f"Lựa chọn: {', '.join(student_answer.get('selected_answers', []))}", indent=True)
            elif q_type == 'short_answer': self.write_body(f"Trả lời: {student_answer.get('answer_text', '')}", indent=True)
            elif q_type == 'essay':
                if student_answer.get('answer_text'): self.write_body(f"Văn bản: {student_answer['answer_text']}", indent=True)
                if student_answer.get('image_data'):
                    try:
                        img_bytes = base64.b64decode(student_answer['image_data'])
                        img = Image.open(io.BytesIO(img_bytes))
                        img_path = f"temp_submission_image_{q_id_str}.png"
                        img.save(img_path)
                        if self.get_y() + 60 > self.page_break_trigger: self.add_page()
                        self.image(img_path, w=100)
                        os.remove(img_path)
                    except Exception as e: self.write_body(f"[Lỗi hiển thị hình ảnh: {e}]", indent=True)
        
        # In đáp án đúng và lời giải
        self.set_font("DejaVu", "B", 11)
        self.cell(0, 8, "Đáp án & Lời giải:", 0, 1)
        if q.get('solution'):
            self.write_body(q['solution'], indent=True)
        else:
            self.write_body("Không có lời giải chi tiết.", indent=True)

        self.line(self.get_x(), self.get_y() + 5, self.get_x() + 190, self.get_y() + 5)
        self.ln(10)

# --- HÀM CHÍNH ĐỂ GỌI TỪ STREAMLIT ---
def generate_pdf_report(exam, submission):
    """Tạo và trả về dữ liệu PDF dưới dạng bytes."""
    if 'pdf_error' in st.session_state: del st.session_state.pdf_error
    try:
        student_name = submission.get('student_info', {}).get('ho_ten', 'N/A')
        pdf = PDFReport(exam.get('title', 'N/A'), student_name)
        
        pdf.add_score_summary(submission, exam)
        
        pdf.write_title("II. Bài làm chi tiết")
        
        student_answers_map = {ans.get('question_id'): ans for ans in submission.get('answers', [])}
        question_scores = submission.get('question_scores', {})
        
        for i, q in enumerate(exam.get('questions', [])):
            q_id = q.get('question_id')
            student_answer = student_answers_map.get(q_id)
            pdf.add_question_detail(i, q, student_answer, question_scores)

        return pdf.output()

    except FileNotFoundError:
        st.session_state.pdf_error = "Lỗi nghiêm trọng: Không tìm thấy file font 'assets/fonts/DejaVuSans.ttf'."
        return None
    except Exception as e:
        error_message = f"Lỗi không xác định khi tạo PDF: {e}"
        st.session_state.pdf_error = error_message
        print(error_message)
        return None