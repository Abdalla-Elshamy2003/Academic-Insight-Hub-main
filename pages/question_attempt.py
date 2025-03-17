import streamlit as st
from database import get_db
from models import Question, StudentProgress, Chapter, Course
from utils import show_error, show_success, show_info
from datetime import datetime
import logging
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_string_similarity(str1, str2):
    """Calculate similarity ratio between two strings"""
    # Handle None values by converting to empty strings
    str1 = str(str1).lower() if str1 is not None else ""
    str2 = str(str2).lower() if str2 is not None else ""
    return SequenceMatcher(None, str1, str2).ratio()

# Hide sidebar
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

# Page title
st.title("Question Attempt")

# Check if user is logged in
if "user" not in st.session_state:
    show_error("Please log in to attempt questions.")
    st.stop()

# Check if a question is selected
if "selected_question_id" not in st.session_state:
    show_error("Please select a question to attempt.")
    if st.button("Go to Questions"):
        st.switch_page("pages/view.py")
    st.stop()

# Get question ID from session
question_id = st.session_state.selected_question_id
user_id = st.session_state.user["id"]

# Get question details
db = next(get_db())
question = db.query(Question).filter(Question.id == question_id).first()

if not question:
    show_error("Question not found.")
    if st.button("Go to Questions"):
        st.switch_page("pages/view.py")
    st.stop()

# Get chapter and course info
chapter = db.query(Chapter).filter(Chapter.id == question.chapter_id).first()
course = db.query(Course).filter(Course.id == chapter.course_id).first() if chapter else None

# Get or create student progress
progress = db.query(StudentProgress).filter(
    StudentProgress.user_id == user_id,
    StudentProgress.question_id == question_id
).first()

if not progress:
    progress = StudentProgress(
        user_id=user_id,
        question_id=question_id,
        attempts=0,
        correct=False,
        last_attempt_date=datetime.utcnow()
    )
    db.add(progress)
    db.commit()

# Display question details
st.header("Question")
st.write(f"**Course:** {course.title if course else 'Unknown'}")
st.write(f"**Chapter:** {chapter.title if chapter else 'Unknown'}")
st.write(f"**Difficulty:** {question.difficulty}/5.0")
st.write(f"**Type:** {question.question_type}")
st.write(f"**Attempts:** {progress.attempts}")
st.write(f"**Status:** {'Correct' if progress.correct else 'Not Completed'}")

# Display question content
st.markdown("---")
st.markdown(f"### {question.content}")
st.markdown("---")

# Handle different question types
if question.question_type == "Multiple Choice":
    # Parse options from correct_answer field (format: "correct_option|option1|option2|option3|option4")
    options = question.correct_answer.split("|")
    correct_option = options[0]
    all_options = options[1:]
    
    # Display options
    selected_option = st.radio("Select your answer:", all_options)
    
    # Submit button
    if st.button("Submit Answer"):
        # Increment attempt count
        progress.attempts += 1
        progress.last_attempt_date = datetime.utcnow()
        
        # Check if answer is correct
        if selected_option == correct_option:
            progress.correct = True
            db.commit()
            show_success("Correct answer! Well done!")
            
            # Show explanation if available
            if question.explanation:
                st.markdown("### Explanation")
                st.markdown(question.explanation)
        else:
            db.commit()
            show_error("Incorrect answer. Try again!")

elif question.question_type == "True/False":
    # Display options
    selected_option = st.radio("Select your answer:", ["True", "False"])
    
    # Submit button
    if st.button("Submit Answer"):
        # Increment attempt count
        progress.attempts += 1
        progress.last_attempt_date = datetime.utcnow()
        
        # Check if answer is correct
        if selected_option.lower() == question.correct_answer.lower():
            progress.correct = True
            db.commit()
            show_success("Correct answer! Well done!")
            
            # Show explanation if available
            if question.explanation:
                st.markdown("### Explanation")
                st.markdown(question.explanation)
        else:
            db.commit()
            show_error("Incorrect answer. Try again!")

elif question.question_type == "Essay":
    # Display text area for essay response
    essay_response = st.text_area("Your answer:", height=200)
    
    # Submit button
    if st.button("Submit Answer"):
        if not essay_response.strip():
            show_error("Please provide an answer before submitting.")
        else:
            # Increment attempt count
            progress.attempts += 1
            progress.last_attempt_date = datetime.utcnow()
            db.commit()
            
            # For essay questions, show the model answer for self-evaluation
            st.markdown("### Model Answer")
            st.markdown(question.correct_answer)
            
            # Show explanation if available
            if question.explanation:
                st.markdown("### Explanation")
                st.markdown(question.explanation)
            
            # Allow self-evaluation
            st.markdown("### Self Evaluation")
            correct = st.radio("Did you answer correctly?", ["Yes", "No"])
            
            if st.button("Save Evaluation"):
                progress.correct = (correct == "Yes")
                db.commit()
                show_success("Evaluation saved!")
                st.rerun()
else:
    # Default to text input for other question types
    user_answer = st.text_input("Your answer:")
    
    # Submit button
    if st.button("Submit Answer"):
        if not user_answer.strip():
            show_error("Please provide an answer before submitting.")
        else:
            # Increment attempt count
            progress.attempts += 1
            progress.last_attempt_date = datetime.utcnow()
            
            # Calculate similarity between user answer and correct answer
            similarity = calculate_string_similarity(user_answer, question.correct_answer)
            similarity_threshold = 0.8  # 80% similarity threshold
            
            # Check if answer is similar enough to be considered correct
            if similarity >= similarity_threshold:
                progress.correct = True
                db.commit()
                show_success("Correct answer! Well done!")
                
                # Show explanation if available
                if question.explanation:
                    st.markdown("### Explanation")
                    st.markdown(question.explanation)
            else:
                db.commit()
                show_error("Incorrect answer. Try again!")

# Display attempt history
if progress.attempts > 0:
    st.markdown("---")
    st.markdown(f"### Attempt History")
    st.markdown(f"You have attempted this question {progress.attempts} times.")
    st.markdown(f"Last attempt: {progress.last_attempt_date}")
    st.markdown(f"Status: {'Correct' if progress.correct else 'Not Completed'}")

# Navigation buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Back to Questions"):
        st.switch_page("pages/view.py")
with col2:
    if st.button("View My Progress"):
        st.switch_page("pages/my_progress.py")
with col3:
    if st.button("Discuss This Question"):
        st.session_state["selected_question_id"] = question_id
        st.switch_page("pages/discussion.py")