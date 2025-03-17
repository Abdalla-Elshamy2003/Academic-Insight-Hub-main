from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
import os
from sqlalchemy.pool import QueuePool
import logging
import streamlit as st
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database engine using Streamlit secrets
engine = create_engine(st.secrets["database_url"])

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
ScopedSession = scoped_session(SessionLocal)

# Create Base class for declarative models
Base = declarative_base()

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_context():
    """
    Get a database session as a context manager.
    Usage:
        with get_db_context() as db:
            # use db here
    """
    db = ScopedSession()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and default data."""
    from models import Base
    
    # Create tables
    if not st.session_state.get("db_initialized", False):
        logger.info("Creating database tables if they don't exist...")
        Base.metadata.create_all(bind=engine)
        st.session_state["db_initialized"] = True
        
        # Import and run database initialization
        try:
            import init_db
            init_db.initialize_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    else:
        logger.debug("Database already initialized")
