# backend/app/models/database.py

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ReadinessLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class SkillCategory(str, enum.Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"

class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class LinkType(str, enum.Enum):
    GITHUB = "github"
    LINKEDIN = "linkedin"
    PORTFOLIO = "portfolio"
    WEBSITE = "website"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    location = Column(String)
    readiness_level = Column(Enum(ReadinessLevel), default=ReadinessLevel.BEGINNER)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    education = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")
    career_goals = relationship("CareerGoal", back_populates="user", uselist=False, cascade="all, delete-orphan")
    career_intent = relationship("CareerIntent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferred_locations = relationship("PreferredLocation", back_populates="user", cascade="all, delete-orphan")
    availability = relationship("Availability", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Education(Base):
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    institution = Column(String, nullable=False)
    degree = Column(String, nullable=False)
    major = Column(String)
    location = Column(String)
    start_date = Column(String)  # Format: "Jan 2020"
    end_date = Column(String)  # Format: "Dec 2024" or "Present"
    duration = Column(String)  # Full duration string
    grade = Column(String)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="education")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    skill = Column(String, nullable=False)
    category = Column(Enum(SkillCategory), default=SkillCategory.TECHNICAL)
    level = Column(Enum(SkillLevel), default=SkillLevel.INTERMEDIATE)
    verified = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="skills")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    tech_stack = Column(String)  # Comma-separated or JSON
    link = Column(String)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")

class Experience(Base):
    __tablename__ = "experience"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    duration = Column(String)
    description = Column(Text)  # responsibilities
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="experience")

class Link(Base):
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(LinkType), nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="links")

class CareerGoal(Base):
    __tablename__ = "career_goals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    target_roles = Column(JSON)  # List of target roles
    target_industry = Column(String)
    short_term_goal = Column(Text)
    long_term_goal = Column(Text)
    target_timeline = Column(String)  # e.g., "6 Months"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="career_goals")

class CareerIntent(Base):
    __tablename__ = "career_intent"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    intent_text = Column(Text, nullable=False)  # Vision statement / career essay
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="career_intent")

class PreferredLocation(Base):
    __tablename__ = "preferred_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    location = Column(String, nullable=False)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="preferred_locations")

class Availability(Base):
    __tablename__ = "availability"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    free_time = Column(String)  # e.g., "2-4 hours"
    study_days = Column(JSON)  # List of days: ["Mon", "Tue", "Wed"]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="availability")

# Resume Storage (for raw text)
class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    raw_text = Column(Text)
    file_name = Column(String)
    file_type = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)