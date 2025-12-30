# backend/app/schemas/interview_schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# ========== INTERVIEW SETUP ==========
class InterviewCreate(BaseModel):
    interview_type: str  # "company_specific" | "custom_topic"
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    custom_topics: Optional[List[str]] = None
    total_rounds: int = 1
    round_configs: List[Dict[str, Any]]  # [{"type": "technical", "difficulty": "medium"}]


class InterviewResponse(BaseModel):
    id: str
    user_id: str
    interview_type: str
    company_name: Optional[str]
    total_rounds: int
    current_round: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== ROUND MANAGEMENT ==========
class RoundResponse(BaseModel):
    id: str
    round_number: int
    round_type: str
    difficulty: str
    status: str
    score: Optional[float]
    pass_status: Optional[bool]
    
    class Config:
        from_attributes = True


# ========== CONVERSATION ==========
class QuestionResponse(BaseModel):
    question_id: int  # ✅ This matches InterviewConversation.id (Integer autoincrement)
    question_text: str
    category: str
    what_to_look_for: List[str]
    audio_url: Optional[str] = None


class AnswerSubmit(BaseModel):
    interview_id: str
    round_id: str
    question_id: int  # ✅ This is correct (matches conversation.id)
    answer_text: str
    audio_url: Optional[str] = None


class AnswerFeedback(BaseModel):
    score: float
    feedback: str
    strengths: List[str]
    improvements: List[str]
    next_question: Optional[QuestionResponse] = None  # ✅ Made optional explicitly


# ========== EVALUATION ==========
class EvaluationResponse(BaseModel):
    technical_score: float
    communication_score: float
    problem_solving_score: float
    confidence_score: float
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


# ========== ANALYTICS ==========
class InterviewHistoryItem(BaseModel):
    id: str
    company_name: Optional[str]
    custom_topics: Optional[List[str]]
    overall_score: float
    pass_fail_status: str
    created_at: datetime
    
class InterviewAnalytics(BaseModel):
    total_interviews: int
    pass_rate: float
    average_score: float
    score_trend: List[Dict[str, Any]]  # [{"date": "2025-01-01", "score": 85}]
    category_scores: Dict[str, float]  # {"technical": 80, "communication": 90}
