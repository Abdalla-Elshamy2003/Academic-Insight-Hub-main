import streamlit as st
import pandas as pd
from database import get_db
from models import Course, Chapter, Question, Exam, ExamQuestion
from datetime import datetime
import logging
from utils import show_success, show_error, rerun
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_exam_builder():
    """Display the exam builder page."""
    st.markdown("## Exam Builder")
    st.markdown("Create exams by selecting questions from the database.")
    
    try:
        db = next(get_db())
        
        # Initialize session state if needed
        if "exam_builder" not in st.session_state:
            st.session_state.exam_builder = {
                "selected_questions": [],
                "filtered_questions": [],
                "selected_course_id": None,
                "selected_chapters": [],
                "auto_generated": False,
                "total_points": 0
            }
        
        # Get all courses
        courses = db.query(Course).all()
        
        if not courses:
            st.info("No courses available yet. You can add courses from the 'Add' tab.")
            # Display a placeholder instead of returning
            st.markdown("### Please add courses to use the Exam Builder")
            return
        
        # Sidebar for filtering
        st.sidebar.markdown("### Exam Parameters")
        
        # Course selection
        selected_course_id = st.sidebar.selectbox(
            "Select Course",
            options=[(c.id, c.title) for c in courses],
            format_func=lambda x: x[1],
            key="exam_course"
        )
        
        # Store selected course in session state
        st.session_state.exam_builder["selected_course_id"] = selected_course_id[0]
        
        # Get chapters for the selected course
        chapters = db.query(Chapter).filter_by(course_id=selected_course_id[0]).all()
        
        if not chapters:
            st.warning(f"No chapters available for the selected course. Please add a chapter first.")
            return
        
        # Chapter selection
        selected_chapters = st.sidebar.multiselect(
            "Select Chapters",
            options=[(c.id, c.title) for c in chapters],
            format_func=lambda x: x[1],
            key="exam_chapters"
        )
        
        # Store selected chapters in session state
        st.session_state.exam_builder["selected_chapters"] = [c[0] for c in selected_chapters]
        
        # Additional filters
        st.sidebar.markdown("### Question Filters")
        
        # Difficulty range
        difficulty_range = st.sidebar.slider(
            "Difficulty Range",
            min_value=1.0,
            max_value=5.0,
            value=(1.0, 5.0),
            step=0.5
        )
        
        # Question types
        question_types = st.sidebar.multiselect(
            "Question Types",
            ["Multiple Choice", "True/False", "Short Answer", "Essay"],
            default=["Multiple Choice", "True/False"]
        )
        
        # Auto-generate exam options
        st.sidebar.markdown("### Auto-Generation")
        
        total_questions = st.sidebar.number_input(
            "Total Questions",
            min_value=5,
            max_value=50,
            value=10
        )
        
        auto_generate = st.sidebar.button("Auto-Generate Exam")
        
        # Basic exam information form
        st.markdown("### Exam Information")
        
        exam_title = st.text_input("Exam Title", value="Exam")
        exam_description = st.text_area("Exam Description", value="")
        
        col1, col2 = st.columns(2)
        
        with col1:
            time_limit = st.number_input("Time Limit (minutes)", min_value=10, value=60)
        
        with col2:
            points_per_question = st.number_input("Default Points per Question", min_value=1, value=1)
        
        # Get questions based on selected filters
        questions_data = []
        
        if selected_chapters:
            questions_query = db.query(
                Question, 
                Chapter.title.label("chapter_title")
            ).join(
                Chapter, Question.chapter_id == Chapter.id
            ).filter(
                Chapter.id.in_([c[0] for c in selected_chapters]),
                Question.difficulty >= difficulty_range[0],
                Question.difficulty <= difficulty_range[1]
            )
            
            if question_types:
                questions_query = questions_query.filter(Question.question_type.in_(question_types))
            
            questions_data = questions_query.all()
            
            # Store filtered questions in session state
            filtered_questions = []
            for q in questions_data:
                filtered_questions.append({
                    "id": q[0].id,
                    "content": q[0].content,
                    "difficulty": q[0].difficulty,
                    "question_type": q[0].question_type,
                    "chapter": q[1],
                    "points": points_per_question
                })
            
            st.session_state.exam_builder["filtered_questions"] = filtered_questions
            
            # Handle auto-generation
            if auto_generate:
                # Clear previous selections
                st.session_state.exam_builder["selected_questions"] = []
                
                # If we have enough questions
                if len(filtered_questions) >= total_questions:
                    # Randomly select questions
                    selected_indices = random.sample(range(len(filtered_questions)), total_questions)
                    for idx in selected_indices:
                        st.session_state.exam_builder["selected_questions"].append(filtered_questions[idx])
                    
                    st.session_state.exam_builder["auto_generated"] = True
                    st.session_state.exam_builder["total_points"] = total_questions * points_per_question
                    
                    show_success(f"Auto-generated exam with {total_questions} questions!")
                    rerun()
                else:
                    show_error(f"Not enough questions available. Only {len(filtered_questions)} questions match your criteria.")
        
        # Display available questions
        st.markdown("### Available Questions")
        
        # Set default message if no questions available
        if not st.session_state.exam_builder["filtered_questions"]:
            st.info("No questions available. Select chapters and filters to view questions.")
        else:
            # Show how many questions available
            st.info(f"{len(st.session_state.exam_builder['filtered_questions'])} questions available.")
            
            # Show questions in expandable list
            for i, q in enumerate(st.session_state.exam_builder["filtered_questions"]):
                # Check if already selected
                is_selected = any(sq["id"] == q["id"] for sq in st.session_state.exam_builder["selected_questions"])
                
                # Only show if not already selected
                if not is_selected:
                    with st.expander(f"{q['chapter']} - {q['content'][:100]}...", expanded=False):
                        st.markdown(f"**Question ID:** {q['id']}")
                        st.markdown(f"**Content:** {q['content']}")
                        st.markdown(f"**Type:** {q['question_type']}")
                        st.markdown(f"**Difficulty:** {q['difficulty']}")
                        
                        # Add button
                        add_col1, add_col2 = st.columns([3, 1])
                        with add_col1:
                            points = st.number_input(f"Points", min_value=1, value=points_per_question, key=f"points_{q['id']}")
                        with add_col2:
                            if st.button("Add to Exam", key=f"add_{q['id']}"):
                                q["points"] = points
                                st.session_state.exam_builder["selected_questions"].append(q)
                                st.session_state.exam_builder["total_points"] += points
                                rerun()
        
        # Display selected questions
        st.markdown("### Selected Questions")
        
        # Set default message if no questions selected
        if not st.session_state.exam_builder["selected_questions"]:
            st.info("No questions selected yet. Use the filters to find and add questions.")
        else:
            # Add button to clear selections
            if st.button("Clear All Selections"):
                st.session_state.exam_builder["selected_questions"] = []
                st.session_state.exam_builder["total_points"] = 0
                rerun()
            
            # Show total
            st.success(f"Total: {len(st.session_state.exam_builder['selected_questions'])} questions, {st.session_state.exam_builder['total_points']} points")
            
            # Create a dataframe for easy reordering
            selected_df = pd.DataFrame(st.session_state.exam_builder["selected_questions"])
            
            # Add order column
            selected_df['order'] = list(range(1, len(selected_df) + 1))
            
            # Reorder columns
            selected_df = selected_df[['order', 'id', 'content', 'chapter', 'question_type', 'difficulty', 'points']]
            
            # Display as a table
            edited_df = st.data_editor(
                selected_df,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "content": st.column_config.TextColumn("Question Content", width="large", disabled=True),
                    "chapter": st.column_config.TextColumn("Chapter", disabled=True),
                    "question_type": st.column_config.TextColumn("Type", disabled=True),
                    "difficulty": st.column_config.NumberColumn("Difficulty", format="%.1f", disabled=True),
                    "points": st.column_config.NumberColumn("Points", min_value=1),
                    "order": st.column_config.NumberColumn("Order", min_value=1)
                },
                hide_index=True,
                use_container_width=True,
                key="selected_questions_editor"
            )
            
            # Update session state with edited values
            selected_questions = []
            total_points = 0
            
            # Sort by order
            edited_df = edited_df.sort_values('order')
            
            for _, row in edited_df.iterrows():
                question = {
                    "id": int(row['id']),
                    "content": row['content'],
                    "chapter": row['chapter'],
                    "question_type": row['question_type'],
                    "difficulty": float(row['difficulty']),
                    "points": int(row['points'])
                }
                selected_questions.append(question)
                total_points += int(row['points'])
            
            # Update session state
            st.session_state.exam_builder["selected_questions"] = selected_questions
            st.session_state.exam_builder["total_points"] = total_points
            
            # Remove button for each question
            for i, q in enumerate(st.session_state.exam_builder["selected_questions"]):
                remove_col = st.columns([5, 1])[1]
                with remove_col:
                    if st.button(f"Remove", key=f"remove_{q['id']}"):
                        st.session_state.exam_builder["total_points"] -= q["points"]
                        st.session_state.exam_builder["selected_questions"].pop(i)
                        rerun()
            
            # Save exam button
            if st.button("Save Exam", type="primary"):
                if not exam_title:
                    show_error("Please provide an exam title.")
                    return
                
                if not st.session_state.exam_builder["selected_questions"]:
                    show_error("Please select at least one question.")
                    return
                
                try:
                    # Create new exam
                    new_exam = Exam(
                        title=exam_title,
                        description=exam_description,
                        course_id=st.session_state.exam_builder["selected_course_id"],
                        created_by=st.session_state.user["id"],
                        time_limit=time_limit,
                        total_points=st.session_state.exam_builder["total_points"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(new_exam)
                    db.flush()  # Get the ID for the new exam
                    
                    # Add questions to the exam
                    for i, q in enumerate(st.session_state.exam_builder["selected_questions"]):
                        exam_question = ExamQuestion(
                            exam_id=new_exam.id,
                            question_id=q["id"],
                            order=i+1,
                            points=q["points"],
                            created_at=datetime.utcnow()
                        )
                        db.add(exam_question)
                    
                    db.commit()
                    
                    show_success(f"Exam '{exam_title}' saved successfully!")
                    
                    # Clear the form
                    st.session_state.exam_builder = {
                        "selected_questions": [],
                        "filtered_questions": [],
                        "selected_course_id": None,
                        "selected_chapters": [],
                        "auto_generated": False,
                        "total_points": 0
                    }
                    
                    rerun()
                    
                except Exception as e:
                    logger.error(f"Error saving exam: {str(e)}")
                    show_error(f"Error saving exam: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in exam builder: {str(e)}")
        show_error(f"Error: {str(e)}")

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    st.title("Exam Builder")
    show_exam_builder()