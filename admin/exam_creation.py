import streamlit as st
import json
import pandas as pd
import base64
import io
import os
import random
import pytz
from datetime import datetime, timedelta
from database.supabase_models import get_database
from auth.login import get_current_user
LOCAL_TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"))
# Safe imports
try:
    from admin.word_parser import show_upload_word_exam, render_mathjax
except ImportError:
    def render_mathjax():
        st.markdown("""
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
        window.MathJax = {
            tex: {inlineMath: [['$', '$'], ['\\(', '\\)']]},
            svg: {fontCache: 'global'}
        };
        </script>
        """, unsafe_allow_html=True)
def load_exam_data_into_session(exam_id, is_cloning=False):
    """Tải dữ liệu của một đề thi vào session state để sửa hoặc nhân bản."""
    db = get_database()
    exam_details = db.get_exam_by_id(exam_id) # Hàm này đã có trong wrapper của bạn
    if not exam_details:
        st.error(f"Không thể tải dữ liệu cho đề thi ID: {exam_id}")
        return False

    # Xóa dữ liệu cũ trước khi tải
    clear_exam_data()

    # Tải dữ liệu vào session state
    st.session_state.exam_title = exam_details.get('title', '')
    st.session_state.exam_description = exam_details.get('description', '')
    st.session_state.exam_instructions = exam_details.get('instructions', '')
    st.session_state.exam_time_limit = exam_details.get('time_limit', 60)
    st.session_state.exam_questions = exam_details.get('questions', [])

    if is_cloning:
        # Nếu nhân bản, thêm chữ [Bản sao] và reset thông tin lớp/thời gian
        st.session_state.exam_title += " [Bản sao]"
        st.session_state.exam_class_id = None # Bắt buộc chọn lại lớp
        # Đặt thời gian mặc định là hiện tại
        st.session_state.exam_start_date = datetime.now().date()
        st.session_state.exam_start_time = datetime.now().time()
        st.session_state.exam_end_date = (datetime.now() + timedelta(days=7)).date()
        st.session_state.exam_end_time = datetime.now().time()
        st.success(f"Đã nhân bản đề thi '{exam_details['title']}'. Vui lòng cập nhật thông tin và lưu lại như một đề mới.")
    else: # Đang sửa
        st.session_state.editing_exam_id_value = exam_id # Lưu ID để biết là đang update
        st.session_state.exam_class_id = exam_details.get('class_id')
        
        # Tải lại thời gian đã lưu
        try:
            start_dt = datetime.fromisoformat(exam_details['start_time']).astimezone(LOCAL_TIMEZONE)
            end_dt = datetime.fromisoformat(exam_details['end_time']).astimezone(LOCAL_TIMEZONE)
            st.session_state.exam_start_date = start_dt.date()
            st.session_state.exam_start_time = start_dt.time()
            st.session_state.exam_end_date = end_dt.date()
            st.session_state.exam_end_time = end_dt.time()
        except: # Fallback nếu thời gian không hợp lệ
            st.session_state.exam_start_date = datetime.now().date()
            st.session_state.exam_start_time = datetime.now().time()
        
        st.success(f"Đang sửa đề thi '{exam_details['title']}'.")

    return True
def update_existing_exam(user):
    """Cập nhật một đề thi đã có."""
    try:
        exam_id = st.session_state.get('editing_exam_id_value')
        if not exam_id:
            st.error("Lỗi: Không tìm thấy ID của đề thi đang sửa.")
            return

        exam_data = prepare_exam_data(user, is_published=False) # is_published sẽ được xử lý riêng
        db = get_database()

        # Chuẩn bị dữ liệu để update
        update_payload = {
            'title': exam_data['title'],
            'description': exam_data['description'],
            'instructions': exam_data['instructions'],
            'class_id': exam_data['class_id'],
            'questions': exam_data['questions'],
            'time_limit': exam_data['time_limit'],
            'start_time': exam_data['start_time'],
            'end_time': exam_data['end_time'],
        }

        if db.update_exam(exam_id, **update_payload):
            st.success("✅ Đã cập nhật đề thi thành công!")
            # Tùy chọn: hỏi có muốn phát hành không nếu nó là bản nháp
            # ...
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Quay lại trang quản lý", use_container_width=True):
                    st.session_state.current_page = "exam_management"
                    clear_exam_data()
                    st.rerun()
            with col2:
                if st.button("➕ Tạo đề thi khác", use_container_width=True):
                    clear_exam_data()
                    st.rerun()
        else:
            st.error("❌ Có lỗi xảy ra khi cập nhật đề thi.")

    except Exception as e:
        st.error(f"❌ Lỗi khi cập nhật đề thi: {e}")
