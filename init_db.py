from database import get_db, init_db
from models import Role, User, UserRole, Base, Exam, ExamQuestion
import json
import logging
from utils import hash_password
from datetime import datetime
import sqlalchemy as sa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_roles():
    """Initialize roles in the database"""
    db = next(get_db())
    
    # Define roles and their permissions
    roles = [
        {
            "name": "professor",
            "permissions": json.dumps({
                "create_course": True,
                "edit_course": True,
                "delete_course": True,
                "create_chapter": True,
                "edit_chapter": True,
                "delete_chapter": True,
                "create_question": True,
                "edit_question": True,
                "delete_question": True,
                "view_analytics": True,
                "view_feedback": True,
                "export_data": True,
                "import_data": True
            })
        },
        {
            "name": "student",
            "permissions": json.dumps({
                "view_course": True,
                "view_chapter": True,
                "view_question": True,
                "submit_feedback": True,
                "attempt_question": True,
                "view_progress": True,
                "participate_discussion": True
            })
        },
        {
            "name": "admin",
            "permissions": json.dumps({
                "create_course": True,
                "edit_course": True,
                "delete_course": True,
                "create_chapter": True,
                "edit_chapter": True,
                "delete_chapter": True,
                "create_question": True,
                "edit_question": True,
                "delete_question": True,
                "view_analytics": True,
                "view_feedback": True,
                "export_data": True,
                "import_data": True,
                "manage_users": True,
                "manage_roles": True,
                "system_settings": True
            })
        },
        {
            "name": "teaching_assistant",
            "permissions": json.dumps({
                "view_course": True,
                "view_chapter": True,
                "view_question": True,
                "create_question": True,
                "edit_question": True,
                "view_analytics": True,
                "view_feedback": True,
                "grade_submissions": True,
                "participate_discussion": True
            })
        }
    ]
    
    # Add roles to database
    for role_data in roles:
        existing_role = db.query(Role).filter_by(name=role_data["name"]).first()
        
        if existing_role:
            logger.info(f"Role '{role_data['name']}' already exists, updating permissions")
            existing_role.permissions = role_data["permissions"]
            existing_role.updated_at = datetime.utcnow()
        else:
            logger.info(f"Creating role '{role_data['name']}'")
            role = Role(
                name=role_data["name"],
                permissions=role_data["permissions"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(role)
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating/updating role '{role_data['name']}': {str(e)}")

def create_admin_user():
    """Create an admin user if it doesn't exist"""
    db = next(get_db())
    
    # Check if admin user exists
    admin_user = db.query(User).filter_by(username="admin").first()
    
    if not admin_user:
        # Get admin role
        admin_role = db.query(Role).filter_by(name="admin").first()
        
        if not admin_role:
            logger.error("Admin role not found. Please run init_roles() first.")
            return
        
        # Create admin user
        hashed_password, salt = hash_password("Admin@123")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password=hashed_password,
            salt=salt,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            db.add(admin_user)
            db.flush()  # Get the user ID
            
            # Assign admin role
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id,
                created_at=datetime.utcnow()
            )
            db.add(user_role)
            db.commit()
            
            logger.info("Admin user created successfully")
            logger.info("Username: admin")
            logger.info("Password: Admin@123")
            logger.info("Please change this password after first login")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
    else:
        logger.info("Admin user already exists")

def run_migrations():
    """Run database migrations to update schema"""
    logger.info("Running database migrations...")
    
    try:
        # Get database connection
        db = next(get_db())
        
        # Check if exams table exists
        inspector = sa.inspect(db.bind)
        has_exams_table = inspector.has_table("exams")
        
        if not has_exams_table:
            logger.info("Creating 'exams' and 'exam_questions' tables...")
            
            # Create exams table
            Base.metadata.tables["exams"].create(db.bind)
            logger.info("'exams' table created successfully")
            
            # Create exam_questions table
            Base.metadata.tables["exam_questions"].create(db.bind)
            logger.info("'exam_questions' table created successfully")
            
            # Update professor and admin roles to add exam management permissions
            professor_role = db.query(Role).filter_by(name="professor").first()
            admin_role = db.query(Role).filter_by(name="admin").first()
            
            if professor_role:
                # Update professor permissions
                permissions = json.loads(professor_role.permissions)
                permissions.update({
                    "create_exam": True,
                    "edit_exam": True,
                    "delete_exam": True,
                    "ai_question_generator": True
                })
                professor_role.permissions = json.dumps(permissions)
                logger.info("Updated professor role permissions to include exam management")
            
            if admin_role:
                # Update admin permissions
                permissions = json.loads(admin_role.permissions)
                permissions.update({
                    "create_exam": True,
                    "edit_exam": True,
                    "delete_exam": True,
                    "ai_question_generator": True
                })
                admin_role.permissions = json.dumps(permissions)
                logger.info("Updated admin role permissions to include exam management")
            
            db.commit()
            logger.info("Role permissions updated successfully")
        
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        # Continue with other init tasks even if migrations fail

# Main initialization function
def initialize_database():
    """Initialize database with default data"""
    try:
        # Run migrations
        run_migrations()
        
        # Initialize roles
        init_roles()
        
        # Initialize default admin user
        create_admin_user()
        
        logger.info("Database initialized successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_database()