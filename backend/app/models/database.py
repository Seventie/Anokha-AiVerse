# backend/app/models/database.py - COMPLETE FIXED VERSION

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Enum, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()

# ==================== ENUMS ====================

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

class InterviewType(str, enum.Enum):
    COMPANY_SPECIFIC = "company_specific"
    CUSTOM_TOPIC = "custom_topic"

class RoundType(str, enum.Enum):
    TECHNICAL = "technical"
    HR = "hr"
    COMMUNICATION = "communication"

class InterviewStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class RoundStatus(str, enum.Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"

class JobType(str, enum.Enum):
    FULLTIME = "fulltime"
    PARTTIME = "parttime"
    INTERNSHIP = "internship"
    CONTRACT = "contract"

class OpportunityStatus(str, enum.Enum):
    RECOMMENDED = "recommended"
    SAVED = "saved"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEWING = "interviewing"

class RoadmapPhase(str, enum.Enum):
    FOUNDATION = "foundation"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SPECIALIZATION = "specialization"

class TaskStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

# ✅ COLD EMAIL ENUMS
class EmailCampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class EmailStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    REPLIED = "replied"
    BOUNCED = "bounced"
    REJECTED = "rejected"

# ==================== USER MODEL ====================

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
    
    # Google OAuth
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)
    
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
    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("UserResume", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    cold_email_campaigns = relationship("ColdEmailCampaign", back_populates="user", cascade="all, delete-orphan")  # ✅ ADDED

# ==================== PROFILE MODELS ====================

class Education(Base):
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    institution = Column(String, nullable=False)
    degree = Column(String, nullable=False)
    major = Column(String)
    location = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    duration = Column(String)
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
    tech_stack = Column(String)
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
    description = Column(Text)
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
    target_roles = Column(JSON)
    target_industry = Column(String)
    short_term_goal = Column(Text)
    long_term_goal = Column(Text)
    target_timeline = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="career_goals")

class CareerIntent(Base):
    __tablename__ = "career_intent"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    intent_text = Column(Text, nullable=False)
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
    free_time = Column(String)
    study_days = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="availability")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    raw_text = Column(Text)
    file_name = Column(String)
    file_type = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

# ==================== INTERVIEW MODELS ====================

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    interview_type = Column(Enum(InterviewType), nullable=False)
    
    company_name = Column(String)
    job_description = Column(Text)
    custom_topics = Column(JSON)
    
    total_rounds = Column(Integer, default=1)
    completed_rounds = Column(Integer, default=0)
    current_round = Column(Integer, default=1)
    
    overall_score = Column(Float)
    pass_fail_status = Column(String)
    
    status = Column(Enum(InterviewStatus), default=InterviewStatus.NOT_STARTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    user = relationship("User", back_populates="interviews")
    rounds = relationship("InterviewRound", back_populates="interview", cascade="all, delete-orphan")
    recording = relationship("InterviewRecording", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    evaluation = relationship("InterviewEvaluation", back_populates="interview", uselist=False, cascade="all, delete-orphan")

class InterviewRound(Base):
    __tablename__ = "interview_rounds"
    
    id = Column(String, primary_key=True)
    interview_id = Column(String, ForeignKey("interviews.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    round_type = Column(Enum(RoundType), nullable=False)
    difficulty = Column(String, default="medium")
    
    status = Column(Enum(RoundStatus), default=RoundStatus.LOCKED)
    
    score = Column(Float)
    pass_threshold = Column(Float, default=70.0)
    pass_status = Column(Boolean)
    
    feedback_summary = Column(Text)
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    interview = relationship("Interview", back_populates="rounds")
    conversations = relationship("InterviewConversation", back_populates="round", cascade="all, delete-orphan")

class InterviewConversation(Base):
    __tablename__ = "interview_conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(String, ForeignKey("interviews.id"), nullable=False)
    round_id = Column(String, ForeignKey("interview_rounds.id"), nullable=False)
    
    speaker = Column(String, nullable=False)
    message_text = Column(Text, nullable=False)
    audio_url = Column(String)
    
    question_category = Column(String)
    expected_answer_points = Column(JSON)
    
    answer_score = Column(Float)
    sentiment_score = Column(Float)
    confidence_detected = Column(String)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    round = relationship("InterviewRound", back_populates="conversations")

class InterviewEvaluation(Base):
    __tablename__ = "interview_evaluations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(String, ForeignKey("interviews.id"), nullable=False, unique=True)
    
    technical_score = Column(Float)
    communication_score = Column(Float)
    problem_solving_score = Column(Float)
    confidence_score = Column(Float)
    overall_score = Column(Float)
    
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    recommendations = Column(JSON)
    
    suggested_topics = Column(JSON)
    next_interview_date = Column(DateTime)
    
    interview = relationship("Interview", back_populates="evaluation")

class InterviewRecording(Base):
    __tablename__ = "interview_recordings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(String, ForeignKey("interviews.id"), nullable=False, unique=True)
    
    video_url = Column(String)
    transcript_url = Column(String)
    transcript_text = Column(Text)
    
    recording_duration = Column(Integer)
    file_size_bytes = Column(BigInteger)
    video_format = Column(String)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    interview = relationship("Interview", back_populates="recording")

# ==================== RESUME PARSER MODEL ====================

class UserResume(Base):
    __tablename__ = "user_resumes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    parsed_data = Column(JSON)
    
    full_name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    
    technical_skills = Column(JSON)
    soft_skills = Column(JSON)
    
    last_jd_matched = Column(Text)
    match_score = Column(Float)
    missing_skills = Column(JSON)
    recommendations = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="resumes")

# ==================== OPPORTUNITIES MODULE ====================

class JobOpportunity(Base):
    __tablename__ = "job_opportunities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    job_type = Column(Enum(JobType), default=JobType.FULLTIME)
    is_remote = Column(Boolean, default=False)
    description = Column(Text)
    requirements = Column(JSON)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="INR")
    experience_level = Column(String(50), nullable=True)
    url = Column(String(500), unique=True)
    source = Column(String(50))
    posted_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Hackathon(Base):
    __tablename__ = "hackathons"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    organizer = Column(String(255))
    platform = Column(String(50))
    description = Column(Text)
    themes = Column(JSON)
    prize_pool = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    registration_deadline = Column(DateTime)
    mode = Column(String(20))
    location = Column(String(255))
    url = Column(String(500), unique=True)
    eligibility = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class UserJobMatch(Base):
    __tablename__ = "user_job_matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    job_id = Column(String, ForeignKey('job_opportunities.id'), nullable=False)
    match_score = Column(Float)
    matching_skills = Column(JSON)
    missing_skills = Column(JSON)
    status = Column(Enum(OpportunityStatus), default=OpportunityStatus.RECOMMENDED)
    recommended_at = Column(DateTime, default=datetime.utcnow)
    viewed = Column(Boolean, default=False)
    applied_at = Column(DateTime)
    notes = Column(Text)
    
    user = relationship("User")
    job = relationship("JobOpportunity")

class UserHackathonMatch(Base):
    __tablename__ = "user_hackathon_matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    hackathon_id = Column(String, ForeignKey('hackathons.id'), nullable=False)
    match_score = Column(Float)
    relevant_skills = Column(JSON)
    reason = Column(Text)
    status = Column(Enum(OpportunityStatus), default=OpportunityStatus.RECOMMENDED)
    recommended_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    hackathon = relationship("Hackathon")

# ==================== JOURNAL MODULE ====================

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255))
    content = Column(Text, nullable=False)
    mood = Column(String(50))
    tags = Column(JSON)
    
    ai_summary = Column(Text)
    key_insights = Column(JSON)
    sentiment_score = Column(Float)
    topics_detected = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    word_count = Column(Integer)
    
    user = relationship("User", back_populates="journal_entries")

