# import streamlit as st
# from database import get_db
# from models import Question, StudentFeedback
# from utils import show_success, show_error

# st.title("Rate Questions")

# def submit_feedback():
#     db = next(get_db())
#     questions = db.query(Question).all()
    
#     st.write("### Your Information")
#     student_gpa = st.number_input("Your GPA (0.0 - 4.0)", min_value=0.0, max_value=4.0, value=3.0, step=0.1)
#     attendance_rate = st.number_input("Your Attendance Rate (0% - 100%)", min_value=0.0, max_value=100.0, value=90.0, step=5.0) / 100
    
#     st.write("### Rate Questions")
#     st.write("Please rate the difficulty of each question you've attempted.")
    
#     for question in questions:
#         with st.expander(f"Question #{question.id}"):
#             st.write(question.content)
#             st.write(f"Professor's Estimated Difficulty: {question.difficulty}/5.0")
#             st.write(f"Estimated Time: {question.estimated_time} minutes")
            
#             difficulty_rating = st.slider(
#                 "How difficult did you find this question?",
#                 min_value=1.0,
#                 max_value=5.0,
#                 value=3.0,
#                 step=0.5,
#                 key=f"rating_{question.id}"
#             )
            
#             if st.button("Submit Rating", key=f"submit_{question.id}"):
#                 try:
#                     feedback = StudentFeedback(
#                         question_id=question.id,
#                         difficulty_rating=difficulty_rating,
#                         student_gpa=student_gpa,
#                         attendance_rate=attendance_rate
#                     )
#                     db.add(feedback)
#                     db.commit()
#                     show_success("Thank you for your feedback!")
#                 except Exception as e:
#                     show_error(f"Error submitting feedback: {str(e)}")

# submit_feedback()



