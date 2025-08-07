# core/grading_logic.py

import streamlit as st
from database.supabase_models import get_database

# Di chuyển các import liên quan đến AI vào đây
try:
    from admin.ai_grader import grade_essay_with_ai
except ImportError:
    def grade_essay_with_ai(*args, **kwargs):
        print("ERROR: AI Grader module not found.")
        return {'suggested_score': 0.0, 'feedback': 'Lỗi AI Grader'}

# --- CÁC HÀM LOGIC CHẤM ĐIỂM ---

def calculate_auto_score(question, student_answer):
    """Tính điểm tự động cho các câu trắc nghiệm."""
    if not student_answer: return 0.0
    q_type = question.get('type')
    points = float(question.get('points', 0))

    if q_type == 'multiple_choice':
        return points if student_answer.get('selected_option') == question.get('correct_answer') else 0.0
    
    if q_type == 'true_false':
        correct_answers = set(question.get('correct_answers', []))
        student_answers = set(student_answer.get('selected_answers', []))
        return points if correct_answers == student_answers else 0.0

    if q_type == 'short_answer':
        correct_options = [ans.lower() for ans in question.get('sample_answers', [])]
        student_ans_text = (student_answer.get('answer_text', '') or '').lower().strip()
        return points if student_ans_text in correct_options else 0.0
        
    return 0.0

def run_essay_auto_grading(submission_id: str):
    """Chạy quy trình chấm tự luận bằng AI và cập nhật tổng điểm."""
    db = get_database()
    try:
        submission = db.get_submission_by_id(submission_id)
        if not submission or submission.get('grading_status') != 'partially_graded':
            return

        exam = db.get_exam_by_id(submission['exam_id'])
        if not exam: return

        student_answers = submission.get('answers', [])
        exam_questions = exam.get('questions', [])
        
        tu_luan_score = 0
        question_scores_map = submission.get('question_scores', {}) 
        feedback_parts = []

        for q in exam_questions:
            if q.get('type') == 'essay':
                q_id_str = str(q.get('question_id'))
                student_answer = next((ans for ans in student_answers if ans.get('question_id') == q['question_id']), None)
                
                rubric = q.get('grading_criteria', '')
                score = 0.0
                if rubric:
                    ai_result = grade_essay_with_ai(
                        question_text=q.get('question', ''),
                        grading_rubric=rubric,
                        max_score=float(q.get('points', 0)),
                        student_answer_text=student_answer.get('answer_text', '') if student_answer else '',
                        student_image_base64=student_answer.get('image_data', None) if student_answer else None
                    )
                    score = ai_result['suggested_score']
                    feedback_parts.append(f"Câu {q['question_id']}: {ai_result['feedback']}")
                
                tu_luan_score += score
                question_scores_map[q_id_str] = score
        
        final_score = submission.get('trac_nghiem_score', 0) + tu_luan_score
        final_feedback = "\n".join(feedback_parts)

        db.update_final_grade(
            submission_id=submission_id,
            final_score=final_score,
            tu_luan_score=tu_luan_score,
            question_scores=question_scores_map,
            feedback=final_feedback
        )
        print(f"SUCCESS: AI grading complete for submission {submission_id}")

    except Exception as e:
        print(f"ERROR: AI grading failed for submission {submission_id}: {e}")