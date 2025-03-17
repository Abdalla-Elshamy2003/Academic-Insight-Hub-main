import streamlit as st
import pandas as pd
from database import get_db
from models import Course, Chapter, Question
from datetime import datetime
import logging
from utils import show_success, show_error, rerun
from llm_utils import analyze_question
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_question_generator():
    """Display the question generator page."""
    st.markdown("## AI Question Generator")
    st.markdown("Enter the question details below. The AI will automatically determine the difficulty level, estimated time, and appropriate student level.")
    
    # Initialize session state for form reset and results display
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    # Reset form if it was just submitted
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
        st.rerun()
    
    # Display analysis results dashboard if available
    if st.session_state.analysis_results:
        display_analysis_dashboard(st.session_state.analysis_results)
    
    try:
        db = next(get_db())
        
        # Get all courses and chapters
        courses = db.query(Course).all()
        
        if not courses:
            st.info("No courses available yet. You can add courses from the 'Add' tab.")
            # Display a placeholder instead of returning
            st.markdown("### Please add courses to use the AI Question Generator")
            return
        
        # Course selection
        selected_course_id = st.selectbox(
            "Select Course",
            options=[(c.id, c.title) for c in courses],
            format_func=lambda x: x[1],
            key="question_course"
        )
        
        # Get chapters for the selected course
        chapters = db.query(Chapter).filter_by(course_id=selected_course_id[0]).all()
        
        if not chapters:
            st.warning(f"No chapters available for the selected course. Please add a chapter first.")
            return
        
        # Chapter selection
        selected_chapter_id = st.selectbox(
            "Select Chapter",
            options=[(c.id, c.title) for c in chapters],
            format_func=lambda x: x[1],
            key="question_chapter"
        )
        
        # Get the selected chapter and course
        selected_chapter = db.query(Chapter).get(selected_chapter_id[0])
        selected_course = db.query(Course).get(selected_course_id[0])
        
        if not selected_chapter:
            st.warning("Selected chapter not found.")
            return
        
        # Question content
        question_content = st.text_area(
            "Question Content", 
            height=150,
            help="Enter the complete question text here.",
            key="question_content"
        )
        
        # Question type selection
        question_type = st.selectbox(
            "Question Type",
            options=["Multiple Choice", "True/False", "Short Answer"],
            help="Select the type of question"
        )
        
        # Correct answer
        correct_answer = st.text_area(
            "Correct Answer", 
            height=100,
            help="Enter the correct answer for this question",
            key="correct_answer"
        )
        
        # Explanation
        explanation = st.text_area(
            "Explanation",
            height=100,
            help="Provide an explanation for why this is the correct answer",
            key="explanation"
        )
        
        # For multiple choice, add options
        options = []
        if question_type == "Multiple Choice":
            st.markdown("### Answer Options")
            st.info("Enter 4 options. Make sure one matches the correct answer exactly.")
            for i in range(4):
                option = st.text_input(f"Option {chr(65+i)}", key=f"option_{i}")
                if option:
                    options.append(f"{chr(65+i)}. {option}")
        
        # Add question button
        if st.button("Generate Question Analysis"):
            if not question_content or not correct_answer or not explanation:
                show_error("Please fill in all required fields: question content, correct answer, and explanation.")
                return
                
            if question_type == "Multiple Choice" and (len(options) != 4 or not all(options)):
                show_error("Please provide all 4 options for multiple choice questions.")
                return
                
            try:
                # First analyze the question with AI
                with st.spinner("AI is analyzing the question..."):
                    # Call analyze_question function to get difficulty and other metrics
                    difficulty_rating, analysis_text = analyze_question(
                        question_content=question_content,
                        question_type=question_type,
                        course_title=selected_course.title,
                        chapter_title=selected_chapter.title,
                        ilos=selected_chapter.ilos
                    )
                    
                    if difficulty_rating is None:
                        show_error("Failed to analyze question. Please try again.")
                        return
                    
                    try:
                        # The estimated_time and student_level are now directly included in the analysis_text
                        # in a structured format, so we don't need to use regex to extract them
                        
                        # Extract time directly from the analysis text
                        time_match = re.search(r'\*\*Estimated Time:\*\* (\d+) minutes', analysis_text)
                        estimated_time = int(time_match.group(1)) if time_match else 5  # default to 5 minutes
                        
                        # Extract student level directly from the analysis text
                        level_match = re.search(r'\*\*Appropriate Student Level:\*\* (\w+)', analysis_text)
                        student_level = level_match.group(1) if level_match else "Intermediate"
                        
                        # Format correct answer for multiple choice questions
                        final_correct_answer = correct_answer
                        if question_type == "Multiple Choice":
                            # Store options in the correct_answer field with format: correct_answer|option1|option2|option3|option4
                            final_correct_answer = f"{correct_answer}|{options[0]}|{options[1]}|{options[2]}|{options[3]}"
                        
                        # Create new question with analyzed attributes
                        new_question = Question(
                            chapter_id=selected_chapter_id[0],
                            content=question_content,
                            question_type=question_type,
                            correct_answer=final_correct_answer,
                            explanation=explanation,
                            difficulty=float(difficulty_rating),
                            estimated_time=estimated_time,
                            student_level=student_level,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            created_by=st.session_state.user["id"]  # Track who created the question
                        )
                        
                        db.add(new_question)
                        db.commit()
                        
                        # Store analysis results in session state
                        st.session_state.analysis_results = {
                            "question_id": new_question.id,
                            "question_content": question_content,
                            "question_type": question_type,
                            "difficulty_rating": difficulty_rating,
                            "estimated_time": estimated_time,
                            "student_level": student_level,
                            "analysis_text": analysis_text,
                            "course": selected_course.title,
                            "chapter": selected_chapter.title,
                            "options": options if question_type == "Multiple Choice" else None,
                            "correct_answer": correct_answer,
                            "explanation": explanation
                        }
                        
                        # Display the dashboard
                        display_analysis_dashboard(st.session_state.analysis_results)
                        
                        # Set form_submitted flag to trigger reset on next rerun
                        st.session_state.form_submitted = True
                        
                    except Exception as e:
                        logger.error(f"Error parsing analysis results: {str(e)}")
                        show_error(f"Error analyzing question: {str(e)}")
                        return
                    
            except Exception as e:
                logger.error(f"Error adding question: {str(e)}")
                show_error(f"Error: {str(e)}")
                if 'db' in locals():
                    db.rollback()
    
    except Exception as e:
        logger.error(f"Error in question generator: {str(e)}")
        show_error(f"Error: {str(e)}")

