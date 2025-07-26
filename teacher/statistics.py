import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np
from datetime import datetime, timedelta

# Safe imports - now using real database
try:
    from auth.login import get_current_user
    from database.supabase_models import SupabaseDatabase
except ImportError:
    # Fallback if modules don't exist
    def get_current_user():
        return {'id': 'mock_teacher_id', 'ho_ten': 'Mock Teacher', 'username': 'teacher', 'role': 'teacher'}
    
    class SupabaseDatabase:
        def get_classes_by_teacher(self, teacher_id):
            return []
        def get_exams_by_teacher(self, teacher_id):
            return []
        def get_dashboard_stats(self, teacher_id):
            return {'class_count': 0, 'student_count': 0, 'exam_count': 0, 'submission_count': 0}

# Set matplotlib style
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'

# Initialize database
@st.cache_resource
def get_database():
    """Get database instance"""
    return SupabaseDatabase()

def show_statistics():
    """Giao diện thống kê chính"""
    st.header("📊 Thống kê")
    
    user = get_current_user()
    db = get_database()
    
    # Sidebar để lọc dữ liệu
    with st.sidebar:
        st.write("### 🔍 Bộ lọc thống kê")
        
        # Lọc theo thời gian
        time_filter = st.selectbox(
            "Khoảng thời gian:",
            ["7 ngày qua", "30 ngày qua", "Học kỳ này", "Năm học này", "Tất cả"],
            key="time_filter"
        )
        
        # Lọc theo lớp
        try:
            classes_data = db.get_classes_by_teacher(user['id'])
            class_options = ["Tất cả lớp"] + [f"{c['ten_lop']}" for c in classes_data]
        except:
            class_options = ["Tất cả lớp"]
            
        selected_class = st.selectbox(
            "Lớp học:",
            class_options,
            key="class_filter"
        )
        
        # Lọc theo loại thống kê
        stat_type = st.selectbox(
            "Loại thống kê:",
            ["Tổng quan", "Chi tiết lớp", "Chi tiết đề thi", "So sánh"],
            key="stat_type"
        )
    
    # Hiển thị thống kê theo loại được chọn
    if stat_type == "Tổng quan":
        show_overview_statistics(user, time_filter, selected_class, db)
    elif stat_type == "Chi tiết lớp":
        show_class_detailed_statistics(user, time_filter, selected_class, db)
    elif stat_type == "Chi tiết đề thi":
        show_exam_detailed_statistics(user, time_filter, selected_class, db)
    elif stat_type == "So sánh":
        show_comparison_statistics(user, time_filter, selected_class, db)

def show_overview_statistics(user, time_filter, selected_class, db):
    """Thống kê tổng quan"""
    st.subheader("📈 Thống kê tổng quan")
    
    # Lấy dữ liệu thống kê từ database thật
    try:
        stats = db.get_dashboard_stats(user['id'])
        
        # Metrics chính
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "🏫 Lớp học", 
                stats['class_count']
            )
        
        with col2:
            st.metric(
                "👥 Học sinh", 
                stats['student_count']
            )
        
        with col3:
            st.metric(
                "📝 Đề thi", 
                stats['exam_count']
            )
        
        with col4:
            st.metric(
                "📊 Bài làm", 
                stats['submission_count']
            )
        
        with col5:
            # Tính điểm trung bình (mock - sẽ implement sau)
            avg_score = 8.2  # TODO: Tính từ database
            st.metric(
                "📈 Điểm TB", 
                f"{avg_score:.1f}"
            )
        
        st.divider()
        
        # Hiển thị biểu đồ với mock data (sẽ thay bằng real data)
        show_overview_charts_with_real_data(user, db)
        
    except Exception as e:
        st.error(f"❌ Lỗi lấy thống kê: {str(e)}")
        # Hiển thị thống kê mock
        show_mock_overview_statistics()

