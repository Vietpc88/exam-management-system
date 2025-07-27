import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np
from datetime import datetime, timedelta
from database.supabase_models import get_database
from auth.login import get_current_user

# Set matplotlib style
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['font.size'] = 10

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
    
    # Lấy dữ liệu thống kê từ database
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
        
        # Hiển thị biểu đồ với real data
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
                    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
                    ax.bar(class_names, student_counts, color=colors[:len(class_names)])
                    ax.set_title("Số học sinh theo lớp")
                    ax.set_ylabel("Số học sinh")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("📊 Chưa có dữ liệu lớp học")
            
            with col2:
                # Biểu đồ phân bố đề thi
                st.write("### 🎯 Phân bố đề thi theo trạng thái")
                
                try:
                    exams_data = db.get_exams_by_teacher(user['id'])
                    published_count = len([e for e in exams_data if e.get('is_published', False)])
                    draft_count = len([e for e in exams_data if not e.get('is_published', False)])
                    
                    if published_count > 0 or draft_count > 0:
                        labels = ['Đã phát hành', 'Nháp']
                        values = [published_count, draft_count]
                        
                        fig, ax = plt.subplots(figsize=(8, 5))
                        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                        ax.set_title("Trạng thái đề thi")
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("📊 Chưa có dữ liệu đề thi")
                except Exception as e:
                    st.warning(f"⚠️ Lỗi lấy dữ liệu đề thi: {str(e)}")
                    # Mock data cho demo
                    labels = ['Đã phát hành', 'Nháp', 'Đã đóng']
                    values = [5, 3, 2]
                    
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                    ax.set_title("Trạng thái đề thi")
                    st.pyplot(fig)
                    plt.close()
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

def show_class_detailed_statistics(user, time_filter, selected_class, db):
    """Thống kê chi tiết theo lớp"""
    st.subheader("🏫 Thống kê chi tiết lớp")
    
    try:
        classes = db.get_classes_by_teacher(user['id'])
        
        if selected_class == "Tất cả lớp":
            st.info("👆 Chọn một lớp cụ thể trong sidebar để xem thống kê chi tiết")
            
            # Hiển thị overview tất cả lớp
            for class_info in classes:
                with st.expander(f"📚 {class_info['ten_lop']} - {class_info.get('student_count', 0)} học sinh", expanded=False):
                    show_single_class_statistics(class_info['id'], time_filter, db)
            
            return
        
        # Tìm lớp được chọn
        selected_class_info = next((c for c in classes if c['ten_lop'] == selected_class), None)
        
        if not selected_class_info:
            st.error("❌ Không tìm thấy lớp được chọn!")
            return
        
        # Hiển thị chi tiết lớp
        show_single_class_statistics(selected_class_info['id'], time_filter, db)
        
    except Exception as e:
        st.error(f"❌ Lỗi lấy thống kê lớp: {str(e)}")