def show_create_exam():
   
    db = get_database()
    
    if 'edit_exam_id' in st.session_state:
        exam_id = st.session_state.edit_exam_id
        del st.session_state.edit_exam_id # Xóa key để không chạy lại
        load_exam_data_into_session(exam_id, is_cloning=False)
        st.rerun()
    elif 'clone_exam_id' in st.session_state:
        exam_id = st.session_state.clone_exam_id
        del st.session_state.clone_exam_id # Xóa key để không chạy lại
        load_exam_data_into_session(exam_id, is_cloning=True)
        st.rerun()
    page_title = "📝 Tạo đề thi mới"
    if st.session_state.get('editing_exam_id_value'):
        page_title = f"✏️ Sửa đề thi: {st.session_state.get('exam_title', '')}"
    
    st.header(page_title)
    
    user = get_current_user()
    
    # Lấy danh sách lớp từ database
    try:
        classes_data = db.get_all_classes()
        
        # Convert to format expected by UI
        classes = []
        for class_data in classes_data:
            student_count = db.get_class_student_count(class_data['id'])
            classes.append({
                'id': class_data['id'],
                'name': class_data['ten_lop'],
                'description': class_data.get('mo_ta', ''),
                'student_count': student_count,
                'created_at': class_data.get('created_at', '')
            })
    except Exception as e:
        st.error(f"❌ Lỗi lấy danh sách lớp: {str(e)}")
        classes = []
    
    if not classes:
        st.warning("⚠️ Bạn cần tạo lớp học trước khi tạo đề thi!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Tạo lớp ngay", use_container_width=True):
                st.session_state.current_page = "manage_classes"
                st.rerun()
        with col2:
            if st.button("📚 Xem hướng dẫn", use_container_width=True):
                show_exam_creation_guide()
        return
    
    # Khởi tạo session state cho questions
    if "exam_questions" not in st.session_state:
        st.session_state.exam_questions = []
    if "current_question" not in st.session_state:
        st.session_state.current_question = {}
    
    # Tabs chính
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Thông tin đề thi", 
        "❓ Thêm câu hỏi", 
        "📝 Xem trước đề", 
        "🚀 Hoàn thành"
    ])
    
    with tab1:
        show_exam_info_tab(classes)
    
    with tab2:
        show_add_questions_tab()
    
    with tab3:
        show_preview_tab()
    
    with tab4:
        is_editing = 'editing_exam_id_value' in st.session_state
        show_complete_tab(user, is_editing)

def show_exam_creation_guide():
    """Hiển thị hướng dẫn tạo đề thi"""
    with st.expander("📚 Hướng dẫn tạo đề thi", expanded=True):
        st.markdown("""
        ### 🔄 Quy trình tạo đề thi:
        
        1. **📋 Thông tin đề thi**
           - Nhập tiêu đề, chọn lớp
           - Đặt thời gian làm bài
           - Cấu hình thời gian mở đề
        
        2. **❓ Thêm câu hỏi**
           - Chọn loại câu hỏi phù hợp
           - Nhập nội dung và đáp án
           - Đặt điểm cho từng câu
           - Upload từ Word với LaTeX và hình ảnh
        
        3. **📝 Xem trước**
           - Kiểm tra toàn bộ đề thi
           - Xem thống kê và phân bố điểm
           - Preview LaTeX và hình ảnh
        
        4. **🚀 Hoàn thành**
           - Lưu nháp hoặc phát hành
        
        ### 📝 Các loại câu hỏi:
        
        - **🔤 Trắc nghiệm:** 4 lựa chọn, 1 đáp án đúng
        - **✅ Đúng/Sai:** Nhiều phát biểu trong 1 câu
        - **📝 Trả lời ngắn:** Học sinh gõ câu trả lời
        - **📄 Tự luận:** Có thể yêu cầu chụp ảnh bài làm
        """)

def show_exam_info_tab(classes):
    """Tab thông tin đề thi"""
    st.subheader("📋 Thông tin cơ bản")
    
    with st.form("exam_basic_info"):
        col1, col2 = st.columns(2)
        
        with col1:
            exam_title = st.text_input(
                "Tiêu đề đề thi *", 
                placeholder="Ví dụ: Kiểm tra 15 phút - Toán học",
                value=st.session_state.get("exam_title", "")
            )
            
            class_options = {f"{c['name']} ({c['student_count']} HS)": c['id'] for c in classes}
            
            # Nếu đã có lớp được chọn từ popup lớp học, tự động chọn
            if st.session_state.get("exam_class_id"):
                for display_name, class_id in class_options.items():
                    if class_id == st.session_state.exam_class_id:
                        selected_index = list(class_options.keys()).index(display_name)
                        break
                else:
                    selected_index = 0
            else:
                selected_index = 0
                
            selected_class_display = st.selectbox(
                "Chọn lớp *", 
                options=list(class_options.keys()),
                index=selected_index
            )
            
            time_limit = st.number_input(
                "Thời gian làm bài (phút) *", 
                min_value=5, max_value=300, 
                value=st.session_state.get("exam_time_limit", 60)
            )
        
        with col2:
            description = st.text_area(
                "Mô tả đề thi", 
                placeholder="Ghi chú về đề thi, yêu cầu đặc biệt...",
                value=st.session_state.get("exam_description", "")
            )
            
            instructions = st.text_area(
                "Hướng dẫn làm bài",
                placeholder="Hướng dẫn chi tiết cho học sinh...",
                value=st.session_state.get("exam_instructions", "")
            )
        
        st.subheader("⏰ Thời gian mở đề")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            start_date = st.date_input(
                "Ngày bắt đầu", 
                value=st.session_state.get("exam_start_date", datetime.now().date())
            )
        with col2:
            start_time = st.time_input(
                "Giờ bắt đầu", 
                value=st.session_state.get("exam_start_time", datetime.now().time())
            )
        with col3:
            end_date = st.date_input(
                "Ngày kết thúc", 
                value=st.session_state.get("exam_end_date", (datetime.now() + timedelta(days=7)).date())
            )
        with col4:
            end_time = st.time_input(
                "Giờ kết thúc", 
                value=st.session_state.get("exam_end_time", datetime.now().time())
            )
        
        if st.form_submit_button("💾 Lưu thông tin đề thi", use_container_width=True):
            if not exam_title or not selected_class_display:
                st.error("❌ Vui lòng nhập đầy đủ thông tin bắt buộc!")
                return
            
            # Lưu vào session state
            st.session_state.exam_title = exam_title
            st.session_state.exam_description = description
            st.session_state.exam_instructions = instructions
            st.session_state.exam_class_id = class_options[selected_class_display]
            st.session_state.exam_class_name = selected_class_display.split(" (")[0]
            st.session_state.exam_time_limit = time_limit
            st.session_state.exam_start_date = start_date
            st.session_state.exam_start_time = start_time
            st.session_state.exam_end_date = end_date
            st.session_state.exam_end_time = end_time
            
            st.success("✅ Đã lưu thông tin đề thi! Chuyển sang tab 'Thêm câu hỏi'")
    
    # Hiển thị thông tin đã lưu
    if st.session_state.get("exam_title"):
        with st.expander("📄 Thông tin đã lưu", expanded=False):
            st.write(f"**Tiêu đề:** {st.session_state.exam_title}")
            st.write(f"**Lớp:** {st.session_state.get('exam_class_name', 'Chưa chọn')}")
            st.write(f"**Thời gian:** {st.session_state.exam_time_limit} phút")
            st.write(f"**Từ:** {st.session_state.exam_start_date} {st.session_state.exam_start_time}")
            st.write(f"**Đến:** {st.session_state.exam_end_date} {st.session_state.exam_end_time}")

