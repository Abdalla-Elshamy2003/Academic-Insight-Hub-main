import streamlit as st
import pandas as pd
from database import get_db
from models import Course, Chapter, Question
from utils import format_ilos, rerun, confirm_action, show_success, show_error, paginate_data
from sqlalchemy import or_
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rerun():
    st.rerun()

def show_courses_and_chapters():
    """Display courses and chapters."""
    db = next(get_db())
    
    # Search functionality
    search_term = st.text_input("Search Courses and Chapters", key="search_courses_chapters")
    
    # --- COURSES ---
    st.markdown("## Courses")
    
    # Query courses with search filter
    query = db.query(Course)
    if search_term:
        query = query.filter(
            or_(
                Course.title.ilike(f"%{search_term}%"),
                Course.description.ilike(f"%{search_term}%")
            )
        )
    
    courses = query.all()
    
    # Paginate courses
    if courses:
        paginated_courses = paginate_data(courses, items_per_page=5, key="courses_view")
        
        for course in paginated_courses:
            with st.expander(f"📘 {course.title}"):
                st.write("**Description:**")
                st.write(course.description)
                
                # Show chapters for this course
                chapters = db.query(Chapter).filter_by(course_id=course.id).all()
                if chapters:
                    st.write("**Chapters:**")
                    for chapter in chapters:
                        st.write(f"- {chapter.title}")
                else:
                    st.write("No chapters available for this course.")
    else:
        st.info("No courses found.")
    
    # --- CHAPTERS ---
    st.markdown("## Chapters")
    
    # Query chapters with search filter
    query = db.query(Chapter).join(Course)
    if search_term:
        query = query.filter(
            or_(
                Chapter.title.ilike(f"%{search_term}%"),
                Chapter.summary.ilike(f"%{search_term}%"),
                Chapter.ilos.ilike(f"%{search_term}%")
            )
        )
    
    chapters = query.all()
    
    # Paginate chapters
    if chapters:
        paginated_chapters = paginate_data(chapters, items_per_page=5, key="chapters_view")
        
        for chapter in paginated_chapters:
            with st.expander(f"📖 {chapter.title} ({chapter.course.title})"):
                st.write("**Summary:**")
                st.write(chapter.summary)
                st.write("**Learning Outcomes:**")
                for ilo in format_ilos(chapter.ilos):
                    st.write(f"- {ilo}")
    else:
        st.info("No chapters found.")

def show_questions():
    """Display questions with filtering options."""
    db = next(get_db())
    
    # --- QUESTIONS ---
    st.markdown("## Questions")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        courses = db.query(Course).all()
        course_options = ["All Courses"] + [course.title for course in courses]
        selected_course = st.selectbox("Filter by Course", course_options, key="question_course_filter")
    
    with col2:
        # Chapter filter depends on selected course
        if selected_course != "All Courses":
            course = db.query(Course).filter_by(title=selected_course).first()
            chapters = db.query(Chapter).filter_by(course_id=course.id).all() if course else []
        else:
            chapters = db.query(Chapter).all()
        
        chapter_options = ["All Chapters"] + [chapter.title for chapter in chapters]
        selected_chapter = st.selectbox("Filter by Chapter", chapter_options, key="question_chapter_filter")
    
    with col3:
        difficulty_options = ["All Difficulties", "Easy (1-2)", "Medium (2-4)", "Hard (4-5)"]
        selected_difficulty = st.selectbox("Filter by Difficulty", difficulty_options, key="question_difficulty_filter")
    
    # Search functionality
    search_term = st.text_input("Search Questions", key="search_questions")
    
    # Build query with filters
    query = db.query(Question).join(Chapter).join(Course)
    
    # Apply course filter
    if selected_course != "All Courses":
        course = db.query(Course).filter_by(title=selected_course).first()
        if course:
            query = query.filter(Chapter.course_id == course.id)
    
    # Apply chapter filter
    if selected_chapter != "All Chapters":
        chapter = db.query(Chapter).filter_by(title=selected_chapter).first()
        if chapter:
            query = query.filter(Question.chapter_id == chapter.id)
    
    # Apply difficulty filter
    if selected_difficulty != "All Difficulties":
        if selected_difficulty == "Easy (1-2)":
            query = query.filter(Question.difficulty <= 2)
        elif selected_difficulty == "Medium (2-4)":
            query = query.filter(Question.difficulty > 2, Question.difficulty <= 4)
        elif selected_difficulty == "Hard (4-5)":
            query = query.filter(Question.difficulty > 4)
    
    # Apply search term
    if search_term:
        query = query.filter(
            or_(
                Question.content.ilike(f"%{search_term}%"),
                Question.tags.ilike(f"%{search_term}%")
            )
        )
    
    questions = query.all()
    
    # Paginate questions
    if questions:
        paginated_questions = paginate_data(questions, items_per_page=5, key="questions_view")
        
        for question in paginated_questions:
            with st.expander(f"❓ {question.content[:100]}... ({question.chapter.title})"):
                st.write("**Question:**")
                st.write(question.content)
                st.write(f"**Difficulty:** {question.difficulty}")
                st.write(f"**Type:** {question.question_type}")
                st.write(f"**Estimated Time:** {question.estimated_time}")
                
                # Show tags if available
                if question.tags:
                    st.write("**Tags:**")
                    tags = question.tags.split(",")
                    for tag in tags:
                        st.write(f"- {tag.strip()}")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Attempt Question", key=f"attempt_{question.id}"):
                        st.session_state.selected_question_id = question.id
                        st.switch_page("pages/question_attempt.py")
                with col2:
                    if st.button("View Discussion", key=f"discuss_{question.id}"):
                        st.session_state.selected_question_id = question.id
                        st.switch_page("pages/discussion.py")
    else:
        st.info("No questions found matching the criteria.")

# Main function for backward compatibility
def main():
    """Main function to display the view page."""
    st.title("View Content")
    
    # Create tabs for different content types
    tab1, tab2 = st.tabs(["Courses & Chapters", "Questions"])
    
    with tab1:
        show_courses_and_chapters()
    
    with tab2:
        show_questions()

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    main()