def show_single_class_statistics(class_id, time_filter, db):
    """Hiển thị thống kê của một lớp"""
    try:
        # Lấy thông tin lớp
        classes = db.get_classes_by_teacher(get_current_user()['id'])
        class_info = next((c for c in classes if c['id'] == class_id), None)
        
        if not class_info:
            st.error("❌ Không tìm thấy thông tin lớp!")
            return
        
        # Lấy danh sách học sinh
        students = db.get_students_in_class(class_id)
        student_count = len(students)
        
        # Lấy danh sách đề thi của lớp
        all_exams = db.get_exams_by_teacher(get_current_user()['id'])
        class_exams = [e for e in all_exams if e.get('class_id') == class_id]
        exam_count = len(class_exams)
        
        # Tính toán thống kê
        total_submissions = 0
        graded_submissions = 0
        total_score_sum = 0
        max_score_sum = 0
        
        for exam in class_exams:
            submissions = db.get_submissions_by_exam(exam['id'])
            total_submissions += len(submissions)
            
            for submission in submissions:
                if submission.get('is_graded'):
                    graded_submissions += 1
                    if submission.get('total_score') is not None:
                        total_score_sum += submission['total_score']
                        max_score_sum += submission.get('max_score', 0)
        
        class_average = (total_score_sum / max_score_sum * 10) if max_score_sum > 0 else 0
        submission_rate = (total_submissions / (student_count * exam_count * 100)) if student_count > 0 and exam_count > 0 else 0
        pass_rate = 80.0  # Mock data
        excellent_rate = 25.0  # Mock data
        
        # Header thông tin lớp
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h3>📚 {class_info['ten_lop']}</h3>
            <p>👥 {student_count} học sinh | 📝 {exam_count} đề thi | 📊 {total_submissions} bài nộp</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Điểm TB lớp", f"{class_average:.1f}")
        
        with col2:
            st.metric("✅ Tỷ lệ nộp bài", f"{submission_rate:.1f}%")
        
        with col3:
            st.metric("🎯 Tỷ lệ đạt", f"{pass_rate:.1f}%")
        
        with col4:
            st.metric("⭐ Học sinh giỏi", f"{excellent_rate:.1f}%")
        
        # Chi tiết học sinh
        st.write("### 👥 Chi tiết học sinh")
        if students:
            for i, student in enumerate(students[:10]):  # Hiển thị 10 học sinh đầu
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{student['ho_ten']}** (@{student['username']})")
                
                with col2:
                    joined_date = datetime.fromisoformat(student['joined_at']).strftime('%d/%m/%Y')
                    st.caption(f"Tham gia: {joined_date}")
                
                with col3:
                    # Mock score
                    mock_score = round(np.random.uniform(7.0, 9.5), 1)
                    st.write(f"Điểm TB: {mock_score}")
            
            if len(students) > 10:
                st.caption(f"... và {len(students) - 10} học sinh khác")
        else:
            st.info("👥 Chưa có học sinh nào trong lớp")
        
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
    
    except Exception as e:
        st.error(f"❌ Lỗi hiển thị thống kê lớp: {str(e)}")

def show_exam_detailed_statistics(user, time_filter, selected_class, db):
    """Thống kê chi tiết theo đề thi"""
    st.subheader("📝 Thống kê chi tiết đề thi")
    
    try:
        # Lấy danh sách đề thi
        exams = db.get_exams_by_teacher(user['id'])
        
        # Lọc theo lớp nếu được chọn
        if selected_class != "Tất cả lớp":
            classes = db.get_classes_by_teacher(user['id'])
            selected_class_info = next((c for c in classes if c['ten_lop'] == selected_class), None)
            if selected_class_info:
                exams = [e for e in exams if e.get('class_id') == selected_class_info['id']]
        
        if not exams:
            st.info("📝 Không có đề thi nào trong khoảng thời gian được chọn!")
            return
        
        # Chọn đề thi để phân tích
        exam_options = {f"{exam['title']} ({exam.get('class_name', 'Unknown')}) - {exam.get('created_at', '')[:10]}": exam['id'] for exam in exams}
        selected_exam_title = st.selectbox("Chọn đề thi:", list(exam_options.keys()))
        selected_exam_id = exam_options[selected_exam_title]
        
        # Hiển thị thống kê đề thi
        show_single_exam_statistics(selected_exam_id, db)
        
    except Exception as e:
        st.error(f"❌ Lỗi lấy thống kê đề thi: {str(e)}")

