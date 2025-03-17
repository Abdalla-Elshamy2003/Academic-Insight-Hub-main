import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_db
from models import StudentProgress, Question, Chapter, Course
from sqlalchemy import func
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_progress():
    # Hide sidebar and navigation
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        div[data-testid="stSidebarNav"] {display: none;}
        section[data-testid="stSidebarUserContent"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    """Display the student progress page."""
    st.markdown("## My Progress")
    
    # Check if user is logged in
    if "user" not in st.session_state:
        st.warning("Please log in to view your progress.")
        return
    
    user_id = st.session_state.user["id"]
    
    try:
        db = next(get_db())
        
        # Get user progress data
        progress_data = db.query(
            StudentProgress,
            Question,
            Chapter,
            Course
        ).join(
            Question, StudentProgress.question_id == Question.id
        ).join(
            Chapter, Question.chapter_id == Chapter.id
        ).join(
            Course, Chapter.course_id == Course.id
        ).filter(
            StudentProgress.user_id == user_id
        ).all()
        
        if not progress_data:
            st.info("You haven't attempted any questions yet. Start practicing to see your progress!")
            return
        
        # Create a DataFrame for analysis
        df = pd.DataFrame([
            {
                'question_id': p[0].question_id,
                'attempts': p[0].attempts,
                'correct': p[0].correct,
                'last_attempt': p[0].last_attempt_date,
                'difficulty': p[1].difficulty,
                'question_type': p[1].question_type,
                'chapter': p[2].title,
                'course': p[3].title
            } for p in progress_data
        ])
        
        # Display summary statistics
        st.markdown("### Summary Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_questions = len(df)
            st.metric("Total Questions Attempted", total_questions)
        
        with col2:
            success_rate = (df['correct'].sum() / total_questions) * 100 if total_questions > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            avg_attempts = df['attempts'].mean() if total_questions > 0 else 0
            st.metric("Average Attempts per Question", f"{avg_attempts:.1f}")
        
        # Progress over time
        st.markdown("### Progress Over Time")
        
        # Convert datetime to date for grouping
        df['date'] = pd.to_datetime(df['last_attempt']).dt.date
        
        # Group by date and count attempts
        time_df = df.groupby('date').size().reset_index(name='questions_attempted')
        
        # Create line chart
        fig = px.line(
            time_df, 
            x='date', 
            y='questions_attempted',
            title='Questions Attempted Over Time',
            labels={'date': 'Date', 'questions_attempted': 'Questions Attempted'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance by difficulty
        st.markdown("### Performance by Difficulty")
        
        # Group by difficulty and calculate success rate
        diff_df = df.groupby('difficulty').agg({
            'correct': 'mean',
            'question_id': 'count'
        }).reset_index()
        diff_df['success_rate'] = diff_df['correct'] * 100
        diff_df['difficulty'] = diff_df['difficulty'].astype(str)
        
        # Create bar chart
        fig = px.bar(
            diff_df, 
            x='difficulty', 
            y='success_rate',
            title='Success Rate by Question Difficulty',
            labels={'difficulty': 'Difficulty Level', 'success_rate': 'Success Rate (%)'},
            text_auto='.1f',
            color='success_rate',
            color_continuous_scale='RdYlGn'
        )
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance by course
        st.markdown("### Performance by Course")
        
        # Group by course and calculate success rate
        course_df = df.groupby('course').agg({
            'correct': 'mean',
            'question_id': 'count'
        }).reset_index()
        course_df['success_rate'] = course_df['correct'] * 100
        
        # Create bar chart
        fig = px.bar(
            course_df, 
            x='course', 
            y='success_rate',
            title='Success Rate by Course',
            labels={'course': 'Course', 'success_rate': 'Success Rate (%)'},
            text_auto='.1f',
            color='success_rate',
            color_continuous_scale='RdYlGn'
        )
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.markdown("### Recent Activity")
        
        # Sort by last attempt date (descending)
        recent_df = df.sort_values('last_attempt', ascending=False).head(10)
        
        for _, row in recent_df.iterrows():
            with st.expander(f"{row['course']} - {row['chapter']} - Question {row['question_id']}"):
                st.write(f"**Last Attempt:** {row['last_attempt']}")
                st.write(f"**Status:** {'Correct ✅' if row['correct'] else 'Incorrect ❌'}")
                st.write(f"**Attempts:** {row['attempts']}")
                st.write(f"**Difficulty:** {row['difficulty']}/5")
                
                if st.button("Retry Question", key=f"retry_{row['question_id']}"):
                    st.session_state.selected_question_id = row['question_id']
                    st.switch_page("pages/question_attempt.py")
        
    except Exception as e:
        logger.error(f"Error displaying progress: {str(e)}")
        st.error(f"Error loading progress data: {str(e)}")

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    st.title("My Progress")
    show_progress()