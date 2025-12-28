# backend/app/routes/dashboard.py

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
import jwt
import logging
import json

from app.config.database import get_db
from app.config.settings import settings
from app.models.database import (
    User, JournalEntry, Interview, Skill, 
    Project, CareerGoal, UserResume
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# ==================== AUTH ====================
async def get_current_user(authorization: str = Header(None)) -> dict:
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

# ==================== DASHBOARD ENDPOINT ====================

@router.get("/home")
async def get_dashboard_home(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """🏠 Get comprehensive dashboard home data with real-time insights"""
    try:
        user_id = current_user["user_id"]
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get career goal for target role
        career_goal = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
        target_role = career_goal.target_roles[0] if career_goal and career_goal.target_roles else "Software Engineer"
        
        # Time ranges
        today = datetime.utcnow()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # ==================== JOURNAL STATS ====================
        journal_entries_week = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= week_ago
        ).all()
        
        journal_entries_month = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= month_ago
        ).count()
        
        # Calculate average sentiment
        if journal_entries_week:
            avg_sentiment = sum([e.sentiment_score or 0 for e in journal_entries_week]) / len(journal_entries_week)
            mood_trend = "positive" if avg_sentiment > 0.3 else "neutral" if avg_sentiment > -0.3 else "needs_attention"
        else:
            avg_sentiment = 0
            mood_trend = "neutral"
        
        # ==================== INTERVIEW STATS ====================
        interviews_completed = db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.status == "completed"
        ).count()
        
        interviews_this_week = db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.created_at >= week_ago
        ).count()
        
        # ==================== SKILLS & PROJECTS ====================
        skills_count = db.query(Skill).filter(Skill.user_id == user_id).count()
        projects_count = db.query(Project).filter(Project.user_id == user_id).count()
        
        # ==================== PROGRESS CALCULATION ====================
        # Calculate weekly progress (journal entries as proxy)
        daily_entries = [0] * 7
        for entry in journal_entries_week:
            days_ago = (today - entry.created_at).days
            if 0 <= days_ago < 7:
                daily_entries[6 - days_ago] += 1
        
        weekly_goal = 7  # Goal: 1 journal entry per day
        completed_days = len([d for d in daily_entries if d > 0])
        
        # ==================== AI-GENERATED DAILY MOTIVATION ====================
        try:
            motivation_prompt = f"""Generate a short, inspiring daily motivation quote for a {target_role} candidate.

Context:
- They've made {len(journal_entries_week)} journal entries this week
- {interviews_completed} interview practice sessions completed
- Mood trend: {mood_trend}

Generate a personalized, encouraging quote (1-2 sentences) that:
- Is specific to their role ({target_role})
- Acknowledges their progress
- Provides actionable motivation
- Is authentic and not generic

Return ONLY the quote text, no extra formatting."""
            
            daily_quote = await llm_service.generate(
                prompt=motivation_prompt,
                system_prompt="You are a supportive career coach. Generate authentic, personalized motivation.",
                temperature=0.9
            )
            daily_quote = daily_quote.strip().strip('"').strip("'")
        except Exception as e:
            logger.error(f"Failed to generate daily quote: {e}")
            daily_quote = f"Every step you take toward becoming a {target_role} is progress. Keep building, keep learning, keep growing."
        
        # ==================== INDUSTRY NEWS & TRENDS ====================
        try:
            news_prompt = f"""Search recent tech industry news and trends relevant to {target_role}.

Provide:
1. One current headline or trend (from last 2 weeks)
2. Why it matters for {target_role} candidates
3. One actionable takeaway

Format as JSON:
{{
  "headline": "Brief headline",
  "summary": "2-3 sentence explanation",
  "takeaway": "One specific action",
  "relevance": "How this impacts {target_role}"
}}"""
            
            news_response = await llm_service.generate_json(
                prompt=news_prompt,
                system_prompt="You are a tech industry analyst. Provide current, relevant insights.",
                model="llama3-70b-8192"
            )
            
            industry_news = {
                "headline": news_response.get("headline", f"AI and {target_role}: The Future is Now"),
                "summary": news_response.get("summary", "The tech industry continues to evolve rapidly with new opportunities."),
                "takeaway": news_response.get("takeaway", "Stay updated with latest technologies and trends."),
                "relevance": news_response.get("relevance", f"Critical for {target_role} candidates")
            }
        except Exception as e:
            logger.error(f"Failed to get industry news: {e}")
            industry_news = {
                "headline": f"Top Skills for {target_role} in 2025",
                "summary": f"The demand for {target_role} professionals continues to grow, with companies seeking candidates who combine technical skills with problem-solving abilities.",
                "takeaway": "Focus on building projects and gaining practical experience.",
                "relevance": f"Essential for aspiring {target_role} professionals"
            }
        
        # ==================== TODAY'S RECOMMENDED ACTIONS ====================
        today_actions = []
        
        # Add journal prompt if none today
        today_entries = [e for e in journal_entries_week if (today - e.created_at).days == 0]
        if not today_entries:
            today_actions.append({
                "type": "journal",
                "title": "Write Today's Journal Entry",
                "description": "Reflect on your progress and learning",
                "priority": "high",
                "time": "10 min",
                "icon": "book"
            })
        
        # Add interview practice if none this week
        if interviews_this_week == 0:
            today_actions.append({
                "type": "interview",
                "title": "Practice Mock Interview",
                "description": f"Prepare for {target_role} interviews",
                "priority": "medium",
                "time": "20 min",
                "icon": "message-circle"
            })
        
        # Add skill learning
        today_actions.append({
            "type": "learn",
            "title": "Learn Something New",
            "description": "Spend 30 minutes on skill development",
            "priority": "medium",
            "time": "30 min",
            "icon": "brain"
        })
        
        # ==================== RECENT ACTIVITY ====================
        recent_activities = []
        
        # Recent journals
        for entry in journal_entries_week[:3]:
            recent_activities.append({
                "type": "journal",
                "title": entry.title,
                "time": entry.created_at.isoformat() if entry.created_at else None,
                "mood": entry.mood
            })
        
        recent_activities = sorted(recent_activities, key=lambda x: x["time"] or "", reverse=True)[:5]
        
        # ==================== STREAK CALCULATION ====================
        # Calculate journal streak
        streak = 0
        current_date = today.date()

        # Get all journal entries for last 30 days as a LIST
        journal_entries_for_streak = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= month_ago
        ).all()  # ✅ Get actual entries, not just count

        for i in range(30):
            check_date = current_date - timedelta(days=i)
            has_entry = any(
                entry.created_at.date() == check_date 
                for entry in journal_entries_for_streak if entry.created_at
            )
            if has_entry:
                streak += 1
            else:
                break

        
        return {
            "success": True,
            "user": {
                # ✅ CORRECT
"name": user.full_name or user.email.split('@')[0],

                "target_role": target_role,
                "location": user.location
            },
            "daily_quote": daily_quote,
            "industry_news": industry_news,
            "stats": {
                "journal_entries_week": len(journal_entries_week),
                "journal_entries_month": journal_entries_month,
                "interviews_completed": interviews_completed,
                "interviews_this_week": interviews_this_week,
                "skills_count": skills_count,
                "projects_count": projects_count,
                "avg_sentiment": round(avg_sentiment, 2),
                "mood_trend": mood_trend,
                "streak_days": streak
            },
            "progress": {
                "completed": completed_days,
                "total": weekly_goal,
                "percentage": round((completed_days / weekly_goal) * 100, 1),
                "daily_entries": daily_entries
            },
            "today_actions": today_actions,
            "recent_activity": recent_activities,
            "quick_stats": {
                "resume_uploaded": db.query(UserResume).filter(
                    UserResume.user_id == user_id,
                    UserResume.is_active == True
                ).first() is not None,
                "profile_completeness": min(100, (
                    (30 if journal_entries_month > 0 else 0) +
                    (20 if interviews_completed > 0 else 0) +
                    (20 if skills_count >= 5 else 0) +
                    (30 if projects_count > 0 else 0)
                ))
            }
        }
    
    except Exception as e:
        logger.error(f"Dashboard home failed: {e}", exc_info=True)
        raise HTTPException(500, str(e))
