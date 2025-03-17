import streamlit as st
from database import get_db
from models import Course, Chapter, Question
from utils import show_success, show_error, format_ilos
from datetime import datetime

st.title("Edit Item")

# Check what we're editing
if "editing_course" in st.session_state:
    item_type = "Course"
    item_id = st.session_state["editing_course"]
elif "editing_chapter" in st.session_state:
    item_type = "Chapter"
    item_id = st.session_state["editing_chapter"]
elif "editing_question" in st.session_state:
    item_type = "Question"
    item_id = st.session_state["editing_question"]
else:
    st.error("No item selected for editing. Please select an item to edit from the View page.")
    st.stop()

# Get database connection
db = next(get_db())

# Edit Course
if item_type == "Course":
    course = db.query(Course).get(item_id)
    if not course:
        st.error("Course not found.")
        st.stop()
    
    st.subheader(f"Edit Course: {course.title}")
    
    with st.form("edit_course_form"):
        title = st.text_input("Course Title", value=course.title)
        description = st.text_area("Course Description", value=course.description or "")
        submit = st.form_submit_button("Update Course")
    
    if submit:
        if title:
            try:
                course.title = title
                course.description = description
                course.updated_at = datetime.utcnow()
                db.commit()
                show_success("Course updated successfully!")
                
                # Clear the editing state
                if st.button("Back to View"):
                    st.session_state.pop("editing_course")
                    st.switch_page("view")
            except Exception as e:
                db.rollback()
                show_error(f"Error updating course: {str(e)}")
        else:
            show_error("Course title is required.")

# Edit Chapter
elif item_type == "Chapter":
    chapter = db.query(Chapter).get(item_id)
    if not chapter:
        st.error("Chapter not found.")
        st.stop()
    
    st.subheader(f"Edit Chapter: {chapter.title}")
    
    with st.form("edit_chapter_form"):
        # Get all courses for the dropdown
        courses = db.query(Course).all()
        course_choice = st.selectbox(
            "Select Course",
            options=[(c.id, c.title) for c in courses],
            format_func=lambda x: x[1],
            index=[i for i, c in enumerate(courses) if c.id == chapter.course_id][0] if courses else 0
        )
        
        title = st.text_input("Chapter Title", value=chapter.title)
        summary = st.text_area("Chapter Summary", value=chapter.summary or "")
        ilos = st.text_area("Intended Learning Outcomes (One per line)", 
                          value=chapter.ilos or "")
        submit = st.form_submit_button("Update Chapter")
    
    if submit:
        if title and course_choice:
            try:
                chapter.course_id = course_choice[0]
                chapter.title = title
                chapter.summary = summary
                chapter.ilos = ilos
                chapter.updated_at = datetime.utcnow()
                db.commit()
                show_success("Chapter updated successfully!")
                
                # Clear the editing state
                if st.button("Back to View"):
                    st.session_state.pop("editing_chapter")
                    st.switch_page("view")
            except Exception as e:
                db.rollback()
                show_error(f"Error updating chapter: {str(e)}")
        else:
            show_error("Chapter title and course are required.")

# Edit Question
elif item_type == "Question":
    question = db.query(Question).get(item_id)
    if not question:
        st.error("Question not found.")
        st.stop()
    
    st.subheader("Edit Question")
    
    with st.form("edit_question_form"):
        # Get all chapters for the dropdown
        chapters = db.query(Chapter).all()
        chapter_choice = st.selectbox(
            "Select Chapter",
            options=[(c.id, f"{c.course.title} - {c.title}") for c in chapters],
            format_func=lambda x: x[1],
            index=[i for i, c in enumerate(chapters) if c.id == question.chapter_id][0] if chapters else 0
        )
        
        content = st.text_area("Question Content", value=question.content)
        difficulty = st.slider("Difficulty Level", 1.0, 5.0, float(question.difficulty or 3.0), 0.5)
        estimated_time = st.number_input("Estimated Time (minutes)", 
                                       min_value=1, value=int(question.estimated_time or 5))
        student_level = st.selectbox("Student Level", 
                                   ["Beginner", "Intermediate", "Advanced"],
                                   index=["Beginner", "Intermediate", "Advanced"].index(question.student_level) 
                                   if question.student_level in ["Beginner", "Intermediate", "Advanced"] else 0)
        
        question_type = st.selectbox("Question Type", 
                                   ["Multiple Choice", "Essay", "Short Answer", "True/False"],
                                   index=["Multiple Choice", "Essay", "Short Answer", "True/False"].index(question.question_type)
                                   if question.question_type in ["Multiple Choice", "Essay", "Short Answer", "True/False"] else 0)
        
        tags = st.text_input("Tags (comma-separated)", value=question.tags or "")
        correct_answer = st.text_area("Correct Answer", value=question.correct_answer or "")
        explanation = st.text_area("Explanation", value=question.explanation or "")
        
        submit = st.form_submit_button("Update Question")
    
    if submit:
        if content and chapter_choice:
            try:
                question.chapter_id = chapter_choice[0]
                question.content = content
                question.difficulty = difficulty
                question.estimated_time = estimated_time
                question.student_level = student_level
                question.question_type = question_type
                question.tags = tags
                question.correct_answer = correct_answer
                question.explanation = explanation
                question.updated_at = datetime.utcnow()
                db.commit()
                show_success("Question updated successfully!")
                
                # Clear the editing state
                if st.button("Back to View"):
                    st.session_state.pop("editing_question")
                    st.switch_page("view")
            except Exception as e:
                db.rollback()
                show_error(f"Error updating question: {str(e)}")
        else:
            show_error("Question content and chapter are required.")

# Add a back button
if st.button("Cancel and Go Back"):
    # Clear all editing states
    if "editing_course" in st.session_state:
        st.session_state.pop("editing_course")
    if "editing_chapter" in st.session_state:
        st.session_state.pop("editing_chapter")
    if "editing_question" in st.session_state:
        st.session_state.pop("editing_question")
    st.switch_page("view") 