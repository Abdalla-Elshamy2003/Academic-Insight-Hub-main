import streamlit as st

def display_analysis_results(analysis):
    """
    Display analysis results in a well-organized, visually appealing card-based layout.
    
    Args:
        analysis: Dictionary containing analysis results with keys:
                 difficulty, estimated_time, student_level, improvements, tags
    """
    # Create a container with a border and padding
    with st.container():
        # Add custom CSS for better styling
        st.markdown("""
        <style>
        .analysis-card {
            background-color: #f0f7ff;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #c9e3ff;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #3a86ff;
        }
        .metric-label {
            font-size: 15px;
            color: #4a5568;
            text-transform: uppercase;
            margin-top: 5px;
        }
        .tag-item {
            display: inline-block;
            background-color: #e2f0ff;
            border-radius: 20px;
            padding: 6px 12px;
            margin: 6px;
            font-size: 13px;
            color: #3a86ff;
            border: 1px solid #c9e3ff;
        }
        .section-header {
            color: #2d3748;
            border-bottom: 2px solid #e2f0ff;
            padding-bottom: 8px;
            margin-top: 20px;
            margin-bottom: 15px;
            font-weight: 600;
            font-size: 18px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main analysis card
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        
        # Title
        st.markdown('<h3 style="text-align: center; color: #333;">AI Analysis Results</h3>', unsafe_allow_html=True)
        
        # Metrics section - display in 3 columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{analysis.get("difficulty", 3.0)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Difficulty</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{analysis.get("estimated_time", 5)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Minutes</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{analysis.get("student_level", "Intermediate")}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Level</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Divider
        st.markdown('<hr style="margin: 20px 0;">', unsafe_allow_html=True)
        
        # Improvements section
        st.markdown('<div class="section-header">Suggested Improvements</div>', unsafe_allow_html=True)
        
        # Handle improvements as list or string
        improvements = analysis.get('improvements', [])
        if isinstance(improvements, list):
            for i, improvement in enumerate(improvements):
                st.markdown(f"- {improvement}")
        else:
            st.write(improvements)
        
        # Tags section
        st.markdown('<div class="section-header">Tags</div>', unsafe_allow_html=True)
        
        # Display tags as chips/badges
        tags_html = '<div style="margin-top: 10px;">'  
        tags = analysis.get('tags', [])
        
        if isinstance(tags, list):
            for tag in tags:
                tags_html += f'<span class="tag-item">{tag}</span>'
        else:
            # If tags is a string, split by commas
            tag_list = [tag.strip() for tag in str(tags).split(',')]
            for tag in tag_list:
                if tag:  # Only add non-empty tags
                    tags_html += f'<span class="tag-item">{tag}</span>'
                
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)
        
        # Close the card div
        st.markdown('</div>', unsafe_allow_html=True)