def display_analysis_dashboard(results):
    """Display a dashboard with the AI analysis results."""
    st.markdown("---")
    st.markdown("## Question Analysis Dashboard")
    
    # Create a 3-column layout for the dashboard
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Column 1: Question Info
    with col1:
        st.markdown("### Question Information")
        st.markdown(f"**Course:** {results['course']}")
        st.markdown(f"**Chapter:** {results['chapter']}")
        st.markdown(f"**Type:** {results['question_type']}")
        st.markdown(f"**ID:** {results['question_id']}")
    
    # Column 2: AI Analysis
    with col2:
        st.markdown("### AI Analysis")
        
        # Create a gauge-like visualization for difficulty
        difficulty = results['difficulty_rating']
        difficulty_color = "green" if difficulty < 2.5 else "orange" if difficulty < 4 else "red"
        st.markdown(f"**Difficulty:** <span style='color:{difficulty_color};font-weight:bold;'>{difficulty}/5.0</span>", unsafe_allow_html=True)
        
        # Display difficulty bar
        st.progress(difficulty/5.0)
        
        st.markdown(f"**Estimated Time:** {results['estimated_time']} minutes")
        st.markdown(f"**Student Level:** {results['student_level']}")
    
    # Column 3: Success Message
    with col3:
        st.markdown("### Status")
        st.success("Question successfully added to database!")
        st.markdown("✅ Analysis complete")
        st.markdown("✅ Saved to question bank")
    
    # Display the question content in an expander
    with st.expander("Question Content", expanded=True):
        st.markdown(f"**{results['question_content']}**")
        
        # Display options for multiple choice
        if results['question_type'] == "Multiple Choice" and results['options']:
            st.markdown("**Options:**")
            for option in results['options']:
                st.markdown(f"- {option}")
        
        st.markdown("**Correct Answer:**")
        st.markdown(f"{results['correct_answer']}")
        
        st.markdown("**Explanation:**")
        st.markdown(f"{results['explanation']}")
    
    # Display the detailed analysis in an expander
    with st.expander("Detailed AI Analysis"):
        st.markdown(results['analysis_text'])
    
    # Add a button to create another question
    if st.button("Create Another Question"):
        # Clear the analysis results and rerun to show the form
        st.session_state.analysis_results = None
        st.rerun()

# For backward compatibility
if __name__ == "__main__":
    show_question_generator()