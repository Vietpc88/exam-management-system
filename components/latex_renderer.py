import streamlit as st
import re

def render_latex_text(text):
    """Render text có chứa LaTeX"""
    if not text:
        return
    
    # Kiểm tra có LaTeX không
    if '$' not in text:
        st.markdown(text)
        return
    
    # Chia text thành các phần
    parts = split_latex_text(text)
    
    # Render từng phần
    for part in parts:
        if part['type'] == 'latex':
            st.latex(part['content'])
        else:
            if part['content'].strip():
                st.markdown(part['content'])

def split_latex_text(text):
    """Chia text thành các phần LaTeX và text thường"""
    parts = []
    current_pos = 0
    
    # Tìm tất cả LaTeX patterns
    latex_patterns = [
        (r'\$\$([^$]+)\$\$', 'display'),  # Display math $$...$$
        (r'\$([^$]+)\$', 'inline')        # Inline math $...$
    ]
    
    matches = []
    for pattern, math_type in latex_patterns:
        for match in re.finditer(pattern, text):
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'content': match.group(1),
                'type': math_type,
                'full_match': match.group(0)
            })
    
    # Sắp xếp theo vị trí
    matches.sort(key=lambda x: x['start'])
    
    # Chia text
    for match in matches:
        # Text trước LaTeX
        if current_pos < match['start']:
            text_part = text[current_pos:match['start']]
            if text_part.strip():
                parts.append({
                    'type': 'text',
                    'content': text_part
                })
        
        # Phần LaTeX
        parts.append({
            'type': 'latex',
            'content': match['content']
        })
        
        current_pos = match['end']
    
    # Text còn lại
    if current_pos < len(text):
        remaining_text = text[current_pos:]
        if remaining_text.strip():
            parts.append({
                'type': 'text',
                'content': remaining_text
            })
    
    return parts

def setup_mathjax():
    """Setup MathJax cho Streamlit"""
    st.markdown("""
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
    window.MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']],
            displayMath: [['$$', '$$'], ['\\[', '\\]']]
        },
        svg: {
            fontCache: 'global'
        }
    };
    </script>
    """, unsafe_allow_html=True)

def render_math_html(text):
    """Render LaTeX as HTML với MathJax"""
    if not text or '$' not in text:
        return st.markdown(text)
    
    # Setup MathJax nếu chưa có
    if 'mathjax_setup' not in st.session_state:
        setup_mathjax()
        st.session_state.mathjax_setup = True
    
    # Render với HTML + MathJax
    html_content = f"""
    <div class="math-content">
        {text}
    </div>
    <script>
        if (window.MathJax) {{
            MathJax.typesetPromise();
        }}
    </script>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)

def clean_latex_for_display(text):
    """Làm sạch LaTeX để hiển thị"""
    if not text:
        return ""
    
    # Các cleanup cơ bản
    text = re.sub(r'\\text\s*\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\left\s*', '', text)
    text = re.sub(r'\\right\s*', '', text)
    text = re.sub(r'\\limits', '', text)
    text = re.sub(r'\\,', ' ', text)
    
    return text

def preview_latex_question(question):
    """Preview câu hỏi có LaTeX"""
    st.markdown("**Câu hỏi:**")
    render_latex_text(question.get('question', ''))
    
    if question['type'] == 'multiple_choice':
        st.markdown("**Lựa chọn:**")
        for i, option in enumerate(question.get('options', [])):
            prefix = "✅" if chr(65+i) == question.get('correct_answer') else "○"
            st.markdown(f"{prefix} **{chr(65+i)}.** ", end="")
            render_latex_text(option)
    
    elif question['type'] == 'short_answer':
        answers = question.get('sample_answers', [])
        if answers:
            st.markdown("**Đáp án:**")
            render_latex_text(", ".join(answers))
    
    # Hiển thị lời giải nếu có
    if question.get('solution'):
        st.markdown("**Lời giải:**")
        render_latex_text(question['solution'])