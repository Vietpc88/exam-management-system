import re
import mammoth
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import io
import base64
from PIL import Image
import json

class WordExamParser:
    """Class phân tích đề thi từ file Word với ánh xạ hình ảnh chính xác"""
    
    def __init__(self):
        self.questions = []
        self.errors = []
        self.warnings = []
        self.images = {}
        self.image_positions = {}  # Lưu vị trí hình ảnh trong HTML
        self.raw_questions_data = []
    
    def parse_docx_file(self, uploaded_file) -> Dict[str, Any]:
        """Phân tích file .docx với xử lý hình ảnh chính xác"""
        try:
            # Reset
            self.questions = []
            self.errors = []
            self.warnings = []
            self.images = {}
            self.image_positions = {}
            self.raw_questions_data = []
            
            # Extract text và HTML để lấy cả hình ảnh
            raw_result = mammoth.extract_raw_text(uploaded_file)
            text_content = raw_result.value
            
            # Reset file pointer và extract HTML với hình ảnh
            uploaded_file.seek(0)
            html_result = mammoth.convert_to_html(
                uploaded_file,
                convert_image=mammoth.images.img_element(self._extract_image_with_position)
            )
            html_content = html_result.value
            
            # Phân tích vị trí hình ảnh trong HTML
            self._analyze_image_positions(html_content)
            
            # Debug mode
            if st.checkbox("🔍 Debug Mode - Xem nội dung file", key="debug_content"):
                with st.expander("📝 Raw Text Content", expanded=False):
                    st.text_area("Raw text:", text_content, height=200)
                
                with st.expander("🌐 HTML Content", expanded=False):
                    st.text_area("HTML:", html_content, height=200)
                
                # Debug hình ảnh và vị trí
                if self.images:
                    with st.expander("🖼️ Images Found", expanded=False):
                        for img_key, img_data in self.images.items():
                            position_info = self.image_positions.get(img_key, "Không xác định")
                            st.write(f"**{img_key}:** {img_data['size']} bytes, {img_data['content_type']}")
                            st.write(f"**Vị trí ước tính:** Câu {position_info}")
                            try:
                                img_bytes = base64.b64decode(img_data['data'])
                                img = Image.open(io.BytesIO(img_bytes))
                                st.image(img, caption=f"{img_key} - Câu {position_info}", width=200)
                            except Exception as e:
                                st.error(f"Lỗi hiển thị {img_key}: {e}")
            
            # Parse theo logic đã sửa lỗi
            self.questions = self._parse_questions_by_sections(text_content, html_content)
            
            # Tạo bảng dữ liệu chuẩn
            self._create_questions_dataframe()
            
            return {
                'success': True,
                'questions': self.questions,
                'raw_data': self.raw_questions_data,
                'errors': self.errors,
                'warnings': self.warnings,
                'total_questions': len(self.questions),
                'images_found': len(self.images)
            }
            
        except Exception as e:
            self.errors.append(f"Lỗi hệ thống khi phân tích file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'questions': [],
                'raw_data': [],
                'errors': self.errors,
                'warnings': [],
                'total_questions': 0,
                'images_found': 0
            }
    
    def _extract_image_with_position(self, image):
        """Extract hình ảnh và ghi nhận vị trí xuất hiện"""
        try:
            image_filename = f"image_{len(self.images)}"
            with image.open() as image_stream:
                image_bytes = image_stream.read()
            image_data = base64.b64encode(image_bytes).decode('ascii')
            
            self.images[image_filename] = {
                'data': image_data,
                'content_type': image.content_type,
                'alt_text': getattr(image, 'alt_text', ''),
                'size': len(image_bytes)
            }
            
            return {
                "src": image_filename,
                "alt": getattr(image, 'alt_text', f'Image {len(self.images)}')
            }
            
        except Exception as e:
            error_msg = f"Không thể extract hình ảnh: {str(e)}"
            self.warnings.append(error_msg)
            return {"src": "", "alt": "image-error"}
    
    def _analyze_image_positions(self, html_content: str):
        """Phân tích vị trí hình ảnh trong HTML để ánh xạ với câu hỏi"""
        try:
            # Tìm tất cả các vị trí xuất hiện của "Câu X." trong HTML
            question_pattern = r'Câu\s+(\d+)\.'
            question_matches = list(re.finditer(question_pattern, html_content, re.IGNORECASE))
            
            # Tìm tất cả các vị trí hình ảnh trong HTML
            image_pattern = r'<img[^>]+src="(image_\d+)"'
            image_matches = list(re.finditer(image_pattern, html_content))
            
            # Ánh xạ mỗi hình ảnh với câu hỏi gần nhất trước nó
            for img_match in image_matches:
                img_position = img_match.start()
                img_filename = img_match.group(1)
                
                # Tìm câu hỏi gần nhất trước vị trí hình ảnh
                closest_question = None
                min_distance = float('inf')
                
                for q_match in question_matches:
                    q_position = q_match.start()
                    q_number = int(q_match.group(1))
                    
                    # Chỉ xem xét câu hỏi xuất hiện trước hình ảnh
                    if q_position < img_position:
                        distance = img_position - q_position
                        if distance < min_distance:
                            min_distance = distance
                            closest_question = q_number
                
                # Nếu không tìm thấy câu hỏi nào trước đó, gán cho câu hỏi đầu tiên sau nó
                if closest_question is None and question_matches:
                    for q_match in question_matches:
                        q_position = q_match.start()
                        q_number = int(q_match.group(1))
                        if q_position > img_position:
                            closest_question = q_number
                            break
                
                if closest_question is not None:
                    self.image_positions[img_filename] = closest_question
                    st.info(f"🖼️ {img_filename} được ánh xạ với Câu {closest_question}")
                else:
                    self.image_positions[img_filename] = 1  # Fallback
                    self.warnings.append(f"Không thể xác định vị trí chính xác cho {img_filename}, gán mặc định cho câu 1")
                    
        except Exception as e:
            self.warnings.append(f"Lỗi phân tích vị trí hình ảnh: {str(e)}")
    
    def _parse_questions_by_sections(self, text: str, html: str) -> List[Dict]:
        """Parse theo sections với logic đã sửa lỗi"""
        questions = []
        lines = text.split('\n')
        
        # Biến trạng thái
        current_question_type = "multiple_choice"
        question_number = 0
        processing_question = False
        current_question_content = ""
        current_options = []
        current_correct_answers = []
        current_solution = ""
        processing_solution = False
        
        st.info(f"🔍 Đang phân tích {len(lines)} dòng văn bản...")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Xác định các "ranh giới"
            is_new_question_boundary = self._is_question_start(line)
            is_new_section_boundary = line.startswith("Phần") or line.startswith("**Phần")

            # Lưu câu hỏi hiện tại trước khi xử lý ranh giới mới
            if is_new_question_boundary or is_new_section_boundary:
                if processing_question and question_number > 0:
                    self._save_current_question(
                        questions, question_number, current_question_type,
                        current_question_content, current_options,
                        current_correct_answers, current_solution.strip(), html
                    )
                    # Reset trạng thái
                    processing_question = False
                    current_question_content = ""
                    current_options = []
                    current_correct_answers = []
                    current_solution = ""
                    processing_solution = False

            # 1. XỬ LÝ PHẦN MỚI
            if is_new_section_boundary:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ["trắc nghiệm chọn 1", "trắc nghiệm 1", "phần 1", "phần i", "mẫu trắc nghiệm"]):
                    current_question_type = "multiple_choice"
                    st.success(f"✅ Phát hiện phần trắc nghiệm: {line}")
                elif any(keyword in line_lower for keyword in ["đúng - sai", "đúng/sai", "phần 2", "phần ii", "mẫu đúng sai"]):
                    current_question_type = "true_false"
                    st.success(f"✅ Phát hiện phần đúng/sai: {line}")
                elif any(keyword in line_lower for keyword in ["trả lời ngắn", "phần 3", "phần iii", "mẫu trả lời ngắn"]):
                    current_question_type = "short_answer"
                    st.success(f"✅ Phát hiện phần trả lời ngắn: {line}")
                elif any(keyword in line_lower for keyword in ["tự luận", "phần 4", "phần iv", "mẫu tự luận", "câu hỏi tự luận"]):
                    current_question_type = "essay"
                    st.success(f"✅ Phát hiện phần tự luận: {line}")
                continue

            # 2. BẮT ĐẦU CÂU HỎI MỚI
            if is_new_question_boundary:
                question_number = self._extract_question_number(line)
                if question_number > 0:
                    processing_question = True
                    current_question_content = self._extract_question_content(line, question_number)
                    st.info(f"📝 Bắt đầu câu {question_number} (Loại: {current_question_type})")
                continue

            # 3. XỬ LÝ CÁC DÒNG BÊN TRONG CÂU HỎI
            if processing_question:
                if line.startswith("Lời giải") or line.startswith("**Lời giải"):
                    processing_solution = True
                    solution_part = re.sub(r'^\*\*?Lời giải\*\*?:?', '', line, flags=re.IGNORECASE).strip()
                    if solution_part:
                        current_solution += f" {solution_part}"
                    continue
                
                if processing_solution:
                    current_solution += f" {line}"
                    continue

                if self._is_option_line(line, current_question_type):
                    option_data = self._parse_option_line(line, current_question_type)
                    if option_data:
                        current_options.append(option_data['text'])
                        if option_data['is_correct']:
                            current_correct_answers.append(option_data['letter'])
                    continue
                
                elif line.startswith("Đáp án:") and current_question_type == "short_answer":
                    answer = line.replace("Đáp án:", "").strip()
                    current_correct_answers = [answer]
                    continue

                # Đối với câu tự luận, không cần xử lý đáp án vì học sinh nộp bằng hình ảnh
                # Chỉ cần lưu nội dung câu hỏi và lời giải

                # Nội dung câu hỏi (cho câu hỏi nhiều dòng)
                current_question_content += f" {line}"
        
        # Lưu câu hỏi cuối cùng
        if processing_question and question_number > 0:
            self._save_current_question(
                questions, question_number, current_question_type,
                current_question_content, current_options, 
                current_correct_answers, current_solution.strip(), html
            )
        
        return questions
    
    def _extract_question_number(self, line: str) -> int:
        """Trích xuất số thứ tự câu hỏi"""
        patterns = [r'Câu\s+(\d+)\.', r'\*\*Câu\s+(\d+)\.\*\*']
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return int(match.group(1))
        self.warnings.append(f"Không thể trích xuất số câu hỏi từ: '{line[:50]}...'")
        return 0
    
    def _is_question_start(self, line: str) -> bool:
        """Kiểm tra xem có phải bắt đầu câu hỏi không"""
        return bool(re.match(r'^(?:\*\*|)?Câu\s+\d+\.', line, re.IGNORECASE))
    
    def _extract_question_content(self, line: str, question_number: int) -> str:
        """Trích xuất nội dung câu hỏi"""
        content = re.sub(rf'^(?:\*\*|)?Câu\s+{question_number}\.', '', line, flags=re.IGNORECASE).strip()
        return content
    
    def _is_option_line(self, line: str, question_type: str) -> bool:
        """Kiểm tra xem có phải dòng option không"""
        if question_type == "multiple_choice":
            return bool(re.match(r'^#?[A-D]\.', line, re.IGNORECASE))
        elif question_type == "true_false":
            return bool(re.match(r'^#?[a-d]\)', line, re.IGNORECASE))
        return False
    
    def _parse_option_line(self, line: str, question_type: str) -> Dict:
        """Parse dòng option"""
        is_correct = line.startswith('#')
        line_clean = line.lstrip('#').strip()
        
        pattern = r'^([A-Da-d])[\.\)](.+)'
        match = re.match(pattern, line_clean, re.IGNORECASE)
        if match:
            letter = match.group(1).upper() if question_type == 'multiple_choice' else match.group(1).lower()
            text = match.group(2).strip()
            return {
                'letter': letter,
                'text': self._clean_text(text),
                'is_correct': is_correct
            }
        return None
    
    def _clean_text(self, text: str) -> str:
        """Làm sạch text LaTeX"""
        if not text: return ""
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_image_for_question(self, question_num: int, html: str) -> str:
        """Lấy hình ảnh cho câu hỏi dựa trên ánh xạ vị trí chính xác"""
        # Tìm hình ảnh được ánh xạ cho câu hỏi này
        for img_key, mapped_question in self.image_positions.items():
            if mapped_question == question_num:
                return self.images[img_key]['data']
        
        # Fallback: không tìm thấy hình ảnh cho câu này
        return ""
    
    def _save_current_question(self, questions: List[Dict], question_number: int, 
                             question_type: str, content: str, options: List[str], 
                             correct_answers: List[str], solution: str, html: str):
        """Lưu câu hỏi hiện tại vào danh sách với ánh xạ hình ảnh chính xác"""
        if not content.strip() or question_number <= 0:
            return
        
        image_base64 = self._get_image_for_question(question_number, html)
        
        question_data = {
            'type': question_type,
            'question_number': question_number,
            'question': self._clean_text(content),
            'image_base64': image_base64,
            'solution': self._clean_text(solution),
            'points': 1.0, 
            'difficulty': 'Trung bình'
        }

        if question_type == "multiple_choice":
            while len(options) < 4: options.append("")
            question_data.update({
                'option_a': options[0], 'option_b': options[1],
                'option_c': options[2], 'option_d': options[3],
                'correct_answer': correct_answers[0] if correct_answers else ""
            })
        
        elif question_type == "true_false":
            statements = [{'letter': chr(ord('a') + i), 'text': opt, 'is_correct': (chr(ord('a') + i) in correct_answers)} for i, opt in enumerate(options)]
            question_data.update({
                'statements': statements,
                'correct_answers': correct_answers,
                'points': len(statements) * 0.25
            })

        elif question_type == "short_answer":
            answer = correct_answers[0] if correct_answers else ""
            question_data.update({
                'correct_answer': self._clean_text(answer),
                'sample_answers': [self._clean_text(answer)] if answer else [],
                'case_sensitive': False
            })

        elif question_type == "essay":
            question_data.update({
                'points': 2.0,  # Câu tự luận thường có điểm cao hơn
                'grading_criteria': 'Chấm bằng hình ảnh do học sinh nộp',
                'submission_type': 'image_upload'
            })

        questions.append(question_data)
        self._add_to_raw_data(question_data)

    def _add_to_raw_data(self, question: Dict):
        """Thêm câu hỏi vào raw data cho bảng hiển thị"""
        q_num = question['question_number']
        q_type = question['type']
        
        common_data = {
            'STT': q_num,
            'Câu hỏi': question['question'][:100] + "...",
            'Có hình ảnh': '✅' if question['image_base64'] else '❌',
            'Điểm': question['points']
        }

        if q_type == 'multiple_choice':
            row = {
                'Loại': '🔤 Trắc nghiệm',
                **common_data,
                'Đáp án A': question['option_a'], 'Đáp án B': question['option_b'],
                'Đáp án C': question['option_c'], 'Đáp án D': question['option_d'],
                'Đáp án đúng': question['correct_answer'],
            }
        elif q_type == 'true_false':
            statements_text = "; ".join([f"{s['letter']}) {s['text'][:20]}..." for s in question['statements']])
            row = {
                'Loại': '✅ Đúng/Sai',
                **common_data,
                'Các phát biểu': statements_text,
                'Đáp án đúng': ", ".join(question['correct_answers'])
            }
        elif q_type == 'short_answer':
            row = {
                'Loại': '📝 Trả lời ngắn',
                **common_data,
                'Đáp án': question['correct_answer']
            }
        elif q_type == 'essay':
            row = {
                'Loại': '📄 Tự luận',
                **common_data,
                'Kiểu nộp bài': 'Hình ảnh',
                'Lời giải có': '✅' if question.get('solution') else '❌'
            }
        else:
            row = {'STT': q_num, 'Loại': 'Không xác định', 'Câu hỏi': 'Lỗi phân tích'}
        
        self.raw_questions_data.append(row)

    def _create_questions_dataframe(self):
        """Tạo DataFrame để hiển thị"""
        if not self.raw_questions_data:
            return pd.DataFrame()
        sorted_data = sorted(self.raw_questions_data, key=lambda x: x['STT'])
        return pd.DataFrame(sorted_data)

    def convert_to_exam_format(self, parsed_questions: List[Dict]) -> List[Dict]:
        """Chuyển đổi sang định dạng hệ thống exam"""
        converted_questions = []
        for q in parsed_questions:
            base_q = {
                'type': q['type'],
                'question': q['question'],
                'points': q.get('points', 1.0),
                'difficulty': q.get('difficulty', 'Trung bình'),
                'solution': q.get('solution', ''),
                'image_data': q.get('image_base64') or None
            }
            if q['type'] == 'multiple_choice':
                base_q.update({
                    'options': [q['option_a'], q['option_b'], q['option_c'], q['option_d']],
                    'correct_answer': q['correct_answer'],
                })
                converted_questions.append(base_q)
            elif q['type'] == 'true_false':
                for stmt in q['statements']:
                    true_false_q = base_q.copy()
                    true_false_q.update({
                        'question': f"{q['question']} - Phát biểu {stmt['letter']}): {stmt['text']}",
                        'correct_answer': 'Đúng' if stmt['is_correct'] else 'Sai',
                        'points': q.get('points', 1.0) / len(q['statements'])
                    })
                    converted_questions.append(true_false_q)
            elif q['type'] == 'short_answer':
                base_q.update({
                    'sample_answers': q['sample_answers'],
                    'case_sensitive': q['case_sensitive']
                })
                converted_questions.append(base_q)
            elif q['type'] == 'essay':
                base_q.update({
                    'grading_criteria': q.get('grading_criteria', 'Chấm bằng hình ảnh do học sinh nộp'),
                    'submission_type': q.get('submission_type', 'image_upload'),
                    'max_score': q.get('points', 2.0)
                })
                converted_questions.append(base_q)
        return converted_questions