def show_add_questions_tab():
    """Tab thêm câu hỏi"""
    st.subheader("❓ Thêm câu hỏi")
    
    if not st.session_state.get("exam_title"):
        st.warning("⚠️ Vui lòng hoàn thành thông tin đề thi ở tab đầu tiên!")
        return
    
    # Kích hoạt MathJax
    render_mathjax()
    
    # Tabs con cho các cách thêm câu hỏi
    subtab1, subtab2, subtab3, subtab4 = st.tabs(["✍️ Thêm thủ công", "📄 Upload từ Word", "📊 Quản lý", "⚖️ Phân phối điểm"])
    
    with subtab1:
        show_manual_question_input()
    
    with subtab2:
        
        try:
            show_upload_word_exam()
        except Exception as e:
            st.error("❌ Lỗi tải word parser!")
            st.code(str(e))
            st.info("💡 Cần cài đặt: `pip install mammoth pandas openpyxl`")
    
    with subtab3:
        show_questions_management()
    
    with subtab4:
        show_point_distribution()

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

def show_manual_question_input():
    """Giao diện thêm câu hỏi thủ công"""
    questions = st.session_state.get("exam_questions", [])
    
    if questions:
        st.write(f"**📝 Đã có {len(questions)} câu hỏi:**")
        total_points = sum(q['points'] for q in questions)
        st.info(f"📊 Tổng điểm: {total_points:.1f} điểm")
        
        for i, question in enumerate(questions):
            with st.expander(f"Câu {i+1}: {question['question'][:50]}...", expanded=False):
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    type_names = {
                        "multiple_choice": "🔤 Trắc nghiệm 4 lựa chọn",
                        "true_false": "✅ Đúng/Sai",
                        "short_answer": "📝 Trả lời ngắn",
                        "essay": "📄 Tự luận"
                    }
                    st.write(f"**Loại:** {type_names[question['type']]}")
                    st.write(f"**Câu hỏi:** {question['question']}")
                    if question.get('image_data'):
                        try:
                            st.image(base64.b64decode(question['image_data']), width=150)
                        except:
                            st.caption("🖼️ Có ảnh đính kèm")
                    st.write(f"**Điểm:** {question['points']}")
                    
                    if question['type'] == 'multiple_choice':
                        st.write("**Các lựa chọn:**")
                        for j, option in enumerate(question.get('options', [])):
                            prefix = "✅" if chr(65+j) == question.get('correct_answer') else "  "
                            st.write(f"  {prefix} {chr(65+j)}. {option}")
                    
                    elif question['type'] == 'true_false':
                        if 'statements' in question and question['statements']:
                            st.write("**📝 Các phát biểu:**")
                            for stmt in question['statements']:
                                icon = "✅" if stmt.get('is_correct', False) else "❌"
                                status = "Đúng" if stmt.get('is_correct', False) else "Sai"
                                st.write(f"  {icon} **{stmt['letter']})** {stmt['text']} ({status})")
                    
                    elif question['type'] == 'short_answer':
                        answers = question.get('sample_answers', [])
                        if answers:
                            st.write(f"**Đáp án mẫu:** {', '.join(answers)}")
                    
                    elif question['type'] == 'essay':
                        st.write("**📄 Loại:** Tự luận")
                        if question.get('requires_image'):
                            st.write("**📷 Yêu cầu chụp ảnh bài làm**")
                
                with col2:
                    if st.button("✏️ Sửa", key=f"edit_q_{i}"):
                        st.session_state.edit_question_index = i
                        st.session_state.current_question = question.copy()
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Xóa", key=f"delete_q_{i}"):
                        st.session_state.exam_questions.pop(i)
                        st.success(f"✅ Đã xóa câu {i+1}")
                        st.rerun()
        
        st.divider()
    
    # Form thêm câu hỏi mới
    show_question_form()

