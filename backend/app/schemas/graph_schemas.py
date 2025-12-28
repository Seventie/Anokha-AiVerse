# backend/app/schemas/graph_schemas.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ========================
# REQUEST SCHEMAS
# ========================

class SkillGapRequest(BaseModel):
    """Request for skill gap analysis"""
    user_id: str
    target_role: str


class ReadinessRequest(BaseModel):
    """Request for readiness calculation"""
    user_id: str
    job_role: str


class LearningPlanRequest(BaseModel):
    """Request for learning plan generation"""
    user_id: str
    limit: int = 10


class SyncUserRequest(BaseModel):
    """Request to sync user to graph"""
    user_id: str
    force: bool = False


# ========================
# RESPONSE SCHEMAS
# ========================

class SkillInfo(BaseModel):
    """Basic skill information"""
    name: str
    category: str
    description: Optional[str] = None


class JobRoleInfo(BaseModel):
    """Basic job role information"""
    name: str
    industry: str
    seniority_levels: List[str]


class ResourceInfo(BaseModel):
    """Learning resource information"""
    title: str
    type: str
    url: str


class SkillGapResponse(BaseModel):
    """Response for skill gap analysis"""
    user_id: str
    target_role: str
    has_skills: List[str]
    missing_skills: List[str]
    learning_skills: List[str]
    match_percentage: float
    recommendations: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadinessResponse(BaseModel):
    """Response for readiness calculation"""
    user_id: str
    job_role: str
    overall_score: float
    skill_coverage: float
    experience_match: float
    project_relevance: float
    ready: bool
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LearningPathItem(BaseModel):
    """Single item in learning path"""
    skill: str
    category: str
    priority: str
    prerequisites: List[str]
    prerequisites_met: bool
    resources: List[Dict[str, str]]
    estimated_hours: int
    can_start_now: bool


class LearningPlanResponse(BaseModel):
    """Response for learning plan"""
    user_id: str
    learning_path: List[LearningPathItem]
    total_estimated_hours: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CareerPathOption(BaseModel):
    """Career path exploration result"""
    role: str
    industry: str
    match_percentage: float
    matched_skills: int
    total_required: int
    missing_skills_count: int
    missing_skills: List[str]
    feasibility: str


class CareerPathResponse(BaseModel):
    """Response for career path exploration"""
    user_id: str
    possible_paths: List[CareerPathOption]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SkillRecommendation(BaseModel):
    """Skill recommendation"""
    skill: str
    category: str
    description: Optional[str]
    relevance_score: int
    prerequisites: List[str]
    resources: List[Dict[str, str]]
    estimated_hours: int


class SkillRecommendationsResponse(BaseModel):
    """Response for skill recommendations"""
    user_id: str
    recommendations: List[SkillRecommendation]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketInsightResponse(BaseModel):
    """Market insights for a skill"""
    skill: str
    roles_requiring: List[Dict[str, str]]
    related_skills: List[str]
    prerequisites: List[str]
    resources: List[Dict[str, str]]
    demand_level: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncResponse(BaseModel):
    """Response for sync operation"""
    user_id: str
    success: bool
    synced_entities: Dict[str, int]
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GraphStatsResponse(BaseModel):
    """Graph statistics"""
    total_nodes: Dict[str, int]
    total_relationships: Dict[str, int]
    user_nodes: int
    static_nodes: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ========================
# GRAPH VISUALIZATION
# ========================

class GraphNode(BaseModel):
    """Node for graph visualization"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    """Edge for graph visualization"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}


class GraphVisualizationResponse(BaseModel):
    """Complete graph for visualization"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = {}