def show_upload_word_exam():
    """Giao diện upload với logic parser chuẩn và ánh xạ hình ảnh chính xác"""
    st.markdown(
    "<h4 style='font-size:18px;'>📄 Upload đề thi từ file Word</h4>", 
    unsafe_allow_html=True
)
    
    with st.expander("📚 Hướng dẫn định dạng file Word", expanded=False):
        st.markdown("""
        ### 📝 Định dạng chuẩn:
        
        **🎯 Phân chia theo phần để xác định loại câu hỏi:**
        
        **Phần 1: Trắc nghiệm**
        ```
        Phần 1: Trắc nghiệm chọn 1 đáp án đúng
        
        Câu 1. Nội dung câu hỏi...
        A. Đáp án A
        #B. Đáp án B đúng (có dấu # ở đầu)
        C. Đáp án C
        D. Đáp án D
        
        Lời giải
        Chi tiết lời giải...
        ```
        
        **Phần 2: Đúng/Sai**
        ```
        Phần 2: Trắc nghiệm đúng - sai
        
        Câu 2. Cho các phát biểu sau:
        #a) Phát biểu a đúng.
        b) Phát biểu b sai.
        c) Phát biểu c sai.
        #d) Phát biểu d đúng.
        
        Lời giải
        ...
        ```
        
        ### 🔑 Lưu ý quan trọng về hình ảnh:
        - **Vị trí hình ảnh:** Đặt hình ảnh ngay sau câu hỏi mà nó thuộc về
        - **Hệ thống sẽ tự động ánh xạ:** Hình ảnh với câu hỏi gần nhất trước nó
        - **Kiểm tra Debug Mode:** Để xác minh ánh xạ hình ảnh đúng
        """)
    
    uploaded_file = st.file_uploader(
        "Chọn file Word (.docx)", type=['docx'], key="word_uploader_main"
    )
    
    if uploaded_file is not None:
        parser = WordExamParser()
        
        with st.spinner("🔍 Đang phân tích file Word, vui lòng chờ..."):
            result = parser.parse_docx_file(uploaded_file)
        
        if result['success']:
            st.success("🎉 Phân tích thành công!")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📝 Tổng câu hỏi", result['total_questions'])
            col2.metric("🖼️ Hình ảnh", result['images_found'])
            col3.metric("⚠️ Cảnh báo", len(result['warnings']))
            col4.metric("❌ Lỗi", len(result['errors']))
            
            if result['raw_data']:
                st.subheader("📊 Dữ liệu câu hỏi đã phân tích")
                df = parser._create_questions_dataframe()
                st.dataframe(df, use_container_width=True)
            
            if result['questions']:
                show_detailed_questions_preview(result['questions'], parser)
                
                st.divider()
                if st.button("📥 Import câu hỏi vào đề thi", type="primary", use_container_width=True):
                    import_questions_to_exam(result['questions'], parser)
                    st.rerun()
            
            if result['warnings']:
                with st.expander("⚠️ Xem cảnh báo", expanded=False):
                    for warning in result['warnings']: st.warning(f"• {warning}")
            
            if result['errors']:
                with st.expander("❌ Xem lỗi", expanded=True):
                    for error in result['errors']: st.error(f"• {error}")
        
        else:
            st.error(f"❌ Lỗi nghiêm trọng khi phân tích file: {result.get('error', 'Không xác định')}")
            if result['errors']:
                for error in result['errors']: st.error(f"• {error}")

