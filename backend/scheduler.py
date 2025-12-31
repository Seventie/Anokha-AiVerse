# backend/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import asyncio
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models.database import User, Roadmap, RoadmapTask, TaskStatus
from app.services.llm_service import llm_service
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# ==================== HELPER FUNCTIONS ====================

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

async def send_weekly_summary_async(user_id: str, db: Session):
    """Send weekly email summary to user"""
    try:
        # Get active roadmap
        roadmap = db.query(Roadmap).filter(
            Roadmap.user_id == user_id,
            Roadmap.is_active == True
        ).first()
        
        if not roadmap:
            logger.info(f"No active roadmap for user {user_id}")
            return
        
        # Get tasks
        tasks = db.query(RoadmapTask).filter(
            RoadmapTask.roadmap_id == roadmap.id
        ).all()
        
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        total = len(tasks)
        
        # Generate email content
        email_content = f"""
🚀 Weekly Roadmap Summary

Target Role: {roadmap.target_role}
Progress: {completed}/{total} tasks completed ({roadmap.overall_progress_percent:.1f}%)

Keep up the great work! 💪
"""
        
        logger.info(f"📧 Weekly email generated for user {user_id}")
        # TODO: Send actual email via SendGrid/Mailgun
        
    except Exception as e:
        logger.error(f"Failed to send weekly summary: {e}")

async def check_daily_streaks_async(user_id: str, db: Session):
    """Check if user missed 3 days and reschedule"""
    try:
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        # Get tasks from last 3 days
        recent_tasks = db.query(RoadmapTask).filter(
            RoadmapTask.user_id == user_id,
            RoadmapTask.due_date >= three_days_ago,
            RoadmapTask.due_date <= datetime.utcnow()
        ).all()
        
        completed_count = len([t for t in recent_tasks if t.status == TaskStatus.COMPLETED])
        
        if completed_count == 0 and len(recent_tasks) >= 3:
            logger.warning(f"⚠️ User {user_id} missed 3 days! Sending notification...")
            # TODO: Send push notification
            # TODO: Reschedule tasks
            
    except Exception as e:
        logger.error(f"Failed to check streaks: {e}")

def send_weekly_summary():
    """Wrapper for weekly summary (sync)"""
    db = get_db()
    try:
        users = db.query(User).all()
        for user in users:
            asyncio.run(send_weekly_summary_async(user.id, db))
    except Exception as e:
        logger.error(f"Weekly summary job failed: {e}")

def check_daily_streaks():
    """Wrapper for daily streak check (sync)"""
    db = get_db()
    try:
        users = db.query(User).all()
        for user in users:
            asyncio.run(check_daily_streaks_async(user.id, db))
    except Exception as e:
        logger.error(f"Daily streak check failed: {e}")

# ==================== SCHEDULE JOBS ====================

# Weekly Sunday 8 AM IST
scheduler.add_job(
    send_weekly_summary,
    CronTrigger(day_of_week='sun', hour=8, minute=0, timezone='Asia/Kolkata'),
    id='weekly_roadmap_email',
    replace_existing=True
)

# Daily 8 PM IST check streaks
scheduler.add_job(
    check_daily_streaks,
    CronTrigger(hour=20, minute=0, timezone='Asia/Kolkata'),
    id='daily_streak_check',
    replace_existing=True
)

# Start scheduler
def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        scheduler.start()
        logger.info("✅ Scheduler started successfully")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Scheduler stopped")
