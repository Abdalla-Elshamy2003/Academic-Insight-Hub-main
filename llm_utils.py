import os
import logging
import json
from typing import Dict, Any, Optional, Tuple, List
from groq import Groq
import streamlit as st
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_groq_client() -> Groq:
    """Get Groq client using API key from .env file or Streamlit secrets."""
    try:
        # Try to get API key from environment variable first (from .env file)
        api_key = os.environ.get("GROQ_API_KEY")
        
        # Fall back to Streamlit secrets if not found in environment
        if not api_key:
            try:
                api_key = st.secrets["groq_api_key"]
            except:
                logger.warning("GROQ_API_KEY not found in Streamlit secrets, checking .env file")
        
        if not api_key:
            logger.error("GROQ_API_KEY not found in environment or Streamlit secrets")
            return None
            
        client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {str(e)}")
        return None

def analyze_question(
    question_content: str, 
    question_type: str, 
    course_title: str, 
    chapter_title: str, 
    ilos: str
) -> Tuple[Optional[float], Optional[str]]:
    """
    Analyze a question using Groq API with LLaMA 3 model to:
    1. Rate its difficulty on a scale of 1-5
    2. Suggest improvements based on the ILOs
    3. Evaluate and suggest appropriate estimated time
    4. Determine appropriate student level
    
    Args:
        question_content: The content of the question
        question_type: The type of question (Multiple Choice, Essay, etc.)
        course_title: The title of the course
        chapter_title: The title of the chapter
        ilos: The intended learning outcomes for the chapter
        
    Returns:
        Tuple containing (difficulty_rating, analysis_text)
    """
    # Get client for this request
    client = get_groq_client()
    if not client:
        logger.error("Groq client not initialized. Cannot analyze question.")
        return None, "Error: Groq client not initialized. Please check your API key configuration."
    
    try:
        # Construct the prompt
        system_prompt = "You are an educational expert that analyzes academic questions and provides feedback. Always respond in valid JSON format."
        
        user_prompt = f"""
        Analyze this academic question and provide feedback:
        
        COURSE: {course_title}
        CHAPTER: {chapter_title}
        QUESTION TYPE: {question_type}
        INTENDED LEARNING OUTCOMES (ILOs): {ilos}
        
        QUESTION: {question_content}
        
        Please analyze this question and provide:
        
        1. DIFFICULTY RATING: Rate the question's difficulty on a scale of 1.0 to 5.0 (where 1 is easiest and 5 is hardest). Consider the complexity, cognitive load, and alignment with the ILOs.
        
        2. ESTIMATED TIME: Carefully evaluate and suggest a precise time (in minutes) that students would need to answer this question. You must be extremely accurate with time estimation. Follow these specific guidelines by question type:

           For Multiple Choice Questions:
           - Basic recall MC questions: 30-60 seconds per option
           - Application/analysis MC questions: 1-2 minutes per option
           - Complex scenario-based MC questions: 2-3 minutes total plus 1 minute per option

           For True/False Questions:
           - Simple factual T/F: 30-45 seconds
           - Complex conceptual T/F: 1-2 minutes

           For Short Answer Questions:
           - Basic recall: 2-3 minutes
           - Application/analysis: 3-5 minutes
           - Problem-solving: 5-8 minutes depending on complexity

           For Essay Questions:
           - Brief response (paragraph): 5-8 minutes
           - Standard essay: 10-20 minutes
           - Complex analysis essay: 20-30 minutes

           For Calculation/Problem-Solving Questions:
           - Simple calculations: 1-2 minutes
           - Multi-step problems: 3-5 minutes per step
           - Complex applications: 10-15 minutes

           Additional factors to consider:
           - Reading time: 200-250 words per minute for question text
           - Cognitive complexity level (recall: fastest, create: slowest)
           - Number of distinct concepts that must be integrated
           - Time needed to review and check work (add 10-20% of total time)

           Calculate the time precisely and provide a whole number of minutes. Be realistic and consider the actual time students need, not the ideal time.
        
        3. STUDENT LEVEL: Indicate which level of student this question is most appropriate for (Beginner, Intermediate, or Advanced).
        
        4. IMPROVEMENT SUGGESTIONS: Provide specific suggestions to improve the question's quality, clarity, and alignment with the ILOs. Consider aspects like:
           - Clarity and precision of language
           - Alignment with stated learning outcomes
           - Cognitive level (knowledge, comprehension, application, analysis, etc.)
           - Potential ambiguities or issues
           - Suggestions for better wording or structure
           - Whether the estimated time is appropriate for the question's complexity
        
        Format your response as a JSON object with the following structure:
        {{"difficulty_rating": float, "estimated_time": int, "student_level": string, "improvement_suggestions": string}}
        
        IMPORTANT: Ensure your response is ONLY the JSON object, with no additional text before or after.
        """
        
        # Call the Groq API with LLaMA 3 model
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",  # Using LLaMA 3 model
            temperature=0.1,  # Lower temperature for more deterministic responses
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        
        # Extract and parse the response
        response_text = response.choices[0].message.content.strip()
        logger.info(f"Received response from Groq API: {response_text[:100]}...")
        
        # Try to extract JSON from the response
        try:
            # Clean the response text to ensure it's valid JSON
            # Remove any markdown code block markers
            response_text = re.sub(r'```json\s*|\s*```', '', response_text)
            # Remove any leading/trailing whitespace
            response_text = response_text.strip()
            
            # Parse the JSON
            result = json.loads(response_text)
            
            difficulty_rating = result.get("difficulty_rating")
            estimated_time = result.get("estimated_time")
            student_level = result.get("student_level")
            improvement_suggestions = result.get("improvement_suggestions")
            
            # Validate difficulty rating
            if difficulty_rating is not None:
                difficulty_rating = float(difficulty_rating)
                difficulty_rating = max(1.0, min(5.0, difficulty_rating))  # Ensure it's between 1 and 5
            else:
                logger.error("No difficulty rating found in response")
                return None, "Error: No difficulty rating provided in analysis"
            
            # Validate estimated time
            if estimated_time is not None:
                estimated_time = int(estimated_time)
                # Ensure time is reasonable (between 1 and 60 minutes)
                estimated_time = max(1, min(60, estimated_time))
            else:
                estimated_time = 5  # Default to 5 minutes if not provided
                
            # Validate student level
            if student_level is not None:
                # Normalize student level to one of the three categories
                student_level = student_level.lower()
                if "beginner" in student_level:
                    student_level = "Beginner"
                elif "advanced" in student_level:
                    student_level = "Advanced"
                else:
                    student_level = "Intermediate"
            else:
                student_level = "Intermediate"  # Default if not provided
            
            if not improvement_suggestions:
                improvement_suggestions = "No specific improvement suggestions provided."
            
            # Create a formatted analysis text that includes all the information
            analysis_text = f"""## Question Analysis

**Difficulty Rating:** {difficulty_rating}/5.0

**Estimated Time:** {estimated_time} minutes

**Appropriate Student Level:** {student_level}

### Improvement Suggestions:
{improvement_suggestions}
"""
            
            return difficulty_rating, analysis_text
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"Response text was: {response_text}")
            
            # Try to extract just the JSON part using regex
            try:
                json_match = re.search(r'\{[^{}]*\}', response_text)
                if json_match:
                    result = json.loads(json_match.group(0))
                    difficulty_rating = float(result.get("difficulty_rating", 3.0))
                    estimated_time = int(result.get("estimated_time", 5))
                    student_level = result.get("student_level", "Intermediate")
                    improvement_suggestions = result.get("improvement_suggestions", "No specific improvement suggestions provided.")
                    
                    # Create a formatted analysis text
                    analysis_text = f"""## Question Analysis

**Difficulty Rating:** {difficulty_rating}/5.0

**Estimated Time:** {estimated_time} minutes

**Appropriate Student Level:** {student_level}

### Improvement Suggestions:
{improvement_suggestions}
"""
                    
                    return difficulty_rating, analysis_text
            except Exception as nested_e:
                logger.error(f"Failed to extract JSON using regex: {nested_e}")
            
            # If all parsing attempts fail, return the raw response as improvement suggestions
            return 3.0, f"Analysis (raw): {response_text}"
        
    except Exception as e:
        logger.error(f"Error calling Groq API: {str(e)}")
        return None, f"Error calling Groq API: {str(e)}"

