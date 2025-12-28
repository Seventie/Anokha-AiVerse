# backend/app/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.vector_db import get_vector_db
from app.services.graph_db import get_graph_db
from app.services.llm_service import llm_service
import logging

logger = logging.getLogger(__name__)

class AgentState:
    """Represents the current state of an agent"""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    ACTING = "acting"
    OBSERVING = "observing"
    IMPROVING = "improving"
    ERROR = "error"

class BaseAgent(ABC):
    """Base class for all agentic components"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.state = AgentState.IDLE
        self.memory: List[Dict[str, Any]] = []
        self.last_run: Optional[datetime] = None
        self.error_count = 0
        
    def log(self, message: str, level: str = "info"):
        """Centralized logging"""
        log_msg = f"[{self.name}] {message}"
        if level == "error":
            logger.error(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def update_state(self, new_state: str):
        """Update agent state"""
        self.log(f"State transition: {self.state} -> {new_state}")
        self.state = new_state
    
    def add_to_memory(self, event: Dict[str, Any]):
        """Add event to agent memory"""
        event["timestamp"] = datetime.utcnow().isoformat()
        self.memory.append(event)
        # Keep only last 100 events
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]
    
    async def think(self, user_id: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        THINK phase: Analyze current situation
        Returns: Analysis and observations
        """
        self.update_state(AgentState.THINKING)
        try:
            analysis = await self._think_impl(user_id, context, db)
            self.add_to_memory({"phase": "think", "result": analysis})
            return analysis
        except Exception as e:
            self.log(f"Error in think phase: {e}", "error")
            self.update_state(AgentState.ERROR)
            self.error_count += 1
            return {"error": str(e)}
    
    async def plan(self, user_id: str, analysis: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        PLAN phase: Create action plan
        Returns: Detailed plan
        """
        self.update_state(AgentState.PLANNING)
        try:
            plan = await self._plan_impl(user_id, analysis, db)
            self.add_to_memory({"phase": "plan", "result": plan})
            return plan
        except Exception as e:
            self.log(f"Error in plan phase: {e}", "error")
            self.update_state(AgentState.ERROR)
            return {"error": str(e)}
    
    async def act(self, user_id: str, plan: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        ACT phase: Execute the plan
        Returns: Execution results
        """
        self.update_state(AgentState.ACTING)
        try:
            results = await self._act_impl(user_id, plan, db)
            self.add_to_memory({"phase": "act", "result": results})
            return results
        except Exception as e:
            self.log(f"Error in act phase: {e}", "error")
            self.update_state(AgentState.ERROR)
            return {"error": str(e)}
    
    async def observe(self, user_id: str, results: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        OBSERVE phase: Evaluate outcomes
        Returns: Observations and metrics
        """
        self.update_state(AgentState.OBSERVING)
        try:
            observations = await self._observe_impl(user_id, results, db)
            self.add_to_memory({"phase": "observe", "result": observations})
            return observations
        except Exception as e:
            self.log(f"Error in observe phase: {e}", "error")
            self.update_state(AgentState.ERROR)
            return {"error": str(e)}
    
    async def improve(self, user_id: str, observations: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        IMPROVE phase: Learn and adapt
        Returns: Improvements made
        """
        self.update_state(AgentState.IMPROVING)
        try:
            improvements = await self._improve_impl(user_id, observations, db)
            self.add_to_memory({"phase": "improve", "result": improvements})
            self.update_state(AgentState.IDLE)
            return improvements
        except Exception as e:
            self.log(f"Error in improve phase: {e}", "error")
            self.update_state(AgentState.ERROR)
            return {"error": str(e)}
    
    async def run_cycle(self, user_id: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute complete THINK → PLAN → ACT → OBSERVE → IMPROVE cycle
        """
        self.log(f"Starting cycle for user {user_id}")
        self.last_run = datetime.utcnow()
        
        # THINK
        analysis = await self.think(user_id, context, db)
        if "error" in analysis:
            return {"success": False, "error": analysis["error"]}
        
        # PLAN
        plan = await self.plan(user_id, analysis, db)
        if "error" in plan:
            return {"success": False, "error": plan["error"]}
        
        # ACT
        results = await self.act(user_id, plan, db)
        if "error" in results:
            return {"success": False, "error": results["error"]}
        
        # OBSERVE
        observations = await self.observe(user_id, results, db)
        if "error" in observations:
            return {"success": False, "error": observations["error"]}
        
        # IMPROVE
        improvements = await self.improve(user_id, observations, db)
        
        self.log(f"Cycle completed successfully")
        return {
            "success": True,
            "analysis": analysis,
            "plan": plan,
            "results": results,
            "observations": observations,
            "improvements": improvements
        }
    
    # Abstract methods to be implemented by specific agents
    @abstractmethod
    async def _think_impl(self, user_id: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Implement thinking logic"""
        pass
    
    @abstractmethod
    async def _plan_impl(self, user_id: str, analysis: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Implement planning logic"""
        pass
    
    @abstractmethod
    async def _act_impl(self, user_id: str, plan: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Implement action logic"""
        pass
    
    @abstractmethod
    async def _observe_impl(self, user_id: str, results: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Implement observation logic"""
        pass
    
    @abstractmethod
    async def _improve_impl(self, user_id: str, observations: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Implement improvement logic"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "state": self.state,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "error_count": self.error_count,
            "memory_size": len(self.memory)
        }