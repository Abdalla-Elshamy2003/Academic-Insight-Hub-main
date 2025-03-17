import streamlit as st
import pandas as pd
from database import get_db
from models import Question, StudentFeedback, StudentProgress, Course, Chapter
from sqlalchemy import func
from utils import create_difficulty_chart, create_gpa_correlation_chart, cache_data
import logging

# تهيئة الـ logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_course_names():
    """جلب أسماء الكورسات من قاعدة البيانات."""
    db = next(get_db())
    courses = db.query(Course.title).all()
    return [course[0] for course in courses]

@cache_data(ttl_seconds=300)
def get_analytics_data(selected_course=None):
    """جلب بيانات التحليلات من قاعدة البيانات مع إمكانية التصفية بالكورس المحدد."""
    db = next(get_db())
    
    if selected_course and selected_course != "All Courses":
        # بيانات توزيع صعوبة الأسئلة بعد التصفية
        difficulty_data = db.query(
            Question.difficulty,
            func.count(Question.id).label('count')
        ).join(Chapter, Question.chapter_id == Chapter.id) \
         .join(Course, Chapter.course_id == Course.id) \
         .filter(Course.title == selected_course) \
         .group_by(Question.difficulty).all()
        
        # بيانات تقييم الطلاب بعد التصفية
        feedback_data = db.query(
            StudentFeedback.difficulty_rating,
            StudentFeedback.student_gpa,
            Question.difficulty
        ).join(Question, StudentFeedback.question_id == Question.id) \
         .join(Chapter, Question.chapter_id == Chapter.id) \
         .join(Course, Chapter.course_id == Course.id) \
         .filter(Course.title == selected_course).all()
        
        # بيانات تقدم الطلاب بعد التصفية (نفترض وجود علاقة بين StudentProgress و Question عبر question_id)
        progress_data = db.query(
            StudentProgress.correct,
            func.count(StudentProgress.id).label('count')
        ).join(Question, StudentProgress.question_id == Question.id) \
         .join(Chapter, Question.chapter_id == Chapter.id) \
         .join(Course, Chapter.course_id == Course.id) \
         .filter(Course.title == selected_course) \
         .group_by(StudentProgress.correct).all()
        
        # إحصائيات إجمالية بعد التصفية
        course_count = 1
        chapter_count = db.query(func.count(Chapter.id)) \
            .join(Course, Chapter.course_id == Course.id) \
            .filter(Course.title == selected_course).scalar()
        question_count = db.query(func.count(Question.id)) \
            .join(Chapter, Question.chapter_id == Chapter.id) \
            .join(Course, Chapter.course_id == Course.id) \
            .filter(Course.title == selected_course).scalar()
        
        # عدد الشباتر لكل كورس (سيكون لكورس واحد فقط)
        course_chapters = db.query(
             Course.title,
             func.count(Chapter.id).label('chapter_count')
        ).join(Chapter, Chapter.course_id == Course.id) \
          .filter(Course.title == selected_course) \
          .group_by(Course.id).all()
          
        # متوسط صعوبة الأسئلة لكل كورس
        course_difficulty = db.query(
            Course.title,
            func.avg(Question.difficulty).label('avg_difficulty')
        ).join(Chapter, Chapter.course_id == Course.id) \
          .join(Question, Question.chapter_id == Chapter.id) \
          .filter(Course.title == selected_course) \
          .group_by(Course.id).all()
        
    else:
        # بدون تصفية (جلب كل البيانات)
        difficulty_data = db.query(
            Question.difficulty,
            func.count(Question.id).label('count')
        ).group_by(Question.difficulty).all()
        
        feedback_data = db.query(
            StudentFeedback.difficulty_rating,
            StudentFeedback.student_gpa,
            Question.difficulty
        ).join(Question, StudentFeedback.question_id == Question.id).all()
        
        progress_data = db.query(
            StudentProgress.correct,
            func.count(StudentProgress.id).label('count')
        ).group_by(StudentProgress.correct).all()
        
        course_count = db.query(func.count(Course.id)).scalar()
        chapter_count = db.query(func.count(Chapter.id)).scalar()
        question_count = db.query(func.count(Question.id)).scalar()
        
        course_chapters = db.query(
            Course.title,
            func.count(Chapter.id).label('chapter_count')
        ).join(Chapter, Chapter.course_id == Course.id) \
          .group_by(Course.id).all()
        
        course_difficulty = db.query(
            Course.title,
            func.avg(Question.difficulty).label('avg_difficulty')
        ).join(Chapter, Chapter.course_id == Course.id) \
          .join(Question, Question.chapter_id == Chapter.id) \
          .group_by(Course.id).all()
    
    return {
        'difficulty_data': difficulty_data,
        'feedback_data': feedback_data,
        'progress_data': progress_data,
        'course_count': course_count,
        'chapter_count': chapter_count,
        'question_count': question_count,
        'course_chapters': course_chapters,
        'course_difficulty': course_difficulty
    }

