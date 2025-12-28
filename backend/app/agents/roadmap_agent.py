# backend/app/agents/roadmap_agent.py

from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from sqlalchemy.orm import Session
from app.services.vector_db import vector_db
from app.services.graph_db import graph_db
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class RoadmapState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    user_profile: dict
    target_role: str
    timeline: str
    current_skills: list
    skill_gaps: list
    milestones: list
    learning_paths: list
    projects: list
    roadmap_json: dict
    excalidraw_data: dict

class RoadmapAgent:
    """
    Roadmap Generator Agent using LangGraph
    - Generates career roadmaps
    - Creates learning paths
    - Suggests projects
    - Time-blocks tasks to calendar
    - Adapts daily based on progress
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.7
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the roadmap generation workflow"""
        workflow = StateGraph(RoadmapState)
        
        # Add nodes
        workflow.add_node("analyze_profile", self.analyze_profile)
        workflow.add_node("identify_gaps", self.identify_skill_gaps)
        workflow.add_node("generate_milestones", self.generate_milestones)
        workflow.add_node("create_learning_paths", self.create_learning_paths)
        workflow.add_node("suggest_projects", self.suggest_projects)
        workflow.add_node("generate_roadmap", self.generate_roadmap_json)
        workflow.add_node("create_visualization", self.create_excalidraw_visualization)
        workflow.add_node("persist_data", self.persist_roadmap_data)
        
        # Define flow
        workflow.set_entry_point("analyze_profile")
        workflow.add_edge("analyze_profile", "identify_gaps")
        workflow.add_edge("identify_gaps", "generate_milestones")
        workflow.add_edge("generate_milestones", "create_learning_paths")
        workflow.add_edge("create_learning_paths", "suggest_projects")
        workflow.add_edge("suggest_projects", "generate_roadmap")
        workflow.add_edge("generate_roadmap", "create_visualization")
        workflow.add_edge("create_visualization", "persist_data")
        workflow.add_edge("persist_data", END)
        
        return workflow.compile()
    
    async def analyze_profile(self, state: RoadmapState) -> RoadmapState:
        """Analyze user profile and current state"""
        
        profile = state["user_profile"]
        
        analysis_prompt = ChatPromptTemplate.from_template("""
Analyze this user profile for career development:

Current Status: {status}
Skills: {skills}
Experience: {experience_count} positions
Education: {education}
Target Role: {target_role}
Timeline: {timeline}

Provide a comprehensive analysis of:
1. Current career level
2. Strengths
3. Areas for improvement
4. Readiness for target role

Return as JSON with keys: level, strengths, improvements, readiness_score (0-100)
""")
        
        chain = analysis_prompt | self.llm
        response = await chain.ainvoke({
            "status": profile.get("currentStatus", "Unknown"),
            "skills": ", ".join(profile.get("skills", {}).get("technical", [])),
            "experience_count": len(profile.get("experience", [])),
            "education": profile.get("education", [{}])[0].get("degree", "N/A") if profile.get("education") else "N/A",
            "target_role": state["target_role"],
            "timeline": state["timeline"]
        })
        
        state["messages"].append(response)
        return state
    
    async def identify_skill_gaps(self, state: RoadmapState) -> RoadmapState:
        """Identify skills needed for target role"""
        
        # Get user's current skills
        current_skills = state["current_skills"]
        target_role = state["target_role"]
        
        # Query knowledge graph for required skills
        role_skills = graph_db.get_recommended_skills(state["user_id"], limit=20)
        
        gap_prompt = ChatPromptTemplate.from_template("""
User wants to become: {target_role}
User has these skills: {current_skills}

Based on industry standards, identify:
1. Critical skills they MUST learn
2. Nice-to-have skills
3. Skills they can leverage
4. Priority order for learning

Return as JSON:
{{
  "critical_skills": ["skill1", "skill2"],
  "nice_to_have": ["skill3", "skill4"],
  "leverage_skills": ["skill5"],
  "learning_priority": [
    {{"skill": "skill1", "priority": "high", "estimated_weeks": 4}}
  ]
}}
""")
        
        chain = gap_prompt | self.llm
        response = await chain.ainvoke({
            "target_role": target_role,
            "current_skills": ", ".join(current_skills)
        })
        
        # Parse response
        try:
            gaps_data = json.loads(response.content)
            state["skill_gaps"] = gaps_data.get("critical_skills", [])
            state["learning_paths"] = gaps_data.get("learning_priority", [])
        except json.JSONDecodeError:
            state["skill_gaps"] = []
        
        state["messages"].append(response)
        return state
    
    async def generate_milestones(self, state: RoadmapState) -> RoadmapState:
        """Generate monthly milestones"""
        
        timeline = state["timeline"]
        months = self._parse_timeline_to_months(timeline)
        
        milestone_prompt = ChatPromptTemplate.from_template("""
Create a {months}-month roadmap for becoming a {target_role}.

Current skills: {current_skills}
Skills to learn: {skill_gaps}
Timeline: {timeline}

Generate monthly milestones with:
- Month number
- Focus area
- Specific goals
- Deliverables
- Skills to master

Return as JSON array of milestones:
[
  {{
    "month": 1,
    "title": "Foundation Phase",
    "focus": "Core fundamentals",
    "goals": ["goal1", "goal2"],
    "deliverables": ["project1"],
    "skills": ["skill1", "skill2"]
  }}
]
""")
        
        chain = milestone_prompt | self.llm
        response = await chain.ainvoke({
            "months": months,
            "target_role": state["target_role"],
            "current_skills": ", ".join(state["current_skills"][:5]),
            "skill_gaps": ", ".join(state["skill_gaps"][:5]),
            "timeline": timeline
        })
        
        try:
            milestones = json.loads(response.content)
            state["milestones"] = milestones
        except json.JSONDecodeError:
            state["milestones"] = []
        
        state["messages"].append(response)
        return state
    
    async def create_learning_paths(self, state: RoadmapState) -> RoadmapState:
        """Create detailed learning paths for each skill"""
        
        learning_prompt = ChatPromptTemplate.from_template("""
For each skill gap, create a learning path:

Skills to learn: {skills}
Timeline: {timeline}

For each skill provide:
- Learning resources (free courses, tutorials, docs)
- Estimated hours
- Practice projects
- Milestones
- Assessment criteria

Return as JSON array.
""")
        
        chain = learning_prompt | self.llm
        response = await chain.ainvoke({
            "skills": ", ".join(state["skill_gaps"]),
            "timeline": state["timeline"]
        })
        
        state["messages"].append(response)
        return state
    
    async def suggest_projects(self, state: RoadmapState) -> RoadmapState:
        """Suggest portfolio projects"""
        
        project_prompt = ChatPromptTemplate.from_template("""
Suggest 3-5 portfolio projects for someone learning:
Target Role: {target_role}
Skills: {skills}

For each project:
- Title
- Description
- Technologies/skills used
- Complexity level
- Estimated timeline
- Why it's valuable

Return as JSON array of projects.
""")
        
        chain = project_prompt | self.llm
        response = await chain.ainvoke({
            "target_role": state["target_role"],
            "skills": ", ".join(state["skill_gaps"])
        })
        
        try:
            projects = json.loads(response.content)
            state["projects"] = projects
        except json.JSONDecodeError:
            state["projects"] = []
        
        state["messages"].append(response)
        return state
    
    async def generate_roadmap_json(self, state: RoadmapState) -> RoadmapState:
        """Compile everything into structured roadmap JSON"""
        
        roadmap = {
            "user_id": state["user_id"],
            "target_role": state["target_role"],
            "timeline": state["timeline"],
            "created_at": datetime.utcnow().isoformat(),
            "milestones": state["milestones"],
            "learning_paths": state["learning_paths"],
            "projects": state["projects"],
            "skill_gaps": state["skill_gaps"],
            "current_skills": state["current_skills"]
        }
        
        state["roadmap_json"] = roadmap
        return state
    
    async def create_excalidraw_visualization(self, state: RoadmapState) -> RoadmapState:
        """Create Excalidraw-compatible visualization data"""
        
        # Generate Excalidraw elements
        elements = []
        y_offset = 100
        
        for idx, milestone in enumerate(state["milestones"]):
            element = {
                "id": f"milestone_{idx}",
                "type": "rectangle",
                "x": 100 + (idx * 250),
                "y": y_offset,
                "width": 200,
                "height": 150,
                "backgroundColor": "#d4d4aa",
                "strokeColor": "#000000",
                "label": {
                    "text": f"Month {milestone.get('month', idx+1)}\n{milestone.get('title', '')}",
                    "fontSize": 16
                }
            }
            elements.append(element)
        
        state["excalidraw_data"] = {
            "type": "excalidraw",
            "version": 2,
            "elements": elements,
            "appState": {
                "viewBackgroundColor": "#ffffff"
            }
        }
        
        return state
    
    async def persist_roadmap_data(self, state: RoadmapState) -> RoadmapState:
        """Persist roadmap to databases"""
        
        user_id = state["user_id"]
        roadmap = state["roadmap_json"]
        
        # Store in vector DB for semantic search
        roadmap_text = f"Career roadmap for {state['target_role']}: {json.dumps(roadmap)}"
        vector_db.add_context(
            user_id=user_id,
            text=roadmap_text,
            metadata={
                "source": "roadmap",
                "type": "career_plan",
                "generated": True,
                "confidence": 0.9
            }
        )
        
        # Store learning paths in knowledge graph
        for skill in state["skill_gaps"]:
            graph_db.create_learning_path(
                user_id=user_id,
                skill=skill,
                resources=[],
                estimated_hours=40,
                priority="high"
            )
        
        logger.info(f"Persisted roadmap for user {user_id}")
        return state
    
    def _parse_timeline_to_months(self, timeline: str) -> int:
        """Convert timeline string to months"""
        if "3" in timeline:
            return 3
        elif "6" in timeline:
            return 6
        elif "12" in timeline or "1 year" in timeline.lower():
            return 12
        return 6  # default
    
    async def generate_roadmap(self, user_id: str, user_profile: dict, db: Session) -> dict:
        """Main entry point to generate roadmap"""
        
        initial_state = RoadmapState(
            messages=[],
            user_id=user_id,
            user_profile=user_profile,
            target_role=user_profile.get("targetRole", "Software Engineer"),
            timeline=user_profile.get("timeline", "6 Months"),
            current_skills=user_profile.get("skills", {}).get("technical", []),
            skill_gaps=[],
            milestones=[],
            learning_paths=[],
            projects=[],
            roadmap_json={},
            excalidraw_data={}
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "roadmap": result["roadmap_json"],
                "visualization": result["excalidraw_data"],
                "milestones": result["milestones"],
                "learning_paths": result["learning_paths"],
                "projects": result["projects"]
            }
        except Exception as e:
            logger.error(f"Roadmap generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
roadmap_agent = RoadmapAgent()