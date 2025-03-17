import streamlit as st
from database import get_db
from models import Discussion, Question, Chapter, Course, User
from utils import show_error, show_success, show_info
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Page title
st.title("Discussion")

# Check if user is logged in
if "user" not in st.session_state:
    show_error("Please log in to participate in discussions.")
    st.stop()

# Check if a question is selected
if "selected_question_id" not in st.session_state:
    show_error("Please select a question to discuss.")
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

# Display question details
st.header("Question Details")
st.write(f"**Course:** {course.title if course else 'Unknown'}")
st.write(f"**Chapter:** {chapter.title if chapter else 'Unknown'}")
st.write(f"**Question:** {question.content}")
st.write(f"**Difficulty:** {question.difficulty}")
st.write(f"**Type:** {question.question_type}")

# Display discussions
st.header("Comments")

# Get all top-level comments for this question
comments = db.query(Discussion).filter(
    Discussion.question_id == question_id,
    Discussion.parent_id == None  # Only top-level comments
).order_by(Discussion.created_at.desc()).all()

# Add new comment
st.subheader("Add a Comment")
with st.form("add_comment_form"):
    comment_text = st.text_area("Your comment")
    submit_comment = st.form_submit_button("Submit Comment")

if submit_comment:
    if not comment_text.strip():
        show_error("Comment cannot be empty.")
    else:
        # Create new comment
        new_comment = Discussion(
            question_id=question_id,
            user_id=user_id,
            content=comment_text,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            db.add(new_comment)
            db.commit()
            show_success("Comment added successfully!")
            st.rerun()  # Refresh to show the new comment
        except Exception as e:
            db.rollback()
            show_error(f"Error adding comment: {str(e)}")

# Display existing comments
if not comments:
    st.info("No comments yet. Be the first to comment!")
else:
    for comment in comments:
        with st.container():
            # Get comment author
            author = db.query(User).filter(User.id == comment.user_id).first()
            author_name = author.username if author else "Unknown User"
            
            # Display comment
            st.markdown(f"**{author_name}** - {comment.created_at.strftime('%Y-%m-%d %H:%M')}")
            st.markdown(comment.content)
            
            # Get replies for this comment
            replies = db.query(Discussion).filter(
                Discussion.parent_id == comment.id
            ).order_by(Discussion.created_at).all()
            
            # Display replies
            if replies:
                with st.expander(f"View {len(replies)} replies"):
                    for reply in replies:
                        reply_author = db.query(User).filter(User.id == reply.user_id).first()
                        reply_author_name = reply_author.username if reply_author else "Unknown User"
                        
                        st.markdown(f"**{reply_author_name}** - {reply.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.markdown(reply.content)
            
            # Add reply form
            with st.expander("Reply"):
                with st.form(f"reply_form_{comment.id}"):
                    reply_text = st.text_area("Your reply", key=f"reply_{comment.id}")
                    submit_reply = st.form_submit_button("Submit Reply")
                
                if submit_reply:
                    if not reply_text.strip():
                        show_error("Reply cannot be empty.")
                    else:
                        # Create new reply
                        new_reply = Discussion(
                            question_id=question_id,
                            user_id=user_id,
                            parent_id=comment.id,
                            content=reply_text,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        try:
                            db.add(new_reply)
                            db.commit()
                            show_success("Reply added successfully!")
                            st.rerun()  # Refresh to show the new reply
                        except Exception as e:
                            db.rollback()
                            show_error(f"Error adding reply: {str(e)}")
            
            st.markdown("---")

# Navigation buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Back to Question"):
        st.switch_page("pages/question_attempt.py")
with col2:
    if st.button("Back to Questions List"):
        st.switch_page("pages/view.py")