# ==================== ROADMAP MODELS ====================

class Roadmap(Base):
    __tablename__ = "roadmaps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    target_role = Column(String(255), nullable=False)
    target_timeline_weeks = Column(Integer, default=12)
    
    roadmap_data = Column(JSON)
    diagram_svg_url = Column(String(1000))
    diagram_png_url = Column(String(1000))
    diagram_text = Column(Text)
    
    overall_progress_percent = Column(Float, default=0.0)
    current_phase = Column(Enum(RoadmapPhase), default=RoadmapPhase.FOUNDATION)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime)
    
    user = relationship("User")
    tasks = relationship("RoadmapTask", back_populates="roadmap", cascade="all, delete-orphan")

class RoadmapTask(Base):
    __tablename__ = "roadmap_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id = Column(String, ForeignKey("roadmaps.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    phase = Column(Enum(RoadmapPhase), nullable=False)
    skill_name = Column(String(255), nullable=False)
    task_title = Column(String(500), nullable=False)
    task_description = Column(Text)
    
    sequence_order = Column(Integer)
    estimated_hours = Column(Integer)
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    
    status = Column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    progress_percent = Column(Float, default=0.0)
    completed_at = Column(DateTime)
    
    google_calendar_event_id = Column(String(255))
    calendar_synced = Column(Boolean, default=False)
    
    resources = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    roadmap = relationship("Roadmap", back_populates="tasks")
    user = relationship("User")

# ==================== COLD EMAIL MODELS ====================

class ColdEmailCampaign(Base):
    __tablename__ = "cold_email_campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    name = Column(String, nullable=False)
    target_role = Column(String, nullable=False)
    target_companies = Column(JSON, default=list)
    
    status = Column(Enum(EmailCampaignStatus), default=EmailCampaignStatus.DRAFT)  # ✅ FIXED
    
    send_interval_days = Column(Integer, default=3)
    last_sent_at = Column(DateTime, nullable=True)
    next_send_at = Column(DateTime, nullable=True)
    
    total_recipients = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    
    require_approval = Column(Boolean, default=True)
    auto_send = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="cold_email_campaigns")
    recipients = relationship("ColdEmailRecipient", back_populates="campaign", cascade="all, delete-orphan")

class ColdEmailRecipient(Base):
    __tablename__ = "cold_email_recipients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("cold_email_campaigns.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    title = Column(String, nullable=True)
    company = Column(String, nullable=False)
    linkedin_url = Column(String, nullable=True)
    
    company_info = Column(JSON, default=dict)
    
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    
    status = Column(Enum(EmailStatus), default=EmailStatus.DRAFT)  # ✅ FIXED
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    
    gmail_message_id = Column(String, nullable=True)
    gmail_thread_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    campaign = relationship("ColdEmailCampaign", back_populates="recipients")
    user = relationship("User")
