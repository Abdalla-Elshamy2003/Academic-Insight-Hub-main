import streamlit as st
from database import get_db
from models import User, Role, UserRole
from sqlalchemy import or_
from utils import show_success, show_error, show_warning, show_info, rerun, paginate_data
from utils import hash_password, validate_email, validate_username, validate_password_strength
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_user_management():
    """Display the user management page."""
    st.markdown("## User Management")
    
    # Check if user is admin
    if "user" not in st.session_state or st.session_state.user.get("role", "").lower() != "admin":
        st.error("You do not have permission to access this page.")
        return
    
    # Create tabs for different user management functions
    tab1, tab2, tab3 = st.tabs(["View Users", "Add User", "Manage Roles"])
    
    with tab1:
        show_users_tab()
    
    with tab2:
        add_user_tab()
    
    with tab3:
        manage_roles_tab()

def show_users_tab():
    """Tab for viewing and managing users."""
    st.markdown("### User List")
    
    try:
        db = next(get_db())
        
        # Search functionality
        search_term = st.text_input("Search users by username or email", key="user_search")
        
        # Get all users with their roles
        users_with_roles = db.query(User, Role).join(
            UserRole, User.id == UserRole.user_id
        ).join(
            Role, UserRole.role_id == Role.id
        ).all()
        
        # Filter users if search term is provided
        if search_term:
            users = [user for user, role in users_with_roles 
                    if (user.username and search_term.lower() in user.username.lower()) or 
                    (user.email and search_term.lower() in user.email.lower())]
        else:
            users = [user for user, _ in users_with_roles]
        
        # Paginate users
        paginated_users = paginate_data(users, items_per_page=10, key="users_management")
        
        # Display users in a table
        if paginated_users:
            for user in paginated_users:
                # Get user role
                user_role = db.query(UserRole).filter_by(user_id=user.id).first()
                role = db.query(Role).get(user_role.role_id) if user_role else None
                
                with st.expander(f"{user.username} ({role.name if role else 'No Role'})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Username:** {user.username}")
                        st.write(f"**Email:** {user.email}")
                        st.write(f"**Role:** {role.name if role else 'No Role'}")
                        st.write(f"**Created:** {user.created_at.strftime('%Y-%m-%d')}")
                        st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
                    
                    with col2:
                        # Edit user role
                        roles = db.query(Role).all()
                        current_role_id = role.id if role else None
                        
                        new_role = st.selectbox(
                            "Change Role",
                            options=[(r.id, r.name) for r in roles],
                            format_func=lambda x: x[1],
                            index=[i for i, r in enumerate(roles) if r.id == current_role_id][0] if current_role_id else 0,
                            key=f"role_select_{user.id}"
                        )
                        
                        if st.button("Update Role", key=f"update_role_{user.id}"):
                            try:
                                # Update user role
                                if user_role:
                                    user_role.role_id = new_role[0]
                                else:
                                    user_role = UserRole(
                                        user_id=user.id,
                                        role_id=new_role[0],
                                        created_at=datetime.utcnow()
                                    )
                                    db.add(user_role)
                                
                                db.commit()
                                show_success(f"Role updated for {user.username}")
                                st.rerun()
                            except Exception as e:
                                logger.error(f"Error updating role: {str(e)}")
                                show_error(f"Error updating role: {str(e)}")
                        
                        # Delete user button
                        if st.button("Delete User", key=f"delete_user_{user.id}"):
                            st.session_state[f"confirm_delete_{user.id}"] = True
                        
                        # Confirmation dialog
                        if st.session_state.get(f"confirm_delete_{user.id}", False):
                            st.warning(f"Are you sure you want to delete user {user.username}? This action cannot be undone.")
                            
                            confirm_col1, confirm_col2 = st.columns(2)
                            with confirm_col1:
                                if st.button("Yes, Delete", key=f"confirm_yes_{user.id}"):
                                    try:
                                        db.delete(user)
                                        db.commit()
                                        show_success(f"User {user.username} deleted successfully")
                                        st.session_state[f"confirm_delete_{user.id}"] = False
                                        st.rerun()
                                    except Exception as e:
                                        logger.error(f"Error deleting user: {str(e)}")
                                        show_error(f"Error deleting user: {str(e)}")
                            
                            with confirm_col2:
                                if st.button("Cancel", key=f"confirm_no_{user.id}"):
                                    st.session_state[f"confirm_delete_{user.id}"] = False
                                    st.rerun()
        else:
            st.info("No users found matching your search criteria.")
    
    except Exception as e:
        logger.error(f"Error displaying users: {str(e)}")
        show_error(f"Error: {str(e)}")