def show_detailed_questions_preview(questions: List[Dict], parser: WordExamParser):
    """Hiển thị preview chi tiết với UI chuẩn"""
    st.subheader("👀 Preview chi tiết câu hỏi")
    
    for i, q in enumerate(questions):
        with st.expander(f"Câu {q['question_number']}: {q['question'][:60]}...", expanded=False):
            st.markdown(f"**📝 Câu hỏi:** {q['question']}")
            
            if q.get('image_base64'):
                st.write("🖼️ **Hình ảnh:**")
                try:
                    img_bytes = base64.b64decode(q['image_base64'])
                    st.image(Image.open(io.BytesIO(img_bytes)), width=400)
                except Exception as e:
                    st.error(f"Lỗi hiển thị hình ảnh: {e}")
            
            if q['type'] == 'multiple_choice':
                st.write("**🔤 Loại:** Trắc nghiệm")
                options = [q['option_a'], q['option_b'], q['option_c'], q['option_d']]
                for j, option in enumerate(options):
                    letter = chr(65 + j)
                    if letter == q['correct_answer']:
                        st.success(f"✅ **{letter}.** {option}")
                    else:
                        st.write(f"◯ **{letter}.** {option}")
            
            elif q['type'] == 'true_false':
                st.write("**✅ Loại:** Đúng/Sai")
                for stmt in q['statements']:
                    if stmt['is_correct']:
                        st.success(f"✅ **{stmt['letter']})** {stmt['text']} (Đúng)")
                    else:
                        st.error(f"❌ **{stmt['letter']})** {stmt['text']} (Sai)")
            
            elif q['type'] == 'short_answer':
                st.write("**📝 Loại:** Trả lời ngắn")
                st.info(f"**Đáp án mẫu:** {q['correct_answer']}")
            
            elif q['type'] == 'essay':
                st.write("**📄 Loại:** Tự luận")
                st.info("**💡 Phương thức:** Học sinh nộp bài bằng hình ảnh")
                st.caption("Giáo viên sẽ chấm điểm dựa trên hình ảnh bài làm")
            
            if q.get('solution'):
                with st.popover("💡 Xem lời giải"):
                    st.markdown(q['solution'])
            
            col1, col2 = st.columns(2)
            col1.caption(f"Điểm: {q['points']}")
            col2.caption(f"Độ khó: {q['difficulty']}")

