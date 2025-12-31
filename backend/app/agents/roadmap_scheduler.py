# backend/app/agents/roadmap_scheduler.py

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated, List, Dict, Any
import operator
import logging
import os

from app.services.llm_service import llm_service
from app.services.calendar_service import calendar_service
from app.config.settings import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ==================== STATE DEFINITION ====================

class RoadmapState(TypedDict):
    user_id: str
    user_profile: Dict[str, Any]
    roadmap_data: Dict[str, Any]
    current_tasks: List[Dict[str, Any]]
    calendar_events: List[Dict[str, Any]]
    schedule_7_days: List[Dict[str, Any]]
    email_content: str
    notifications: List[str]
    next_action: str

# ==================== TOOLS ====================

@tool
async def analyze_user_progress(user_id: str, tasks: List[Dict]) -> str:
    """Analyze user's progress on roadmap tasks"""
    if not tasks:
        return "No tasks to analyze"
    
    completed = len([t for t in tasks if t.get('status') == 'completed'])
    total = len(tasks)
    progress = f"{completed}/{total} tasks completed ({(completed/total)*100:.1f}%)" if total > 0 else "0/0"
    
    prompt = f"""
User {user_id} roadmap progress: {progress}
Recent tasks: {tasks[:3] if len(tasks) >= 3 else tasks}

Analyze:
1. Completion streak (days)
2. Areas of strength
3. Tasks at risk of missing deadline
4. Recommended next focus
5. Motivation level assessment
"""
    
    result = await llm_service.generate(prompt, temperature=0.7)
    return result

@tool
async def generate_daily_schedule(tasks: List[Dict], date: str) -> Dict:
    """Generate optimal daily schedule for a specific date"""
    if not tasks:
        return {
            "date": date,
            "primary_task": None,
            "message": "No tasks available"
        }
    
    # Get first not-started or in-progress task
    available_task = None
    for task in tasks:
        if task.get('status') in ['not_started', 'in_progress']:
            available_task = task
            break
    
    if not available_task:
        return {
            "date": date,
            "primary_task": None,
            "message": "All tasks completed!"
        }
    
    prompt = f"""
Generate optimal daily schedule for date {date} with this task:
Task: {available_task.get('skill_name')}
Estimated: {available_task.get('estimated_hours', 2)} hours
Resources: {available_task.get('resources', [])}

Consider:
- 2 hours max per day
- Best learning time: mornings (9-11 AM)
- Evening review: 8-9 PM

Return JSON:
{{
  "date": "{date}",
  "task_id": "{available_task.get('id')}",
  "primary_task": "task_name",
  "skill_name": "skill",
  "duration": "2h",
  "resources": ["link1", "link2"],
  "morning_session": "9-11 AM",
  "evening_review": "8-9 PM"
}}
"""
    
    try:
        result = await llm_service.generate_json(prompt)
        result['task_id'] = available_task.get('id')
        result['date'] = date
        return result
    except Exception as e:
        logger.error(f"Failed to generate schedule: {e}")
        return {
            "date": date,
            "task_id": available_task.get('id'),
            "primary_task": available_task.get('skill_name'),
            "skill_name": available_task.get('skill_name'),
            "duration": "2h",
            "resources": available_task.get('resources', []),
            "morning_session": "9-11 AM",
            "evening_review": "8-9 PM"
        }

@tool
async def check_completion_streak(user_id: str, days: int = 3) -> Dict:
    """Check if user completed tasks for last N days"""
    # This would check database in production
    streak = {
        "days_completed": 0,
        "consecutive": False,
        "last_missed": None,
        "needs_notification": False,
        "reschedule": False
    }
    
    # For now, return default
    return streak

# ==================== INITIALIZE LLM (WITH API KEY FIX) ====================

def get_llm():
    """Initialize ChatGroq with API key from settings"""
    api_key = (
        getattr(settings, 'GROQ_API_KEY_JOURNAL', None) or 
        getattr(settings, 'GROQ_API_KEY', None) or 
        getattr(settings, 'GROQ_API_KEY_INTERVIEW', None) or
        os.getenv('GROQ_API_KEY') or
        os.getenv('GROQ_API_KEY_JOURNAL')
    )
    
    if not api_key:
        logger.warning("No Groq API key found, LangGraph features will be limited")
        return None
    
    try:
        return ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize ChatGroq: {e}")
        return None

# Initialize LLM lazily
_llm_instance = None

def get_or_create_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm()
    return _llm_instance

# ==================== NODES ====================

async def generate_roadmap_node(state: RoadmapState) -> RoadmapState:
    """Generate detailed roadmap using LLM"""
    try:
        roadmap = await llm_service.generate_roadmap(
            user_profile=state["user_profile"],
            target_role=state["user_profile"].get("target_role", "Full Stack Developer"),
            timeline="12 weeks"
        )
        return {"roadmap_data": roadmap, "next_action": "schedule_7_days"}
    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}")
        return {"roadmap_data": {}, "next_action": "schedule_7_days"}

async def analyze_progress_node(state: RoadmapState) -> RoadmapState:
    """Analyze user's current progress"""
    try:
        progress = await analyze_user_progress(state["user_id"], state["current_tasks"])
        return {"notifications": [progress], "next_action": "generate_schedule"}
    except Exception as e:
        logger.error(f"Progress analysis failed: {e}")
        return {"notifications": [], "next_action": "generate_schedule"}

