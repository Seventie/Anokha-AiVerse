# backend/app/routes/journal.py

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import jwt
import logging
from datetime import datetime, timedelta

from app.config.database import get_db
from app.config.settings import settings
from app.services.journal_service import journal_analyzer
from app.models.database import JournalEntry, User

logger = logging.getLogger(__name__)

# ⚠️ ADD THIS - Router initialization
router = APIRouter(prefix="/api/journal", tags=["Journal"])

# ==================== AUTH ====================
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

# ==================== SCHEMAS ====================
class JournalEntryCreate(BaseModel):
    title: Optional[str] = None
    content: str
    mood: Optional[str] = None
    tags: Optional[List[str]] = []

class JournalEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None

# ==================== ENDPOINTS ====================

@router.post("/entries")
async def create_entry(
    entry_data: JournalEntryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """✍️ Create a new journal entry with AI analysis + Vector DB storage"""
    try:
        user_id = current_user["user_id"]
        
        # Create entry first to get ID
        entry = JournalEntry(
            user_id=user_id,
            title=entry_data.title or f"Entry - {datetime.utcnow().strftime('%B %d, %Y')}",
            content=entry_data.content,
            mood=entry_data.mood,
            tags=entry_data.tags or [],
            word_count=len(entry_data.content.split())
        )
        
        db.add(entry)
        db.flush()
        
        logger.info(f"📝 Creating journal entry for user {user_id}: {entry.id}")
        
        # Analyze content with AI + Store in Vector DB
        analysis = await journal_analyzer.analyze_entry(
            content=entry_data.content,
            title=entry.title,
            user_id=user_id,
            entry_id=entry.id
        )
        
        # ✅ ADD THIS - Log what we got from analysis
        logger.info(f"🤖 Analysis result: {analysis}")
        
        # Update entry with analysis
        entry.mood = entry.mood or analysis.get("mood_detected", "neutral")
        entry.ai_summary = analysis.get("summary")
        entry.key_insights = analysis.get("key_insights", [])
        entry.sentiment_score = analysis.get("sentiment_score", 0.0)
        entry.topics_detected = analysis.get("topics_detected", [])
        
        db.commit()
        db.refresh(entry)
        
        logger.info(f"✅ Journal entry created & stored in vector DB: {entry.id}")
        
        # ✅ PREPARE RESPONSE
        response_data = {
            "success": True,
            "message": "Entry saved successfully",
            "entry_id": entry.id,
            "analysis": {
                "summary": analysis.get("summary"),
                "insights": analysis.get("key_insights", []),
                "suggestions": analysis.get("suggestions", []),
                "mood": analysis.get("mood_detected"),
                "sentiment": analysis.get("sentiment_score")
            }
        }
        
        # ✅ LOG THE RESPONSE WE'RE SENDING
        logger.info(f"📤 Sending response: {response_data}")
        
        return response_data
    
    except Exception as e:
        logger.error(f"❌ Failed to create entry: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(500, f"Failed to create entry: {str(e)}")


@router.get("/entries")
async def get_entries(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📚 Get user's journal entries"""
    try:
        user_id = current_user["user_id"]
        
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id
        ).order_by(JournalEntry.created_at.desc()).offset(offset).limit(limit).all()
        
        total = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id
        ).count()
        
        return {
            "success": True,
            "entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "content": e.content,
                    "mood": e.mood,
                    "tags": e.tags or [],
                    "ai_summary": e.ai_summary,
                    "key_insights": e.key_insights or [],
                    "sentiment_score": e.sentiment_score,
                    "topics_detected": e.topics_detected or [],
                    "word_count": e.word_count,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "updated_at": e.updated_at.isoformat() if e.updated_at else None
                }
                for e in entries
            ],
            "total": total,
            "page": offset // limit + 1,
            "pages": (total + limit - 1) // limit
        }
    
    except Exception as e:
        logger.error(f"Failed to get entries: {e}")
        raise HTTPException(500, str(e))

