from database import get_db
import logging
import sqlalchemy as sa
from sqlalchemy import Column, Integer, ForeignKey

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_created_by_column():
    """Add created_by column to questions table"""
    logger.info("Adding created_by column to questions table...")
    
    try:
        # Get database connection
        db = next(get_db())
        
        # Check if created_by column exists
        inspector = sa.inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('questions')]
        
        if 'created_by' not in columns:
            logger.info("'created_by' column does not exist, adding it now...")
            
            # Add created_by column
            with db.bind.connect() as conn:
                conn.execute(sa.text(
                    "ALTER TABLE questions ADD COLUMN created_by INTEGER REFERENCES users(id)"
                ))
                conn.commit()
                
            logger.info("'created_by' column added successfully")
        else:
            logger.info("'created_by' column already exists")
            
    except Exception as e:
        logger.error(f"Error adding created_by column: {str(e)}")
        raise

if __name__ == "__main__":
    add_created_by_column()