def add_user_tab():
    """Tab for adding new users."""
    st.markdown("### Add New User")
    
    try:
        db = next(get_db())
        roles = db.query(Role).all()
        
        with st.form("add_user_form"):
            username = st.text_input("Username (3-50 characters, alphanumeric)")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password", 
                                   help="At least 8 characters with uppercase, lowercase, number, and special character")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            role = st.selectbox(
                "Role",
                options=[(r.id, r.name) for r in roles],
                format_func=lambda x: x[1]
            )
            
            submit = st.form_submit_button("Add User")
        
        if submit:
            # Validate inputs
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
                    # Check if username or email already exists
                    existing_user = db.query(User).filter(
                        or_(User.username == username, User.email == email)
                    ).first()
                    
                    if existing_user:
                        show_error("Username or email already exists")
                    else:
                        # Create new user
                        hashed_password, salt = hash_password(password)
                        new_user = User(
                            username=username,
                            email=email,
                            password=hashed_password,
                            salt=salt,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        db.add(new_user)
                        db.flush()  # Get the user ID
                        
                        # Assign role
                        user_role = UserRole(
                            user_id=new_user.id,
                            role_id=role[0],
                            created_at=datetime.utcnow()
                        )
                        db.add(user_role)
                        
                        db.commit()
                        show_success(f"User {username} added successfully")
                        st.rerun()
                
                except Exception as e:
                    logger.error(f"Error adding user: {str(e)}")
                    show_error(f"Error adding user: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in add_user_tab: {str(e)}")
        show_error(f"Error: {str(e)}")

def manage_roles_tab():
    """Tab for managing roles and permissions."""
    st.markdown("### Manage Roles")
    
    try:
        db = next(get_db())
        roles = db.query(Role).all()
        
        # Display existing roles
        st.markdown("#### Existing Roles")
        
        for role in roles:
            with st.expander(f"{role.name}"):
                # Display role details
                st.write(f"**Role ID:** {role.id}")
                st.write(f"**Created:** {role.created_at.strftime('%Y-%m-%d')}")
                
                # Display permissions
                st.write("**Permissions:**")
                try:
                    permissions = json.loads(role.permissions)
                    for perm, value in permissions.items():
                        st.write(f"- {perm}: {'Yes' if value else 'No'}")
                except:
                    st.write("No permissions defined or invalid format")
                
                # Edit permissions
                st.markdown("**Edit Permissions:**")
                
                try:
                    current_permissions = json.loads(role.permissions)
                except:
                    current_permissions = {}
                
                # Define available permissions
                available_permissions = [
                    "can_add_course", "can_edit_course", "can_delete_course",
                    "can_add_chapter", "can_edit_chapter", "can_delete_chapter",
                    "can_add_question", "can_edit_question", "can_delete_question",
                    "can_view_analytics", "can_manage_users"
                ]
                
                # Create checkboxes for each permission
                new_permissions = {}
                for perm in available_permissions:
                    new_permissions[perm] = st.checkbox(
                        perm.replace("_", " ").title(),
                        value=current_permissions.get(perm, False),
                        key=f"{role.id}_{perm}"
                    )
                
                # Update button
                if st.button("Update Permissions", key=f"update_perm_{role.id}"):
                    try:
                        role.permissions = json.dumps(new_permissions)
                        role.updated_at = datetime.utcnow()
                        db.commit()
                        show_success(f"Permissions updated for role {role.name}")
                    except Exception as e:
                        logger.error(f"Error updating permissions: {str(e)}")
                        show_error(f"Error updating permissions: {str(e)}")
        
        # Add new role
        st.markdown("#### Add New Role")
        
        with st.form("add_role_form"):
            role_name = st.text_input("Role Name")
            
            # Define permissions for new role
            st.write("**Permissions:**")
            new_role_permissions = {}
            
            for perm in available_permissions:
                new_role_permissions[perm] = st.checkbox(
                    perm.replace("_", " ").title(),
                    key=f"new_role_{perm}"
                )
            
            submit = st.form_submit_button("Add Role")
        
        if submit and role_name:
            try:
                # Check if role already exists
                existing_role = db.query(Role).filter_by(name=role_name.lower()).first()
                
                if existing_role:
                    show_error(f"Role '{role_name}' already exists")
                else:
                    # Create new role
                    new_role = Role(
                        name=role_name.lower(),
                        permissions=json.dumps(new_role_permissions),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(new_role)
                    db.commit()
                    show_success(f"Role '{role_name}' added successfully")
                    st.rerun()
            
            except Exception as e:
                logger.error(f"Error adding role: {str(e)}")
                show_error(f"Error adding role: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in manage_roles_tab: {str(e)}")
        show_error(f"Error: {str(e)}")

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    st.title("User Management")
    show_user_management() 