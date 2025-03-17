import streamlit as st
from database import get_db
from models import User
from utils import show_success, show_error, validate_email, validate_password_strength, hash_password, verify_password
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_profile():
    """Display the user profile page."""
    st.markdown("## My Profile")
    
    # Check if user is logged in
    if "user" not in st.session_state:
        logger.info("User not logged in, showing auth page")
        # Render the auth page inline
        import pages.auth as auth
        auth.show_auth_page()
        st.stop()  # Stop execution here if not logged in

    # Log successful authentication
    if "authenticated" not in st.session_state:
        logger.info(f"User authenticated: {st.session_state.user.get('username')}")
        st.session_state["authenticated"] = True

    # Render main content only if authenticated
    if st.session_state.get("authenticated"):
        # --- Header for Logged-In Users ---
        header_cols = st.columns([4, 1])
        with header_cols[0]:
            st.markdown(f"### Welcome to Academic Insight Hub, {st.session_state.user['username']}!")
        with header_cols[1]:
            if st.button("Logout"):
                logger.info(f"User logging out: {st.session_state.user.get('username')}")
                # Clear all session state to ensure clean logout
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        user_id = st.session_state.user["id"]
        
        try:
            db = next(get_db())
            user = db.query(User).get(user_id)
            
            if not user:
                st.error("User not found.")
                return
            
            # Display user information
            st.markdown("### User Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Username:** {user.username}")
                st.write(f"**Email:** {user.email}")
                st.write(f"**Role:** {st.session_state.user.get('role', 'Unknown')}")
                st.write(f"**Account Created:** {user.created_at.strftime('%Y-%m-%d')}")
                st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
            
            # Create tabs for different profile actions
            tab1, tab2 = st.tabs(["Update Email", "Change Password"])
            
            with tab1:
                st.markdown("### Update Email")
                
                with st.form("update_email_form"):
                    new_email = st.text_input("New Email Address")
                    current_password = st.text_input("Current Password", type="password")
                    
                    submit = st.form_submit_button("Update Email")
                
                if submit:
                    if not new_email or not current_password:
                        show_error("Please fill in all fields.")
                        return
                    
                    # Validate email
                    if not validate_email(new_email):
                        show_error("Please enter a valid email address.")
                        return
                    
                    # Verify current password
                    if not verify_password(user.password, current_password, user.salt):
                        show_error("Current password is incorrect.")
                        return
                    
                    try:
                        # Check if email is already in use
                        existing_user = db.query(User).filter(User.email == new_email, User.id != user_id).first()
                        if existing_user:
                            show_error("Email address is already in use.")
                            return
                        
                        # Update email
                        user.email = new_email
                        user.updated_at = datetime.utcnow()
                        
                        db.commit()
                        
                        # Update session state
                        st.session_state.user["email"] = new_email
                        
                        show_success("Email updated successfully!")
                        st.rerun()
                    
                    except Exception as e:
                        logger.error(f"Error updating email: {str(e)}")
                        show_error(f"Error updating email: {str(e)}")
            
            with tab2:
                st.markdown("### Change Password")
                
                with st.form("change_password_form"):
                    current_password = st.text_input("Current Password", type="password", key="current_pwd_change")
                    new_password = st.text_input("New Password", type="password", 
                                              help="At least 8 characters with uppercase, lowercase, number, and special character")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    
                    submit = st.form_submit_button("Change Password")
                
                if submit:
                    if not current_password or not new_password or not confirm_password:
                        show_error("Please fill in all fields.")
                        return
                    
                    # Verify current password
                    if not verify_password(user.password, current_password, user.salt):
                        show_error("Current password is incorrect.")
                        return
                    
                    # Validate new password
                    is_strong, message = validate_password_strength(new_password)
                    if not is_strong:
                        show_error(message)
                        return
                    
                    # Check if passwords match
                    if new_password != confirm_password:
                        show_error("New passwords do not match.")
                        return
                    
                    try:
                        # Update password
                        hashed_password, salt = hash_password(new_password)
                        
                        user.password = hashed_password
                        user.salt = salt
                        user.updated_at = datetime.utcnow()
                        
                        db.commit()
                        
                        show_success("Password changed successfully!")
                    
                    except Exception as e:
                        logger.error(f"Error changing password: {str(e)}")
                        show_error(f"Error changing password: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error displaying profile: {str(e)}")
            show_error(f"Error: {str(e)}")

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    st.title("My Profile")
    show_profile() 