import streamlit as st
from database import get_db
from models import Question, StudentFeedback, Chapter, Course
from utils import show_success, show_error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_feedback():
    """Display the student feedback page."""
    st.markdown("## Student Feedback")
    
    # Check if user is logged in
    if "user" not in st.session_state:
        st.warning("Please log in to provide feedback.")
        return
    
    user_id = st.session_state.user["id"]
    
    try:
        db = next(get_db())
        
        # Get courses for filtering
        courses = db.query(Course).all()
        
        # Create filters
        col1, col2 = st.columns(2)
        
        with col1:
            selected_course = st.selectbox(
                "Select Course",
                options=[(0, "All Courses")] + [(c.id, c.title) for c in courses],
                format_func=lambda x: x[1],
                key="feedback_course_select"
            )
        
        # Get chapters based on selected course
        if selected_course[0] == 0:
            chapters = db.query(Chapter).all()
        else:
            chapters = db.query(Chapter).filter_by(course_id=selected_course[0]).all()
        
        with col2:
            selected_chapter = st.selectbox(
                "Select Chapter",
                options=[(0, "All Chapters")] + [(c.id, c.title) for c in chapters],
                format_func=lambda x: x[1],
                key="feedback_chapter_select"
            )
        
        # Get questions based on filters
        query = db.query(Question).join(Chapter).join(Course)
        
        if selected_course[0] != 0:
            query = query.filter(Chapter.course_id == selected_course[0])
        
        if selected_chapter[0] != 0:
            query = query.filter(Question.chapter_id == selected_chapter[0])
        
        questions = query.all()
        
        if not questions:
            st.info("No questions found for the selected filters.")
            return
        
        # Select a question to provide feedback on
        selected_question = st.selectbox(
            "Select a Question to Provide Feedback",
            options=[(q.id, f"{q.content[:50]}..." if len(q.content) > 50 else q.content) for q in questions],
            format_func=lambda x: x[1],
            key="feedback_question_select"
        )
        
        # Get the selected question
        question = db.query(Question).get(selected_question[0])
        
        if question:
            st.markdown("### Question Details")
            st.write(f"**Question:** {question.content}")
            st.write(f"**Type:** {question.question_type}")
            st.write(f"**Difficulty (set by instructor):** {question.difficulty}/5")
            
            # Check if user has already provided feedback for this question
            existing_feedback = db.query(StudentFeedback).filter_by(
                question_id=question.id,
                user_id=user_id
            ).first()
            
            if existing_feedback:
                st.info("You have already provided feedback for this question.")
                
                # Show existing feedback
                st.markdown("### Your Feedback")
                st.write(f"**Difficulty Rating:** {existing_feedback.difficulty_rating}/5")
                st.write(f"**Your GPA:** {existing_feedback.student_gpa}")
                st.write(f"**Your Attendance Rate:** {existing_feedback.attendance_rate * 100}%")
                
                # Option to update feedback
                if st.button("Update Feedback"):
                    st.session_state.updating_feedback = True
                    st.session_state.feedback_id = existing_feedback.id
                    st.rerun()
            else:
                # Provide new feedback
                with st.form("feedback_form"):
                    st.markdown("### Provide Your Feedback")
                    
                    difficulty_rating = st.slider(
                        "How difficult did you find this question? (1-5)",
                        min_value=1.0,
                        max_value=5.0,
                        step=0.5,
                        value=3.0
                    )
                    
                    student_gpa = st.slider(
                        "What is your current GPA? (0-4)",
                        min_value=0.0,
                        max_value=4.0,
                        step=0.1,
                        value=3.0
                    )
                    
                    attendance_rate = st.slider(
                        "What is your attendance rate? (0-100%)",
                        min_value=0,
                        max_value=100,
                        step=5,
                        value=80
                    ) / 100  # Convert to decimal
                    
                    submit = st.form_submit_button("Submit Feedback")
                    
                    if submit:
                        try:
                            # Create new feedback
                            new_feedback = StudentFeedback(
                                question_id=question.id,
                                user_id=user_id,
                                difficulty_rating=difficulty_rating,
                                student_gpa=student_gpa,
                                attendance_rate=attendance_rate
                            )
                            
                            db.add(new_feedback)
                            db.commit()
                            
                            show_success("Feedback submitted successfully!")
                            st.rerun()
                            
                        except Exception as e:
                            logger.error(f"Error submitting feedback: {str(e)}")
                            show_error(f"Error submitting feedback: {str(e)}")
        
        # Handle updating feedback
        if "updating_feedback" in st.session_state and st.session_state.updating_feedback:
            feedback_id = st.session_state.feedback_id
            feedback = db.query(StudentFeedback).get(feedback_id)
            
            if feedback:
                with st.form("update_feedback_form"):
                    st.markdown("### Update Your Feedback")
                    
                    difficulty_rating = st.slider(
                        "How difficult did you find this question? (1-5)",
                        min_value=1.0,
                        max_value=5.0,
                        step=0.5,
                        value=feedback.difficulty_rating
                    )
                    
                    student_gpa = st.slider(
                        "What is your current GPA? (0-4)",
                        min_value=0.0,
                        max_value=4.0,
                        step=0.1,
                        value=feedback.student_gpa
                    )
                    
                    attendance_rate = st.slider(
                        "What is your attendance rate? (0-100%)",
                        min_value=0,
                        max_value=100,
                        step=5,
                        value=int(feedback.attendance_rate * 100)
                    ) / 100  # Convert to decimal
                    
                    update = st.form_submit_button("Update Feedback")
                    
                    if update:
                        try:
                            # Update feedback
                            feedback.difficulty_rating = difficulty_rating
                            feedback.student_gpa = student_gpa
                            feedback.attendance_rate = attendance_rate
                            
                            db.commit()
                            
                            show_success("Feedback updated successfully!")
                            st.session_state.updating_feedback = False
                            st.rerun()
                            
                        except Exception as e:
                            logger.error(f"Error updating feedback: {str(e)}")
                            show_error(f"Error updating feedback: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error displaying feedback page: {str(e)}")
        show_error(f"Error loading feedback page: {str(e)}")

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    st.title("Student Feedback")
    show_feedback()
