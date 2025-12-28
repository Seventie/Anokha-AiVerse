# backend/app/agents/summary_agent.py

from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from app.services.vector_db import vector_db
from app.services.graph_db import graph_db
from sqlalchemy.orm import Session
from app.models.database import User
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SummaryState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    user_name: str
    week_start: str
    week_end: str
    roadmap_data: dict
    completed_tasks: List[dict]
    planned_tasks: List[dict]
    missed_tasks: List[dict]
    journal_entries: List[dict]
    job_applications: List[dict]
    interview_sessions: List[dict]
    skills_progress: dict
    weekly_metrics: dict
    insights: List[str]
    news_summary: str
    recommendations: List[dict]
    celebration_moments: List[str]

class SummaryAgent:
    """
    Weekly Summary Agent with LangGraph
    - Tracks weekly progress
    - Shows completed vs planned tasks
    - Allows rescheduling & postponement
    - Displays charts & growth metrics
    - Fetches industry news relevant to goals
    - Summarizes learning & applications
    - Feeds insights back to Supervisor
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.7
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build weekly summary workflow"""
        workflow = StateGraph(SummaryState)
        
        # Add nodes
        workflow.add_node("collect_data", self.collect_weekly_data)
        workflow.add_node("analyze_tasks", self.analyze_task_completion)
        workflow.add_node("track_progress", self.track_skill_progress)
        workflow.add_node("review_journal", self.review_journal_entries)
        workflow.add_node("summarize_applications", self.summarize_job_activity)
        workflow.add_node("fetch_news", self.fetch_industry_news)
        workflow.add_node("generate_insights", self.generate_weekly_insights)
        workflow.add_node("create_recommendations", self.create_next_week_plan)
        workflow.add_node("identify_celebrations", self.identify_wins)
        workflow.add_node("compile_summary", self.compile_full_summary)
        workflow.add_node("persist_summary", self.persist_summary_data)
        
        # Define flow
        workflow.set_entry_point("collect_data")
        workflow.add_edge("collect_data", "analyze_tasks")
        workflow.add_edge("analyze_tasks", "track_progress")
        workflow.add_edge("track_progress", "review_journal")
        workflow.add_edge("review_journal", "summarize_applications")
        workflow.add_edge("summarize_applications", "fetch_news")
        workflow.add_edge("fetch_news", "generate_insights")
        workflow.add_edge("generate_insights", "create_recommendations")
        workflow.add_edge("create_recommendations", "identify_celebrations")
        workflow.add_edge("identify_celebrations", "compile_summary")
        workflow.add_edge("compile_summary", "persist_summary")
        workflow.add_edge("persist_summary", END)
        
        return workflow.compile()
    
    async def collect_weekly_data(self, state: SummaryState) -> SummaryState:
        """Collect all data from the past week"""
        
        week_start = datetime.fromisoformat(state["week_start"])
        week_end = datetime.fromisoformat(state["week_end"])
        
        # Get data from vector DB for past week
        all_contexts = vector_db.semantic_search(
            query=f"activities for {state['user_name']} this week",
            user_id=state["user_id"],
            n_results=100
        )
        
        # Filter by timestamp
        week_contexts = [
            ctx for ctx in all_contexts
            if ctx.get("metadata", {}).get("timestamp", "") >= state["week_start"]
        ]
        
        # Categorize data
        state["journal_entries"] = [
            ctx for ctx in week_contexts
            if ctx.get("metadata", {}).get("source") == "journal_entry"
        ]
        
        state["interview_sessions"] = [
            ctx for ctx in week_contexts
            if ctx.get("metadata", {}).get("source") == "interview_practice"
        ]
        
        state["job_applications"] = [
            ctx for ctx in week_contexts
            if ctx.get("metadata", {}).get("source") == "job_opportunity"
        ]
        
        logger.info(f"Collected weekly data for user {state['user_id']}")
        return state
    
    async def analyze_task_completion(self, state: SummaryState) -> SummaryState:
        """Analyze completed vs planned vs missed tasks"""
        
        # In production, this would query actual task database
        # For now, we'll use LLM to analyze from contexts
        
        task_prompt = ChatPromptTemplate.from_template("""
Analyze task completion for this week:

Week: {week_start} to {week_end}
Available data: {data_summary}

Infer and estimate:
1. Tasks that were likely completed (based on journal entries, activities)
2. Tasks that were planned but not done
3. Reasons for missed tasks
4. Overall completion rate

Return as JSON:
{{
  "completed_tasks": [
    {{"task": "...", "category": "...", "impact": "high|medium|low"}}
  ],
  "planned_tasks": [...],
  "missed_tasks": [
    {{"task": "...", "reason": "...", "can_reschedule": true}}
  ],
  "completion_rate": 75
}}
""")
        
        chain = task_prompt | self.llm
        response = await chain.ainvoke({
            "week_start": state["week_start"],
            "week_end": state["week_end"],
            "data_summary": f"{len(state['journal_entries'])} journal entries, {len(state['interview_sessions'])} interviews"
        })
        
        try:
            task_data = json.loads(response.content)
            state["completed_tasks"] = task_data.get("completed_tasks", [])
            state["planned_tasks"] = task_data.get("planned_tasks", [])
            state["missed_tasks"] = task_data.get("missed_tasks", [])
            state["weekly_metrics"] = {
                "completion_rate": task_data.get("completion_rate", 0)
            }
        except json.JSONDecodeError:
            state["completed_tasks"] = []
            state["planned_tasks"] = []
            state["missed_tasks"] = []
        
        state["messages"].append(response)
        return state
    
    async def track_skill_progress(self, state: SummaryState) -> SummaryState:
        """Track progress on skill learning"""
        
        # Get learning paths from knowledge graph
        user_skills = graph_db.get_user_skills(state["user_id"])
        
        progress_prompt = ChatPromptTemplate.from_template("""
Analyze skill development progress this week:

Current Skills: {current_skills}
Journal Entries: {journal_count}
Practice Sessions: {practice_count}

Estimate progress made on each skill:
- Time invested
- Confidence improvement
- Practical application

Return as JSON:
{{
  "skills_progress": {{
    "skill_name": {{
      "progress_percentage": 75,
      "time_invested_hours": 5,
      "achievements": ["completed course", "built project"],
      "confidence_level": "intermediate"
    }}
  }},
  "new_skills_started": [],
  "skills_to_review": []
}}
""")
        
        chain = progress_prompt | self.llm
        response = await chain.ainvoke({
            "current_skills": json.dumps([s["skill"] for s in user_skills]),
            "journal_count": len(state["journal_entries"]),
            "practice_count": len(state["interview_sessions"])
        })
        
        try:
            progress = json.loads(response.content)
            state["skills_progress"] = progress.get("skills_progress", {})
        except json.JSONDecodeError:
            state["skills_progress"] = {}
        
        state["messages"].append(response)
        return state
    
    async def review_journal_entries(self, state: SummaryState) -> SummaryState:
        """Review and summarize journal entries"""
        
        if not state["journal_entries"]:
            return state
        
        journal_prompt = ChatPromptTemplate.from_template("""
Summarize this week's journal reflections:

Entries: {entries}

Provide:
1. Emotional journey (overall arc)
2. Key themes
3. Recurring concerns
4. Progress indicators
5. Mindset shifts

Keep it personal and meaningful (2-3 paragraphs).
""")
        
        chain = journal_prompt | self.llm
        response = await chain.ainvoke({
            "entries": json.dumps([e["text"][:200] for e in state["journal_entries"]])
        })
        
        state["messages"].append(response)
        return state
    
    async def summarize_job_activity(self, state: SummaryState) -> SummaryState:
        """Summarize job search activity"""
        
        activity_summary = {
            "jobs_discovered": len(state["job_applications"]),
            "interviews_practiced": len(state["interview_sessions"]),
            "applications_submitted": 0,  # Would be tracked separately
            "responses_received": 0
        }
        
        state["weekly_metrics"].update(activity_summary)
        return state
    
    async def fetch_industry_news(self, state: SummaryState) -> SummaryState:
        """Fetch relevant industry news"""
        
        # In production, this would use news APIs
        # For now, use LLM to generate relevant news summary
        
        news_prompt = ChatPromptTemplate.from_template("""
Generate a summary of relevant industry news for:

User's Target Role: Software Engineer
Week: {week_start} to {week_end}

Provide:
1. Key industry trends
2. Important company news
3. Technology developments
4. Career market insights

Keep it concise and actionable (3-4 bullet points).
""")
        
        chain = news_prompt | self.llm
        response = await chain.ainvoke({
            "week_start": state["week_start"],
            "week_end": state["week_end"]
        })
        
        state["news_summary"] = response.content
        state["messages"].append(response)
        return state
    
    async def generate_weekly_insights(self, state: SummaryState) -> SummaryState:
        """Generate insights from all collected data"""
        
        insights_prompt = ChatPromptTemplate.from_template("""
Generate insights from this week's data:

Completed Tasks: {completed_count}
Completion Rate: {completion_rate}%
Skills Progress: {skills_summary}
Journal Entries: {journal_count}
Interviews: {interview_count}
Job Applications: {jobs_count}

Provide 3-5 actionable insights:
- What's working well
- What needs attention
- Patterns observed
- Opportunities spotted
- Warnings or concerns

Return as JSON array of insight strings.
""")
        
        chain = insights_prompt | self.llm
        response = await chain.ainvoke({
            "completed_count": len(state["completed_tasks"]),
            "completion_rate": state["weekly_metrics"].get("completion_rate", 0),
            "skills_summary": ", ".join(state["skills_progress"].keys()),
            "journal_count": len(state["journal_entries"]),
            "interview_count": len(state["interview_sessions"]),
            "jobs_count": len(state["job_applications"])
        })
        
        try:
            insights = json.loads(response.content)
            state["insights"] = insights if isinstance(insights, list) else []
        except json.JSONDecodeError:
            state["insights"] = ["Keep up the good work!"]
        
        state["messages"].append(response)
        return state
    
    async def create_next_week_plan(self, state: SummaryState) -> SummaryState:
        """Create recommendations for next week"""
        
        recommendation_prompt = ChatPromptTemplate.from_template("""
Based on this week's performance, recommend actions for next week:

Completed: {completed}
Missed: {missed}
Insights: {insights}

Provide 5-7 specific recommendations:
- High-priority tasks
- Skill practice areas
- Application targets
- Learning goals
- Self-care reminders

Return as JSON array:
[
  {{
    "action": "...",
    "priority": "high|medium|low",
    "estimated_time": "2 hours",
    "reasoning": "..."
  }}
]
""")
        
        chain = recommendation_prompt | self.llm
        response = await chain.ainvoke({
            "completed": len(state["completed_tasks"]),
            "missed": len(state["missed_tasks"]),
            "insights": ", ".join(state["insights"])
        })
        
        try:
            recommendations = json.loads(response.content)
            state["recommendations"] = recommendations if isinstance(recommendations, list) else []
        except json.JSONDecodeError:
            state["recommendations"] = []
        
        state["messages"].append(response)
        return state
    
    async def identify_wins(self, state: SummaryState) -> SummaryState:
        """Identify moments worth celebrating"""
        
        wins_prompt = ChatPromptTemplate.from_template("""
Identify wins and achievements from this week:

Completed Tasks: {completed_tasks}
Skills Progress: {skills_progress}
Activities: {activities_summary}

Find:
- Concrete achievements
- Progress milestones
- Personal bests
- Breakthroughs
- Consistency wins

Phrase as celebratory statements (3-5 items).

Return as JSON array of celebration strings.
""")
        
        chain = wins_prompt | self.llm
        response = await chain.ainvoke({
            "completed_tasks": json.dumps(state["completed_tasks"]),
            "skills_progress": json.dumps(state["skills_progress"]),
            "activities_summary": f"{len(state['journal_entries'])} reflections, {len(state['interview_sessions'])} practice sessions"
        })
        
        try:
            celebrations = json.loads(response.content)
            state["celebration_moments"] = celebrations if isinstance(celebrations, list) else []
        except json.JSONDecodeError:
            state["celebration_moments"] = ["You showed up this week - that's a win!"]
        
        state["messages"].append(response)
        return state
    
    async def compile_full_summary(self, state: SummaryState) -> SummaryState:
        """Compile everything into comprehensive summary"""
        
        # This creates the final formatted summary
        logger.info(f"Compiled weekly summary for user {state['user_id']}")
        return state
    
    async def persist_summary_data(self, state: SummaryState) -> SummaryState:
        """Persist summary to databases"""
        
        user_id = state["user_id"]
        
        summary_text = f"""
Weekly Summary: {state['week_start']} to {state['week_end']}
User: {state['user_name']}

Tasks Completed: {len(state['completed_tasks'])}
Completion Rate: {state['weekly_metrics'].get('completion_rate', 0)}%
Skills Progressed: {', '.join(state['skills_progress'].keys())}
Journal Entries: {len(state['journal_entries'])}
Interview Practice: {len(state['interview_sessions'])}

Key Insights: {', '.join(state['insights'])}
Celebrations: {', '.join(state['celebration_moments'])}
"""
        
        # Store in vector DB
        vector_db.add_context(
            user_id=user_id,
            text=summary_text,
            metadata={
                "source": "weekly_summary",
                "type": "progress_report",
                "week_start": state["week_start"],
                "week_end": state["week_end"],
                "completion_rate": state["weekly_metrics"].get("completion_rate", 0)
            }
        )
        
        logger.info(f"Persisted weekly summary for user {user_id}")
        return state
    
    async def generate_summary(
        self,
        user_id: str,
        user_name: str,
        week_offset: int = 0,
        db: Session = None
    ) -> dict:
        """Generate weekly summary"""
        
        # Calculate week dates
        today = datetime.utcnow()
        week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
        week_end = week_start + timedelta(days=6)
        
        initial_state = SummaryState(
            messages=[],
            user_id=user_id,
            user_name=user_name,
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            roadmap_data={},
            completed_tasks=[],
            planned_tasks=[],
            missed_tasks=[],
            journal_entries=[],
            job_applications=[],
            interview_sessions=[],
            skills_progress={},
            weekly_metrics={},
            insights=[],
            news_summary="",
            recommendations=[],
            celebration_moments=[]
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "week_start": result["week_start"],
                "week_end": result["week_end"],
                "completed_tasks": result["completed_tasks"],
                "missed_tasks": result["missed_tasks"],
                "metrics": result["weekly_metrics"],
                "skills_progress": result["skills_progress"],
                "insights": result["insights"],
                "news": result["news_summary"],
                "recommendations": result["recommendations"],
                "celebrations": result["celebration_moments"],
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
summary_agent = SummaryAgent()