def generate_questions(
    course_title: str,
    chapter_title: str,
    chapter_summary: str,
    ilos: str,
    num_questions: int = 3,
    difficulty_level: str = "mixed",
    question_types: List[str] = ["Multiple Choice", "True/False", "Short Answer"],
    existing_questions: List[str] = [],
    model: str = "llama-3.1-8b-instant"  # Default to LLaMA, can also use DeepSeek models
) -> List[Dict]:
    """
    Generate questions for a chapter using Groq API with specified model
    
    Args:
        course_title: The title of the course
        chapter_title: The title of the chapter
        chapter_summary: The summary of the chapter
        ilos: The intended learning outcomes for the chapter
        num_questions: Number of questions to generate
        difficulty_level: Difficulty level (easy, medium, hard, mixed)
        question_types: List of question types to generate
        existing_questions: List of existing questions as examples
        model: The model to use (e.g., "llama-3.1-8b-instant" or "deepseek-coder-instruct-6.7b")
        
    Returns:
        List of dictionaries with generated questions
    """
    # Get client for this request
    client = get_groq_client()
    if not client:
        logger.error("Groq client not initialized. Cannot generate questions.")
        return []
    
    try:
        # Construct the prompt
        system_prompt = "You are an educational expert specialized in creating high-quality academic questions that assess understanding and critical thinking."
        
        # Format example questions if any
        examples_text = ""
        if existing_questions:
            examples_text = "Here are some example questions from this course:\n\n"
            for i, q in enumerate(existing_questions[:3]):  # Limit to 3 examples
                examples_text += f"Example {i+1}:\n{q}\n\n"
        
        user_prompt = f"""
        Create {num_questions} educational questions for:
        
        COURSE: {course_title}
        CHAPTER: {chapter_title}
        CHAPTER SUMMARY: {chapter_summary}
        INTENDED LEARNING OUTCOMES (ILOs): {ilos}
        
        {examples_text}
        
        GUIDELINES:
        1. Create {num_questions} unique questions with the following distribution:
           - Difficulty: {difficulty_level}
           - Question types: {', '.join(question_types)}
        
        2. Each question should:
           - Directly align with the ILOs
           - Be clearly worded and academically rigorous
           - Include the correct answer and a brief explanation
           - For multiple-choice questions, include 4 options with only one correct answer
        
        Format each question as a JSON object with the following structure:
        {{
            "question_content": "The full question text",
            "question_type": "Multiple Choice/True/False/Short Answer/Essay",
            "difficulty": float (1.0-5.0 where 1=easiest, 5=hardest),
            "estimated_time": int (minutes to complete),
            "student_level": "Beginner/Intermediate/Advanced",
            "tags": "comma-separated tags",
            "correct_answer": "The correct answer",
            "explanation": "Explanation of why this is correct",
            "options": ["A. option1", "B. option2", "C. option3", "D. option4"] (for multiple choice only)
        }}
        
        Return a JSON array of question objects. The output should be valid parseable JSON.
        """
        
        # Call the Groq API with specified model
        logger.info(f"Using model: {model} to generate questions")
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=False
        )
        
        # Extract and parse the response
        response_text = response.choices[0].message.content
        logger.info(f"Received question generation response from Groq API using {model}")
        
        # Try to extract JSON from the response
        try:
            # Look for JSON pattern in the response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                questions = json.loads(json_str)
                
                # Validate and clean up questions
                validated_questions = []
                for q in questions:
                    # Ensure all required fields are present
                    if not all(k in q for k in ["question_content", "question_type", "difficulty", "correct_answer"]):
                        continue
                    
                    # Ensure difficulty is in range
                    q["difficulty"] = max(1.0, min(5.0, float(q["difficulty"])))
                    
                    # Ensure estimated_time is an integer
                    if "estimated_time" in q:
                        q["estimated_time"] = int(q["estimated_time"])
                    else:
                        q["estimated_time"] = 5  # Default
                    
                    # Set default student_level if not present
                    if "student_level" not in q:
                        q["student_level"] = "Intermediate"
                    
                    validated_questions.append(q)
                
                return validated_questions
            else:
                logger.error("Could not find JSON array in LLM response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            return []
        
    except Exception as e:
        logger.error(f"Error calling Groq API to generate questions: {str(e)}")
        return []