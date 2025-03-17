import streamlit as st
import plotly.express as px
import pandas as pd
import hashlib
import os
import re
import logging
from functools import wraps
import time
from typing import List, Dict, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# UI Helpers
def show_success(message: str) -> None:
    """Display a success message with consistent styling."""
    st.success(message)
    logger.info(f"Success: {message}")

def show_error(message: str) -> None:
    """Display an error message with consistent styling."""
    st.error(message)
    logger.error(f"Error: {message}")

def show_warning(message: str) -> None:
    """Display a warning message with consistent styling."""
    st.warning(message)
    logger.warning(f"Warning: {message}")

def show_info(message: str) -> None:
    """Display an info message with consistent styling."""
    st.info(message)
    logger.info(f"Info: {message}")

def confirm_action(action_name: str) -> bool:
    """Display a confirmation dialog for destructive actions."""
    return st.checkbox(f"Confirm {action_name}")

# Security Functions
def generate_salt() -> str:
    """Generate a random salt for password hashing."""
    return os.urandom(32).hex()

def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """
    Hash a password using PBKDF2 with SHA-256.
    Returns a tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = generate_salt()
    
    # Use a stronger hashing algorithm with more iterations
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100000,
        dklen=128
    )
    
    return key.hex(), salt

def verify_password(stored_password: str, provided_password: str, salt: str) -> bool:
    """Verify a password against its stored hash."""
    new_hash, _ = hash_password(provided_password, salt)
    return new_hash == stored_password

# Input Validation
def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_username(username: str) -> bool:
    """Validate username format (alphanumeric, 3-50 chars)."""
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return bool(re.match(pattern, username))

def validate_password_strength(password: str) -> tuple:
    """
    Validate password strength.
    Returns (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

# Performance Helpers
def cache_data(ttl_seconds=300):
    """
    Cache decorator for expensive operations.
    """
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            current_time = time.time()
            
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    return result
            
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result
        
        return wrapper
    
    return decorator

# Data Visualization
def create_difficulty_chart(data):
    """Create a histogram of question difficulty."""
    fig = px.histogram(
        data,
        x="difficulty",
        title="Question Difficulty Distribution",
        labels={"difficulty": "Difficulty Level", "count": "Number of Questions"},
        nbins=20
    )
    return fig

def create_gpa_correlation_chart(data):
    """Create a scatter plot of GPA vs perceived difficulty."""
    fig = px.scatter(
        data,
        x="student_gpa",
        y="difficulty_rating",
        title="GPA vs Perceived Difficulty",
        labels={
            "student_gpa": "Student GPA",
            "difficulty_rating": "Perceived Difficulty"
        }
    )
    return fig

def format_ilos(ilos_text):
    """Convert ILOs text to formatted list."""
    if not ilos_text:
        return []
    return [ilo.strip() for ilo in ilos_text.split('\n') if ilo.strip()]

# Reusable UI Components
def paginate_data(items: List[Any], items_per_page: int = 10, key: str = None) -> List[Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        items_per_page: Number of items per page
        key: Unique key for the pagination controls
        
    Returns:
        List of items for the current page
    """
    # Get total number of items
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # Get current page from session state
    page_key = f"pagination_{key}" if key else f"pagination_{id(items)}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    
    # Get items for current page
    page = st.session_state[page_key]
    start = (page - 1) * items_per_page
    end = min(start + items_per_page, total_items)
    
    # Get the items for the current page
    current_page_items = items[start:end]
    
    # Add pagination controls at the bottom
    if total_pages > 1:
        st.markdown("---")  # Add a separator
        cols = st.columns([2, 1, 2, 1, 2])
        
        # Previous page button
        if cols[0].button("← Previous", key=f"{page_key}_prev", disabled=(page <= 1)):
            st.session_state[page_key] = max(1, page - 1)
            st.rerun()
        
        # Page number display
        cols[2].markdown(f"<div style='text-align: center; margin-top: 5px;'>Page {page} of {total_pages}</div>", unsafe_allow_html=True)
        
        # Next page button
        if cols[4].button("Next →", key=f"{page_key}_next", disabled=(page >= total_pages)):
            st.session_state[page_key] = min(total_pages, page + 1)
            st.rerun()
    
    return current_page_items

def rerun():
    """Rerun the app using meta refresh."""
    st.markdown("<meta http-equiv='refresh' content='0'>", unsafe_allow_html=True)
    st.stop()
