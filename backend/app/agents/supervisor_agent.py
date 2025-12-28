# backend/app/agents/supervisor_agent.py

from typing import TypedDict, Annotated, Sequence, Literal
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config.settings import settings
from sqlalchemy.orm import Session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Define the state for the supervisor
class SupervisorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    current_agent: str
    next_action: str
    user_context: dict
    agent_results: dict
    errors: list

class SupervisorAgent:
    """
    Global Supervisor Agent using LangGraph
    Orchestrates all other agents and maintains system health
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.7
        )
        
        # Available agents
        self.agents = [
            "roadmap_agent",
            "opportunities_agent",
            "resume_agent",
            "journal_agent",
            "interview_agent",
            "summary_agent",
            "profile_agent"
        ]
        
        # Build the graph
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(SupervisorState)
        
        # Add nodes
        workflow.add_node("analyze_state", self.analyze_user_state)
        workflow.add_node("decide_action", self.decide_next_action)
        workflow.add_node("execute_agent", self.execute_agent)
        workflow.add_node("monitor_health", self.monitor_system_health)
        workflow.add_node("resolve_conflicts", self.resolve_conflicts)
        
        # Add edges
        workflow.set_entry_point("analyze_state")
        
        workflow.add_edge("analyze_state", "decide_action")
        workflow.add_conditional_edges(
            "decide_action",
            self.route_decision,
            {
                "execute": "execute_agent",
                "monitor": "monitor_health",
                "resolve": "resolve_conflicts",
                "end": END
            }
        )
        workflow.add_edge("execute_agent", "monitor_health")
        workflow.add_edge("monitor_health", "decide_action")
        workflow.add_edge("resolve_conflicts", "decide_action")
        
        return workflow.compile()
    
    async def analyze_user_state(self, state: SupervisorState) -> SupervisorState:
        """Analyze current user state and needs"""
        logger.info(f"Analyzing state for user: {state['user_id']}")
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a career development supervisor AI. Analyze the user's current state:
            
User Context: {context}

Determine:
1. What information is missing or outdated
2. Which tasks are overdue
3. What actions would benefit the user most right now
4. Any urgent items that need attention

Respond with a clear analysis."""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        chain = analysis_prompt | self.llm
        
        response = await chain.ainvoke({
            "context": state["user_context"],
            "messages": state["messages"]
        })
        
        state["messages"].append(AIMessage(content=response.content))
        return state
    
    async def decide_next_action(self, state: SupervisorState) -> SupervisorState:
        """Decide which agent to activate or what action to take"""
        
        decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the supervisor deciding what to do next.

Available agents:
- roadmap_agent: Updates career roadmaps and goals
- opportunities_agent: Finds jobs and internships
- resume_agent: Optimizes resumes
- journal_agent: Provides emotional support and reflection
- interview_agent: Conducts mock interviews
- summary_agent: Generates progress reports
- profile_agent: Manages user profile

Based on the analysis, decide:
1. Which agent should run (if any)?
2. What should be the priority?
3. Are there any conflicts to resolve?

Respond in format:
ACTION: [execute|monitor|resolve|end]
AGENT: [agent_name or none]
PRIORITY: [high|medium|low]
REASON: [brief explanation]"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        chain = decision_prompt | self.llm
        response = await chain.ainvoke({"messages": state["messages"]})
        
        # Parse the response
        content = response.content
        action = "execute"
        agent = "roadmap_agent"
        
        if "ACTION:" in content:
            action_line = [line for line in content.split("\n") if "ACTION:" in line][0]
            action = action_line.split("ACTION:")[1].strip().lower()
        
        if "AGENT:" in content:
            agent_line = [line for line in content.split("\n") if "AGENT:" in line][0]
            agent = agent_line.split("AGENT:")[1].strip()
        
        state["next_action"] = action
        state["current_agent"] = agent if agent != "none" else ""
        state["messages"].append(response)
        
        return state
    
    def route_decision(self, state: SupervisorState) -> Literal["execute", "monitor", "resolve", "end"]:
        """Route based on decision"""
        action = state.get("next_action", "end")
        
        if action in ["execute", "monitor", "resolve", "end"]:
            return action
        return "end"
    
    async def execute_agent(self, state: SupervisorState) -> SupervisorState:
        """Execute the selected agent"""
        agent_name = state.get("current_agent", "")
        
        if not agent_name or agent_name not in self.agents:
            logger.warning(f"Invalid agent: {agent_name}")
            return state
        
        logger.info(f"Executing agent: {agent_name}")
        
        # Here we would actually call the specific agent
        # For now, we'll log and track
        state["agent_results"][agent_name] = {
            "status": "executed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state["messages"].append(
            AIMessage(content=f"Executed {agent_name} successfully")
        )
        
        return state
    
    async def monitor_system_health(self, state: SupervisorState) -> SupervisorState:
        """Monitor system health and agent performance"""
        
        health_check = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents_active": len(state.get("agent_results", {})),
            "errors": len(state.get("errors", [])),
            "status": "healthy" if len(state.get("errors", [])) == 0 else "issues_detected"
        }
        
        logger.info(f"Health check: {health_check}")
        
        state["messages"].append(
            AIMessage(content=f"System health: {health_check['status']}")
        )
        
        return state
    
    async def resolve_conflicts(self, state: SupervisorState) -> SupervisorState:
        """Resolve conflicts between agents or data"""
        
        conflicts = state.get("errors", [])
        
        if conflicts:
            resolution_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are resolving conflicts in the system.

Conflicts detected: {conflicts}

Provide:
1. Root cause analysis
2. Resolution steps
3. Prevention measures"""),
                MessagesPlaceholder(variable_name="messages"),
            ])
            
            chain = resolution_prompt | self.llm
            response = await chain.ainvoke({
                "conflicts": conflicts,
                "messages": state["messages"]
            })
            
            state["messages"].append(response)
            state["errors"] = []  # Clear after resolution
        
        return state
    
    async def run_cycle(self, user_id: str, user_context: dict, db: Session) -> dict:
        """Run a complete supervision cycle"""
        
        initial_state = SupervisorState(
            messages=[HumanMessage(content="Start supervision cycle")],
            user_id=user_id,
            current_agent="",
            next_action="",
            user_context=user_context,
            agent_results={},
            errors=[]
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "user_id": user_id,
                "agents_executed": list(result.get("agent_results", {}).keys()),
                "messages": [msg.content for msg in result.get("messages", [])],
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Supervisor cycle error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
supervisor_agent = SupervisorAgent()