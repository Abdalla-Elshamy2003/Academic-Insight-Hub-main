import streamlit as st
from database import engine, get_db, init_db
import models
from models import Role, UserRole
import logging
from utils import show_error, show_info, show_success, rerun
import traceback
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config first (before any other Streamlit commands)
st.set_page_config(
    page_title="Academic Insight Hub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the default sidebar pages
st.markdown("""
<style>
[data-testid="collapsedControl"] {display: none}
section[data-testid="stSidebar"] div.block-container {padding-top: 2rem;}
.main > div {padding-left: 20px; padding-right: 20px;}
div[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

try:
    # Initialize database (will only run once due to session state flag)
    init_db()
    
    # --- Authentication Check ---
    if "user" not in st.session_state:
        logger.info("User not logged in, showing auth page")
        import pages.auth as auth
        auth.show_auth_page()
        st.stop()
    
    if "authenticated" not in st.session_state:
        logger.info(f"User authenticated: {st.session_state.user.get('username')}")
        st.session_state["authenticated"] = True
    
    if st.session_state.get("authenticated"):
        logger.info("Rendering main content")
        # --- Header for Logged-In Users ---
        header_cols = st.columns([4, 1])
        with header_cols[0]:
            st.markdown(f"### Welcome to Academic Insight Hub, {st.session_state.user['username']}!")
        with header_cols[1]:
            if st.button("Logout", key="logout_button"):
                logger.info(f"User logging out: {st.session_state.user.get('username')}")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.query_params.clear()  # Clear query params to reset state
                st.stop()
        
        # --- Get User Role and Permissions ---
        if "role" not in st.session_state.user:
            try:
                logger.info(f"Fetching role for user: {st.session_state.user.get('username')}")
                db = next(get_db())
                user_role = db.query(UserRole).filter_by(user_id=st.session_state.user["id"]).first()
                if user_role:
                    role = db.query(Role).get(user_role.role_id)
                    if role:
                        st.session_state.user["role"] = role.name
                        # Parse permissions
                        import json
                        permissions = json.loads(role.permissions)
                        st.session_state.user["permissions"] = permissions
                        logger.info(f"Role assigned: {role.name}")
                    else:
                        logger.error(f"Role not found for user {st.session_state.user['username']}")
                else:
                    logger.error(f"UserRole not found for user {st.session_state.user['username']}")
            except Exception as e:
                logger.error(f"Error getting user role: {str(e)}")
                logger.error(traceback.format_exc())
        
        # --- Main Navigation Tabs ---
        role = st.session_state.user.get("role", "").lower()
        logger.debug(f"User role for navigation: {role}")
        
        # Display user info in sidebar
        with st.sidebar:
            st.markdown("### User Information")
            st.write(f"**Username:** {st.session_state.user['username']}")
            st.write(f"**Email:** {st.session_state.user['email']}")
            st.write(f"**Role:** {st.session_state.user.get('role', 'Unknown')}")
            st.markdown("---")
        
        # Main tabs based on role
        if role in ["admin", "professor", "teaching_assistant"]:
            # Initialize states if not exists
            if "current_tab" not in st.session_state:
                st.session_state.current_tab = "View"
            if "add_option" not in st.session_state:
                st.session_state.add_option = "Course"

            # Create tabs
            tab_titles = ["View", "Add", "Manage Profile"]
            current_tab = st.tabs(tab_titles)
            
            # View Tab Content
            with current_tab[0]:
                if "View" not in st.session_state:
                    st.session_state.View = {}
                
                st.markdown("### View Content")
                view_option = st.radio(
                    "Select what to view:",
                    ["Courses and Chapters", "Questions", "Analytics Dashboard"],
                    horizontal=True,
                    key="staff_view_option"
                )
                
                if view_option == "Courses and Chapters":
                    import pages.view as view_page
                    view_page.show_courses_and_chapters()
                elif view_option == "Questions":
                    import pages.view as view_page
                    view_page.show_questions()
                elif view_option == "Analytics Dashboard":
                    import pages.Analytics_Dashboard as analytics
                    analytics.show_analytics()
            
            # Add Tab Content
            with current_tab[1]:
                if "Add" not in st.session_state:
                    st.session_state.Add = {}
                    
                st.markdown("### Add Content")
                add_option = st.radio(
                    "What would you like to add?",
                    ["Course", "Chapter", "Question", "AI Question Generator", "Exam Builder", "View Exams"],
                    horizontal=True,
                    key="staff_add_option"
                )
                
                if add_option == "Course":
                    import pages.add as add_page
                    add_page.add_course()
                elif add_option == "Chapter":
                    import pages.add as add_page
                    add_page.add_chapter()
                elif add_option == "Question":
                    import pages.add as add_page
                    add_page.add_question()
                elif add_option == "AI Question Generator":
                    import pages.question_generator as qg_page
                    qg_page.show_question_generator()
                elif add_option == "Exam Builder":
                    import pages.exam_builder as eb_page
                    eb_page.show_exam_builder()
                elif add_option == "View Exams":
                    import pages.add as add_page
                    add_page.view_exams()
            
            # Manage Profile Tab Content
            with current_tab[2]:
                if "Manage" not in st.session_state:
                    st.session_state.Manage = {}
                    
                st.markdown("### Manage Profile")
                if role == "admin":
                    manage_option = st.radio(
                        "Management Options:",
                        ["My Profile", "User Management", "Question Bank"],
                        horizontal=True,
                        key="admin_manage_option"
                    )
                    
                    if manage_option == "My Profile":
                        import pages.profile as profile
                        profile.show_profile()
                    elif manage_option == "User Management":
                        import pages.user_management as user_mgmt
                        user_mgmt.show_user_management()
                    elif manage_option == "Question Bank":
                        import pages.question_bank as qb
                        qb.show_question_bank()
                
                elif role == "professor":
                    manage_option = st.radio(
                        "Management Options:",
                        ["My Profile", "Question Bank"],
                        horizontal=True,
                        key="professor_manage_option"
                    )
                    
                    if manage_option == "My Profile":
                        import pages.profile as profile
                        profile.show_profile()
                    elif manage_option == "Question Bank":
                        import pages.question_bank as qb
                        qb.show_question_bank()
                else:  # teaching assistant
                    manage_option = st.radio(
                        "Management Options:",
                        ["My Profile"],
                        horizontal=True,
                        key="ta_manage_option"
                    )
                    import pages.profile as profile
                    profile.show_profile()

        # Student role has different tabs
        else:  # student role
            # Create tabs
            tab_titles = ["View", "My Progress", "Manage Profile"]
            current_tab = st.tabs(tab_titles)
            
            # View Tab Content
            with current_tab[0]:
                if "View" not in st.session_state:
                    st.session_state.View = {}
                    
                st.markdown("### View Content")
                view_option = st.radio(
                    "Select what to view:",
                    ["Courses and Chapters", "Questions"],
                    horizontal=True,
                    key="student_view_option"
                )
                
                if view_option == "Courses and Chapters":
                    import pages.view as view_page
                    view_page.show_courses_and_chapters()
                elif view_option == "Questions":
                    import pages.view as view_page
                    view_page.show_questions()
            
            # My Progress Tab Content
            with current_tab[1]:
                if "Progress" not in st.session_state:
                    st.session_state.Progress = {}
                    
                import pages.my_progress as progress
                progress.show_progress()
            
            # Manage Profile Tab Content
            with current_tab[2]:
                if "Manage" not in st.session_state:
                    st.session_state.Manage = {}
                    
                st.markdown("### Manage Profile")
                manage_option = st.radio(
                    "Options:",
                    ["My Profile", "Student Feedback"],
                    horizontal=True,
                    key="student_manage_option"
                )
                
                if manage_option == "My Profile":
                    import pages.profile as profile
                    profile.show_profile()
                elif manage_option == "Student Feedback":
                    import pages.student_feedback as feedback
                    feedback.show_feedback()

except Exception as e:
    show_error(f"Application error: {str(e)}")
    logger.error(f"Application error: {str(e)}")
    logger.error(traceback.format_exc())

