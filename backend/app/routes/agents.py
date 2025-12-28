# backend/app/routes/agents.py - COMPLETE VERSION

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
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
# WEBSOCKET ENDPOINT (REAL-TIME COMMUNICATION)
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time AI agent communication
    Connect: ws://localhost:8000/api/agents/ws?token=YOUR_JWT_TOKEN
    """
    
    # Authenticate via query parameter
    if not token:
        logger.warning("WebSocket rejected: No token provided")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return
    
    payload = decode_access_token(token)
    if not payload:
        logger.warning("WebSocket rejected: Invalid token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("WebSocket rejected: No user_id in token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
        return
    
    # Accept connection
    await websocket.accept()
    logger.info(f"✓ WebSocket connected for user: {user_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            logger.info(f"Received from user {user_id}: {data.get('type', 'unknown')}")
            
            message_type = data.get("type")
            
            if message_type == "agent_query":
                query = data.get("query", "")
                agent_type = data.get("agent", "general")
                context = data.get("context", {})
                
                # Send processing status
                await websocket.send_json({
                    "type": "status",
                    "status": "processing",
                    "message": f"Processing your {agent_type} query..."
                })
                
                # Route to appropriate agent
                try:
                    response = await route_agent_query(user_id, agent_type, query, context)
                    await websocket.send_json({
                        "type": "response",
                        "agent": agent_type,
                        "query": query,
                        "response": response
                    })
                except Exception as e:
                    logger.error(f"Agent query error for user {user_id}: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to process query. Please try again."
                    })
            
            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"✗ WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


async def route_agent_query(user_id: str, agent_type: str, query: str, context: Dict[str, Any] = None) -> str:
    """Route query to appropriate agent"""
    
    context = context or {}
    
    # Simple routing logic - extend this based on your agent implementations
    if agent_type == "journal":
        return f"📔 Journal Agent: Reflecting on '{query}'. This is a placeholder response."
    elif agent_type == "career":
        return f"🎯 Career Advisor: Regarding '{query}', I recommend focusing on skill development."
    elif agent_type == "interview":
        return f"💼 Interview Coach: For '{query}', practice the STAR method."
    elif agent_type == "roadmap":
        return f"🗺️ Roadmap Agent: Your path for '{query}' includes 3 key milestones."
    else:
        return f"🤖 General Response: I understand you're asking about '{query}'. How can I help further?"


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
    
    try:
        # Get user context from database
        user_context = {"user_id": user_id}
        
        result = await supervisor_agent.run_cycle(user_id, user_context, db)
        return result
    except Exception as e:
        logger.error(f"Supervisor trigger failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger supervisor"
        )


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
    
    try:
        # In production, fetch from database
        return {
            "roadmap": None,
            "message": "No roadmap found. Generate one to get started."
        }
    except Exception as e:
        logger.error(f"Get roadmap failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roadmap"
        )


@router.post("/roadmap/generate")
async def generate_roadmap(
    request: RoadmapRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Generate new roadmap"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        user_profile = {
            "targetRole": request.target_role,
            "timeline": request.timeline,
            "skills": {"technical": request.current_skills}
        }
        
        result = await roadmap_agent.generate_roadmap(request.user_id, user_profile, db)
        return result
    except Exception as e:
        logger.error(f"Roadmap generation failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate roadmap"
        )


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
    
    try:
        # In production, integrate with Google Calendar API
        return {
            "success": True,
            "message": "Roadmap synced to calendar",
            "events_created": len(roadmap.get("milestones", []))
        }
    except Exception as e:
        logger.error(f"Calendar sync failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync calendar"
        )


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
    
    try:
        # Fetch from database
        return {
            "opportunities": [],
            "last_scan": "6 hours ago"
        }
    except Exception as e:
        logger.error(f"Get opportunities failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve opportunities"
        )


@router.post("/opportunities/scan")
async def scan_opportunities(
    request: OpportunitiesRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Trigger opportunities scan"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        # Get user profile
        user_profile = {
            "skills": {"technical": []},
            "targetRole": "Software Engineer",
            "preferredLocations": []
        }
        
        result = await opportunities_agent.scan_opportunities(request.user_id, user_profile, db)
        return result
    except Exception as e:
        logger.error(f"Opportunities scan failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan opportunities"
        )


@router.post("/opportunities/save")
async def save_job(
    request: SaveJobRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Save job opportunity"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        return {
            "success": True,
            "message": "Job saved to your list"
        }
    except Exception as e:
        logger.error(f"Save job failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save job"
        )


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
    
    try:
        result = await resume_agent.analyze_resume(
            user_id=request.user_id,
            resume_text=request.resume_text,
            user_profile={},
            job_description=request.job_description,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Resume analysis failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze resume"
        )


@router.post("/resume/optimize")
async def optimize_resume(
    request: ResumeOptimizeRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Optimize resume for specific job"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
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
    except Exception as e:
        logger.error(f"Resume optimization failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize resume"
        )


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
    
    try:
        return {
            "entries": [],
            "count": 0
        }
    except Exception as e:
        logger.error(f"Get journal entries failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve journal entries"
        )


@router.post("/journal/add")
async def add_journal_entry(
    request: JournalEntryRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Add journal entry and get AI reflection"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        result = await journal_agent.chat(
            user_id=request.user_id,
            user_name="User",
            message=request.message,
            mood=request.mood,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Add journal entry failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add journal entry"
        )


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
    
    try:
        result = await journal_agent.chat(
            user_id=user_id,
            user_name="User",
            message="I need some motivation today",
            mood="neutral",
            context=context,
            db=db
        )
        
        return {"motivation": result.get("motivation", "")}
    except Exception as e:
        logger.error(f"Get motivation failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get motivation"
        )


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
    
    try:
        result = await interview_agent.start_interview(
            user_id=request.user_id,
            job_title=request.job_title,
            company=request.company,
            difficulty=request.difficulty,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Start interview failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start interview"
        )


@router.post("/interview/answer")
async def submit_interview_answer(
    request: InterviewAnswerRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Submit answer to interview question"""
    
    try:
        result = await interview_agent.submit_answer(
            session_id=request.session_id,
            question_index=request.question_index,
            answer=request.answer,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Submit interview answer failed for session {request.session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answer"
        )


@router.get("/interview/feedback/{session_id}")
async def get_interview_feedback(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get final interview feedback"""
    
    try:
        return {
            "session_id": session_id,
            "final_score": 75,
            "feedback": "Good interview performance",
            "improvements": []
        }
    except Exception as e:
        logger.error(f"Get interview feedback failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback"
        )


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
    
    try:
        result = await summary_agent.generate_summary(
            user_id=user_id,
            user_name="User",
            week_offset=week_offset,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Get weekly summary failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary"
        )


@router.post("/summary/generate")
async def generate_summary(
    request: SummaryRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Generate new weekly summary"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        result = await summary_agent.generate_summary(
            user_id=request.user_id,
            user_name="User",
            week_offset=request.week_offset,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Generate summary failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary"
        )


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
    
    try:
        result = await profile_agent.get_profile_completeness(user_id, db)
        return result
    except Exception as e:
        logger.error(f"Get profile analysis failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze profile"
        )


@router.post("/profile/update")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    if request.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        result = await profile_agent.manage_profile(
            user_id=request.user_id,
            action="update",
            update_data=request.update_data,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Update profile failed for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


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
    
    try:
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
    except Exception as e:
        logger.error(f"Get dashboard data failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )
