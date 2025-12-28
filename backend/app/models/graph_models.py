# backend/app/models/graph_models.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# ========================
# NODE TYPE DEFINITIONS
# ========================

class NodeType(str, Enum):
    """All node types in the knowledge graph"""
    # Static Nodes
    JOB_ROLE = "JobRole"
    SKILL = "Skill"
    RESOURCE = "Resource"
    
    # User Nodes
    USER = "User"
    PROJECT = "Project"
    INTERVIEW = "Interview"
    FEEDBACK = "Feedback"
    CAREER_GOAL = "CareerGoal"

class RelationshipType(str, Enum):
    """All relationship types in the knowledge graph"""
    # Static Relationships
    REQUIRES = "REQUIRES"  # JobRole -> Skill (core)
    NICE_TO_HAVE = "NICE_TO_HAVE"  # JobRole -> Skill (optional)
    PREREQUISITE_OF = "PREREQUISITE_OF"  # Skill -> Skill
    RELATED_TO = "RELATED_TO"  # Skill -> Skill
    TEACHES = "TEACHES"  # Resource -> Skill
    
    # User Relationships
    HAS_SKILL = "HAS_SKILL"  # User -> Skill
    LEARNING_SKILL = "LEARNING_SKILL"  # User -> Skill
    ASPIRES_TO = "ASPIRES_TO"  # User -> JobRole
    HAS_GOAL = "HAS_GOAL"  # User -> CareerGoal
    BUILT = "BUILT"  # User -> Project
    USES = "USES"  # Project -> Skill
    HAS_FEEDBACK = "HAS_FEEDBACK"  # Interview -> Feedback
    INDICATES_WEAKNESS = "INDICATES_WEAKNESS"  # Feedback -> Skill
    INDICATES_STRENGTH = "INDICATES_STRENGTH"  # Feedback -> Skill
    
    # Hybrid Relationships
    MISSING_SKILL = "MISSING_SKILL"  # User -> Skill
    PARTIAL_MATCH = "PARTIAL_MATCH"  # User -> JobRole
    MATCHES = "MATCHES"  # User -> JobRole
    LACKS = "LACKS"  # User -> Skill
    SHOULD_LEARN = "SHOULD_LEARN"  # User -> Skill
    RECOMMENDED_RESOURCE = "RECOMMENDED_RESOURCE"  # Resource -> User

# ========================
# STATIC NODE MODELS
# ========================

class JobRoleNode(BaseModel):
    """JobRole node - represents a job title/role"""
    name: str
    short_description: str
    industry: str
    seniority_levels: List[str]  # ["junior", "mid", "senior"]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Backend Engineer",
                "short_description": "Designs and implements server-side logic",
                "industry": "Software Engineering",
                "seniority_levels": ["junior", "mid", "senior"]
            }
        }

class SkillNode(BaseModel):
    """Skill node - represents a technical/soft skill"""
    name: str
    category: str  # Programming, Systems, Data, ML, DevOps, Theory, Tools, Soft
    description: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python",
                "category": "Programming",
                "description": "General-purpose programming language"
            }
        }

class ResourceNode(BaseModel):
    """Resource node - represents learning material"""
    title: str
    resource_type: str  # GitHub, Course, Documentation, Book, Tutorial, Platform
    url: str
    teaches_skills: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Fast.ai Deep Learning",
                "resource_type": "Course",
                "url": "https://fast.ai",
                "teaches_skills": ["Deep Learning", "PyTorch"]
            }
        }

# ========================
# USER NODE MODELS
# ========================

class UserNode(BaseModel):
    """User node - represents a platform user"""
    id: str
    name: str
    email: str
    target_role: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectNode(BaseModel):
    """Project node - user's project"""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    tech_stack: List[str] = []

class InterviewNode(BaseModel):
    """Interview node - interview session"""
    id: str
    user_id: str
    job_role: str
    company: Optional[str] = None
    conducted_at: datetime = Field(default_factory=datetime.utcnow)
    overall_score: Optional[float] = None

class FeedbackNode(BaseModel):
    """Feedback node - interview feedback"""
    id: str
    interview_id: str
    content: str
    sentiment: str  # positive, negative, neutral
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CareerGoalNode(BaseModel):
    """CareerGoal node - user's career aspiration"""
    id: str
    user_id: str
    target_roles: List[str]
    timeline: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ========================
# RELATIONSHIP MODELS
# ========================

class RelationshipBase(BaseModel):
    """Base model for relationships"""
    type: RelationshipType
    properties: Dict[str, Any] = {}

class HasSkillRelationship(RelationshipBase):
    """User HAS_SKILL Skill"""
    level: str = "intermediate"  # beginner, intermediate, advanced, expert
    verified: bool = False
    added_at: datetime = Field(default_factory=datetime.utcnow)

class LearningSkillRelationship(RelationshipBase):
    """User LEARNING_SKILL Skill"""
    progress: int = 0  # 0-100
    started_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_hours: Optional[int] = None
    resources: List[str] = []

class JobSkillRelationship(RelationshipBase):
    """JobRole REQUIRES/NICE_TO_HAVE Skill"""
    importance: str = "core"  # core, nice_to_have

class SkillGapResult(BaseModel):
    """Result of skill gap analysis"""
    user_id: str
    target_role: str
    has_skills: List[str]
    missing_skills: List[str]
    learning_skills: List[str]
    match_percentage: float
    recommendations: List[Dict[str, Any]]

class ReadinessScore(BaseModel):
    """Job readiness scoring result"""
    user_id: str
    job_role: str
    score: float  # 0-100
    skill_coverage: float
    experience_match: float
    project_relevance: float
    recommendations: List[str]
    ready: bool

# ========================
# GRAPH QUERY RESULTS
# ========================

class GraphNode(BaseModel):
    """Generic graph node for visualization"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    """Generic graph edge for visualization"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}

class GraphVisualization(BaseModel):
    """Complete graph structure for frontend"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = {}
