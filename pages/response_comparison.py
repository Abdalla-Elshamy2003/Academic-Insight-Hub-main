import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_db
from models import Question, Chapter, Course
import logging
from analysis_display import display_analysis_results
from llm_utils import analyze_question

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_response_comparison():
    """Display a dashboard comparing professor evaluations with model responses."""
    st.markdown("### Professor vs AI Model Response Comparison")
    
    # Create a container with custom styling for the dashboard
    st.markdown("""
    <style>
    .dashboard-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        height: 100%;
    }
    .metric-card.easy {
        border-left: 5px solid #28a745;
    }
    .metric-card.medium {
        border-left: 5px solid #ffc107;
    }
    .metric-card.hard {
        border-left: 5px solid #dc3545;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #6c757d;
    }
    .comparison-header {
        background-color: #e9ecef;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get database connection
    db = next(get_db())
    
    # Get all courses for filtering
    courses = db.query(Course).all()
    course_options = [(c.id, c.title) for c in courses]
    
    # Add an "All Courses" option
    course_options.insert(0, (0, "All Courses"))
    
    # Course filter
    selected_course = st.selectbox(
        "Select Course",
        options=course_options,
        format_func=lambda x: x[1]
    )
    
    # Get questions based on course filter
    if selected_course[0] == 0:  # All Courses
        questions = db.query(Question).join(Chapter).join(Course).all()
    else:
        questions = db.query(Question).join(Chapter).join(Course).filter(Course.id == selected_course[0]).all()
    
    if not questions:
        st.info("No questions available for analysis. Please add questions first.")
        return
    
    # Select a question for detailed comparison
    question_options = [(q.id, f"{q.content[:50]}...") for q in questions]
    selected_question_id = st.selectbox(
        "Select a question for detailed comparison",
        options=question_options,
        format_func=lambda x: x[1]
    )[0]
    
    # Get the selected question
    selected_question = db.query(Question).filter(Question.id == selected_question_id).first()
    
    if selected_question:
        # Get chapter and course information
        chapter = db.query(Chapter).filter(Chapter.id == selected_question.chapter_id).first()
        course = db.query(Course).filter(Course.id == chapter.course_id).first()
        
        # Display the question content
        st.markdown("<div class='comparison-header'>Question Content</div>", unsafe_allow_html=True)
        st.markdown(f"**{selected_question.content}**")
        
        # Create two columns for professor vs AI comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='comparison-header'>Professor Evaluation</div>", unsafe_allow_html=True)
            
            # Determine difficulty category for styling
            difficulty_class = "easy"
            if selected_question.difficulty > 2.5 and selected_question.difficulty <= 3.5:
                difficulty_class = "medium"
            elif selected_question.difficulty > 3.5:
                difficulty_class = "hard"
            
            # Display professor metrics in cards
            st.markdown(f"<div class='metric-card {difficulty_class}'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-label'>Difficulty Rating</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{selected_question.difficulty}/5.0</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-label'>Estimated Time</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{selected_question.estimated_time} minutes</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-label'>Student Level</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{selected_question.student_level}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='comparison-header'>AI Model Evaluation</div>", unsafe_allow_html=True)
            
            # Get AI analysis for the question
            with st.spinner("Analyzing question with AI model..."):
                try:
                    # Get chapter ILOs
                    ilos = chapter.ilos if chapter.ilos else "Not specified"
                    
                    # Call the analyze_question function
                    difficulty_rating, analysis_text = analyze_question(
                        question_content=selected_question.content,
                        question_type=selected_question.question_type,
                        course_title=course.title,
                        chapter_title=chapter.title,
                        ilos=ilos
                    )
                    
                    # Extract estimated time and student level from analysis text
                    import re
                    estimated_time_match = re.search(r'Estimated Time:\*\* (\d+)', analysis_text)
                    student_level_match = re.search(r'Student Level:\*\* (\w+)', analysis_text)
                    
                    ai_estimated_time = int(estimated_time_match.group(1)) if estimated_time_match else 5
                    ai_student_level = student_level_match.group(1) if student_level_match else "Intermediate"
                    
                    # Determine AI difficulty category for styling
                    ai_difficulty_class = "easy"
                    if difficulty_rating > 2.5 and difficulty_rating <= 3.5:
                        ai_difficulty_class = "medium"
                    elif difficulty_rating > 3.5:
                        ai_difficulty_class = "hard"
                    
                    # Display AI metrics in cards
                    st.markdown(f"<div class='metric-card {ai_difficulty_class}'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='metric-label'>Difficulty Rating</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='metric-value'>{difficulty_rating}/5.0</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='metric-label'>Estimated Time</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='metric-value'>{ai_estimated_time} minutes</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='metric-label'>Student Level</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='metric-value'>{ai_student_level}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error analyzing question: {str(e)}")
                    logger.error(f"Error analyzing question: {str(e)}")
        
        # Comparison charts section
        st.markdown("<div class='comparison-header'>Comparison Analysis</div>", unsafe_allow_html=True)
        
        # Create comparison metrics
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            try:
                # Calculate difficulty difference
                diff_percentage = ((difficulty_rating - selected_question.difficulty) / selected_question.difficulty) * 100
                diff_text = "higher" if diff_percentage > 0 else "lower"
                
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-label'>Difficulty Difference</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>{abs(diff_percentage):.1f}% {diff_text}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            except:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-label'>Difficulty Difference</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>N/A</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with metrics_col2:
            try:
                # Calculate time difference
                time_diff = ai_estimated_time - selected_question.estimated_time
                time_diff_text = "longer" if time_diff > 0 else "shorter"
                
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-label'>Time Estimate Difference</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>{abs(time_diff)} min {time_diff_text}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            except:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-label'>Time Estimate Difference</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>N/A</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with metrics_col3:
            try:
                # Level agreement
                level_match = ai_student_level.lower() == selected_question.student_level.lower()
                level_text = "Match" if level_match else "Mismatch"
                level_color = "#28a745" if level_match else "#dc3545"
                
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-label'>Student Level</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value' style='color: {level_color};'>{level_text}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            except:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-label'>Student Level</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>N/A</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Create comparison charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Difficulty comparison chart
            try:
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=['Professor', 'AI Model'],
                    y=[selected_question.difficulty, difficulty_rating],
                    marker_color=['#4e73df', '#36b9cc'],
                    text=[f"{selected_question.difficulty}/5.0", f"{difficulty_rating}/5.0"],
                    textposition='auto'
                ))
                
                fig.update_layout(
                    title="Difficulty Rating Comparison",
                    yaxis=dict(title="Difficulty (1-5)", range=[0, 5.5]),
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("Could not generate difficulty comparison chart.")
        
        with chart_col2:
            # Time estimate comparison chart
            try:
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=['Professor', 'AI Model'],
                    y=[selected_question.estimated_time, ai_estimated_time],
                    marker_color=['#4e73df', '#36b9cc'],
                    text=[f"{selected_question.estimated_time} min", f"{ai_estimated_time} min"],
                    textposition='auto'
                ))
                
                fig.update_layout(
                    title="Time Estimate Comparison",
                    yaxis=dict(title="Time (minutes)"),
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("Could not generate time estimate comparison chart.")
        
        # Display AI analysis text
        st.markdown("<div class='comparison-header'>AI Analysis Details</div>", unsafe_allow_html=True)
        st.markdown(analysis_text)

# Main function for the page
def main():
    """Main function to display the response comparison page."""
    st.title("Professor vs AI Response Comparison")
    show_response_comparison()

# For backward compatibility - this will be called when the file is run directly
if __name__ == "__main__":
    main()