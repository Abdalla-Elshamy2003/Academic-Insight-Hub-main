import streamlit as st
import pandas as pd
from database import get_db
from models import Course, Chapter, Question
from datetime import datetime
import logging
from utils import show_success, show_error, rerun
from llm_utils import generate_questions
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_bulk_question_generator():
    """Display the bulk question generator page."""
    st.markdown("## AI Bulk Question Generator")
    st.markdown("Select a course and chapter, then configure the AI to automatically generate multiple questions for you.")
    
    # Initialize session state for generated questions and form reset
    if 'bulk_generator' not in st.session_state:
        st.session_state.bulk_generator = {
            "generated_questions": [],
            "form_submitted": False,
            "selected_questions": [],
            "generation_complete": False
        }
    
    # Reset form if it was just submitted
    if st.session_state.bulk_generator["form_submitted"]:
        st.session_state.bulk_generator["form_submitted"] = False
        st.rerun()
    
    try:
        db = next(get_db())
        
        # Get all courses
        courses = db.query(Course).all()
        
        if not courses:
            st.info("No courses available yet. You can add courses from the 'Add' tab.")
            st.markdown("### Please add courses to use the AI Bulk Question Generator")
            return
        
        # Course selection
        selected_course_id = st.selectbox(
            "Select Course",
            options=[(c.id, c.title) for c in courses],
            format_func=lambda x: x[1],
            key="bulk_course"
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
            key="bulk_chapter"
        )
        
        # Get the selected chapter and course
        selected_chapter = db.query(Chapter).get(selected_chapter_id[0])
        selected_course = db.query(Course).get(selected_course_id[0])
        
        if not selected_chapter:
            st.warning("Selected chapter not found.")
            return
        
        # Configuration options
        st.markdown("### Generation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Number of questions to generate
            num_questions = st.slider(
                "Number of Questions", 
                min_value=1, 
                max_value=10, 
                value=3,
                help="How many questions should the AI generate?"
            )
            
            # Difficulty level
            difficulty_level = st.selectbox(
                "Difficulty Level",
                options=["easy", "medium", "hard", "mixed"],
                index=3,  # Default to mixed
                help="Select the difficulty level for generated questions"
            )
        
        with col2:
            # Question types
            question_types = st.multiselect(
                "Question Types",
                options=["Multiple Choice", "True/False", "Short Answer", "Essay"],
                default=["Multiple Choice", "True/False", "Short Answer"],
                help="Select the types of questions to generate"
            )
            
            # AI model selection
            model = st.selectbox(
                "AI Model",
                options=["llama-3.1-8b-instant", "llama-3.1-70b-instant"],
                index=0,
                help="Select the AI model to use for generation"
            )
        
        # Get existing questions for the chapter as examples
        existing_questions = []
        chapter_questions = db.query(Question).filter_by(chapter_id=selected_chapter_id[0]).limit(3).all()
        for q in chapter_questions:
            existing_questions.append(q.content)
        
        # Generate button
        if st.button("Generate Questions"):
            if not question_types:
                show_error("Please select at least one question type.")
                return
                
            try:
                # Call the AI to generate questions
                with st.spinner(f"AI is generating {num_questions} questions... This may take a moment."):
                    generated_questions = generate_questions(
                        course_title=selected_course.title,
                        chapter_title=selected_chapter.title,
                        chapter_summary=selected_chapter.summary or "",
                        ilos=selected_chapter.ilos or "",
                        num_questions=num_questions,
                        difficulty_level=difficulty_level,
                        question_types=question_types,
                        existing_questions=existing_questions,
                        model=model
                    )
                    
                    if not generated_questions:
                        show_error("Failed to generate questions. Please try again.")
                        return
                    
                    # Store generated questions in session state
                    st.session_state.bulk_generator["generated_questions"] = generated_questions
                    st.session_state.bulk_generator["generation_complete"] = True
                    
                    # Show success message
                    show_success(f"Successfully generated {len(generated_questions)} questions!")
                    
                    # Rerun to display the questions
                    st.rerun()
                    
            except Exception as e:
                logger.error(f"Error generating questions: {str(e)}")
                show_error(f"Error: {str(e)}")
        
        # Display generated questions if available
        if st.session_state.bulk_generator["generation_complete"] and st.session_state.bulk_generator["generated_questions"]:
            display_generated_questions(selected_chapter_id[0])
    
    except Exception as e:
        logger.error(f"Error in bulk question generator: {str(e)}")
        show_error(f"Error: {str(e)}")

def display_generated_questions(chapter_id):
    """Display the generated questions with options to save them."""
    st.markdown("---")
    st.markdown("## Generated Questions")
    
    generated_questions = st.session_state.bulk_generator["generated_questions"]
    
    # Create a dataframe for better display
    questions_data = []
    for i, q in enumerate(generated_questions):
        questions_data.append({
            "ID": i + 1,
            "Question": q["question_content"][:100] + "...",
            "Type": q["question_type"],
            "Difficulty": f"{q['difficulty']}/5.0",
            "Time": f"{q.get('estimated_time', 5)} min",
            "Level": q.get("student_level", "Intermediate")
        })
    
    df = pd.DataFrame(questions_data)
    st.dataframe(df, use_container_width=True)
    
    # Display each question in an expander
    for i, question in enumerate(generated_questions):
        with st.expander(f"Question {i+1}: {question['question_content'][:100]}...", expanded=False):
            st.markdown(f"**Question Content:** {question['question_content']}")
            st.markdown(f"**Question Type:** {question['question_type']}")
            st.markdown(f"**Difficulty:** {question['difficulty']}/5.0")
            st.markdown(f"**Estimated Time:** {question.get('estimated_time', 5)} minutes")
            st.markdown(f"**Student Level:** {question.get('student_level', 'Intermediate')}")
            
            if "tags" in question and question["tags"]:
                st.markdown(f"**Tags:** {question['tags']}")
                
            st.markdown(f"**Correct Answer:** {question['correct_answer']}")
            st.markdown(f"**Explanation:** {question['explanation']}")
            
            if question['question_type'] == "Multiple Choice" and "options" in question:
                st.markdown("**Options:**")
                for option in question["options"]:
                    st.markdown(f"- {option}")
            
            # Checkbox to select this question for saving
            if st.checkbox("Save this question", key=f"save_q_{i}", value=True):
                if i not in st.session_state.bulk_generator["selected_questions"]:
                    st.session_state.bulk_generator["selected_questions"].append(i)
            else:
                if i in st.session_state.bulk_generator["selected_questions"]:
                    st.session_state.bulk_generator["selected_questions"].remove(i)
    
    # Save selected questions button
    if st.button("Save Selected Questions to Database"):
        save_questions_to_database(generated_questions, st.session_state.bulk_generator["selected_questions"], chapter_id)

def save_questions_to_database(generated_questions, selected_indices, chapter_id):
    """Save the selected generated questions to the database."""
    if not selected_indices:
        show_error("Please select at least one question to save.")
        return
    
    try:
        db = next(get_db())
        saved_count = 0
        
        for idx in selected_indices:
            q = generated_questions[idx]
            
            # Format correct answer for multiple choice questions
            final_correct_answer = q["correct_answer"]
            if q["question_type"] == "Multiple Choice" and "options" in q:
                # Store options in the correct_answer field with format: correct_answer|option1|option2|option3|option4
                options_str = "|".join(q["options"])
                final_correct_answer = f"{q['correct_answer']}|{options_str}"
            
            # Create new question
            new_question = Question(
                chapter_id=chapter_id,
                content=q["question_content"],
                question_type=q["question_type"],
                correct_answer=final_correct_answer,
                explanation=q["explanation"],
                difficulty=float(q["difficulty"]),
                estimated_time=int(q.get("estimated_time", 5)),
                student_level=q.get("student_level", "Intermediate"),
                tags=q.get("tags", ""),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_question)
            saved_count += 1
        
        db.commit()
        
        # Show success message
        show_success(f"Successfully saved {saved_count} questions to the database!")
        
        # Reset the form
        st.session_state.bulk_generator = {
            "generated_questions": [],
            "form_submitted": True,
            "selected_questions": [],
            "generation_complete": False
        }
        
    except Exception as e:
        logger.error(f"Error saving questions to database: {str(e)}")
        show_error(f"Error: {str(e)}")
        if 'db' in locals():
            db.rollback()