def card(title, value, bg_color):
    """دالة لإنشاء كارد HTML ملون لعرض الإحصائيات."""
    card_html = f"""
    <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; text-align: center; color: white; margin: 10px;">
        <h3 style="margin: 0;">{title}</h3>
        <h2 style="margin: 0;">{value}</h2>
    </div>
    """
    return card_html

def show_analytics():
    """عرض داشبورد التحليلات."""
    st.markdown("## Analytics Dashboard")
    
    try:
        # إضافة دروب داون لتصفية الكورسات
        courses = ["All Courses"] + get_course_names()
        selected_course = st.selectbox("Select Course", courses)
        
        # جلب البيانات مع التصفية إذا تم اختيار كورس محدد
        data = get_analytics_data(selected_course)
        
        # عرض الكاردات الملونة للإحصائيات الأساسية
        st.markdown("<h3>Summary Metrics</h3>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(card("Total Courses", data['course_count'], "#4CAF50"), unsafe_allow_html=True)
        with col2:
            st.markdown(card("Total Chapters", data['chapter_count'], "#2196F3"), unsafe_allow_html=True)
        with col3:
            st.markdown(card("Total Questions", data['question_count'], "#FF9800"), unsafe_allow_html=True)
        
        # حساب إجمالي عدد المحاولات من بيانات تقدم الطلاب
        total_attempts = sum([row[1] for row in data['progress_data']]) if data['progress_data'] else 0
        with col4:
            st.markdown(card("Total Attempts", total_attempts, "#9C27B0"), unsafe_allow_html=True)
        
        # توزيع صعوبة الأسئلة
        st.markdown("### Question Difficulty Distribution")
        if data['difficulty_data']:
            df_difficulty = pd.DataFrame(data['difficulty_data'], columns=['difficulty', 'count'])
            chart = create_difficulty_chart(df_difficulty)
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("No question difficulty data available.")
            
        # رسم علاقة معدل الطالب مع تقييم الصعوبة
        st.markdown("### Student GPA vs. Perceived Difficulty")
        if data['feedback_data']:
            df_gpa = pd.DataFrame(data['feedback_data'], columns=['perceived_difficulty', 'student_gpa', 'actual_difficulty'])
            chart = create_gpa_correlation_chart(df_gpa)
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("No student feedback data available.")
        
        # معدل نجاح الطلاب
        st.markdown("### Student Success Rate")
        if data['progress_data']:
            success_data = {row[0]: row[1] for row in data['progress_data']}
            correct = success_data.get(True, 0)
            incorrect = success_data.get(False, 0)
            total = correct + incorrect
            if total > 0:
                success_rate = (correct / total) * 100
                st.progress(success_rate / 100)
                st.write(f"Success Rate: {success_rate:.1f}%")
            else:
                st.info("No student progress data available.")
        else:
            st.info("No student progress data available.")
        
        # متوسط صعوبة الأسئلة لكل كورس
        st.markdown("### Average Difficulty by Course")
        if data['course_difficulty']:
            df_course = pd.DataFrame(data['course_difficulty'], columns=['course', 'avg_difficulty'])
            df_course = df_course.sort_values('avg_difficulty', ascending=False)
            import plotly.express as px
            fig = px.bar(
                df_course, 
                x='course', 
                y='avg_difficulty',
                title='Average Question Difficulty by Course',
                labels={'course': 'Course', 'avg_difficulty': 'Average Difficulty'},
                color='avg_difficulty',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No course difficulty data available.")
        
 
        st.markdown("### Chapters per Course")
        if data['course_chapters']:
            for course_title, chap_count in data['course_chapters']:
                st.markdown(card(course_title, chap_count, "#607D8B"), unsafe_allow_html=True)
        else:
            st.info("No course chapters data available.")
        
    except Exception as e:
        logger.error(f"Error displaying analytics: {str(e)}")
        st.error(f"Error loading analytics data: {str(e)}")

 
if __name__ == "__main__":
    st.title("Analytics Dashboard")
    show_analytics()