def show_question_form():
    """Form thêm/sửa câu hỏi"""
    is_editing = "edit_question_index" in st.session_state
    form_title = "✏️ Chỉnh sửa câu hỏi" if is_editing else "➕ Thêm câu hỏi mới"
    
    st.write(f"**{form_title}:**")
    
    current_question = st.session_state.get("current_question", {}) if is_editing else {}
    
    question_type = st.selectbox(
        "Loại câu hỏi",
        ["multiple_choice", "true_false", "short_answer", "essay"],
        format_func=lambda x: {
            "multiple_choice": "🔤 Trắc nghiệm 4 lựa chọn",
            "true_false": "✅ Đúng/Sai",
            "short_answer": "📝 Trả lời ngắn",
            "essay": "📄 Tự luận"
        }[x],
        index=["multiple_choice", "true_false", "short_answer", "essay"].index(current_question.get('type', 'multiple_choice')),
        key="new_question_type"
    )
    
    with st.form("add_question_form"):
        question_text = st.text_area(
            "Nội dung câu hỏi *", 
            value=current_question.get('question', ''),
            placeholder="Nhập câu hỏi... (Hỗ trợ LaTeX: $x^2$ hoặc $\\int_0^1 f(x)dx$)",
            height=100
        )
        
        ### <<< THÊM MỚI: Phần tải ảnh lên >>>
        uploaded_image = st.file_uploader(
            "Tải ảnh minh họa cho câu hỏi (tùy chọn)",
            type=['png', 'jpg', 'jpeg'],
            key="question_image_uploader"
        )
        
        # Hiển thị ảnh hiện tại (nếu đang sửa và đã có ảnh)
        if is_editing and current_question.get('image_data'):
            st.image(base64.b64decode(current_question['image_data']), width=200, caption="Ảnh hiện tại")
        ### <<< KẾT THÚC PHẦN THÊM MỚI >>>
        
        col1, col2 = st.columns(2)
        with col1:
            points = st.number_input(
                "Điểm", 
                min_value=0.25, max_value=20.0, 
                value=current_question.get('points', 1.0), 
                step=0.25
            )
        
        with col2:
            difficulty = st.selectbox(
                "Độ khó", 
                ["Dễ", "Trung bình", "Khó"],
                index=["Dễ", "Trung bình", "Khó"].index(current_question.get('difficulty', 'Trung bình'))
            )
        
        solution = st.text_area(
            "Lời giải (tùy chọn)",
            value=current_question.get('solution', ''),
            placeholder="Nhập lời giải chi tiết... (Hỗ trợ LaTeX)",
            height=80
        )
        
        question_data = {
            "type": question_type,
            "question": question_text,
            "points": points,
            "difficulty": difficulty,
            "solution": solution
        }
        
        # Xử lý specific cho từng loại câu hỏi
        if question_type == "multiple_choice":
            show_multiple_choice_form(question_data, current_question)
        elif question_type == "true_false":
            show_true_false_form(question_data, current_question)
        elif question_type == "short_answer":
            show_short_answer_form(question_data, current_question)
        elif question_type == "essay":
            show_essay_form(question_data, current_question)
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_text = "💾 Cập nhật câu hỏi" if is_editing else "✅ Thêm câu hỏi"
            if st.form_submit_button(submit_text, use_container_width=True):
                ### <<< THÊM MỚI: Xử lý dữ liệu ảnh trước khi lưu >>>
                if uploaded_image:
                    img_bytes = uploaded_image.getvalue()
                    base64_string = base64.b64encode(img_bytes).decode('utf-8')
                    question_data['image_data'] = base64_string
                elif is_editing and 'image_data' in current_question:
                    question_data['image_data'] = current_question['image_data']
                else:
                    question_data['image_data'] = None
                ### <<< KẾT THÚC PHẦN THÊM MỚI >>>

                if validate_and_save_question(question_data, is_editing):
                    st.rerun()
        
        with col2:
            cancel_text = "❌ Hủy chỉnh sửa" if is_editing else "🔄 Làm mới"
            if st.form_submit_button(cancel_text, use_container_width=True):
                if is_editing:
                    del st.session_state.edit_question_index
                    del st.session_state.current_question
                st.rerun()

def show_multiple_choice_form(question_data, current_question):
    """Form cho câu hỏi trắc nghiệm"""
    st.write("**Các lựa chọn:**")
    current_options = current_question.get('options', ['', '', '', ''])
    options = []
    
    for i in range(4):
        option = st.text_input(
            f"Lựa chọn {chr(65+i)}", 
            value=current_options[i] if i < len(current_options) else '',
            key=f"option_{i}",
            placeholder="Có thể dùng LaTeX: $x^2$"
        )
        options.append(option)
    
    current_correct = current_question.get('correct_answer', 'A')
    correct_answer = st.selectbox(
        "Đáp án đúng", 
        ["A", "B", "C", "D"],
        index=["A", "B", "C", "D"].index(current_correct) if current_correct in ["A", "B", "C", "D"] else 0
    )
    
    question_data.update({
        "options": options,
        "correct_answer": correct_answer
    })

