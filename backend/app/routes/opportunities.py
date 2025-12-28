# backend/app/routes/opportunities.py

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any
import jwt
import logging

from app.config.database import get_db
from app.config.settings import settings
from app.services.opportunities_service import opportunities_service
from app.models.database import UserJobMatch, OpportunityStatus
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/opportunities", tags=["Opportunities"])

# ==================== AUTH HELPER ====================
async def get_current_user(authorization: str = Header(None)) -> dict:
    """Extract user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authentication token")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        return {"user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# ==================== ENDPOINTS ====================

@router.post("/scan")
async def scan_opportunities(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    🔍 Scan the web for job opportunities and hackathons
    
    **What this does:**
    - Scrapes LinkedIn, Indeed, Glassdoor for jobs
    - Scrapes Internshala for internships
    - Scrapes Devpost, Unstop, MLH for hackathons
    - Uses AI to match opportunities with your profile
    - Returns top matches with compatibility scores
    
    **Returns:**
    - jobs_found: Total jobs scraped
    - jobs_stored: New jobs added to database
    - job_matches: Number of matching jobs
    - hackathon_matches: Number of matching hackathons
    - top_jobs: Top 10 job matches
    - top_hackathons: Top 5 hackathon matches
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"🚀 Starting opportunity scan for user {user_id}")
        
        result = await opportunities_service.scan_and_match_opportunities(user_id, db)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Found {result['job_matches']} job matches and {result['hackathon_matches']} hackathons!",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": result.get("error", "Scan failed"),
                "data": result
            }
    
    except Exception as e:
        logger.error(f"❌ Opportunity scan error: {e}", exc_info=True)
        raise HTTPException(500, f"Scan failed: {str(e)}")

@router.get("/matches")
async def get_user_opportunities(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    📋 Get your matched opportunities
    
    Returns all jobs and hackathons matched to your profile,
    sorted by compatibility score.
    """
    try:
        user_id = current_user["user_id"]
        matches = opportunities_service.get_user_matches(user_id, db, limit)
        
        return {
            "success": True,
            "data": matches
        }
    
    except Exception as e:
        logger.error(f"❌ Error fetching matches: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@router.patch("/job/{job_match_id}/status")
async def update_job_status(
    job_match_id: int,
    status: str,  # "saved", "applied", "rejected", "interviewing"
    notes: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ✏️ Update job application status
    
    Track your application progress:
    - **saved**: Bookmarked for later
    - **applied**: Application submitted
    - **interviewing**: Got interview call
    - **rejected**: Application rejected
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate status
        valid_statuses = ["saved", "applied", "rejected", "interviewing", "recommended"]
        if status not in valid_statuses:
            raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        match = db.query(UserJobMatch).filter(
            UserJobMatch.id == job_match_id,
            UserJobMatch.user_id == user_id
        ).first()
        
        if not match:
            raise HTTPException(404, "Job match not found")
        
        # Update status
        match.status = OpportunityStatus(status)
        if notes:
            match.notes = notes
        if status == "applied":
            match.applied_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Status updated to {status}"
        }
    
    except ValueError:
        raise HTTPException(400, f"Invalid status value")
    except Exception as e:
        logger.error(f"❌ Status update error: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@router.get("/stats")
async def get_opportunity_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📊 Get your opportunity statistics
    
    Returns counts of:
    - Total matches
    - Applied jobs
    - Saved jobs
    - Interviewing jobs
    """
    try:
        user_id = current_user["user_id"]
        
        total_matches = db.query(UserJobMatch).filter(
            UserJobMatch.user_id == user_id
        ).count()
        
        applied = db.query(UserJobMatch).filter(
            UserJobMatch.user_id == user_id,
            UserJobMatch.status == OpportunityStatus.APPLIED
        ).count()
        
        saved = db.query(UserJobMatch).filter(
            UserJobMatch.user_id == user_id,
            UserJobMatch.status == OpportunityStatus.SAVED
        ).count()
        
        interviewing = db.query(UserJobMatch).filter(
            UserJobMatch.user_id == user_id,
            UserJobMatch.status == OpportunityStatus.INTERVIEWING
        ).count()
        
        return {
            "success": True,
            "stats": {
                "total_matches": total_matches,
                "applied": applied,
                "saved": saved,
                "interviewing": interviewing
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Stats error: {e}", exc_info=True)
        raise HTTPException(500, str(e))
