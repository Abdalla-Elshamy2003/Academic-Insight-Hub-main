import streamlit as st
from analysis_display import display_analysis_results

# Sample analysis data provided by the user
sample_analysis = {
    "difficulty": 4,
    "estimated_time": 0.5,
    "student_level": "Intermediate",
    "improvements": [
        "Add more specific options to the multiple-choice question to avoid ambiguity.",
        "Consider adding a brief explanation or context about neural networks to help students understand the relevance of activation functions.",
        "Use more precise language in the question to avoid confusion, e.g., 'What is the primary purpose of activation functions in artificial neural networks?'"
    ],
    "tags": [
        "neural networks",
        "activation functions",
        "machine learning",
        "artificial intelligence"
    ]
}

# Set up the Streamlit page
st.title("Analysis Display Demo")
st.write("This is a demonstration of the card-based layout for displaying question analysis results.")

# Display the analysis results using our custom function
display_analysis_results(sample_analysis)

# Instructions for running the demo
st.markdown("---")
st.markdown("### How to Run This Demo")
st.code("streamlit run test_analysis_display.py", language="bash")