# In backend/app/agents/roadmap_scheduler.py
# Update the generate_7_day_schedule_node function:

async def generate_7_day_schedule_node(state: RoadmapState) -> RoadmapState:
    """Generate next 7 days calendar schedule"""
    try:
        today = datetime.now().date()
        schedule = []
        tasks = state.get("current_tasks", [])
        
        if not tasks:
            logger.warning("No tasks available for scheduling")
            return {"schedule_7_days": [], "next_action": "send_email"}
        
        for i in range(7):
            day_date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
            daily_schedule = await generate_daily_schedule(tasks, day_date)
            schedule.append(daily_schedule)
        
        # Create calendar events if authenticated
        try:
            from app.services.calendar_service import calendar_service
            if calendar_service.service:
                event_ids = await calendar_service.create_multiple_events(schedule)
                for i, event_id in enumerate(event_ids):
                    if i < len(schedule):
                        schedule[i]['event_id'] = event_id
                logger.info(f"✅ Created {len(event_ids)} calendar events")
        except Exception as e:
            logger.warning(f"Calendar events not created: {e}")
        
        logger.info(f"✅ Generated {len(schedule)} day schedule")
        return {"schedule_7_days": schedule, "next_action": "send_email"}
        
    except Exception as e:
        logger.error(f"Schedule generation failed: {e}", exc_info=True)
        return {"schedule_7_days": [], "next_action": "send_email"}


async def send_weekly_email_node(state: RoadmapState) -> RoadmapState:
    """Generate and send weekly email summary"""
    try:
        schedule_summary = "\n".join([
            f"- {s.get('date')}: {s.get('primary_task', 'Rest day')}"
            for s in state.get("schedule_7_days", [])
        ])
        
        email_content = f"""
🚀 Weekly Roadmap Update

Your 7-day learning schedule:
{schedule_summary}

Progress: Keep learning every day!
"""
        
        logger.info(f"📧 Weekly email generated for user {state['user_id']}")
        
        return {"email_content": email_content, "next_action": "end"}
        
    except Exception as e:
        logger.error(f"Email generation failed: {e}")
        return {"email_content": "", "next_action": "end"}

async def check_streak_and_notify_node(state: RoadmapState) -> RoadmapState:
    """Check 3-day streak and send notifications/reschedule"""
    try:
        streak = await check_completion_streak(state["user_id"])
        
        if streak.get("needs_notification"):
            notifications = [
                "⏰ Missed 3 days! Let's get back on track 🚀",
                "Rescheduled tasks to next available slots"
            ]
            return {"notifications": notifications, "next_action": "send_email"}
        
        return {"notifications": [], "next_action": "send_email"}
        
    except Exception as e:
        logger.error(f"Streak check failed: {e}")
        return {"notifications": [], "next_action": "send_email"}

# ==================== ROUTER NODE ====================

def router_node(state: RoadmapState) -> str:
    """Route to appropriate node based on next_action"""
    action = state.get("next_action", "generate_roadmap")
    
    routes = {
        "generate_roadmap": "generate_roadmap",
        "analyze_progress": "analyze_progress", 
        "generate_schedule": "generate_7_day_schedule",
        "schedule_7_days": "generate_7_day_schedule",
        "send_email": "send_weekly_email",
        "check_streak": "check_streak_and_notify",
        "end": END
    }
    
    return routes.get(action, "generate_7_day_schedule")

# ==================== WORKFLOW GRAPH ====================

def create_workflow():
    """Create and compile the workflow graph"""
    workflow = StateGraph(RoadmapState)
    
    # Add nodes
    workflow.add_node("generate_roadmap", generate_roadmap_node)
    workflow.add_node("analyze_progress", analyze_progress_node)
    workflow.add_node("generate_7_day_schedule", generate_7_day_schedule_node)
    workflow.add_node("send_weekly_email", send_weekly_email_node)
    workflow.add_node("check_streak_and_notify", check_streak_and_notify_node)
    
    # Set entry point
    workflow.set_entry_point("generate_7_day_schedule")
    
    # Add edges
    workflow.add_edge("generate_roadmap", "generate_7_day_schedule")
    workflow.add_edge("analyze_progress", "generate_7_day_schedule")
    workflow.add_edge("generate_7_day_schedule", "send_weekly_email")
    workflow.add_edge("check_streak_and_notify", "send_weekly_email")
    workflow.add_edge("send_weekly_email", END)
    
    return workflow.compile()

# Compile graph
roadmap_scheduler = create_workflow()

# ==================== PUBLIC API ====================

async def run_roadmap_scheduler(user_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Run the complete roadmap scheduling workflow"""
    try:
        initial_state = {
            "user_id": user_id,
            "user_profile": user_profile,
            "roadmap_data": {},
            "current_tasks": user_profile.get("current_tasks", []),
            "calendar_events": [],
            "schedule_7_days": [],
            "email_content": "",
            "notifications": [],
            "next_action": "generate_7_day_schedule"  # Start directly with scheduling
        }
        
        logger.info(f"🚀 Starting roadmap scheduler for user {user_id}")
        
        result = await roadmap_scheduler.ainvoke(initial_state)
        
        logger.info(f"✅ Scheduler completed for user {user_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Roadmap scheduler failed: {e}", exc_info=True)
        return {
            "user_id": user_id,
            "schedule_7_days": [],
            "notifications": [f"Scheduler failed: {str(e)}"],
            "email_content": "",
            "error": str(e)
        }
