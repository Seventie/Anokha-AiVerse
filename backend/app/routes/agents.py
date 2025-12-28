# backend/app/routes/agents.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.utils.auth import decode_access_token
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import all agents
from app.agents.supervisor_agent import supervisor_agent
from app.agents.roadmap_agent import roadmap_agent
from app.agents.opportunities_agent import opportunities_agent
from app.agents.resume_agent import resume_agent
from app.agents.journal_agent import journal_agent
from app.agents.interview_agent import interview_agent
from app.agents.summary_agent import summary_agent
from app.agents.profile_agent import profile_agent

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["Agents"])
security = HTTPBearer()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RoadmapRequest(BaseModel):
    user_id: str
    target_role: str
    timeline: str
    current_skills: List[str]

class OpportunitiesRequest(BaseModel):
    user_id: str

class ResumeAnalysisRequest(BaseModel):
    user_id: str
    resume_text: str
    job_description: Optional[str] = None

class ResumeOptimizeRequest(BaseModel):
    user_id: str
    job_description: str

class SaveJobRequest(BaseModel):
    user_id: str
    job_id: str

class JournalEntryRequest(BaseModel):
    user_id: str
    message: str
    mood: str = "neutral"

class InterviewRequest(BaseModel):
    user_id: str
    job_title: str
    company: str = "Tech Company"
    difficulty: str = "medium"

class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_index: int
    answer: str

class SummaryRequest(BaseModel):
    user_id: str
    week_offset: int = 0

class ProfileUpdateRequest(BaseModel):
    user_id: str
    update_data: Dict[str, Any]

# ============================================================================
# AUTHENTICATION HELPER
# ============================================================================

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract user ID from JWT token"""
    try:
        payload = decode_access_token(credentials.credentials)
        if not payload:
            logger.warning("Token decode failed: Invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing user ID in payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID"
            )
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# ============================================================================
# SUPERVISOR AGENT ROUTES
# ============================================================================

@router.get("/supervisor/status")
async def get_supervisor_status(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get supervisor agent status"""
    return {
        "supervisor": "active",
        "last_check": "2 minutes ago",
        "agents_managed": 7
    }

