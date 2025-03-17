import streamlit as st
import pandas as pd
from database import get_db
from models import Question, Chapter, Course, User
from utils import show_success, show_error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_question_bank():
    """Display the question bank page."""
    st.markdown("## Question Bank")
    
    try:
        db = next(get_db())
        
        # Get all questions with related data
        questions_data = db.query(
            Question, 
            Chapter.title.label("chapter_title"), 
            Course.title.label("course_title"),
            User.username.label("creator_username")
        ).join(
            Chapter, Question.chapter_id == Chapter.id
        ).join(
            Course, Chapter.course_id == Course.id
        ).outerjoin(
            User, Question.created_by == User.id
        ).all()
        
        if not questions_data:
            st.info("No questions available in the question bank.")
            return
        
        # Create DataFrame for analysis
        df = pd.DataFrame([
            {
                "id": q[0].id,
                "content": q[0].content[:100] + "..." if len(q[0].content) > 100 else q[0].content,
                "difficulty": q[0].difficulty,
                "question_type": q[0].question_type,
                "estimated_time": q[0].estimated_time,
                "student_level": q[0].student_level,
                "chapter": q[1],
                "course": q[2],
                "tags": q[0].tags,
                "creator": q[3] if q[3] else "Unknown"
            } for q in questions_data
        ])
        
        # Add filters
        st.markdown("### Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Course filter
            courses = sorted(df["course"].unique())
            selected_courses = st.multiselect("Filter by Course", courses)
            
            if selected_courses:
                df = df[df["course"].isin(selected_courses)]
        
        with col2:
            # Difficulty filter
            min_diff, max_diff = st.slider(
                "Difficulty Range",
                min_value=1.0,
                max_value=5.0,
                value=(1.0, 5.0),
                step=0.5
            )
            
            df = df[(df["difficulty"] >= min_diff) & (df["difficulty"] <= max_diff)]
        
        with col3:
            # Question type filter
            types = sorted(df["question_type"].unique())
            selected_types = st.multiselect("Question Type", types)
            
            if selected_types:
                df = df[df["question_type"].isin(selected_types)]
        
        # Search by content or tags
        search_term = st.text_input("Search by content or tags")
        
        if search_term:
            df = df[
                df["content"].str.contains(search_term, case=False) | 
                df["tags"].str.contains(search_term, case=False)
            ]
        
        # Display question count
        st.markdown(f"### Questions ({len(df)})")
        
        if df.empty:
            st.warning("No questions match your filters.")
            return
        
        # Display questions in expandable sections
        for _, row in df.iterrows():
            with st.expander(f"{row['course']} - {row['chapter']} - {row['content']}"):
                st.write(f"**Question ID:** {row['id']}")
                st.write(f"**Content:** {row['content']}")
                st.write(f"**Difficulty:** {row['difficulty']}")
                st.write(f"**Type:** {row['question_type']}")
                st.write(f"**Estimated Time:** {row['estimated_time']}")
                st.write(f"**Student Level:** {row['student_level']}")
                st.write(f"**Created By:** {row['creator']}")
                
                if row['tags']:
                    st.write(f"**Tags:** {row['tags']}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Edit", key=f"edit_{row['id']}"):
                        st.session_state.editing_question = row['id']
                        st.switch_page("pages/edit.py")
                
                with col2:
                    if st.button("View Discussion", key=f"discuss_{row['id']}"):
                        st.session_state.selected_question_id = row['id']
                        st.switch_page("pages/discussion.py")
                
                # Removed the Analyze button that redirected to Question Analysis page
    
    except Exception as e:
        logger.error(f"Error displaying question bank: {str(e)}")
        show_error(f"Error loading question bank: {str(e)}")

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    st.title("Question Bank")
    show_question_bank()