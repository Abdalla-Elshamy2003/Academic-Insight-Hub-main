import streamlit as st
from database import get_db
from models import User, Role, UserRole
from sqlalchemy.exc import IntegrityError
from utils import (
    hash_password, verify_password, validate_email, 
    validate_username, validate_password_strength,
    show_success, show_error, show_warning, show_info, rerun
)
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_auth_page():
    """Main function to display the authentication page."""
    # Hide sidebar and navigation for login/register pages
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
    
    # Center the authentication form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # --- Initialize authentication view ---
        if "auth_view" not in st.session_state:
            st.session_state.auth_view = "login"
            
        # App logo/header
        st.image("https://img.icons8.com/color/96/000000/student-center.png", width=100)
        st.title("Academic Insight Hub")
        st.markdown("##### Your Educational Platform")
        st.markdown("---")

        # --- LOGIN VIEW ---
        if st.session_state.auth_view == "login":
            st.subheader("Login")
            
            # For testing/demo purposes, show default admin credentials
            st.info("Default admin credentials: admin / Admin@123")
            
            with st.form("login_form", clear_on_submit=False):
                username_or_email = st.text_input("Username or Email", value="admin")
                password = st.text_input("Password", type="password", value="Admin@123")
                login_submit = st.form_submit_button("Login", use_container_width=True)
                
            if login_submit:
                if username_or_email and password:
                    try:
                        logger.info(f"Attempting login for user: {username_or_email}")
                        db = next(get_db())
                        user = db.query(User).filter(
                            (User.username == username_or_email) | (User.email == username_or_email)
                        ).first()
                        
                        if user and verify_password(user.password, password, user.salt):
                            logger.info(f"Login successful for user: {user.username}")
                            
                            # Get user role
                            user_role = db.query(UserRole).filter_by(user_id=user.id).first()
                            if not user_role:
                                logger.error(f"No role found for user: {user.username}")
                                show_error("User role not found. Please contact an administrator.")
                                return
                                
                            role = db.query(Role).filter(Role.id == user_role.role_id).first()
                            if not role:
                                logger.error(f"Role ID {user_role.role_id} not found in database")
                                show_error("Role not found. Please contact an administrator.")
                                return
                            
                            # Update last login time
                            user.last_login = datetime.utcnow()
                            db.commit()
                            
                            # Store user info in session state
                            st.session_state["user"] = {
                                "id": user.id,
                                "username": user.username,
                                "email": user.email,
                                "role": role.name
                            }
                            
                            # Parse permissions if role exists
                            try:
                                permissions = json.loads(role.permissions)
                                st.session_state.user["permissions"] = permissions
                            except Exception as e:
                                logger.error(f"Error parsing permissions: {str(e)}")
                                st.session_state.user["permissions"] = {}
                            
                            # Clear any previous database initialization flag to ensure clean state
                            if 'db_initialized' in st.session_state:
                                st.session_state.pop('db_initialized')
                                
                            show_success("Login successful!")
                            
                            # Force a full page rerun to apply session state changes
                            st.rerun()
                        else:
                            logger.warning(f"Invalid login attempt for user: {username_or_email}")
                            show_error("Invalid credentials")
                    except Exception as e:
                        logger.error(f"Login error: {str(e)}")
                        show_error(f"Login error: {str(e)}")
                else:
                    show_error("Please fill in all fields")

            # Registration and forgot password links
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create an Account", use_container_width=True):
                    st.session_state.auth_view = "register"
                    st.rerun()
            with col2:
                if st.button("Forgot Password?", use_container_width=True):
                    st.session_state.auth_view = "forgot_password"
                    st.rerun()

        # --- REGISTER VIEW ---
        elif st.session_state.auth_view == "register":
            st.subheader("Create an Account")
            
            # Get available roles from database
            try:
                db = next(get_db())
                available_roles = [role.name.capitalize() for role in db.query(Role).all() 
                                if role.name.lower() != "admin"]  # Exclude admin role from registration
                
                if not available_roles:
                    st.error("No roles available for registration. Please contact an administrator.")
                    if st.button("Back to Login", use_container_width=True):
                        st.session_state.auth_view = "login"
                        st.rerun()
                    return
            except Exception as e:
                logger.error(f"Error fetching roles: {str(e)}")
                st.error("Error fetching roles. Please try again later.")
                if st.button("Back to Login", use_container_width=True):
                    st.session_state.auth_view = "login"
                    st.rerun()
                return
            
            with st.form("register_form", clear_on_submit=True):
                username = st.text_input("Username (3-50 characters, alphanumeric)")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password", 
                                    help="At least 8 characters with uppercase, lowercase, number, and special character")
                confirm_password = st.text_input("Confirm Password", type="password")
                role_type = st.selectbox("Register as", available_roles)
                submit = st.form_submit_button("Register", use_container_width=True)
            
            if submit:
                # Validate all inputs
                valid_inputs = True
                
                if not username or not email or not password or not confirm_password:
                    show_error("Please fill in all fields")
                    valid_inputs = False
                
                if valid_inputs and not validate_username(username):
                    show_error("Username must be 3-50 characters and contain only letters, numbers, and underscores")
                    valid_inputs = False
                    
                if valid_inputs and not validate_email(email):
                    show_error("Please enter a valid email address")
                    valid_inputs = False
                    
                if valid_inputs:
                    is_strong, message = validate_password_strength(password)
                    if not is_strong:
                        show_error(message)
                        valid_inputs = False
                        
                if valid_inputs and password != confirm_password:
                    show_error("Passwords do not match")
                    valid_inputs = False
                    
                if valid_inputs:
                    try:
                        # Check if role exists
                        role = db.query(Role).filter_by(name=role_type.lower()).first()
                        if not role:
                            show_error("Role not found. Please contact an administrator.")
                            valid_inputs = False
                    except Exception as e:
                        logger.error(f"Error checking role: {str(e)}")
                        show_error(f"Database error: {str(e)}")
                        valid_inputs = False
                        
                if valid_inputs:
                    # Create new user with secure password
                    try:
                        hashed_password, salt = hash_password(password)
                        new_user = User(
                            username=username,
                            email=email,
                            password=hashed_password,
                            salt=salt,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        # Add user and role
                        db.add(new_user)
                        db.flush()  # Get the user ID
                        
                        user_role = UserRole(
                            user_id=new_user.id, 
                            role_id=role.id,
                            created_at=datetime.utcnow()
                        )
                        db.add(user_role)
                        db.commit()
                        
                        logger.info(f"User registered successfully: {username}")
                        show_success("Registration successful! Please login.")
                        st.session_state.auth_view = "login"
                        st.rerun()
                    except IntegrityError:
                        db.rollback()
                        logger.warning(f"Registration failed - username or email already exists: {username}, {email}")
                        show_error("Username or email already exists")
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Registration error: {str(e)}")
                        show_error(f"An error occurred: {str(e)}")

            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_view = "login"
                st.rerun()

        # --- FORGOT PASSWORD VIEW ---
        elif st.session_state.auth_view == "forgot_password":
            st.subheader("Reset Password")
            
            with st.form("reset_password_form", clear_on_submit=True):
                email = st.text_input("Email")
                submit = st.form_submit_button("Send Reset Link", use_container_width=True)
            
            if submit and email:
                if validate_email(email):
                    # In a real application, this would send an email with a reset link
                    # For this demo, we'll just show a success message
                    logger.info(f"Password reset requested for email: {email}")
                    show_info("If an account with this email exists, a password reset link will be sent.")
                    # In a real app, you would generate a token, store it, and send an email
                else:
                    show_error("Please enter a valid email address")
            
            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_view = "login"
                st.rerun()

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    show_auth_page()
