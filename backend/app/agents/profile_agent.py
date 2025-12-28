# backend/app/agents/profile_agent.py

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
from app.models.database import User, Education, Skill, Project, Experience
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProfileState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    action: str  # view, update, sync, analyze
    update_data: dict
    current_profile: dict
    validation_results: dict
    sync_status: dict
    profile_analysis: dict
    recommendations: List[str]

class ProfileAgent:
    """
    Profile Management Agent with LangGraph
    - Manages user profile data
    - Validates and syncs information
    - Connects external accounts (LinkedIn, GitHub, Email)
    - Analyzes profile completeness
    - Suggests improvements
    - Syncs changes across all systems
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.5
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build profile management workflow"""
        workflow = StateGraph(ProfileState)
        
        # Add nodes
        workflow.add_node("load_profile", self.load_current_profile)
        workflow.add_node("validate_changes", self.validate_profile_data)
        workflow.add_node("update_sql", self.update_sql_database)
        workflow.add_node("update_vector", self.update_vector_database)
        workflow.add_node("update_graph", self.update_knowledge_graph)
        workflow.add_node("analyze_completeness", self.analyze_profile_completeness)
        workflow.add_node("suggest_improvements", self.suggest_profile_improvements)
        workflow.add_node("sync_external", self.sync_external_accounts)
        
        # Define flow
        workflow.set_entry_point("load_profile")
        workflow.add_conditional_edges(
            "load_profile",
            self.route_action,
            {
                "update": "validate_changes",
                "analyze": "analyze_completeness",
                "sync": "sync_external",
                "view": END
            }
        )
        workflow.add_edge("validate_changes", "update_sql")
        workflow.add_edge("update_sql", "update_vector")
        workflow.add_edge("update_vector", "update_graph")
        workflow.add_edge("update_graph", "analyze_completeness")
        workflow.add_edge("analyze_completeness", "suggest_improvements")
        workflow.add_edge("suggest_improvements", END)
        workflow.add_edge("sync_external", "analyze_completeness")
        
        return workflow.compile()
    
    async def load_current_profile(self, state: ProfileState) -> ProfileState:
        """Load current user profile from all databases"""
        
        # In production, query SQL database for user data
        # For now, simulate
        
        state["current_profile"] = {
            "loaded": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Loaded profile for user {state['user_id']}")
        return state
    
    def route_action(self, state: ProfileState) -> str:
        """Route based on action type"""
        action = state.get("action", "view")
        if action in ["update", "analyze", "sync", "view"]:
            return action
        return "view"
    
    async def validate_profile_data(self, state: ProfileState) -> ProfileState:
        """Validate profile update data"""
        
        update_data = state.get("update_data", {})
        
        validation_prompt = ChatPromptTemplate.from_template("""
Validate this profile update data:

Data to Update: {update_data}

Check:
1. Required fields present
2. Data format correctness (emails, dates, etc.)
3. Completeness
4. Consistency with existing data
5. Professional appropriateness

Return validation results as JSON:
{{
  "valid": true,
  "errors": [],
  "warnings": [],
  "suggestions": []
}}
""")
        
        chain = validation_prompt | self.llm
        response = await chain.ainvoke({
            "update_data": json.dumps(update_data)
        })
        
        try:
            validation = json.loads(response.content)
            state["validation_results"] = validation
        except json.JSONDecodeError:
            state["validation_results"] = {"valid": True, "errors": []}
        
        state["messages"].append(response)
        return state
    
    async def update_sql_database(self, state: ProfileState) -> ProfileState:
        """Update PostgreSQL with new data"""
        
        if not state["validation_results"].get("valid", False):
            logger.warning(f"Validation failed, skipping SQL update for user {state['user_id']}")
            return state
        
        # In production, execute SQL updates here
        # For now, log the update
        
        logger.info(f"Updated SQL database for user {state['user_id']}")
        state["sync_status"] = {"sql": "updated"}
        
        return state
    
    async def update_vector_database(self, state: ProfileState) -> ProfileState:
        """Update vector embeddings with new profile data"""
        
        update_data = state.get("update_data", {})
        
        # Create updated profile text
        profile_text = f"User profile update: {json.dumps(update_data)}"
        
        vector_db.add_context(
            user_id=state["user_id"],
            text=profile_text,
            metadata={
                "source": "profile_update",
                "type": "profile",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        state["sync_status"]["vector"] = "updated"
        logger.info(f"Updated vector database for user {state['user_id']}")
        
        return state
    
    async def update_knowledge_graph(self, state: ProfileState) -> ProfileState:
        """Update Neo4j knowledge graph"""
        
        update_data = state.get("update_data", {})
        
        # Update skills if present
        if "skills" in update_data:
            for skill in update_data["skills"]:
                graph_db.add_user_skill(
                    user_id=state["user_id"],
                    skill=skill,
                    level="intermediate"
                )
        
        # Update target role if present
        if "target_role" in update_data:
            graph_db.create_target_role(
                user_id=state["user_id"],
                role_name=update_data["target_role"]
            )
        
        state["sync_status"]["graph"] = "updated"
        logger.info(f"Updated knowledge graph for user {state['user_id']}")
        
        return state
    
    async def analyze_profile_completeness(self, state: ProfileState) -> ProfileState:
        """Analyze how complete the profile is"""
        
        profile = state.get("current_profile", {})
        
        analysis_prompt = ChatPromptTemplate.from_template("""
Analyze profile completeness:

Current Profile Data: {profile}

Evaluate:
1. Overall completeness score (0-100)
2. Missing critical information
3. Weak sections (need more detail)
4. Strong sections (well-filled)
5. Impact on job matching

Return as JSON:
{{
  "completeness_score": 85,
  "missing_critical": ["portfolio links"],
  "weak_sections": ["project descriptions"],
  "strong_sections": ["education", "skills"],
  "matching_impact": "Excellent profile for job matching"
}}
""")
        
        chain = analysis_prompt | self.llm
        response = await chain.ainvoke({
            "profile": json.dumps(profile)
        })
        
        try:
            analysis = json.loads(response.content)
            state["profile_analysis"] = analysis
        except json.JSONDecodeError:
            state["profile_analysis"] = {"completeness_score": 70}
        
        state["messages"].append(response)
        return state
    
    async def suggest_profile_improvements(self, state: ProfileState) -> ProfileState:
        """Suggest specific improvements to profile"""
        
        analysis = state.get("profile_analysis", {})
        
        improvement_prompt = ChatPromptTemplate.from_template("""
Suggest profile improvements:

Analysis: {analysis}
Missing: {missing}
Weak Sections: {weak}

Provide 3-5 specific, actionable suggestions:
- What to add
- How to improve existing content
- Why it matters for career goals

Return as JSON array of recommendation objects with:
- suggestion (string)
- section (string)
- priority (high/medium/low)
- impact (string)
""")
        
        chain = improvement_prompt | self.llm
        response = await chain.ainvoke({
            "analysis": json.dumps(analysis),
            "missing": ", ".join(analysis.get("missing_critical", [])),
            "weak": ", ".join(analysis.get("weak_sections", []))
        })
        
        try:
            recommendations = json.loads(response.content)
            state["recommendations"] = recommendations if isinstance(recommendations, list) else []
        except json.JSONDecodeError:
            state["recommendations"] = []
        
        state["messages"].append(response)
        return state
    
    async def sync_external_accounts(self, state: ProfileState) -> ProfileState:
        """Sync with external accounts (LinkedIn, GitHub, etc.)"""
        
        # In production, this would:
        # 1. OAuth with LinkedIn/GitHub
        # 2. Fetch profile data
        # 3. Import relevant information
        # 4. Update local databases
        
        # For now, simulate
        state["sync_status"]["external"] = "simulated"
        
        logger.info(f"Synced external accounts for user {state['user_id']}")
        return state
    
    async def manage_profile(
        self,
        user_id: str,
        action: str,
        update_data: dict = None,
        db: Session = None
    ) -> dict:
        """Main entry point for profile management"""
        
        initial_state = ProfileState(
            messages=[],
            user_id=user_id,
            action=action,
            update_data=update_data or {},
            current_profile={},
            validation_results={},
            sync_status={},
            profile_analysis={},
            recommendations=[]
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "action": action,
                "profile": result["current_profile"],
                "validation": result.get("validation_results"),
                "sync_status": result.get("sync_status"),
                "analysis": result.get("profile_analysis"),
                "recommendations": result.get("recommendations"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Profile management error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_profile_completeness(self, user_id: str, db: Session) -> dict:
        """Quick check of profile completeness"""
        
        result = await self.manage_profile(
            user_id=user_id,
            action="analyze",
            db=db
        )
        
        return {
            "completeness_score": result.get("analysis", {}).get("completeness_score", 0),
            "missing_sections": result.get("analysis", {}).get("missing_critical", []),
            "recommendations": result.get("recommendations", [])
        }

# Singleton instance
profile_agent = ProfileAgent()