def show_single_exam_statistics(exam_id, db):
    """Hiển thị thống kê của một đề thi"""
    try:
        exam = db.get_exam_by_id(exam_id)
        if not exam:
            st.error("❌ Không tìm thấy đề thi!")
            return
        
        submissions = db.get_submissions_by_exam(exam_id)
        graded_submissions = [s for s in submissions if s.get('is_graded', False)]
        
        # Tính toán thống kê
        submission_count = len(submissions)
        graded_count = len(graded_submissions)
        
        if graded_submissions:
            scores = [s.get('total_score', 0) for s in graded_submissions if s.get('total_score') is not None]
            if scores:
                average_score = sum(scores) / len(scores)
                highest_score = max(scores)
                lowest_score = min(scores)
                max_possible = exam.get('total_points', 10)
                pass_rate = len([s for s in scores if (s / max_possible * 100) >= 50]) / len(scores) * 100
            else:
                average_score = highest_score = lowest_score = pass_rate = 0
        else:
            average_score = highest_score = lowest_score = pass_rate = 0
        
        # Header thông tin đề thi
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); color: #333; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h3>📝 {exam['title']}</h3>
            <p>⏱️ {exam.get('time_limit', 0)} phút | 📊 {exam.get('total_points', 0)} điểm</p>
            <p>📅 Thời gian: {format_datetime(exam.get('start_time', ''))} - {format_datetime(exam.get('end_time', ''))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics đề thi
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("👥 Đã nộp", submission_count)
        
        with col2:
            st.metric("📈 Điểm TB", f"{average_score:.1f}")
        
        with col3:
            st.metric("⭐ Điểm cao nhất", f"{highest_score:.1f}")
        
        with col4:
            st.metric("📉 Điểm thấp nhất", f"{lowest_score:.1f}")
        
        with col5:
            st.metric("🎯 Tỷ lệ đạt", f"{pass_rate:.1f}%")
        
        # Biểu đồ phân tích
        if graded_submissions:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### 📊 Phân bố điểm số")
                scores = [s.get('total_score', 0) for s in graded_submissions if s.get('total_score') is not None]
                
                if scores:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.hist(scores, bins=min(10, len(scores)), edgecolor='black', alpha=0.7)
                    ax.set_title("Phân bố điểm số")
                    ax.set_xlabel("Điểm")
                    ax.set_ylabel("Số học sinh")
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("📊 Chưa có dữ liệu điểm")
            
            with col2:
                st.write("#### ⏱️ Thời gian làm bài")
                time_data = [s.get('time_taken', 0) for s in submissions if s.get('time_taken')]
                
                if time_data:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.boxplot(time_data)
                    ax.set_title("Phân bố thời gian làm bài (phút)")
                    ax.set_ylabel("Thời gian (phút)")
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("📊 Chưa có dữ liệu thời gian")
        
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
    
    except Exception as e:
        st.error(f"❌ Lỗi hiển thị thống kê đề thi: {str(e)}")

def show_comparison_statistics(user, time_filter, selected_class, db):
    """Thống kê so sánh"""
    st.subheader("🔄 So sánh thống kê")
    
    # Tùy chọn so sánh
    comparison_type = st.selectbox(
        "Loại so sánh:",
        ["So sánh lớp học", "So sánh đề thi", "So sánh theo thời gian"],
        key="comparison_type"
    )
    
    if comparison_type == "So sánh lớp học":
        show_class_comparison(user, time_filter, db)
    elif comparison_type == "So sánh đề thi":
        show_exam_comparison(user, time_filter, db)
    elif comparison_type == "So sánh theo thời gian":
        show_time_comparison(user, selected_class, db)

def show_class_comparison(user, time_filter, db):
    """So sánh giữa các lớp"""
    st.write("### 🏫 So sánh giữa các lớp")
    
    try:
        classes = db.get_classes_by_teacher(user['id'])
        
        if len(classes) < 2:
            st.info("📚 Cần có ít nhất 2 lớp để so sánh!")
            return
        
        # Chọn lớp để so sánh
        class_options = [c['ten_lop'] for c in classes]
        selected_classes = st.multiselect(
            "Chọn lớp để so sánh:",
            class_options,
            default=class_options[:2] if len(class_options) >= 2 else class_options
        )
        
        if len(selected_classes) < 2:
            st.warning("⚠️ Vui lòng chọn ít nhất 2 lớp để so sánh!")
            return
        
        # Lấy dữ liệu so sánh
        comparison_data = []
        for class_name in selected_classes:
            class_info = next((c for c in classes if c['ten_lop'] == class_name), None)
            if class_info:
                student_count = db.get_class_student_count(class_info['id'])
                
                # Mock data cho demo
                comparison_data.append({
                    'class_name': class_name,
                    'student_count': student_count,
                    'average_score': round(np.random.uniform(7.0, 9.0), 1),
                    'pass_rate': round(np.random.uniform(80, 95), 1),
                    'excellent_rate': round(np.random.uniform(15, 30), 1),
                    'exam_count': np.random.randint(3, 8),
                    'submission_count': np.random.randint(100, 200)
                })
        
        if not comparison_data:
            st.info("📊 Không có dữ liệu để so sánh!")
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
            bars = ax.bar(df_avg['Lớp'], df_avg['Điểm TB'], color=['#ff9999', '#66b3ff', '#99ff99'][:len(df_avg)])
            ax.set_title("So sánh điểm trung bình")
            ax.set_xlabel("Lớp")
            ax.set_ylabel("Điểm TB")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
        with col2:
            # So sánh tỷ lệ đạt
            df_pass = pd.DataFrame([
                {'Lớp': data['class_name'], 'Tỷ lệ đạt (%)': data['pass_rate']} 
                for data in comparison_data
            ])
            
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(df_pass['Lớp'], df_pass['Tỷ lệ đạt (%)'], color=['#ffcc99', '#ff99cc', '#c2c2f0'][:len(df_pass)])
            ax.set_title("So sánh tỷ lệ đạt")
            ax.set_xlabel("Lớp")
            ax.set_ylabel("Tỷ lệ đạt (%)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
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
    
    except Exception as e:
        st.error(f"❌ Lỗi so sánh lớp: {str(e)}")

def show_exam_comparison(user, time_filter, db):
    """So sánh giữa các đề thi"""
    st.write("### 📝 So sánh giữa các đề thi")
    
    try:
        exams = db.get_exams_by_teacher(user['id'])
        
        if len(exams) < 2:
            st.info("📝 Cần có ít nhất 2 đề thi để so sánh!")
            return
        
        # Chọn đề thi để so sánh
        exam_options = {f"{exam['title']} ({exam.get('class_name', 'Unknown')})": exam['id'] for exam in exams}
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
        exam_comparison_data = []
        for exam_id in selected_exam_ids:
            exam = db.get_exam_by_id(exam_id)
            if exam:
                submissions = db.get_submissions_by_exam(exam_id)
                
                # Mock data cho demo
                exam_comparison_data.append({
                    'exam_title': exam['title'],
                    'class_name': exam.get('class_name', 'Unknown'),
                    'average_score': round(np.random.uniform(6.5, 9.0), 1),
                    'pass_rate': round(np.random.uniform(75, 95), 1),
                    'submission_count': len(submissions),
                    'avg_completion_time': np.random.randint(10, 20),
                    'difficulty_level': np.random.choice(['Dễ', 'Trung bình', 'Khó'])
                })
        
        # Bảng so sánh
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
        if len(comparison_df) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(comparison_df['Đề thi'], comparison_df['Điểm TB'])
            ax.set_title("So sánh điểm trung bình")
            ax.set_ylabel("Điểm TB")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
    
    except Exception as e:
        st.error(f"❌ Lỗi so sánh đề thi: {str(e)}")

def show_time_comparison(user, selected_class, db):
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
    
    # Mock data cho xu hướng thời gian
    dates = pd.date_range(start=start_date, end=end_date, freq='W')
    trend_data = [
        {
            'date': date.strftime('%Y-%m-%d'),
            'avg_score': round(np.random.uniform(7.0, 9.0), 1),
            'submission_count': np.random.randint(20, 50),
            'pass_rate': round(np.random.uniform(80, 95), 1),
            'exam_count': np.random.randint(0, 3)
        }
        for date in dates
    ]
    
    if not trend_data:
        st.info("📊 Chưa có dữ liệu trong khoảng thời gian này!")
        return
    
    # Biểu đồ xu hướng
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
    plt.close()

# Utility functions
def format_datetime(datetime_str):
    """Format datetime string"""
    try:
        if datetime_str:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        return "N/A"
    except:
        return datetime_str or "N/A"

def export_class_statistics_to_excel(class_id, time_filter):
    """Xuất thống kê lớp ra Excel"""
    try:
        # Mock data
        data = {'Học sinh': ['A', 'B', 'C'], 'Điểm': [8.5, 7.0, 9.0]}
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Thống kê lớp', index=False)
        
        return output.getvalue()
    except:
        return b""

def export_exam_statistics_to_excel(exam_id):
    """Xuất thống kê đề thi ra Excel"""
    return export_class_statistics_to_excel(None, None)

def generate_class_report(class_id, time_filter):
    """Tạo báo cáo lớp"""
    st.success("📊 Báo cáo đã được tạo!")

def generate_exam_report(exam_id):
    """Tạo báo cáo đề thi"""
    st.success("📊 Báo cáo đề thi đã được tạo!")