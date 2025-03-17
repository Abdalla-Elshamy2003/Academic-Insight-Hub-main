from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hashed password
    salt = Column(String(255), nullable=False)  # Salt for password hashing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Add these relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("StudentProgress", back_populates="user", cascade="all, delete-orphan")
    discussions = relationship("Discussion", back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    permissions = Column(Text)  # JSON string of permissions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    title = Column(String(100), nullable=False)
    summary = Column(Text)
    ilos = Column(Text)  # Intended Learning Outcomes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    course = relationship("Course", back_populates="chapters")
    questions = relationship("Question", back_populates="chapter", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    difficulty = Column(Float)  # 1-5 scale
    estimated_time = Column(Integer)  # in minutes
    student_level = Column(String(20))  # Beginner, Intermediate, Advanced
    tags = Column(String(255))  # Comma-separated tags
    question_type = Column(String(50))  # Multiple Choice, Essay, etc.
    correct_answer = Column(Text)
    explanation = Column(Text)  # Explanation for the correct answer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))  # Track who created the question
    
    chapter = relationship("Chapter", back_populates="questions")
    feedback = relationship("StudentFeedback", back_populates="question", cascade="all, delete-orphan")
    student_progress = relationship("StudentProgress", back_populates="question", cascade="all, delete-orphan")
    discussions = relationship("Discussion", back_populates="question", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

class StudentFeedback(Base):
    __tablename__ = "student_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    difficulty_rating = Column(Float)
    student_gpa = Column(Float)
    attendance_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    question = relationship("Question", back_populates="feedback")
    user = relationship("User", foreign_keys=[user_id])

class StudentProgress(Base):
    __tablename__ = "student_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    attempts = Column(Integer, default=0)
    correct = Column(Boolean, default=False)
    last_attempt_date = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="progress")
    question = relationship("Question", back_populates="student_progress")

class Discussion(Base):
    __tablename__ = "discussions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    parent_id = Column(Integer, ForeignKey("discussions.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    question = relationship("Question", back_populates="discussions")
    user = relationship("User", back_populates="discussions")
    replies = relationship("Discussion", 
                          backref=backref("parent", remote_side=[id]),
                          cascade="all, delete-orphan")

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    created_by = Column(Integer, ForeignKey("users.id"))
    time_limit = Column(Integer)  # in minutes
    total_points = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    course = relationship("Course")
    creator = relationship("User", foreign_keys=[created_by])
    exam_questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    
class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    order = Column(Integer, nullable=False)  # Order in which questions appear
    points = Column(Integer, nullable=False, default=1)  # Points for this question
    created_at = Column(DateTime, default=datetime.utcnow)
    
    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question")