@router.get("/entries/{entry_id}")
async def get_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📄 Get a specific journal entry"""
    user_id = current_user["user_id"]
    
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.user_id == user_id
    ).first()
    
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    return {
        "success": True,
        "entry": {
            "id": entry.id,
            "title": entry.title,
            "content": entry.content,
            "mood": entry.mood,
            "tags": entry.tags or [],
            "ai_summary": entry.ai_summary,
            "key_insights": entry.key_insights or [],
            "sentiment_score": entry.sentiment_score,
            "topics_detected": entry.topics_detected or [],
            "word_count": entry.word_count,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
        }
    }

@router.patch("/entries/{entry_id}")
async def update_entry(
    entry_id: str,
    entry_data: JournalEntryUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """✏️ Update a journal entry"""
    user_id = current_user["user_id"]
    
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.user_id == user_id
    ).first()
    
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    # Update fields
    if entry_data.title is not None:
        entry.title = entry_data.title
    if entry_data.content is not None:
        entry.content = entry_data.content
        entry.word_count = len(entry_data.content.split())
        
        # Re-analyze if content changed
        analysis = await journal_analyzer.analyze_entry(
            content=entry_data.content,
            title=entry.title,
            user_id=user_id,
            entry_id=entry_id
        )
        entry.ai_summary = analysis.get("summary")
        entry.key_insights = analysis.get("key_insights", [])
        entry.sentiment_score = analysis.get("sentiment_score", 0.0)
        entry.topics_detected = analysis.get("topics_detected", [])
    
    if entry_data.mood is not None:
        entry.mood = entry_data.mood
    if entry_data.tags is not None:
        entry.tags = entry_data.tags
    
    entry.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(entry)
    
    return {
        "success": True,
        "message": "Entry updated successfully"
    }

@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """🗑️ Delete a journal entry"""
    user_id = current_user["user_id"]
    
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.user_id == user_id
    ).first()
    
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    db.delete(entry)
    db.commit()
    
    return {"message": "Entry deleted successfully"}

@router.get("/prompts")
async def get_prompts(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """💡 Get daily journal prompts for inspiration"""
    prompts = journal_analyzer.get_daily_prompts(category)
    
    return {
        "success": True,
        "prompts": prompts,
        "category": category or "mixed"
    }

@router.get("/summary/weekly")
async def get_weekly_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📊 Get AI-generated weekly summary"""
    try:
        user_id = current_user["user_id"]
        
        # Get last 7 days of entries
        week_ago = datetime.utcnow() - timedelta(days=7)
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= week_ago
        ).order_by(JournalEntry.created_at.desc()).all()
        
        # Convert to dict
        entries_data = [
            {
                "title": e.title,
                "content": e.content,
                "mood": e.mood,
                "created_at": e.created_at
            }
            for e in entries
        ]
        
        # Generate summary
        summary = await journal_analyzer.generate_weekly_summary(entries_data, user_id)
        
        return {
            "success": True,
            "summary": summary,
            "entries_count": len(entries),
            "period": f"{week_ago.strftime('%B %d')} - {datetime.utcnow().strftime('%B %d, %Y')}"
        }
    
    except Exception as e:
        logger.error(f"Weekly summary failed: {e}")
        raise HTTPException(500, str(e))