def show_overview_charts_with_real_data(user, db):
    """Hiển thị biểu đồ với dữ liệu thật"""
    try:
        classes_data = db.get_classes_by_teacher(user['id'])
        
        if classes_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Biểu đồ số học sinh theo lớp (real data)
                st.write("### 📈 Số học sinh theo lớp")
                
                class_names = []
                student_counts = []
                
                for class_data in classes_data:
                    class_names.append(class_data['ten_lop'])
                    student_count = db.get_class_student_count(class_data['id'])
                    student_counts.append(student_count)
                
                if class_names:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.bar(class_names, student_counts, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc'])
                    ax.set_title("Số học sinh theo lớp")
                    ax.set_ylabel("Số học sinh")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.info("📊 Chưa có dữ liệu lớp học")
            
            with col2:
                # Biểu đồ phân bố đề thi (mock - sẽ implement)
                st.write("### 🎯 Phân bố đề thi theo trạng thái")
                
                # Mock data cho demo
                labels = ['Đã phát hành', 'Nháp', 'Đã đóng']
                values = [5, 3, 2]  # TODO: Lấy từ database
                
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title("Trạng thái đề thi")
                st.pyplot(fig)
        else:
            st.info("📊 Chưa có dữ liệu để hiển thị biểu đồ")
            
    except Exception as e:
        st.warning(f"⚠️ Lỗi hiển thị biểu đồ: {str(e)}")
        show_mock_overview_charts()

def show_mock_overview_statistics():
    """Hiển thị thống kê mock khi có lỗi"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🏫 Lớp học", "--", delta="DB Error")
    with col2:
        st.metric("👥 Học sinh", "--", delta="DB Error")
    with col3:
        st.metric("📝 Đề thi", "--", delta="DB Error")
    with col4:
        st.metric("📊 Bài làm", "--", delta="DB Error")
    with col5:
        st.metric("📈 Điểm TB", "--", delta="DB Error")

def show_mock_overview_charts():
    """Hiển thị biểu đồ mock"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("📊 Biểu đồ sẽ hiển thị khi có dữ liệu lớp học")
    
    with col2:
        st.info("📊 Biểu đồ sẽ hiển thị khi có dữ liệu đề thi")

def show_class_detailed_statistics(user, time_filter, selected_class):
    """Thống kê chi tiết theo lớp"""
    st.subheader("🏫 Thống kê chi tiết lớp")
    
    classes = get_classes_by_teacher(user['id'])
    
    if selected_class == "Tất cả lớp":
        st.info("👆 Chọn một lớp cụ thể trong sidebar để xem thống kê chi tiết")
        
        # Hiển thị overview tất cả lớp
        for class_info in classes:
            with st.expander(f"📚 {class_info['name']} - {class_info['student_count']} học sinh", expanded=False):
                show_single_class_statistics(class_info['id'], time_filter)
        
        return
    
    # Tìm lớp được chọn
    selected_class_info = next((c for c in classes if c['name'] == selected_class), None)
    
    if not selected_class_info:
        st.error("❌ Không tìm thấy lớp được chọn!")
        return
    
    # Hiển thị chi tiết lớp
    show_single_class_statistics(selected_class_info['id'], time_filter)

def show_single_class_statistics(class_id, time_filter):
    """Hiển thị thống kê của một lớp"""
    class_stats = get_class_detailed_stats(class_id, time_filter)
    
    # Header thông tin lớp
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3>📚 {class_stats['class_name']}</h3>
        <p>👥 {class_stats['total_students']} học sinh | 📝 {class_stats['total_exams']} đề thi | 📊 {class_stats['total_submissions']} bài nộp</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Điểm TB lớp", f"{class_stats['class_average']:.1f}")
    
    with col2:
        st.metric("✅ Tỷ lệ nộp bài", f"{class_stats['submission_rate']:.1f}%")
    
    with col3:
        st.metric("🎯 Tỷ lệ đạt", f"{class_stats['pass_rate']:.1f}%")
    
    with col4:
        st.metric("⭐ Học sinh giỏi", f"{class_stats['excellent_rate']:.1f}%")
    
    # Biểu đồ và bảng
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 📈 Xu hướng điểm theo thời gian")
        score_trend = get_class_score_trend(class_id, time_filter)
        
        if score_trend:
            df_trend = pd.DataFrame(score_trend)
            fig, ax = plt.subplots(figsize=(10, 6))
            df_trend['exam_date'] = pd.to_datetime(df_trend['exam_date'])
            ax.plot(df_trend['exam_date'], df_trend['average_score'], marker='o')
            ax.set_title("Điểm trung bình theo đề thi")
            ax.set_xlabel("Ngày thi")
            ax.set_ylabel("Điểm TB")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("📊 Chưa có dữ liệu xu hướng")
    
    with col2:
        st.write("#### 🎯 Phân bố học lực")
        grade_distribution = get_class_grade_distribution(class_id, time_filter)
        
        if grade_distribution:
            labels = ['Xuất sắc', 'Giỏi', 'Khá', 'Trung bình', 'Yếu']
            values = [grade_distribution.get(label, 0) for label in labels]
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title("Phân bố học lực")
            st.pyplot(fig)
        else:
            st.info("📊 Chưa có dữ liệu học lực")
    
    # Bảng chi tiết học sinh
    st.write("#### 👥 Chi tiết học sinh")
    student_details = get_class_student_details(class_id, time_filter)
    
    if student_details:
        df_students = pd.DataFrame(student_details)
        
        # Thêm cột xếp hạng
        df_students = df_students.sort_values('average_score', ascending=False)
        df_students['rank'] = range(1, len(df_students) + 1)
        
        # Format hiển thị
        display_columns = ['rank', 'student_name', 'average_score', 'total_submissions', 'grade']
        display_df = df_students[display_columns].copy()
        display_df.columns = ['Hạng', 'Học sinh', 'Điểm TB', 'Số bài', 'Học lực']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Buttons xuất dữ liệu
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Xuất Excel", key=f"export_class_{class_id}"):
                excel_data = export_class_statistics_to_excel(class_id, time_filter)
                st.download_button(
                    label="💾 Tải file Excel",
                    data=excel_data,
                    file_name=f"thong_ke_lop_{class_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if st.button("📊 Tạo báo cáo", key=f"report_class_{class_id}"):
                generate_class_report(class_id, time_filter)
    else:
        st.info("👥 Chưa có dữ liệu học sinh")

def show_exam_detailed_statistics(user, time_filter, selected_class):
    """Thống kê chi tiết theo đề thi"""
    st.subheader("📝 Thống kê chi tiết đề thi")
    
    # Lấy danh sách đề thi
    exams = get_teacher_exams(user['id'], time_filter, selected_class)
    
    if not exams:
        st.info("📝 Không có đề thi nào trong khoảng thời gian được chọn!")
        return
    
    # Chọn đề thi để phân tích
    exam_options = {f"{exam['title']} ({exam['class_name']}) - {exam['created_at'][:10]}": exam['id'] for exam in exams}
    selected_exam_title = st.selectbox("Chọn đề thi:", list(exam_options.keys()))
    selected_exam_id = exam_options[selected_exam_title]
    
    # Hiển thị thống kê đề thi
    show_single_exam_statistics(selected_exam_id)

def show_single_exam_statistics(exam_id):
    """Hiển thị thống kê của một đề thi"""
    exam_stats = get_exam_detailed_stats(exam_id)
    
    # Header thông tin đề thi
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); color: #333; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3>📝 {exam_stats['title']}</h3>
        <p>🏫 {exam_stats['class_name']} | ⏱️ {exam_stats['time_limit']} phút | 📊 {exam_stats['total_points']} điểm</p>
        <p>📅 Thời gian: {exam_stats['start_time'][:16]} - {exam_stats['end_time'][:16]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics đề thi
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("👥 Đã nộp", exam_stats['submission_count'])
    
    with col2:
        st.metric("📈 Điểm TB", f"{exam_stats['average_score']:.1f}")
    
    with col3:
        st.metric("⭐ Điểm cao nhất", f"{exam_stats['highest_score']:.1f}")
    
    with col4:
        st.metric("📉 Điểm thấp nhất", f"{exam_stats['lowest_score']:.1f}")
    
    with col5:
        st.metric("🎯 Tỷ lệ đạt", f"{exam_stats['pass_rate']:.1f}%")
    
    # Biểu đồ phân tích
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 📊 Phân bố điểm số")
        score_histogram = get_exam_score_histogram(exam_id)
        
        if score_histogram:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.hist(score_histogram, bins=10, edgecolor='black', alpha=0.7)
            ax.set_title("Phân bố điểm số")
            ax.set_xlabel("Điểm")
            ax.set_ylabel("Số học sinh")
            st.pyplot(fig)
        else:
            st.info("📊 Chưa có dữ liệu điểm")
    
    with col2:
        st.write("#### ⏱️ Thời gian làm bài")
        time_distribution = get_exam_time_distribution(exam_id)
        
        if time_distribution:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.boxplot(time_distribution)
            ax.set_title("Phân bố thời gian làm bài (phút)")
            ax.set_ylabel("Thời gian (phút)")
            st.pyplot(fig)
        else:
            st.info("📊 Chưa có dữ liệu thời gian")
    
    # Thống kê theo câu hỏi
    st.write("#### 📝 Phân tích từng câu hỏi")
    question_analysis = get_exam_question_analysis(exam_id)
    
    if question_analysis:
        df_questions = pd.DataFrame(question_analysis)
        
        # Tạo biểu đồ tỷ lệ đúng
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(df_questions['question_number'], df_questions['correct_rate'], 
               color=plt.cm.RdYlGn(df_questions['correct_rate']/100))
        ax.set_title("Tỷ lệ trả lời đúng theo câu")
        ax.set_xlabel("Câu hỏi")
        ax.set_ylabel("Tỷ lệ đúng (%)")
        st.pyplot(fig)
        
        # Bảng chi tiết
        display_df = df_questions.copy()
        display_df.columns = ['Câu', 'Loại', 'Điểm', 'Tỷ lệ đúng (%)', 'Điểm TB', 'Độ khó']
        st.dataframe(display_df, use_container_width=True)
        
        # Phân tích câu hỏi khó
        difficult_questions = df_questions[df_questions['correct_rate'] < 50]
        if not difficult_questions.empty:
            st.warning(f"⚠️ **Phát hiện {len(difficult_questions)} câu hỏi khó:**")
            for _, q in difficult_questions.iterrows():
                st.write(f"- Câu {q['question_number']}: {q['correct_rate']:.1f}% học sinh trả lời đúng")
    else:
        st.info("📊 Chưa có dữ liệu phân tích câu hỏi")
    
    # Xuất báo cáo
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Xuất báo cáo Excel", key=f"export_exam_{exam_id}"):
            excel_data = export_exam_statistics_to_excel(exam_id)
            st.download_button(
                label="💾 Tải file Excel",
                data=excel_data,
                file_name=f"thong_ke_de_thi_{exam_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📊 Tạo báo cáo chi tiết", key=f"report_exam_{exam_id}"):
            generate_exam_report(exam_id)

def show_comparison_statistics(user, time_filter, selected_class):
    """Thống kê so sánh"""
    st.subheader("🔄 So sánh thống kê")
    
    # Tùy chọn so sánh
    comparison_type = st.selectbox(
        "Loại so sánh:",
        ["So sánh lớp học", "So sánh đề thi", "So sánh theo thời gian", "So sánh học sinh"],
        key="comparison_type"
    )
    
    if comparison_type == "So sánh lớp học":
        show_class_comparison(user, time_filter)
    elif comparison_type == "So sánh đề thi":
        show_exam_comparison(user, time_filter)
    elif comparison_type == "So sánh theo thời gian":
        show_time_comparison(user, selected_class)
    elif comparison_type == "So sánh học sinh":
        show_student_comparison(user, time_filter, selected_class)

def show_class_comparison(user, time_filter):
    """So sánh giữa các lớp"""
    st.write("### 🏫 So sánh giữa các lớp")
    
    classes = get_classes_by_teacher(user['id'])
    
    if len(classes) < 2:
        st.info("📚 Cần có ít nhất 2 lớp để so sánh!")
        return
    
    # Chọn lớp để so sánh
    class_options = [c['name'] for c in classes]
    selected_classes = st.multiselect(
        "Chọn lớp để so sánh:",
        class_options,
        default=class_options[:2] if len(class_options) >= 2 else class_options
    )
    
    if len(selected_classes) < 2:
        st.warning("⚠️ Vui lòng chọn ít nhất 2 lớp để so sánh!")
        return
    
    # Lấy dữ liệu so sánh
    comparison_data = get_class_comparison_data(user['id'], selected_classes, time_filter)
    
    if not comparison_data:
        st.info("📊 Chưa có dữ liệu để so sánh!")
        return
    
    # Biểu đồ so sánh
    col1, col2 = st.columns(2)
    
    with col1:
        # So sánh điểm trung bình
        df_avg = pd.DataFrame([
            {'Lớp': data['class_name'], 'Điểm TB': data['average_score']} 
            for data in comparison_data
        ])
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(df_avg['Lớp'], df_avg['Điểm TB'], color=plt.cm.RdYlGn(df_avg['Điểm TB']/10))
        ax.set_title("So sánh điểm trung bình")
        ax.set_xlabel("Lớp")
        ax.set_ylabel("Điểm TB")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        # So sánh tỷ lệ đạt
        df_pass = pd.DataFrame([
            {'Lớp': data['class_name'], 'Tỷ lệ đạt (%)': data['pass_rate']} 
            for data in comparison_data
        ])
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(df_pass['Lớp'], df_pass['Tỷ lệ đạt (%)'], color=plt.cm.RdYlGn(df_pass['Tỷ lệ đạt (%)']/100))
        ax.set_title("So sánh tỷ lệ đạt")
        ax.set_xlabel("Lớp")
        ax.set_ylabel("Tỷ lệ đạt (%)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    
    # Bảng so sánh chi tiết
    st.write("### 📊 Bảng so sánh chi tiết")
    
    comparison_df = pd.DataFrame([
        {
            'Lớp': data['class_name'],
            'Số HS': data['student_count'],
            'Điểm TB': data['average_score'],
            'Tỷ lệ đạt (%)': data['pass_rate'],
            'HS Giỏi (%)': data['excellent_rate'],
            'Số đề thi': data['exam_count'],
            'Số bài nộp': data['submission_count']
        }
        for data in comparison_data
    ])
    
    st.dataframe(comparison_df, use_container_width=True)

def show_exam_comparison(user, time_filter):
    """So sánh giữa các đề thi"""
    st.write("### 📝 So sánh giữa các đề thi")
    
    exams = get_teacher_exams(user['id'], time_filter, "Tất cả lớp")
    
    if len(exams) < 2:
        st.info("📝 Cần có ít nhất 2 đề thi để so sánh!")
        return
    
    # Chọn đề thi để so sánh
    exam_options = {f"{exam['title']} ({exam['class_name']})": exam['id'] for exam in exams}
    selected_exams = st.multiselect(
        "Chọn đề thi để so sánh:",
        list(exam_options.keys()),
        default=list(exam_options.keys())[:2] if len(exam_options) >= 2 else list(exam_options.keys())
    )
    
    if len(selected_exams) < 2:
        st.warning("⚠️ Vui lòng chọn ít nhất 2 đề thi để so sánh!")
        return
    
    selected_exam_ids = [exam_options[exam_name] for exam_name in selected_exams]
    
    # Lấy dữ liệu so sánh
    exam_comparison_data = get_exam_comparison_data(selected_exam_ids)
    
    # Biểu đồ so sánh đơn giản
    st.write("### 📊 So sánh các đề thi")
    
    comparison_df = pd.DataFrame([
        {
            'Đề thi': data['exam_title'],
            'Lớp': data['class_name'],
            'Điểm TB': data['average_score'],
            'Tỷ lệ đạt (%)': data['pass_rate'],
            'Số bài nộp': data['submission_count'],
            'Thời gian TB (phút)': data['avg_completion_time'],
            'Độ khó': data['difficulty_level']
        }
        for data in exam_comparison_data
    ])
    
    st.dataframe(comparison_df, use_container_width=True)
    
    # Biểu đồ so sánh điểm TB
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(comparison_df['Đề thi'], comparison_df['Điểm TB'])
    ax.set_title("So sánh điểm trung bình")
    ax.set_ylabel("Điểm TB")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

def show_time_comparison(user, selected_class):
    """So sánh theo thời gian"""
    st.write("### 📅 So sánh theo thời gian")
    
    # Chọn khoảng thời gian
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Từ ngày:", value=datetime.now().date() - timedelta(days=90))
    
    with col2:
        end_date = st.date_input("Đến ngày:", value=datetime.now().date())
    
    if start_date >= end_date:
        st.error("❌ Ngày bắt đầu phải trước ngày kết thúc!")
        return
    
    # Lấy dữ liệu xu hướng
    trend_data = get_time_trend_data(user['id'], start_date, end_date, selected_class)
    
    if not trend_data:
        st.info("📊 Chưa có dữ liệu trong khoảng thời gian này!")
        return
    
    # Biểu đồ xu hướng đơn giản
    df_trend = pd.DataFrame(trend_data)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Điểm trung bình
    df_trend['date'] = pd.to_datetime(df_trend['date'])
    ax1.plot(df_trend['date'], df_trend['avg_score'], marker='o')
    ax1.set_title('Điểm trung bình')
    ax1.set_ylabel('Điểm TB')
    
    # Số bài nộp
    ax2.plot(df_trend['date'], df_trend['submission_count'], marker='s')
    ax2.set_title('Số bài nộp')
    ax2.set_ylabel('Bài nộp')
    
    # Tỷ lệ đạt
    ax3.plot(df_trend['date'], df_trend['pass_rate'], marker='^')
    ax3.set_title('Tỷ lệ đạt')
    ax3.set_ylabel('Tỷ lệ đạt (%)')
    
    # Số đề thi
    ax4.plot(df_trend['date'], df_trend['exam_count'], marker='d')
    ax4.set_title('Số đề thi tạo')
    ax4.set_ylabel('Đề thi')
    
    plt.tight_layout()
    st.pyplot(fig)

def show_student_comparison(user, time_filter, selected_class):
    """So sánh học sinh"""
    st.write("### 👥 So sánh học sinh")
    
    if selected_class == "Tất cả lớp":
        st.info("👆 Vui lòng chọn một lớp cụ thể trong sidebar để so sánh học sinh!")
        return
    
    # Lấy danh sách học sinh
    classes = get_classes_by_teacher(user['id'])
    selected_class_info = next((c for c in classes if c['name'] == selected_class), None)
    
    if not selected_class_info:
        st.error("❌ Không tìm thấy lớp được chọn!")
        return
    
    students = get_class_students_for_comparison(selected_class_info['id'], time_filter)
    
    if len(students) < 2:
        st.info("👥 Cần có ít nhất 2 học sinh có dữ liệu để so sánh!")
        return
    
    # Chọn học sinh để so sánh
    student_options = [f"{s['name']} ({s['username']})" for s in students]
    selected_students = st.multiselect(
        "Chọn học sinh để so sánh:",
        student_options,
        default=student_options[:3] if len(student_options) >= 3 else student_options
    )
    
    if len(selected_students) < 2:
        st.warning("⚠️ Vui lòng chọn ít nhất 2 học sinh để so sánh!")
        return
    
    # Lấy dữ liệu so sánh
    student_comparison_data = get_student_comparison_data(
        selected_class_info['id'], 
        selected_students, 
        time_filter
    )
    
    # Biểu đồ so sánh
    col1, col2 = st.columns(2)
    
    with col1:
        # So sánh điểm theo đề thi
        comparison_df = pd.DataFrame(student_comparison_data)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        students = comparison_df['student_name'].unique()
        for student in students:
            student_data = comparison_df[comparison_df['student_name'] == student]
            ax.plot(student_data['exam_title'], student_data['score'], marker='o', label=student)
        
        ax.set_title("Điểm số theo đề thi")
        ax.set_xlabel("Đề thi")
        ax.set_ylabel("Điểm")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        # So sánh điểm trung bình
        avg_scores = {}
        for data in student_comparison_data:
            if data['student_name'] not in avg_scores:
                avg_scores[data['student_name']] = []
            avg_scores[data['student_name']].append(data['score'])
        
        avg_df = pd.DataFrame([
            {'Học sinh': name, 'Điểm TB': sum(scores)/len(scores)}
            for name, scores in avg_scores.items()
        ])
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(avg_df['Học sinh'], avg_df['Điểm TB'], color=plt.cm.RdYlGn(avg_df['Điểm TB']/10))
        ax.set_title("Điểm trung bình")
        ax.set_xlabel("Học sinh")
        ax.set_ylabel("Điểm TB")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

# Mock database functions - Thay thế bằng implementation thực tế

def get_teacher_overview_stats(teacher_id, time_filter, selected_class):
    """Mock function - lấy thống kê tổng quan"""
    return {
        'total_classes': 3,
        'classes_change': 1,
        'total_students': 75,
        'students_change': 5,
        'total_exams': 12,
        'exams_change': 2,
        'total_submissions': 450,
        'submissions_change': 30,
        'average_score': 7.8,
        'score_change': 0.3
    }

def get_activity_timeline(teacher_id, time_filter):
    """Mock function - lấy timeline hoạt động"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
    return [
        {
            'date': date.strftime('%Y-%m-%d'),
            'exams_created': np.random.randint(0, 3),
            'submissions_received': np.random.randint(5, 25)
        }
        for date in dates
    ]

def get_score_distribution(teacher_id, time_filter, selected_class):
    """Mock function - phân bố điểm"""
    return [5, 10, 25, 35, 25]  # 0-20%, 21-40%, 41-60%, 61-80%, 81-100%

def get_class_rankings(teacher_id, time_filter):
    """Mock function - xếp hạng lớp"""
    return [
        {'class_name': 'Lớp 10A1', 'average_score': 8.5, 'total_students': 30, 'total_submissions': 150},
        {'class_name': 'Lớp 10B1', 'average_score': 7.8, 'total_students': 28, 'total_submissions': 140},
        {'class_name': 'Lớp 10C1', 'average_score': 7.2, 'total_students': 25, 'total_submissions': 125}
    ]

def get_question_type_statistics(teacher_id, time_filter):
    """Mock function - thống kê loại câu hỏi"""
    return [
        {'question_type': 'Trắc nghiệm', 'count': 120, 'average_score': 8.2},
        {'question_type': 'Đúng/Sai', 'count': 80, 'average_score': 7.5},
        {'question_type': 'Trả lời ngắn', 'count': 40, 'average_score': 6.8},
        {'question_type': 'Tự luận', 'count': 20, 'average_score': 7.0}
    ]

def get_class_detailed_stats(class_id, time_filter):
    """Mock function - thống kê chi tiết lớp"""
    return {
        'class_name': 'Lớp 10A1',
        'total_students': 30,
        'total_exams': 5,
        'total_submissions': 150,
        'class_average': 8.2,
        'submission_rate': 95.0,
        'pass_rate': 87.0,
        'excellent_rate': 23.0
    }

def get_class_score_trend(class_id, time_filter):
    """Mock function - xu hướng điểm lớp"""
    return [
        {'exam_date': '2024-01-15', 'average_score': 7.5},
        {'exam_date': '2024-01-22', 'average_score': 8.0},
        {'exam_date': '2024-01-29', 'average_score': 8.2},
        {'exam_date': '2024-02-05', 'average_score': 8.5},
        {'exam_date': '2024-02-12', 'average_score': 8.3}
    ]

def get_class_grade_distribution(class_id, time_filter):
    """Mock function - phân bố học lực lớp"""
    return {
        'Xuất sắc': 7,
        'Giỏi': 12,
        'Khá': 8,
        'Trung bình': 3,
        'Yếu': 0
    }

def get_class_student_details(class_id, time_filter):
    """Mock function - chi tiết học sinh lớp"""
    names = ['Nguyễn Văn A', 'Trần Thị B', 'Lê Văn C', 'Phạm Thị D', 'Hoàng Văn E']
    return [
        {
            'student_name': name,
            'average_score': round(np.random.uniform(6.0, 9.5), 1),
            'total_submissions': np.random.randint(8, 12),
            'grade': np.random.choice(['Xuất sắc', 'Giỏi', 'Khá', 'Trung bình'])
        }
        for name in names
    ]

def get_teacher_exams(teacher_id, time_filter, selected_class):
    """Mock function - danh sách đề thi"""
    return [
        {
            'id': 1,
            'title': 'Kiểm tra 15 phút',
            'class_name': 'Lớp 10A1',
            'created_at': '2024-01-15T08:00:00'
        },
        {
            'id': 2,
            'title': 'Kiểm tra giữa kỳ',
            'class_name': 'Lớp 10A1',
            'created_at': '2024-01-22T08:00:00'
        }
    ]

def get_exam_detailed_stats(exam_id):
    """Mock function - thống kê chi tiết đề thi"""
    return {
        'title': 'Kiểm tra 15 phút - Toán 10',
        'class_name': 'Lớp 10A1',
        'time_limit': 15,
        'total_points': 10.0,
        'start_time': '2024-01-15T08:00:00',
        'end_time': '2024-01-15T08:15:00',
        'submission_count': 28,
        'average_score': 8.2,
        'highest_score': 10.0,
        'lowest_score': 5.5,
        'pass_rate': 85.7
    }

def get_exam_score_histogram(exam_id):
    """Mock function - histogram điểm đề thi"""
    return [5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0] * 3

def get_exam_time_distribution(exam_id):
    """Mock function - phân bố thời gian làm bài"""
    return [8, 10, 12, 13, 14, 15, 15, 15, 13, 12, 11, 10, 9, 8]

def get_exam_question_analysis(exam_id):
    """Mock function - phân tích câu hỏi"""
    return [
        {
            'question_number': i,
            'question_type': np.random.choice(['Trắc nghiệm', 'Đúng/Sai', 'Trả lời ngắn']),
            'points': 1.0,
            'correct_rate': round(np.random.uniform(30, 95), 1),
            'average_score': round(np.random.uniform(0.3, 0.95), 2),
            'difficulty': np.random.choice(['Dễ', 'Trung bình', 'Khó'])
        }
        for i in range(1, 11)
    ]

def export_class_statistics_to_excel(class_id, time_filter):
    """Xuất thống kê lớp ra Excel"""
    # Mock implementation
    data = {'Học sinh': ['A', 'B', 'C'], 'Điểm': [8.5, 7.0, 9.0]}
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    return excel_buffer.getvalue()

def export_exam_statistics_to_excel(exam_id):
    """Xuất thống kê đề thi ra Excel"""
    # Mock implementation
    return export_class_statistics_to_excel(None, None)

def generate_class_report(class_id, time_filter):
    """Tạo báo cáo lớp"""
    st.success("📊 Báo cáo đã được tạo!")

def generate_exam_report(exam_id):
    """Tạo báo cáo đề thi"""
    st.success("📊 Báo cáo đề thi đã được tạo!")

# Thêm các mock functions khác
def get_class_comparison_data(teacher_id, selected_classes, time_filter):
    """Mock comparison data"""
    return [
        {
            'class_name': class_name,
            'student_count': np.random.randint(25, 35),
            'average_score': round(np.random.uniform(7.0, 9.0), 1),
            'pass_rate': round(np.random.uniform(80, 95), 1),
            'excellent_rate': round(np.random.uniform(15, 30), 1),
            'exam_count': np.random.randint(3, 8),
            'submission_count': np.random.randint(100, 200)
        }
        for class_name in selected_classes
    ]

def get_exam_comparison_data(exam_ids):
    """Mock exam comparison"""
    return [
        {
            'exam_title': f'Đề thi {exam_id}',
            'class_name': f'Lớp 10A{exam_id}',
            'average_score': round(np.random.uniform(6.5, 9.0), 1),
            'pass_rate': round(np.random.uniform(75, 95), 1),
            'submission_count': np.random.randint(25, 35),
            'avg_completion_time': np.random.randint(10, 20),
            'time_limit': 20,
            'difficulty_score': np.random.randint(60, 90),
            'difficulty_level': np.random.choice(['Dễ', 'Trung bình', 'Khó']),
            'submission_rate': round(np.random.uniform(85, 98), 1)
        }
        for exam_id in exam_ids
    ]

def get_time_trend_data(teacher_id, start_date, end_date, selected_class):
    """Mock time trend data"""
    dates = pd.date_range(start=start_date, end=end_date, freq='W')
    return [
        {
            'date': date.strftime('%Y-%m-%d'),
            'avg_score': round(np.random.uniform(7.0, 9.0), 1),
            'submission_count': np.random.randint(20, 50),
            'pass_rate': round(np.random.uniform(80, 95), 1),
            'exam_count': np.random.randint(0, 3)
        }
        for date in dates
    ]

def get_class_students_for_comparison(class_id, time_filter):
    """Mock students for comparison"""
    return [
        {'name': f'Học sinh {i}', 'username': f'hocsinh{i}'}
        for i in range(1, 11)
    ]

def get_student_comparison_data(class_id, selected_students, time_filter):
    """Mock student comparison data"""
    exam_titles = ['Đề 1', 'Đề 2', 'Đề 3', 'Đề 4']
    data = []
    
    for student in selected_students:
        student_name = student.split(' (')[0]
        for exam in exam_titles:
            data.append({
                'student_name': student_name,
                'exam_title': exam,
                'score': round(np.random.uniform(6.0, 10.0), 1)
            })
    
    return data

# Import numpy for random data generation
import numpy as np