def show_true_false_form(question_data, current_question):
    """Form cho câu hỏi đúng/sai"""
    st.write("**📝 Các phát biểu đúng/sai:**")
    current_statements = current_question.get('statements', [])
    statements = []
    correct_answers = []
    
    for i in range(4):
        col1, col2 = st.columns([3, 1])
        
        current_stmt = None
        if i < len(current_statements):
            current_stmt = current_statements[i]
        
        with col1:
            statement_text = st.text_input(
                f"Phát biểu {chr(ord('a') + i)}", 
                value=current_stmt['text'] if current_stmt else '',
                key=f"statement_{i}"
            )
        
        with col2:
            is_correct = st.checkbox(
                "Đúng", 
                value=current_stmt['is_correct'] if current_stmt else False,
                key=f"correct_{i}"
            )
        
        if statement_text.strip():
            statements.append({
                'letter': chr(ord('a') + i),
                'text': statement_text.strip(),
                'is_correct': is_correct
            })
            
            if is_correct:
                correct_answers.append(chr(ord('a') + i))
    
    question_data.update({
        "statements": statements,
        "correct_answers": correct_answers
    })

def show_short_answer_form(question_data, current_question):
    """Form cho câu hỏi trả lời ngắn"""
    current_answers = current_question.get('sample_answers', [])
    sample_answers_text = '; '.join(current_answers) if current_answers else ''
    
    sample_answers = st.text_area(
        "Câu trả lời mẫu", 
        value=sample_answers_text,
        placeholder="Nhập các câu trả lời đúng, cách nhau bằng dấu ;"
    )
    
    case_sensitive = st.checkbox(
        "Phân biệt hoa thường",
        value=current_question.get('case_sensitive', False)
    )
    
    question_data.update({
        "sample_answers": [ans.strip() for ans in sample_answers.split(";") if ans.strip()],
        "case_sensitive": case_sensitive
    })

def show_essay_form(question_data, current_question):
    """Form cho câu hỏi tự luận"""
    requires_image = st.checkbox(
        "Yêu cầu chụp ảnh bài làm",
        value=current_question.get('requires_image', False)
    )
    
    grading_rubric = st.text_area(
        "Tiêu chí chấm điểm (Rubric for AI) *", 
        value=current_question.get('grading_criteria', ''),
        placeholder="Mô tả chi tiết tiêu chí chấm điểm cho câu tự luận để AI dựa vào đó chấm bài. Ví dụ:\n- Trình bày logic, sạch sẽ: 1 điểm\n- Áp dụng đúng công thức: 2 điểm\n- Kết quả chính xác: 2 điểm",
        height=150
    )
    
    question_data.update({
        "requires_image": requires_image,
        "grading_criteria": grading_rubric
    })

def validate_and_save_question(question_data, is_editing):
    """Validate và lưu câu hỏi"""
    # Validation
    if not question_data['question'].strip():
        st.error("❌ Vui lòng nhập nội dung câu hỏi!")
        return False
    elif question_data['type'] == "multiple_choice" and not all(question_data.get('options', [])):
        st.error("❌ Vui lòng nhập đầy đủ 4 lựa chọn!")
        return False
    elif question_data['type'] == "true_false" and len(question_data.get("statements", [])) == 0:
        st.error("❌ Vui lòng nhập ít nhất 1 phát biểu!")
        return False
    elif question_data['type'] == "short_answer" and not question_data.get("sample_answers", []):
        st.error("❌ Vui lòng nhập ít nhất 1 câu trả lời mẫu!")
        return False
    else:
    
        # Lưu câu hỏi
        if is_editing:
            st.session_state.exam_questions[st.session_state.edit_question_index] = question_data
            del st.session_state.edit_question_index
            del st.session_state.current_question
            st.success("✅ Đã cập nhật câu hỏi!")
        else:
            st.session_state.exam_questions.append(question_data)
            st.success("✅ Đã thêm câu hỏi!")
        
        return True