@router.post("/supervisor/trigger")
async def trigger_supervisor(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Manually trigger supervisor cycle"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Get user context from database
    user_context = {"user_id": user_id}
    
    result = await supervisor_agent.run_cycle(user_id, user_context, db)
    return result

# ============================================================================
# ROADMAP AGENT ROUTES
# ============================================================================

@router.get("/roadmap/{user_id}")
async def get_roadmap(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get existing roadmap"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # In production, fetch from database
    return {
        "roadmap": None,
        "message": "No roadmap found. Generate one to get started."
    }

@router.post("/roadmap/generate")
async def generate_roadmap(
    request: RoadmapRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Generate new roadmap"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    user_profile = {
        "targetRole": request.target_role,
        "timeline": request.timeline,
        "skills": {"technical": request.current_skills}
    }
    
    result = await roadmap_agent.generate_roadmap(request.user_id, user_profile, db)
    return result

@router.post("/roadmap/sync-calendar")
async def sync_roadmap_to_calendar(
    request: Dict[str, Any],
    current_user_id: str = Depends(get_current_user_id)
):
    """Sync roadmap to Google Calendar"""
    
    user_id = request.get("user_id")
    roadmap = request.get("roadmap", {})
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # In production, integrate with Google Calendar API
    return {
        "success": True,
        "message": "Roadmap synced to calendar",
        "events_created": len(roadmap.get("milestones", []))
    }

# ============================================================================
# OPPORTUNITIES AGENT ROUTES
# ============================================================================

@router.get("/opportunities/{user_id}")
async def get_opportunities(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get discovered opportunities"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Fetch from database
    return {
        "opportunities": [],
        "last_scan": "6 hours ago"
    }

@router.post("/opportunities/scan")
async def scan_opportunities(
    request: OpportunitiesRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Trigger opportunities scan"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Get user profile
    user_profile = {
        "skills": {"technical": []},
        "targetRole": "Software Engineer",
        "preferredLocations": []
    }
    
    result = await opportunities_agent.scan_opportunities(request.user_id, user_profile, db)
    return result

@router.post("/opportunities/save")
async def save_job(
    request: SaveJobRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Save job opportunity"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {
        "success": True,
        "message": "Job saved to your list"
    }

# ============================================================================
# RESUME AGENT ROUTES
# ============================================================================

@router.post("/resume/analyze")
async def analyze_resume(
    request: ResumeAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Analyze resume"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await resume_agent.analyze_resume(
        user_id=request.user_id,
        resume_text=request.resume_text,
        user_profile={},
        job_description=request.job_description,
        db=db
    )
    
    return result

@router.post("/resume/optimize")
async def optimize_resume(
    request: ResumeOptimizeRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Optimize resume for specific job"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Get current resume
    resume_text = "User's resume text here..."
    
    result = await resume_agent.analyze_resume(
        user_id=request.user_id,
        resume_text=resume_text,
        user_profile={},
        job_description=request.job_description,
        db=db
    )
    
    return result

# ============================================================================
# JOURNAL AGENT ROUTES
# ============================================================================

@router.get("/journal/{user_id}")
async def get_journal_entries(
    user_id: str,
    limit: int = 10,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get journal entries"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {
        "entries": [],
        "count": 0
    }

@router.post("/journal/add")
async def add_journal_entry(
    request: JournalEntryRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Add journal entry and get AI reflection"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await journal_agent.chat(
        user_id=request.user_id,
        user_name="User",
        message=request.message,
        mood=request.mood,
        db=db
    )
    
    return result

@router.post("/journal/motivation")
async def get_motivation(
    user_id: str,
    context: Dict[str, Any],
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get motivational message"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await journal_agent.chat(
        user_id=user_id,
        user_name="User",
        message="I need some motivation today",
        mood="neutral",
        context=context,
        db=db
    )
    
    return {"motivation": result.get("motivation", "")}

# ============================================================================
# INTERVIEW AGENT ROUTES
# ============================================================================

@router.post("/interview/start")
async def start_interview(
    request: InterviewRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Start mock interview session"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await interview_agent.start_interview(
        user_id=request.user_id,
        job_title=request.job_title,
        company=request.company,
        difficulty=request.difficulty,
        db=db
    )
    
    return result

@router.post("/interview/answer")
async def submit_interview_answer(
    request: InterviewAnswerRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Submit answer to interview question"""
    
    result = await interview_agent.submit_answer(
        session_id=request.session_id,
        question_index=request.question_index,
        answer=request.answer,
        db=db
    )
    
    return result

@router.get("/interview/feedback/{session_id}")
async def get_interview_feedback(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get final interview feedback"""
    
    return {
        "session_id": session_id,
        "final_score": 75,
        "feedback": "Good interview performance",
        "improvements": []
    }

# ============================================================================
# SUMMARY AGENT ROUTES
# ============================================================================

@router.get("/summary/{user_id}")
async def get_weekly_summary(
    user_id: str,
    week_offset: int = 0,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get weekly summary"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await summary_agent.generate_summary(
        user_id=user_id,
        user_name="User",
        week_offset=week_offset,
        db=db
    )
    
    return result

@router.post("/summary/generate")
async def generate_summary(
    request: SummaryRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Generate new weekly summary"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await summary_agent.generate_summary(
        user_id=request.user_id,
        user_name="User",
        week_offset=request.week_offset,
        db=db
    )
    
    return result

# ============================================================================
# PROFILE AGENT ROUTES
# ============================================================================

@router.get("/profile/{user_id}")
async def get_profile_analysis(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get profile completeness analysis"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await profile_agent.get_profile_completeness(user_id, db)
    return result

@router.post("/profile/update")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    result = await profile_agent.manage_profile(
        user_id=request.user_id,
        action="update",
        update_data=request.update_data,
        db=db
    )
    
    return result

# ============================================================================
# DASHBOARD DATA AGGREGATION
# ============================================================================

@router.get("/dashboard/{user_id}")
async def get_dashboard_data(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get aggregated dashboard data"""
    
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {
        "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "schedule": [
            {
                "time": "09:00 AM",
                "title": "React Learning Session",
                "description": "Complete module 3"
            },
            {
                "time": "02:00 PM",
                "title": "Mock Interview Practice",
                "description": "Behavioral questions"
            }
        ],
        "topJobs": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "compatibility": 85
            },
            {
                "title": "Frontend Developer",
                "company": "Startup Inc",
                "location": "Remote",
                "compatibility": 78
            }
        ],
        "progress": {
            "completed": 12,
            "total": 15
        }
    }