@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📈 Get journal statistics"""
    user_id = current_user["user_id"]
    
    total_entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == user_id
    ).count()
    
    # This week
    week_ago = datetime.utcnow() - timedelta(days=7)
    this_week = db.query(JournalEntry).filter(
        JournalEntry.user_id == user_id,
        JournalEntry.created_at >= week_ago
    ).count()
    
    # This month
    month_ago = datetime.utcnow() - timedelta(days=30)
    this_month = db.query(JournalEntry).filter(
        JournalEntry.user_id == user_id,
        JournalEntry.created_at >= month_ago
    ).count()
    
    # Current streak (simplified)
    recent_entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == user_id
    ).order_by(JournalEntry.created_at.desc()).limit(30).all()
    
    streak = 0
    if recent_entries:
        current_date = datetime.utcnow().date()
        for entry in recent_entries:
            entry_date = entry.created_at.date()
            if (current_date - entry_date).days <= streak + 1:
                streak += 1
                current_date = entry_date
            else:
                break
    
    return {
        "success": True,
        "stats": {
            "total_entries": total_entries,
            "this_week": this_week,
            "this_month": this_month,
            "current_streak": streak
        }
    }
@router.get("/summary/comprehensive")
async def get_comprehensive_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    📊 Get comprehensive weekly summary with all metrics
    """
    try:
        user_id = current_user["user_id"]
        
        from app.models.database import Interview, Skill, Project
        from sqlalchemy import func
        
        # Get last 7 days of data
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # Journal entries this week
        journal_entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= week_ago
        ).order_by(JournalEntry.created_at.desc()).all()
        
        # Interviews this week
        interviews = db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.created_at >= week_ago
        ).all()
        
        # Total interviews completed
        completed_interviews = db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.status == 'completed'
        ).count()
        
        # Skills count
        skills = db.query(Skill).filter(
            Skill.user_id == user_id
        ).all()
        
        # Projects count
        projects = db.query(Project).filter(
            Project.user_id == user_id
        ).all()
        
        # Calculate metrics
        total_journal_entries = len(journal_entries)
        avg_sentiment = sum([e.sentiment_score or 0 for e in journal_entries]) / len(journal_entries) if journal_entries else 0
        
        # Mood distribution
        mood_counts = {}
        for entry in journal_entries:
            mood = entry.mood or 'neutral'
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        # Topics mentioned
        all_topics = []
        for entry in journal_entries:
            if entry.topics_detected:
                all_topics.extend(entry.topics_detected)
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Generate AI summary
        summary_data = await journal_analyzer.generate_weekly_summary(
            entries=[
                {
                    "title": e.title,
                    "content": e.content,
                    "mood": e.mood,
                    "created_at": e.created_at
                }
                for e in journal_entries
            ],
            user_id=user_id
        )
        
        # Build comprehensive response
        return {
            "success": True,
            "period": {
                "start": week_ago.strftime('%B %d, %Y'),
                "end": datetime.utcnow().strftime('%B %d, %Y')
            },
            "metrics": {
                "journal_entries": total_journal_entries,
                "interviews_practiced": len(interviews),
                "total_interviews_completed": completed_interviews,
                "skills_count": len(skills),
                "projects_count": len(projects),
                "avg_sentiment": round(avg_sentiment, 2),
                "completion_rate": round((total_journal_entries / 7) * 100, 1) if total_journal_entries > 0 else 0
            },
            "mood_distribution": [
                {"name": mood, "value": count}
                for mood, count in mood_counts.items()
            ],
            "top_topics": sorted(
                [{"name": topic, "count": count} for topic, count in topic_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:5],
            "daily_activity": [
                {
                    "date": (datetime.utcnow() - timedelta(days=i)).strftime('%a'),
                    "entries": len([e for e in journal_entries if (datetime.utcnow() - e.created_at).days == i])
                }
                for i in range(6, -1, -1)
            ],
            "ai_summary": summary_data,
            "skills_breakdown": [
                {
                    "name": skill.skill,
                    "level": skill.level.value if skill.level else "intermediate",
                    "category": skill.category.value if skill.category else "technical"
                }
                for skill in skills[:10]
            ],
            "recent_entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "mood": e.mood,
                    "sentiment_score": e.sentiment_score,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in journal_entries[:5]
            ]
        }
    
    except Exception as e:
        logger.error(f"Comprehensive summary failed: {e}", exc_info=True)
        raise HTTPException(500, str(e))