def show_questions_management():
    """Tab quản lý câu hỏi"""
    st.subheader("📊 Quản lý câu hỏi")
    
    questions = st.session_state.get("exam_questions", [])
    
    if not questions:
        st.info("📝 Chưa có câu hỏi nào. Hãy thêm câu hỏi ở các tab khác!")
        return
    
    # Thống kê tổng quan
    total_questions = len(questions)
    total_points = sum(q['points'] for q in questions)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Tổng câu", total_questions)
    with col2:
        st.metric("📊 Tổng điểm", f"{total_points:.1f}")
    with col3:
        avg_points = total_points / total_questions if total_questions > 0 else 0
        st.metric("📈 TB điểm/câu", f"{avg_points:.1f}")
    with col4:
        image_count = len([q for q in questions if q.get('image_data')])
        st.metric("🖼️ Có hình ảnh", image_count)
    
    # Danh sách câu hỏi
    st.write("### 📋 Danh sách câu hỏi")
    
    for i, q in enumerate(questions):
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 4, 2, 1])
            
            with col1:
                st.write(f"**Câu {i+1}**")
            
            with col2:
                type_names = {
                    "multiple_choice": "🔤 Trắc nghiệm",
                    "true_false": "✅ Đúng/Sai",
                    "short_answer": "📝 Trả lời ngắn",
                    "essay": "📄 Tự luận"
                }
                st.write(f"**{type_names[q['type']]}** - {q['points']} điểm")
                st.caption(q['question'][:60] + "..." if len(q['question']) > 60 else q['question'])
            
            with col3:
                # Hiển thị đáp án
                if q['type'] == 'multiple_choice':
                    st.caption(f"Đáp án: {q.get('correct_answer', 'N/A')}")
                elif q['type'] == 'true_false':
                    if 'statements' in q and q['statements']:
                        correct_letters = [stmt['letter'] for stmt in q['statements'] if stmt.get('is_correct', False)]
                        st.caption(f"Đúng: {', '.join(correct_letters)}")
                elif q['type'] == 'short_answer':
                    answers = q.get('sample_answers', [])
                    if answers:
                        st.caption(f"Đáp án: {answers[0][:20]}...")
                elif q['type'] == 'essay':
                    st.caption("Tự luận")
            
            with col4:
                if st.button("🗑️", key=f"delete_manage_{i}", help="Xóa"):
                    st.session_state.exam_questions.pop(i)
                    st.rerun()
            
            st.divider()

def show_point_distribution():
    """Tab phân phối điểm"""
    st.subheader("⚖️ Phân phối điểm")
    
    questions = st.session_state.get("exam_questions", [])
    if not questions:
        st.info("📝 Chưa có câu hỏi nào để phân phối điểm!")
        return
    
    current_total = sum(q['points'] for q in questions)
    st.info(f"📊 **Tổng điểm hiện tại:** {current_total:.1f} điểm từ {len(questions)} câu hỏi")
    
    # Phân phối tự động
    with st.form("auto_point_distribution"):
        st.write("**🤖 Phân phối tự động theo loại:**")
        
        total_target = st.number_input("🎯 Tổng điểm mục tiêu", min_value=1.0, max_value=100.0, value=10.0, step=0.5)
        
        # Đếm số câu theo loại
        type_counts = {}
        for q in questions:
            q_type = q['type']
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        point_settings = {}
        type_names = {
            "multiple_choice": "🔤 Trắc nghiệm",
            "true_false": "✅ Đúng/Sai",
            "short_answer": "📝 Trả lời ngắn",
            "essay": "📄 Tự luận"
        }
        
        for q_type, count in type_counts.items():
            if count > 0:
                default_points = {
                    "multiple_choice": 1.0,
                    "true_false": 1.0,
                    "short_answer": 1.5,
                    "essay": 2.0
                }.get(q_type, 1.0)
                
                point_settings[q_type] = st.number_input(
                    f"Điểm cho {type_names[q_type]} ({count} câu)",
                    min_value=0.25, max_value=20.0, value=default_points, step=0.25,
                    key=f"auto_points_{q_type}"
                )
        
        if st.form_submit_button("⚖️ Áp dụng phân phối tự động", use_container_width=True):
            apply_auto_distribution(point_settings, total_target, type_counts)

def apply_auto_distribution(point_settings, total_target, type_counts):
    """Áp dụng phân phối điểm tự động"""
    # Tính tổng điểm theo cài đặt
    calculated_total = sum(point_settings[q_type] * count for q_type, count in type_counts.items() if q_type in point_settings)
    
    if calculated_total == 0:
        st.error("❌ Tổng điểm tính toán bằng 0!")
        return
    
    # Tính tỷ lệ điều chỉnh
    adjustment_ratio = total_target / calculated_total
    
    questions = st.session_state.exam_questions
    
    for i, q in enumerate(questions):
        if q['type'] in point_settings:
            adjusted_points = point_settings[q['type']] * adjustment_ratio
            questions[i]['points'] = round(adjusted_points, 2)
    
    final_total = sum(q['points'] for q in questions)
    st.success(f"✅ Đã áp dụng phân phối tự động! Tổng điểm: {final_total:.1f}")
    st.rerun()

