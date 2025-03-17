# Academic Insight Hub

A comprehensive educational platform for course management, question banks, and student analytics.

## Features

- **User Management**: Role-based access control with professors, students, teaching assistants, and administrators
- **Course Management**: Create, edit, and organize educational courses
- **Chapter Organization**: Structure courses into logical chapters with learning outcomes
- **Question Bank**: Create, categorize, and manage questions of various types
- **Student Feedback**: Collect and analyze student feedback on questions
- **Analytics Dashboard**: Visualize student performance and question statistics
- **Discussion Forums**: Enable discussions around specific questions
- **Student Progress Tracking**: Monitor student performance and progress
- **Import/Export**: Import and export questions in CSV format
- **AI-Powered Question Analysis**: Analyze questions using LLM to rate difficulty and suggest improvements based on learning outcomes
- **AI Question Generator**: Generate high-quality questions automatically using Groq or DeepSeek models
- **Exam Builder**: Create exams by selecting questions from the database or auto-generating them

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AcademicInsightHub.git
   cd AcademicInsightHub
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file to add your Groq API key for the AI-powered question analysis feature.

5. Initialize the database:
   ```
   python init_db.py
   ```

6. Run the application:
   ```
   streamlit run main.py
   ```

## Initial Login

After initializing the database, you can log in with the following credentials:

- **Admin User**:
  - Username: admin
  - Password: Admin@123

## Project Structure

- `main.py`: Application entry point
- `models.py`: Database models
- `database.py`: Database connection and utilities
- `utils.py`: Utility functions
- `llm_utils.py`: LLM integration utilities
- `init_db.py`: Database initialization script
- `pages/`: Streamlit pages
  - `add.py`: Add courses, chapters, and questions
  - `auth.py`: Authentication (login/register)
  - `view.py`: View courses, chapters, and questions
  - `edit.py`: Edit courses, chapters, and questions
  - `Analytics_Dashboard.py`: Analytics and statistics
  - `student_feedback.py`: Student feedback collection
  - `question_bank.py`: Question bank management
  - `discussion.py`: Question discussions
  - `my_progress.py`: Student progress tracking
  - `question_attempt.py`: Question attempt interface
  - `user_management.py`: User and role management
  - `question_analysis.py`: AI-powered question analysis
  - `question_generator.py`: AI-powered question generation
  - `exam_builder.py`: Create and manage exams

## User Roles

- **Administrator**: Full access to all features, including user management
- **Professor**: Create and manage courses, chapters, questions, and view analytics
- **Teaching Assistant**: Create and manage questions, view analytics
- **Student**: View courses, attempt questions, provide feedback, track progress

## Security Features

- Secure password hashing with PBKDF2
- Input validation for all user inputs
- Role-based access control
- Session management
- Database connection pooling

## Development

### Requirements

- Python 3.8+
- SQLite (default) or PostgreSQL

### Testing

```
pytest
```

### Code Formatting

```
black .
flake8
isort .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Streamlit for the web framework
- SQLAlchemy for the ORM
- Plotly for data visualization 

## AI-Powered Features

The application includes several AI-powered features:

### Question Analysis

Uses the Groq API with the LLaMA-3 model to:

1. Rate the difficulty of questions on a scale of 1-5
2. Suggest improvements to questions based on the course's Intended Learning Outcomes (ILOs)
3. Help professors create better-aligned questions

### AI Question Generator

Automatically generates high-quality educational questions based on chapter content and learning outcomes:

1. Supports multiple LLM models through Groq, including:
   - LLaMA-3 (8B and 70B variants)
   - DeepSeek (6.7B)
   - Mixtral (8x7B)
2. Generate questions of various types (Multiple Choice, True/False, Short Answer, Essay)
3. Customizable difficulty levels and question counts
4. Generated questions can be saved directly to the database

### Exam Builder

Create comprehensive exams from existing questions:

1. Filter questions by course, chapter, difficulty, and type
2. Auto-generate exams with specified question counts and parameters
3. Customize point values for each question
4. Reorder questions to structure the exam
5. Save exams for later use

To use these AI features:

1. Obtain an API key from Groq: [https://console.groq.com/](https://console.groq.com/)
2. Add your API key to the `.env` file
3. Navigate to the respective pages in the application

These features are available to users with Professor or Admin roles. 