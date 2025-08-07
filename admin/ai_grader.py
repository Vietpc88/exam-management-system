import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64
import json
import re

def get_gemini_model():
    """
    Hàm trợ giúp để khởi tạo và trả về model Gemini.
    Nó chỉ được gọi khi thực sự cần chấm điểm.
    """
    try:
        api_key = st.secrets["google_ai"]["api_key"]
        genai.configure(api_key=api_key)
        # Sử dụng model có khả năng xử lý cả text và image
        model = genai.GenerativeModel('gemini-2.5-pro')
        return model
    except Exception as e:
        # Hiển thị lỗi một cách an toàn nếu không có key
        st.error(f"Lỗi cấu hình Gemini API: {e}. Vui lòng kiểm tra file secrets.toml.")
        return None

def grade_essay_with_ai(question_text: str, grading_rubric: str, max_score: float, student_answer_text: str, student_image_base64: str = None):
    """
    Chấm một câu hỏi tự luận bằng Gemini AI.

    Args:
        question_text: Nội dung câu hỏi.
        grading_rubric: Tiêu chí chấm điểm do giáo viên cung cấp.
        max_score: Điểm tối đa cho câu hỏi.
        student_answer_text: Phần trả lời bằng văn bản của học sinh.
        student_image_base64: Phần trả lời bằng hình ảnh của học sinh (dạng base64).

    Returns:
        Một dictionary chứa 'suggested_score' và 'feedback'.
    """
    model = get_gemini_model()
    if not model:
        return {
            'suggested_score': 0.0,
            'feedback': "Lỗi: Không thể kết nối đến dịch vụ AI Grader."
        }

    try:
        # Xây dựng prompt cho AI
        prompt_parts = [
            "Bạn là một trợ lý giáo dục chuyên nghiệp, nhiệm vụ của bạn là chấm bài thi tự luận một cách công bằng và chi tiết. Hãy dựa vào các thông tin sau:",
            f"\n--- ĐỀ BÀI ---\n{question_text}",
            f"\n--- TIÊU CHÍ CHẤM ĐIỂM (RUBRIC) ---\n{grading_rubric}",
            f"\n--- THANG ĐIỂM TỐI ĐA ---\n{max_score} điểm.",
            "\n--- BÀI LÀM CỦA HỌC SINH ---"
        ]

        # Thêm phần bài làm của học sinh (text và/hoặc image)
        has_content = False
        if student_answer_text and student_answer_text.strip():
            prompt_parts.append(f"Phần trả lời bằng văn bản:\n{student_answer_text}")
            has_content = True
        
        if student_image_base64:
            try:
                # Chuyển đổi base64 thành đối tượng Image của PIL
                image_bytes = base64.b64decode(student_image_base64)
                img = Image.open(io.BytesIO(image_bytes))
                prompt_parts.append("\nPhần trả lời bằng hình ảnh:")
                prompt_parts.append(img)
                has_content = True
            except Exception as img_e:
                return {
                    'suggested_score': 0.0,
                    'feedback': f"Lỗi xử lý hình ảnh của học sinh: {img_e}"
                }

        if not has_content:
            return {
                'suggested_score': 0.0,
                'feedback': "Học sinh không nộp bài làm cho câu này."
            }

        # Thêm yêu cầu cuối cùng cho AI
        prompt_parts.append(
            "\n--- YÊU CẦU ---\n"
            "Dựa vào đề bài và tiêu chí chấm điểm, hãy phân tích bài làm của học sinh và trả về kết quả dưới dạng JSON chính xác theo cấu trúc sau:\n"
            "{\n"
            '  "diem_de_xuat": [một số thập phân, ví dụ: 3.5],\n'
            '  "nhan_xet_chi_tiet": "[một chuỗi văn bản nhận xét chi tiết, chỉ ra điểm mạnh, điểm yếu và góp ý cho học sinh]"\n'
            "}\n"
            "Lưu ý: Chỉ trả về đối tượng JSON, không thêm bất kỳ văn bản nào khác."
        )

        # Gọi API của Gemini
        with st.spinner("🤖 AI đang phân tích và chấm điểm..."):
            response = model.generate_content(prompt_parts)
            
            # Xử lý kết quả trả về
            # Gemini có thể trả về text có chứa ```json ... ```, cần trích xuất nó ra
            import json
            import re
            
            # Tìm khối JSON trong response text
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.text, re.DOTALL)
            if json_match:
                json_string = json_match.group(1)
            else:
                # Nếu không có ```json```, giả sử toàn bộ text là JSON
                json_string = response.text

            result_json = json.loads(json_string)
            
            score = float(result_json.get("diem_de_xuat", 0.0))
            feedback = result_json.get("nhan_xet_chi_tiet", "AI không cung cấp nhận xét.")
            
            # Đảm bảo điểm không vượt quá thang điểm
            if score > max_score:
                score = max_score
            if score < 0:
                score = 0

            return {
                'suggested_score': score,
                'feedback': feedback
            }

    except Exception as e:
        st.error(f"Lỗi khi gọi AI Grader: {e}")
        return {
            'suggested_score': 0.0,
            'feedback': f"Đã xảy ra lỗi trong quá trình chấm bằng AI: {e}"
        }