import streamlit as st
import base64
from datetime import datetime
from database.supabase_models import get_database
from auth.login import get_current_user

# Giả sử bạn có hàm render_mathjax từ một module khác
try:
    from admin.word_parser import render_mathjax
except ImportError:
    def render_mathjax():
        st.warning("Lỗi: Không thể tải hàm render_mathjax.")

# --- HÀM CHÍNH ĐIỀU HƯỚNG (ROUTER) ---
def show_view_results():
    """
    Hàm chính cho trang "Xem kết quả".
    Hoạt động như một router để quyết định hiển thị danh sách hay chi tiết.
    """
    user = get_current_user()
    db = get_database()

    # Nếu có submission_id được chọn (từ trang làm bài hoặc danh sách), hiển thị chi tiết
    # `last_submission_id` được set khi vừa nộp bài xong
    # `selected_submission_id` được set khi bấm nút "Xem chi tiết" từ danh sách
    submission_id_to_view = st.session_state.get("last_submission_id") or st.session_state.get("selected_submission_id")

    if submission_id_to_view:
        show_exam_result_detail(user, db, submission_id_to_view)
    else:
        # Nếu không, hiển thị danh sách tất cả kết quả
        show_all_results_list(user, db)

# --- TRANG 1: DANH SÁCH TẤT CẢ KẾT QUẢ ---
def show_all_results_list(user, db):
    """Hiển thị danh sách tất cả kết quả thi của học sinh."""
    st.header("📊 Bảng điểm của tôi")
    
    try:
        results = db.get_student_results(user['id'])
        if not results:
            st.info("💡 Bạn chưa có bài thi nào được chấm điểm.")
            return
        
        results.sort(key=lambda r: r.get('submitted_at', ''), reverse=True)

        for result in results:
            score = result.get('score')
            max_score = result.get('max_score', 0)
            
            with st.container(border=True):
                st.markdown(f"#### {result.get('exam_title', 'Không có tiêu đề')}")
                st.caption(f"Lớp: {result.get('class_name', 'N/A')}")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    submitted_date_str = result.get('submitted_at', '')
                    if submitted_date_str:
                        submitted_date = datetime.fromisoformat(submitted_date_str.replace('Z', '+00:00')).strftime('%H:%M - %d/%m/%Y')
                        st.write(f"**Nộp bài lúc:** {submitted_date}")

                    if result.get('is_graded'):
                        st.progress(int((score / max_score) * 100) if max_score > 0 else 0)
                        st.write(f"**Điểm số:** **<span style='font-size: 1.2em; color: #0984e3;'>{score:.2f} / {max_score:.2f}</span>**", unsafe_allow_html=True)
                    else:
                        st.info("⏳ _Bài thi đang được chấm..._")
                
                with col2:
                    if result.get('is_graded'):
                        grade, color, icon = get_grade_info((score / max_score) * 100 if max_score > 0 else 0)
                        st.markdown(f"""
                        <div style='background-color: {color}; color: white; border-radius: 8px; text-align: center; padding: 10px; margin-top: 10px;'>
                            <span style='font-size:1.5em; font-weight: bold;'>{icon} {grade}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if st.button("👁️ Xem chi tiết", key=f"view_detail_{result['id']}", use_container_width=True, type="primary"):
                        st.session_state.selected_submission_id = result['id']
                        st.rerun()
                st.markdown("---")
                
    except Exception as e:
        st.error(f"❌ Lỗi khi tải bảng điểm: {e}")

# --- TRANG 2: KẾT QUẢ CHI TIẾT CỦA MỘT BÀI THI ---
def show_exam_result_detail(user, db, submission_id):
    """Hiển thị chi tiết kết quả bài làm của học sinh một cách trực quan."""
    try:
        submission = db.get_submission_by_id(submission_id)
        if not submission: st.error("Không tìm thấy dữ liệu bài làm."); return
        exam = db.get_exam_by_id(submission['exam_id'])
        if not exam: st.error("Không tìm thấy dữ liệu đề thi."); return
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu kết quả: {e}"); return

    render_mathjax()
    st.header(f"📜 Kết quả chi tiết: {exam.get('title', '')}")
    
    # Nút quay lại danh sách
    if st.button("⬅️ Quay lại danh sách kết quả"):
        # Xóa các key state để đảm bảo quay lại đúng trang danh sách
        if "selected_submission_id" in st.session_state: del st.session_state.selected_submission_id
        if "last_submission_id" in st.session_state: del st.session_state.last_submission_id
        st.rerun()

    # BẢNG ĐIỂM TÓM TẮT
    st.subheader("📊 Bảng điểm")
    grading_status = submission.get('grading_status', 'pending')
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        trac_nghiem_score = submission.get('trac_nghiem_score', 0)
        max_trac_nghiem = sum(q.get('points', 0) for q in exam.get('questions', []) if q.get('type') != 'essay')
        col1.metric("Điểm Trắc nghiệm", f"{trac_nghiem_score or 0:.2f}", f"/ {max_trac_nghiem:.2f}")

        if grading_status == 'fully_graded':
            tu_luan_score = submission.get('tu_luan_score', 0)
            max_tu_luan = sum(q.get('points', 0) for q in exam.get('questions', []) if q.get('type') == 'essay')
            col2.metric("Điểm Tự luận", f"{tu_luan_score or 0:.2f}", f"/ {max_tu_luan:.2f}")
            col3.metric("🎉 TỔNG ĐIỂM", f"{submission.get('score', 0):.2f}", f"/ {exam.get('total_points', 0):.2f}")
        else:
            col2.metric("Điểm Tự luận", "⏳", "Đang chấm")
            col3.metric("Tổng điểm (Tạm tính)", f"{submission.get('score', 0):.2f}")

    if submission.get('feedback'):
        with st.expander("💬 Xem nhận xét chung"): st.markdown(submission['feedback'])

    st.divider()
    st.subheader("📝 Bài làm chi tiết")

    # HIỂN THỊ CHI TIẾT TỪNG CÂU
    student_answers_map = {ans.get('question_id'): ans for ans in submission.get('answers', [])}
    for i, question in enumerate(exam.get('questions', [])):
        q_id = question.get('question_id')
        student_answer = student_answers_map.get(q_id)
        
        with st.container(border=True):
            st.markdown(f"**Câu {i+1}:** ({question.get('points', 0)} điểm)")
            st.markdown(question.get('question', ''))
            if question.get('image_data'):
                try: st.image(base64.b64decode(question['image_data']))
                except: st.caption("Lỗi hiển thị hình ảnh câu hỏi.")
            st.markdown("---")
            
            # --- Xử lý hiển thị theo loại câu hỏi ---
            q_type = question.get('type')
            if q_type == 'multiple_choice':
                render_mc_result(question, student_answer)
            elif q_type == 'true_false':
                render_tf_result(question, student_answer)
            elif q_type == 'short_answer':
                render_sa_result(question, student_answer)
            elif q_type == 'essay':
                render_essay_result(question, student_answer, submission)

            if question.get('solution'):
                with st.expander("💡 Xem lời giải chi tiết"): st.markdown(question['solution'])

# --- HÀM RENDER CHI TIẾT CHO TỪNG LOẠI CÂU HỎI ---
def render_mc_result(question, student_answer):
    correct_option = question.get('correct_answer')
    student_choice = student_answer.get('selected_option') if student_answer else None
    for j, option_text in enumerate(question.get('options', [])):
        option_letter = chr(ord('A') + j)
        display_text = f"**{option_letter}.** {option_text}"
        if option_letter == correct_option:
            st.success(f" {display_text} (Đáp án đúng)", icon="✅")
        elif option_letter == student_choice:
            st.error(f" {display_text} (Lựa chọn của bạn)", icon="❌")
        else:
            st.write(display_text)
    if not student_choice: st.warning("Bạn đã không trả lời câu này.", icon="⚠️")

def render_tf_result(question, student_answer):
    correct_answers = set(question.get('correct_answers', []))
    student_choices = set(student_answer.get('selected_answers', [])) if student_answer else set()
    for stmt in question.get('statements', []):
        stmt_letter = stmt.get('letter')
        is_correct = stmt_letter in correct_answers
        did_choose = stmt_letter in student_choices
        display_text = f"**{stmt_letter})** {stmt.get('text')}"
        if is_correct:
            st.success(f" {display_text} (Đáp án đúng)", icon="✅" if did_choose else " ")
        else: # Đáp án là Sai
            if did_choose: st.error(f" {display_text} (Bạn chọn sai)", icon="❌")
            else: st.write(display_text)
    if not student_choices: st.warning("Bạn đã không trả lời câu này.", icon="⚠️")

def render_sa_result(question, student_answer):
    correct_answers = question.get('sample_answers', [])
    student_text = (student_answer.get('answer_text') or '').strip() if student_answer else ""
    st.success(f"**Đáp án đúng:** {', '.join(correct_answers)}", icon="✅")
    if not student_text:
        st.warning("Bạn đã không trả lời câu này.", icon="⚠️")
    elif student_text.lower() in [ans.lower() for ans in correct_answers]:
        st.success(f"**Bạn trả lời:** {student_text}", icon="👍")
    else:
        st.error(f"**Bạn trả lời:** {student_text}", icon="❌")

def render_essay_result(question, student_answer, submission):
    st.info("Đây là câu hỏi tự luận. Điểm và nhận xét được cung cấp bởi giáo viên hoặc AI.", icon="✍️")
    if student_answer:
        if student_answer.get('answer_text'):
            st.text_area("Bài làm của bạn (văn bản):", student_answer['answer_text'], disabled=True, height=150)
        if student_answer.get('image_data'):
            st.image(base64.b64decode(student_answer['image_data']), caption="Bài làm của bạn (hình ảnh)")
    else:
        st.warning("Bạn đã không trả lời câu này.", icon="⚠️")
    
    q_id = str(question.get('question_id'))
    q_scores = submission.get('question_scores', {})
    essay_score = q_scores.get(q_id)
    if essay_score is not None:
        st.success(f"**Điểm nhận được:** {essay_score:.2f} / {question.get('points', 0)}")

# --- HÀM HỖ TRỢ ---
def get_grade_info(percentage: float) -> tuple[str, str, str]:
    """Trả về (Xếp loại, Màu sắc, Icon) dựa trên phần trăm điểm."""
    if not isinstance(percentage, (int, float)): return "Chưa có", "#bdc3c7", "❓"
    if percentage >= 90: return "Xuất sắc", "#27ae60", "🌟"
    if percentage >= 80: return "Giỏi", "#2980b9", "🏆"
    if percentage >= 65: return "Khá", "#f39c12", "👍"
    if percentage >= 50: return "Đạt", "#d35400", "📚"
    return "Cần cố gắng", "#c0392b", "📖"