def show_preview_tab():
    """Tab xem trước đề thi"""
    st.subheader("📝 Xem trước đề thi")
    
    if not st.session_state.get("exam_title") or not st.session_state.exam_questions:
        st.warning("⚠️ Vui lòng hoàn thành thông tin đề thi và thêm câu hỏi!")
        return
    
    # Load MathJax
    render_mathjax()
    
    # Header đề thi
    st.markdown(f"""
    <div style='text-align: center; border: 2px solid #667eea; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h2>📝 {st.session_state.exam_title}</h2>
        <p><strong>Lớp:</strong> {st.session_state.get('exam_class_name', '')}</p>
        <p><strong>Thời gian:</strong> {st.session_state.exam_time_limit} phút</p>
        <p><strong>Tổng điểm:</strong> {sum(q['points'] for q in st.session_state.exam_questions):.1f} điểm</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Hiển thị câu hỏi
    for i, question in enumerate(st.session_state.exam_questions):
        st.markdown(f"### Câu {i+1}: ({question['points']} điểm)")
        st.markdown(question['question'])
        
        # Hiển thị hình ảnh nếu có
        if question.get('image_data'):
            try:
                image_bytes = base64.b64decode(question['image_data'])
                st.image(image_bytes, caption=f"Hình ảnh câu {i+1}", width=300)
            except Exception as e:
                st.error(f"Lỗi hiển thị hình ảnh câu {i+1}: {e}")
        
        if question['type'] == 'multiple_choice':
            for j, option in enumerate(question.get('options', [])):
                st.markdown(f"  **{chr(65+j)}.** {option}")
            st.caption(f"✅ Đáp án đúng: {question.get('correct_answer', 'N/A')}")
        
        elif question['type'] == 'true_false':
            if 'statements' in question and question['statements']:
                st.markdown("**📝 Đánh dấu Đúng (✓) hoặc Sai (✗) cho mỗi phát biểu:**")
                for stmt in question['statements']:
                    st.markdown(f"  **{stmt['letter']})** {stmt['text']} **[ ]** Đúng **[ ]** Sai")
                
                correct_letters = [stmt['letter'] for stmt in question['statements'] if stmt.get('is_correct', False)]
                st.caption(f"✅ Đáp án đúng: {', '.join(correct_letters)}")
        
        elif question['type'] == 'short_answer':
            st.markdown("📝 *Câu trả lời ngắn*")
            if question.get('sample_answers'):
                st.caption(f"✅ Đáp án mẫu: {', '.join(question['sample_answers'])}")
        
        elif question['type'] == 'essay':
            st.markdown("📄 *Trả lời tự luận*")
            if question.get('requires_image'):
                st.markdown("📷 *Yêu cầu chụp ảnh bài làm*")
        
        st.divider()

def show_complete_tab(user,is_editing=False):
    """Tab hoàn thành và lưu đề thi"""
    st.subheader("🚀 Hoàn thành đề thi")
    
    if not st.session_state.get("exam_title") or not st.session_state.exam_questions:
        st.error("❌ Chưa đủ thông tin để tạo đề thi!")
        return
    
    # Tóm tắt đề thi
    total_questions = len(st.session_state.exam_questions)
    total_points = sum(q['points'] for q in st.session_state.exam_questions)
    
    st.success("✅ Đề thi đã sẵn sàng!")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Câu hỏi", total_questions)
    with col2:
        st.metric("📊 Tổng điểm", f"{total_points:.1f}")
    with col3:
        st.metric("⏱️ Thời gian", f"{st.session_state.exam_time_limit} phút")
    with col4:
        avg_points = total_points / total_questions if total_questions > 0 else 0
        st.metric("📈 TB điểm/câu", f"{avg_points:.1f}")
    
    # Validation
    validation_issues = validate_exam()
    
    if validation_issues:
        st.error("❌ **Phát hiện vấn đề cần sửa:**")
        for issue in validation_issues:
            st.write(issue)
        return
    
    # Tùy chọn lưu
    if is_editing:
        st.write("**🚀 Cập nhật thay đổi**")
        if st.button("💾 Lưu thay đổi", use_container_width=True, type="primary"):
            update_existing_exam(user)
    else: # Đang tạo mới hoặc nhân bản
        col1, col2 = st.columns(2)
        with col1:
            st.write("**📝 Lưu nháp**")
            if st.button("💾 Lưu nháp", use_container_width=True, type="secondary"):
                save_exam_as_draft(user)
        with col2:
            st.write("**🚀 Phát hành ngay**")
            if st.button("🚀 Phát hành đề thi", use_container_width=True, type="primary"):
                publish_exam(user)
def validate_exam():
    """Validate đề thi trước khi lưu"""
    validation_issues = []
    
    # Kiểm tra thời gian
    start_datetime = datetime.combine(st.session_state.exam_start_date, st.session_state.exam_start_time)
    end_datetime = datetime.combine(st.session_state.exam_end_date, st.session_state.exam_end_time)
    
    if start_datetime >= end_datetime:
        validation_issues.append("⚠️ Thời gian kết thúc phải sau thời gian bắt đầu")
    
    # Kiểm tra câu hỏi
    for i, q in enumerate(st.session_state.exam_questions):
        if q['type'] == 'true_false' and 'statements' in q:
            if not any(stmt.get('is_correct', False) for stmt in q['statements']):
                validation_issues.append(f"⚠️ Câu {i+1} (đúng/sai) không có phát biểu nào đúng")
        elif q['type'] == 'multiple_choice' and not q.get('correct_answer'):
            validation_issues.append(f"⚠️ Câu {i+1} (trắc nghiệm) chưa có đáp án đúng")
    
    return validation_issues

def save_exam_as_draft(user):
    """Lưu đề thi dưới dạng nháp"""
    try:
        exam_data = prepare_exam_data(user, is_published=False)
        db = get_database()
        
        exam_id = db.create_exam(
            title=exam_data['title'],
            description=exam_data['description'],
            class_id=exam_data['class_id'],
            # teacher_id=exam_data['teacher_id'],
            questions=exam_data['questions'],
            time_limit=exam_data['time_limit'],
            start_time=exam_data['start_time'],
            end_time=exam_data['end_time'],
            instructions=exam_data.get('instructions')
        )
        
        if exam_id:
            st.success("✅ Đã lưu đề thi dưới dạng nháp!")
            st.info(f"📋 **Mã đề thi:** {exam_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Tạo đề thi mới", type="primary"):
                    clear_exam_data()
                    st.rerun()
            with col2:
                if st.button("📊 Xem danh sách đề thi"):
                    st.session_state.current_page = "statistics"
                    clear_exam_data()
                    st.rerun()
        else:
            st.error("❌ Lỗi lưu đề thi vào database!")
                
    except Exception as e:
        st.error(f"❌ Lỗi lưu đề thi: {str(e)}")

def publish_exam(user):
    """Phát hành đề thi"""
    try:
        exam_data = prepare_exam_data(user, is_published=True)
        db = get_database()
        
        exam_id = db.create_exam(
            title=exam_data['title'],
            description=exam_data['description'],
            class_id=exam_data['class_id'],
            # teacher_id=exam_data['teacher_id'],
            questions=exam_data['questions'],
            time_limit=exam_data['time_limit'],
            start_time=exam_data['start_time'],
            end_time=exam_data['end_time'],
            instructions=exam_data.get('instructions')
        )
        
        if exam_id:
            # Phát hành đề thi
            if db.publish_exam(exam_id):
                st.success("🎉 Đã phát hành đề thi thành công!")
                st.success(f"🔗 **Mã đề thi:** {exam_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📊 Theo dõi kết quả", type="primary"):
                        st.session_state.current_page = "grading"
                        clear_exam_data()
                        st.rerun()
                
                with col2:
                    if st.button("➕ Tạo đề thi mới"):
                        clear_exam_data()
                        st.rerun()
            else:
                st.error("❌ Lỗi phát hành đề thi!")
        else:
            st.error("❌ Lỗi tạo đề thi!")
                
    except Exception as e:
        st.error(f"❌ Lỗi phát hành đề thi: {str(e)}")

def prepare_exam_data(user, is_published=True):
    """Chuẩn bị dữ liệu đề thi để lưu"""
    # 1. Kết hợp ngày và giờ để tạo datetime "naive" từ lựa chọn của người dùng
    naive_start_datetime = datetime.combine(st.session_state.exam_start_date, st.session_state.exam_start_time)
    naive_end_datetime = datetime.combine(st.session_state.exam_end_date, st.session_state.exam_end_time)

    # 2. Gán múi giờ địa phương (đã định nghĩa ở đầu file) để biến nó thành "aware"
    aware_start_datetime = LOCAL_TIMEZONE.localize(naive_start_datetime)
    aware_end_datetime = LOCAL_TIMEZONE.localize(naive_end_datetime)

    # 3. Chuyển đổi thành chuỗi ISO 8601 chuẩn. 
    # Chuỗi này sẽ chứa thông tin múi giờ (ví dụ: ...+07:00)
    start_time_iso = aware_start_datetime.isoformat()
    end_time_iso = aware_end_datetime.isoformat()

    # (Tùy chọn) In ra để debug, bạn có thể xóa sau khi xác nhận
    print(f"DEBUG (Teacher Side): Start time selected (local): {aware_start_datetime}")
    print(f"DEBUG (Teacher Side): Start time to be saved (ISO): {start_time_iso}")
    
    processed_questions = []
    for i, q in enumerate(st.session_state.exam_questions):
        question_data = {
            'question_id': i + 1,
            'type': q['type'],
            'question': q['question'],
            'points': q['points'],
            'difficulty': q.get('difficulty', 'Trung bình'),
            'solution': q.get('solution', ''),
            'image_data': q.get('image_data')
        }
        
        if q['type'] == 'multiple_choice':
            question_data.update({
                'options': q['options'],
                'correct_answer': q['correct_answer']
            })
        elif q['type'] == 'true_false':
            question_data.update({
                'statements': q['statements'],
                'correct_answers': q.get('correct_answers', [])
            })
        elif q['type'] == 'short_answer':
            question_data.update({
                'sample_answers': q['sample_answers'],
                'case_sensitive': q.get('case_sensitive', False)
            })
        elif q['type'] == 'essay':
            question_data.update({
                'grading_criteria': q.get('grading_criteria', ''),
                'submission_type': q.get('submission_type', 'text'),
                'requires_image': q.get('requires_image', False)
            })
        
        processed_questions.append(question_data)
    
    exam_data = {
        'title': st.session_state.exam_title,
        'description': st.session_state.get('exam_description', ''),
        'instructions': st.session_state.get('exam_instructions', ''),
        'class_id': st.session_state.exam_class_id,
        # 'teacher_id': user['id'],
        'time_limit': st.session_state.exam_time_limit,
        'start_time': start_time_iso,
        'end_time': end_time_iso,
        'is_published': is_published,
        'questions': processed_questions
    }
    
    return exam_data

def clear_exam_data():
    """Xóa tất cả dữ liệu đề thi trong session"""
    keys_to_clear = [
        'exam_title', 'exam_description', 'exam_instructions',
        'exam_class_id', 'exam_class_name', 'exam_time_limit',
        'exam_start_date', 'exam_start_time', 'exam_end_date', 'exam_end_time',
        'exam_questions', 'current_question', 'edit_question_index'
        'editing_exam_id_value'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]