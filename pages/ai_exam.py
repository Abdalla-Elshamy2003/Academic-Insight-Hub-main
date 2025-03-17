import streamlit as st
import pandas as pd
from database import get_db
from models import Question, Chapter, Course, User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_ai_exam():
    """Display all AI-generated questions in a simple exam format."""
    st.markdown("## AI Exam Questions")
    st.markdown("This page displays all questions created with the AI Question Generator in a simple exam format.")
    
    try:
        db = next(get_db())
        
        # Get all questions with related data including creator
        questions_data = db.query(
            Question, 
            Chapter.title.label("chapter_title"), 
            Course.title.label("course_title"),
            User.username.label("creator_name")
        ).join(
            Chapter, Question.chapter_id == Chapter.id
        ).join(
            Course, Chapter.course_id == Course.id
        ).join(
            User, Question.created_by == User.id
        ).all()
        
        if not questions_data:
            st.info("No questions available in the database.")
            return
        
        # Display questions in a simple exam format
        for i, (question, chapter_title, course_title, creator_name) in enumerate(questions_data):
            # Create a card-like container for each question
            with st.container():
                st.markdown(f"### Question {i+1}")
                
                # Display question content
                st.markdown(f"**{question.content}**")
                
                # Display difficulty level in a human-readable format
                difficulty_text = "Easy"
                if question.difficulty > 2.5 and question.difficulty <= 3.5:
                    difficulty_text = "Medium"
                elif question.difficulty > 3.5:
                    difficulty_text = "Hard"
                
                # Display metadata in columns
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"**Difficulty:** {difficulty_text} ({question.difficulty}/5.0)")
                with col2:
                    st.markdown(f"**Time:** {question.estimated_time} minutes")
                with col3:
                    st.markdown(f"**Type:** {question.question_type}")
                with col4:
                    st.markdown(f"**Created by:** {creator_name}")
                
                # For multiple choice questions, display options
                if question.question_type == "Multiple Choice" and "|" in question.correct_answer:
                    # Parse options from the correct_answer field
                    parts = question.correct_answer.split("|")
                    correct_answer = parts[0]
                    options = parts[1:] if len(parts) > 1 else []
                    
                    # Display options
                    st.markdown("**Options:**")
                    for option in options:
                        st.markdown(f"- {option}")
                
                # Add a separator between questions
                st.markdown("---")
    
    except Exception as e:
        logger.error(f"Error displaying AI exam: {str(e)}")
        st.error(f"Error loading questions: {str(e)}")

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    st.title("AI Exam")
    show_ai_exam()