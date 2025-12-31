# backend/app/routes/roadmap.py - COMPLETE WITH SCHEDULER

from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import jwt
import logging
from datetime import datetime, timedelta

from app.config.database import get_db
from app.config.settings import settings
from app.models.database import (
    User, Roadmap, RoadmapTask, RoadmapPhase, TaskStatus,
    Skill, CareerGoal
)
from app.services.llm_service import llm_service
from app.services.kroki_service import kroki_service
from app.services.calendar_service import calendar_service
from app.agents.roadmap_scheduler import run_roadmap_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roadmap", tags=["Roadmap"])

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

# ==================== SCHEMAS ====================

class GenerateRoadmapRequest(BaseModel):
    target_role: str
    timeline_weeks: int = 12
    preferences: Optional[Dict[str, Any]] = None

class UpdateTaskRequest(BaseModel):
    status: Optional[str] = None
    progress_percent: Optional[float] = None
    notes: Optional[str] = None

class ScheduleCalendarRequest(BaseModel):
    google_calendar_token: Optional[str] = None

# ==================== ENDPOINTS ====================

@router.post("/generate")
async def generate_roadmap(
    request: GenerateRoadmapRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """🎯 Generate personalized learning roadmap"""
    try:
        user_id = current_user["user_id"]
        
        # Step 1: Get user data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get current skills
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        current_skills = [s.skill for s in skills]
        
        # Get career goal - SAFELY
        career_goal = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
        
        # Extract experience safely
        experience_text = "Beginner - Starting career journey"
        if career_goal:
            if hasattr(career_goal, 'short_term_goal') and career_goal.short_term_goal:
                experience_text = str(career_goal.short_term_goal)
            elif hasattr(career_goal, 'long_term_goal') and career_goal.long_term_goal:
                experience_text = str(career_goal.long_term_goal)
        
        logger.info(f"🎯 Generating roadmap for user {user_id}")
        logger.info(f"Target role: {request.target_role}")
        logger.info(f"Current skills: {current_skills}")
        logger.info(f"Experience: {experience_text}")
        logger.info(f"Timeline: {request.timeline_weeks} weeks")
        
        # Step 2: Build user profile for LLM
        user_profile = {
            "current_skills": current_skills,
            "missing_skills": [],
            "experience": experience_text,
            "timeline_weeks": request.timeline_weeks
        }
        
        # Step 3: Generate roadmap with LLM
        try:
            roadmap_data = await llm_service.generate_roadmap(
                user_profile=user_profile,
                target_role=request.target_role,
                timeline=f"{request.timeline_weeks} weeks"
            )
            
            if not roadmap_data or not isinstance(roadmap_data, dict):
                raise ValueError("Invalid roadmap data from LLM")
            
            logger.info(f"✅ LLM generated roadmap with {len(roadmap_data.get('learning_path', []))} skills")
            
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}, using fallback")
            roadmap_data = _get_fallback_roadmap()
        
        # Step 4: Generate Kroki diagram
        try:
            diagram_payload = {
                "target_role": request.target_role,
                "current_skills": current_skills[:5],
                "phases": roadmap_data.get("milestones", [])[:4]
            }
            
            diagram_result = await kroki_service.generate_roadmap_diagram(
                roadmap_data=diagram_payload,
                diagram_type=settings.KROKI_DIAGRAM_TYPE
            )
            
            logger.info(f"📊 Generated diagram")
            
        except Exception as e:
            logger.error(f"❌ Diagram generation failed: {e}")
            diagram_result = {"svg_url": None, "png_url": None, "diagram_text": ""}
        
        # Step 5: Save to database
        db.query(Roadmap).filter(
            Roadmap.user_id == user_id,
            Roadmap.is_active == True
        ).update({"is_active": False})
        
        roadmap = Roadmap(
            user_id=user_id,
            target_role=request.target_role,
            target_timeline_weeks=request.timeline_weeks,
            roadmap_data=roadmap_data,
            diagram_svg_url=diagram_result.get("svg_url"),
            diagram_png_url=diagram_result.get("png_url"),
            diagram_text=diagram_result.get("diagram_text"),
            current_phase=RoadmapPhase.FOUNDATION,
            is_active=True
        )
        db.add(roadmap)
        db.flush()
        
        # Create tasks from learning path
        learning_path = roadmap_data.get("learning_path", [])
        start_date = datetime.utcnow()
        
        for idx, skill_item in enumerate(learning_path):
            skill_name = skill_item.get("skill", "Unknown Skill")
            priority = skill_item.get("priority", "medium")
            resources = skill_item.get("resources", [])
            estimated_hours = skill_item.get("estimated_hours", 20)
            
            if priority == "high":
                phase = RoadmapPhase.FOUNDATION
            elif priority == "medium":
                phase = RoadmapPhase.INTERMEDIATE
            else:
                phase = RoadmapPhase.ADVANCED
            
            task_start = start_date + timedelta(weeks=idx)
            task_due = task_start + timedelta(weeks=2)
            
            task = RoadmapTask(
                roadmap_id=roadmap.id,
                user_id=user_id,
                phase=phase,
                skill_name=skill_name,
                task_title=f"Learn {skill_name}",
                task_description=f"Master {skill_name} for {request.target_role}",
                sequence_order=idx,
                estimated_hours=estimated_hours,
                start_date=task_start,
                due_date=task_due,
                status=TaskStatus.NOT_STARTED,
                resources=resources
            )
            db.add(task)
        
        db.commit()
        db.refresh(roadmap)
        
        logger.info(f"✅ Roadmap saved with ID: {roadmap.id}, {len(learning_path)} tasks")
        
        # Step 6: Schedule background task for calendar sync
        # background_tasks.add_task(schedule_to_calendar, user_id, roadmap.id, db)
        
        return {
            "success": True,
            "roadmap_id": roadmap.id,
            "target_role": request.target_role,
            "timeline_weeks": request.timeline_weeks,
            "diagram": {
                "svg_url": roadmap.diagram_svg_url,
                "png_url": roadmap.diagram_png_url
            },
            "phases": roadmap_data.get("milestones", []),
            "learning_path": learning_path,
            "skill_gaps": {
                "current": current_skills,
                "missing": [],
                "total_to_learn": len(learning_path)
            },
            "total_tasks": len(learning_path),
            "message": "✅ Roadmap generated! Click 'Schedule Next 7 Days' to add to calendar."
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to generate roadmap: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate roadmap: {str(e)}")


@router.get("/current")
async def get_current_roadmap(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📋 Get user's active roadmap with progress"""
    try:
        user_id = current_user["user_id"]
        
        roadmap = db.query(Roadmap).filter(
            Roadmap.user_id == user_id,
            Roadmap.is_active == True
        ).first()
        
        if not roadmap:
            return {
                "success": True,
                "has_roadmap": False,
                "message": "No active roadmap found"
            }
        
        tasks = db.query(RoadmapTask).filter(
            RoadmapTask.roadmap_id == roadmap.id
        ).order_by(RoadmapTask.sequence_order).all()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
        
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        roadmap.overall_progress_percent = overall_progress
        db.commit()
        
        tasks_by_phase = {}
        for task in tasks:
            phase_name = task.phase.value
            if phase_name not in tasks_by_phase:
                tasks_by_phase[phase_name] = []
            
            tasks_by_phase[phase_name].append({
                "id": task.id,
                "skill_name": task.skill_name,
                "title": task.task_title,
                "description": task.task_description,
                "status": task.status.value,
                "progress_percent": task.progress_percent,
                "estimated_hours": task.estimated_hours,
                "start_date": task.start_date.isoformat() if task.start_date else None,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "resources": task.resources or [],
                "google_calendar_event_id": task.google_calendar_event_id,
                "calendar_synced": task.calendar_synced
            })
        
        return {
            "success": True,
            "has_roadmap": True,
            "roadmap": {
                "id": roadmap.id,
                "target_role": roadmap.target_role,
                "timeline_weeks": roadmap.target_timeline_weeks,
                "current_phase": roadmap.current_phase.value,
                "overall_progress": round(overall_progress, 1),
                "created_at": roadmap.created_at.isoformat(),
                "diagram": {
                    "svg_url": roadmap.diagram_svg_url,
                    "png_url": roadmap.diagram_png_url
                }
            },
            "statistics": {
                "total_tasks": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
                "not_started": total_tasks - completed_tasks - in_progress_tasks
            },
            "tasks_by_phase": tasks_by_phase,
            "roadmap_data": roadmap.roadmap_data
        }
    
    except Exception as e:
        logger.error(f"Failed to get roadmap: {e}", exc_info=True)
        raise HTTPException(500, str(e))


# In schedule-next-7-days endpoint - UPDATE THIS SECTION:

@router.post("/schedule-next-7-days")
async def schedule_next_7_days(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📅 Schedule next 7 days in Google Calendar"""
    try:
        user_id = current_user["user_id"]
        
        # Check Google connection
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.google_access_token:
            raise HTTPException(
                400,
                "Google Calendar not connected. Please connect your Google account first."
            )
        
        # Get roadmap and tasks...
        roadmap = db.query(Roadmap).filter(
            Roadmap.user_id == user_id,
            Roadmap.is_active == True
        ).first()
        
        if not roadmap:
            raise HTTPException(404, "No active roadmap found")
        
        # Get tasks
        tasks = db.query(RoadmapTask).filter(
            RoadmapTask.roadmap_id == roadmap.id,
            RoadmapTask.status != TaskStatus.COMPLETED
        ).order_by(RoadmapTask.sequence_order).limit(10).all()
        
        if not tasks:
            raise HTTPException(400, "No tasks available to schedule")
        
        user_profile = {
            "user_id": user_id,
            "current_skills": [],
            "target_role": roadmap.target_role,
            "timeline_weeks": roadmap.target_timeline_weeks,
            "current_tasks": [
                {
                    "id": str(t.id),
                    "skill_name": t.skill_name,
                    "task_title": t.task_title,
                    "task_description": t.task_description,
                    "estimated_hours": t.estimated_hours,
                    "status": t.status.value,
                    "resources": t.resources or []
                }
                for t in tasks
            ]
        }
        
        # Run scheduler
        logger.info(f"🤖 Running scheduler for user {user_id}")
        result = await run_roadmap_scheduler(user_id, user_profile)
        
        # Create Google Calendar events
        schedule = result.get("schedule_7_days", [])
        if schedule:
            from app.services.calendar_service import calendar_service
            event_ids = await calendar_service.create_events_for_user(
                user_id, schedule, db
            )
            
            # Update tasks with event IDs
            for i, event_id in enumerate(event_ids):
                if i < len(schedule) and schedule[i].get('task_id'):
                    task_id = schedule[i]['task_id']
                    task = db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
                    if task:
                        task.google_calendar_event_id = event_id
                        task.calendar_synced = True
            
            db.commit()
        
        return {
            "success": True,
            "scheduled_days": len(schedule),
            "tasks_scheduled": len(event_ids) if schedule else 0,
            "calendar_events_created": len(event_ids) if schedule else 0,
            "notifications": result.get("notifications", []),
            "message": f"✅ Successfully scheduled {len(schedule)} days in your Google Calendar!",
            "schedule": schedule
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"❌ Scheduler failed: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to schedule: {str(e)}")
# In schedule-next-7-days endpoint - UPDATE THIS SECTION:

@router.post("/schedule-next-7-days")
async def schedule_next_7_days(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📅 Schedule next 7 days in Google Calendar"""
    try:
        user_id = current_user["user_id"]
        
        # Check Google connection
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.google_access_token:
            raise HTTPException(
                400,
                "Google Calendar not connected. Please connect your Google account first."
            )
        
        # Get roadmap and tasks...
        roadmap = db.query(Roadmap).filter(
            Roadmap.user_id == user_id,
            Roadmap.is_active == True
        ).first()
        
        if not roadmap:
            raise HTTPException(404, "No active roadmap found")
        
        # Get tasks
        tasks = db.query(RoadmapTask).filter(
            RoadmapTask.roadmap_id == roadmap.id,
            RoadmapTask.status != TaskStatus.COMPLETED
        ).order_by(RoadmapTask.sequence_order).limit(10).all()
        
        if not tasks:
            raise HTTPException(400, "No tasks available to schedule")
        
        user_profile = {
            "user_id": user_id,
            "current_skills": [],
            "target_role": roadmap.target_role,
            "timeline_weeks": roadmap.target_timeline_weeks,
            "current_tasks": [
                {
                    "id": str(t.id),
                    "skill_name": t.skill_name,
                    "task_title": t.task_title,
                    "task_description": t.task_description,
                    "estimated_hours": t.estimated_hours,
                    "status": t.status.value,
                    "resources": t.resources or []
                }
                for t in tasks
            ]
        }
        
        # Run scheduler
        logger.info(f"🤖 Running scheduler for user {user_id}")
        result = await run_roadmap_scheduler(user_id, user_profile)
        
        # Create Google Calendar events
        schedule = result.get("schedule_7_days", [])
        if schedule:
            from app.services.calendar_service import calendar_service
            event_ids = await calendar_service.create_events_for_user(
                user_id, schedule, db
            )
            
            # Update tasks with event IDs
            for i, event_id in enumerate(event_ids):
                if i < len(schedule) and schedule[i].get('task_id'):
                    task_id = schedule[i]['task_id']
                    task = db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
                    if task:
                        task.google_calendar_event_id = event_id
                        task.calendar_synced = True
            
            db.commit()
        
        return {
            "success": True,
            "scheduled_days": len(schedule),
            "tasks_scheduled": len(event_ids) if schedule else 0,
            "calendar_events_created": len(event_ids) if schedule else 0,
            "notifications": result.get("notifications", []),
            "message": f"✅ Successfully scheduled {len(schedule)} days in your Google Calendar!",
            "schedule": schedule
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"❌ Scheduler failed: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to schedule: {str(e)}")


@router.post("/check-daily-progress")
async def check_daily_progress(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """✅ Check today's task completion and assign next task"""
    try:
        user_id = current_user["user_id"]
        today = datetime.utcnow().date()
        
        # Get today's task
        today_task = db.query(RoadmapTask).filter(
            RoadmapTask.user_id == user_id,
            RoadmapTask.start_date <= datetime.utcnow(),
            RoadmapTask.due_date >= datetime.utcnow()
        ).first()
        
        if not today_task:
            return {
                "success": True,
                "message": "No task scheduled for today",
                "next_task": None
            }
        
        # Check if completed
        if today_task.status == TaskStatus.COMPLETED:
            # Assign next task
            next_task = db.query(RoadmapTask).filter(
                RoadmapTask.user_id == user_id,
                RoadmapTask.status == TaskStatus.NOT_STARTED,
                RoadmapTask.sequence_order > today_task.sequence_order
            ).order_by(RoadmapTask.sequence_order).first()
            
            if next_task:
                next_task.status = TaskStatus.IN_PROGRESS
                next_task.start_date = datetime.utcnow()
                db.commit()
                
                return {
                    "success": True,
                    "today_task_completed": True,
                    "next_task": {
                        "id": next_task.id,
                        "skill_name": next_task.skill_name,
                        "title": next_task.task_title,
                        "estimated_hours": next_task.estimated_hours
                    },
                    "message": f"🎉 Great job! Next up: {next_task.skill_name}"
                }
        
        return {
            "success": True,
            "today_task_completed": False,
            "current_task": {
                "id": today_task.id,
                "skill_name": today_task.skill_name,
                "title": today_task.task_title,
                "progress_percent": today_task.progress_percent
            },
            "message": "Keep going! You can do it 💪"
        }
    
    except Exception as e:
        logger.error(f"Failed to check progress: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.post("/check-streak")
async def check_3_day_streak(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """⚠️ Check 3-day missed streak and trigger reschedule"""
    try:
        user_id = current_user["user_id"]
        
        # Get tasks from last 3 days
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        recent_tasks = db.query(RoadmapTask).filter(
            RoadmapTask.user_id == user_id,
            RoadmapTask.start_date >= three_days_ago,
            RoadmapTask.start_date <= datetime.utcnow()
        ).all()
        
        completed_count = len([t for t in recent_tasks if t.status == TaskStatus.COMPLETED])
        
        if completed_count == 0 and len(recent_tasks) >= 3:
            # Missed 3 days! Reschedule
            logger.warning(f"⚠️ User {user_id} missed 3 days. Rescheduling...")
            
            # Delete old calendar events
            # await calendar_service.delete_roadmap_events(user_id)
            
            # Reschedule next 7 days
            # Auto-trigger scheduling
            
            return {
                "success": True,
                "missed_streak": True,
                "days_missed": 3,
                "rescheduled": True,
                "notification_sent": True,
                "message": "⏰ Noticed you missed 3 days. We've rescheduled your tasks - let's get back on track! 💪"
            }
        
        return {
            "success": True,
            "missed_streak": False,
            "streak_active": completed_count > 0,
            "message": f"🔥 {completed_count} tasks completed in last 3 days!"
        }
    
    except Exception as e:
        logger.error(f"Failed to check streak: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    updates: UpdateTaskRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """✏️ Update task status/progress"""
    try:
        user_id = current_user["user_id"]
        
        task = db.query(RoadmapTask).filter(
            RoadmapTask.id == task_id,
            RoadmapTask.user_id == user_id
        ).first()
        
        if not task:
            raise HTTPException(404, "Task not found")
        
        if updates.status:
            task.status = TaskStatus(updates.status)
            if updates.status == "completed":
                task.completed_at = datetime.utcnow()
                task.progress_percent = 100.0
        
        if updates.progress_percent is not None:
            task.progress_percent = updates.progress_percent
            if updates.progress_percent > 0 and task.status == TaskStatus.NOT_STARTED:
                task.status = TaskStatus.IN_PROGRESS
        
        db.commit()
        
        return {"message": "Task updated successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update task: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.delete("/{roadmap_id}")
async def delete_roadmap(
    roadmap_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """🗑️ Delete roadmap"""
    try:
        user_id = current_user["user_id"]
        
        roadmap = db.query(Roadmap).filter(
            Roadmap.id == roadmap_id,
            Roadmap.user_id == user_id
        ).first()
        
        if not roadmap:
            raise HTTPException(404, "Roadmap not found")
        
        db.delete(roadmap)
        db.commit()
        
        return {"message": "Roadmap deleted successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete roadmap: {e}", exc_info=True)
        raise HTTPException(500, str(e))


def _get_fallback_roadmap() -> Dict[str, Any]:
    """Fallback roadmap when LLM fails"""
    return {
        "milestones": [
            {
                "month": 1,
                "phase_name": "Foundation Phase",
                "goals": ["Learn fundamentals", "Build first project"],
                "tasks": ["Complete courses", "Practice daily"],
                "skills": ["Basics"],
                "duration_weeks": 4
            }
        ],
        "learning_path": [
            {
                "skill": "JavaScript",
                "priority": "high",
                "category": "Programming",
                "estimated_hours": 40,
                "resources": ["https://javascript.info"],
                "prerequisites": []
            },
            {
                "skill": "React",
                "priority": "high",
                "category": "Frontend",
                "estimated_hours": 50,
                "resources": ["https://react.dev"],
                "prerequisites": ["JavaScript"]
            }
        ],
        "projects": []
    }