def import_questions_to_exam(questions: list, parser):
    """Import câu hỏi vào session_state - SỬA: Giữ nguyên cấu trúc ban đầu"""
    try:
        # KHÔNG CHUYỂN ĐỔI - Giữ nguyên cấu trúc từ parser
        if "exam_questions" not in st.session_state:
            st.session_state.exam_questions = []
        
        # Import trực tiếp without conversion để giữ nguyên cấu trúc
        imported_count = 0
        for q in questions:
            # Đảm bảo có các trường cần thiết cho exam format
            exam_question = {
                'type': q['type'],
                'question': q['question'],
                'points': q.get('points', 1.0),
                'difficulty': q.get('difficulty', 'Trung bình'),
                'solution': q.get('solution', ''),
                'image_data': q.get('image_base64') or None  # Đổi tên field
            }
            
            if q['type'] == 'multiple_choice':
                exam_question.update({
                    'options': [q['option_a'], q['option_b'], q['option_c'], q['option_d']],
                    'correct_answer': q['correct_answer']
                })
            elif q['type'] == 'true_false':
                # QUAN TRỌNG: Giữ nguyên cấu trúc statements
                exam_question.update({
                    'statements': q['statements'],
                    'correct_answers': q['correct_answers']
                })
            elif q['type'] == 'short_answer':
                exam_question.update({
                    'sample_answers': q.get('sample_answers', [q.get('correct_answer', '')]),
                    'case_sensitive': q.get('case_sensitive', False)
                })
            elif q['type'] == 'essay':
                exam_question.update({
                    'grading_criteria': q.get('grading_criteria', 'Chấm bằng hình ảnh do học sinh nộp'),
                    'submission_type': q.get('submission_type', 'image_upload'),
                    'requires_image': True
                })
            
            st.session_state.exam_questions.append(exam_question)
            imported_count += 1
        
        st.success(f"✅ Đã import thành công {imported_count} câu hỏi vào đề thi!")
        st.info("💡 Chuyển sang tab 'Quản lý' để xem danh sách câu hỏi đã import")
        
    except Exception as e:
        st.error(f"❌ Lỗi khi import: {str(e)}")
        st.code(str(e))  # Debug info

# Hàm render MathJax để hỗ trợ LaTeX
def render_mathjax():
    """Load MathJax để hiển thị LaTeX"""
    mathjax_script = """
    <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true,
        processEnvironments: true
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
      }
    };
    </script>
    <script
      type="text/javascript"
      id="MathJax-script"
      async
      src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
    </script>
    """
    st.components.v1.html(mathjax_script, height=0)

# Ví dụ về cách gọi hàm trong ứng dụng Streamlit chính
if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="Word Exam Parser")
    st.title("Trình phân tích đề thi từ file Word")
    render_mathjax()
    show_upload_word_exam()