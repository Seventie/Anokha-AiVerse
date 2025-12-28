# backend/app/agents/journal_agent.py

from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config.settings import settings
from app.services.vector_db import vector_db
from sqlalchemy.orm import Session
from app.models.database import User
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JournalState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    user_name: str
    entry_text: str
    mood: str
    context: dict
    sentiment_analysis: dict
    reflection_insights: List[str]
    motivational_message: str
    action_suggestions: List[str]
    burnout_signals: List[str]
    conversation_history: List[dict]
    voice_command: str

class JournalAgent:
    """
    Career Journal Agent with LangGraph
    - Daily reflection chatbot (voice-first)
    - Emotional & motivational support
    - Voice commands for actions
    - Stores thoughts, reflections, emotions
    - Generates journey summaries
    - Identifies burnout/stagnation signals
    - Triggers supportive actions
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.9  # Higher temperature for empathetic responses
        )
        self.graph = self._build_graph()
        
        # System personality
        self.system_prompt = """You are a warm, empathetic career coach and journal companion.

Your role:
- Listen actively and validate feelings
- Provide genuine encouragement
- Ask thoughtful follow-up questions
- Celebrate wins, no matter how small
- Help process setbacks constructively
- Identify patterns in career journey
- Suggest actionable next steps
- Recognize signs of burnout or stagnation

Tone:
- Warm and supportive, never cold or clinical
- Use natural, conversational language
- Be honest but kind
- Show genuine interest and care
- Balance empathy with practical advice

Remember: You're not just recording - you're a supportive companion in their career journey."""
    
    def _build_graph(self) -> StateGraph:
        """Build journal conversation workflow"""
        workflow = StateGraph(JournalState)
        
        # Add nodes
        workflow.add_node("process_input", self.process_user_input)
        workflow.add_node("analyze_sentiment", self.analyze_sentiment)
        workflow.add_node("detect_patterns", self.detect_emotional_patterns)
        workflow.add_node("generate_reflection", self.generate_reflection)
        workflow.add_node("provide_support", self.provide_emotional_support)
        workflow.add_node("suggest_actions", self.suggest_next_actions)
        workflow.add_node("check_burnout", self.check_burnout_signals)
        workflow.add_node("persist_entry", self.persist_journal_entry)
        
        # Define flow
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", "analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "detect_patterns")
        workflow.add_edge("detect_patterns", "generate_reflection")
        workflow.add_edge("generate_reflection", "provide_support")
        workflow.add_edge("provide_support", "suggest_actions")
        workflow.add_edge("suggest_actions", "check_burnout")
        workflow.add_edge("check_burnout", "persist_entry")
        workflow.add_edge("persist_entry", END)
        
        return workflow.compile()
    
    async def process_user_input(self, state: JournalState) -> JournalState:
        """Process and understand user's journal entry or voice command"""
        
        # Check for voice commands
        voice_commands = {
            "find jobs": "trigger_opportunities_agent",
            "update roadmap": "trigger_roadmap_agent",
            "summarize week": "trigger_summary_agent",
            "practice interview": "trigger_interview_agent"
        }
        
        entry_lower = state["entry_text"].lower()
        for command, action in voice_commands.items():
            if command in entry_lower:
                state["voice_command"] = action
                break
        
        logger.info(f"Processed journal entry for user {state['user_id']}")
        return state
    
    async def analyze_sentiment(self, state: JournalState) -> JournalState:
        """Analyze emotional sentiment of the entry"""
        
        sentiment_prompt = ChatPromptTemplate.from_template("""
Analyze the emotional sentiment of this journal entry:

Entry: {entry}
Stated Mood: {mood}

Determine:
1. Primary emotion (happy/sad/anxious/frustrated/excited/neutral/confused/overwhelmed)
2. Intensity (1-10)
3. Underlying feelings
4. Positive aspects mentioned
5. Concerns or worries expressed
6. Energy level (high/medium/low)

Return as JSON.
""")
        
        chain = sentiment_prompt | self.llm
        response = await chain.ainvoke({
            "entry": state["entry_text"],
            "mood": state["mood"]
        })
        
        try:
            sentiment = json.loads(response.content)
            state["sentiment_analysis"] = sentiment
        except json.JSONDecodeError:
            state["sentiment_analysis"] = {"primary_emotion": "neutral", "intensity": 5}
        
        state["messages"].append(response)
        return state
    
    async def detect_emotional_patterns(self, state: JournalState) -> JournalState:
        """Detect patterns from recent journal entries"""
        
        # Get recent entries from vector DB
        recent_entries = vector_db.semantic_search(
            query=f"journal entries for {state['user_name']}",
            user_id=state["user_id"],
            n_results=10,
            filter_metadata={"source": "journal_entry"}
        )
        
        if not recent_entries:
            state["reflection_insights"] = ["This is your first journal entry - exciting start!"]
            return state
        
        pattern_prompt = ChatPromptTemplate.from_template("""
Analyze patterns across recent journal entries:

Current Entry: {current_entry}
Sentiment: {sentiment}

Recent Entries Summary:
{recent_entries}

Identify:
1. Recurring themes or concerns
2. Progress indicators
3. Emotional trends (improving/declining/stable)
4. Stuck points or obstacles
5. Wins and achievements (even small ones)

Provide insights as a supportive friend would.

Return as JSON with "insights" array.
""")
        
        chain = pattern_prompt | self.llm
        response = await chain.ainvoke({
            "current_entry": state["entry_text"],
            "sentiment": json.dumps(state["sentiment_analysis"]),
            "recent_entries": json.dumps([e["text"][:200] for e in recent_entries[:5]])
        })
        
        try:
            patterns = json.loads(response.content)
            state["reflection_insights"] = patterns.get("insights", [])
        except json.JSONDecodeError:
            state["reflection_insights"] = []
        
        state["messages"].append(response)
        return state
    
    async def generate_reflection(self, state: JournalState) -> JournalState:
        """Generate thoughtful reflection on the entry"""
        
        reflection_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", """The user just shared this in their career journal:

"{entry}"

They're feeling: {mood}
Sentiment analysis: {sentiment}
Recent patterns: {patterns}

Provide a warm, thoughtful reflection that:
1. Acknowledges their feelings genuinely
2. Highlights any positive aspects
3. Validates their experience
4. Offers a fresh perspective if helpful
5. Asks 1-2 thoughtful follow-up questions

Keep it conversational and supportive (2-3 paragraphs).
""")
        ])
        
        chain = reflection_prompt | self.llm
        response = await chain.ainvoke({
            "entry": state["entry_text"],
            "mood": state["mood"],
            "sentiment": json.dumps(state["sentiment_analysis"]),
            "patterns": ", ".join(state.get("reflection_insights", []))
        })
        
        state["messages"].append(response)
        return state
    
    async def provide_emotional_support(self, state: JournalState) -> JournalState:
        """Generate personalized motivational message"""
        
        support_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", """Based on how {name} is feeling ({mood}) and their recent journey, provide genuine encouragement.

Current situation: {entry}
Sentiment: {sentiment}

Create a personalized, uplifting message that:
- Feels authentic and specific to their situation
- Reminds them of their strengths
- Puts challenges in perspective
- Energizes them for what's ahead
- Is warm but not overly saccharine

2-3 sentences maximum.
""")
        ])
        
        chain = support_prompt | self.llm
        response = await chain.ainvoke({
            "name": state["user_name"],
            "mood": state["mood"],
            "entry": state["entry_text"],
            "sentiment": json.dumps(state["sentiment_analysis"])
        })
        
        state["motivational_message"] = response.content
        state["messages"].append(response)
        return state
    
    async def suggest_next_actions(self, state: JournalState) -> JournalState:
        """Suggest actionable next steps based on entry"""
        
        action_prompt = ChatPromptTemplate.from_template("""
Based on this journal entry, suggest 2-3 concrete next actions:

Entry: {entry}
Mood: {mood}
Patterns: {patterns}

Actions should be:
- Specific and actionable
- Appropriate for their current state
- Varied (learning, applying, self-care, networking, etc.)
- Achievable within 24-48 hours

If they seem overwhelmed, suggest smaller steps.
If they're energized, suggest ambitious actions.

Return as JSON array of actions with:
- action (string)
- reasoning (string)
- urgency (high/medium/low)
""")
        
        chain = action_prompt | self.llm
        response = await chain.ainvoke({
            "entry": state["entry_text"],
            "mood": state["mood"],
            "patterns": ", ".join(state.get("reflection_insights", []))
        })
        
        try:
            actions = json.loads(response.content)
            state["action_suggestions"] = actions if isinstance(actions, list) else []
        except json.JSONDecodeError:
            state["action_suggestions"] = []
        
        state["messages"].append(response)
        return state
    
    async def check_burnout_signals(self, state: JournalState) -> JournalState:
        """Check for signs of burnout or stagnation"""
        
        burnout_prompt = ChatPromptTemplate.from_template("""
Analyze for signs of burnout or stagnation:

Current Entry: {entry}
Recent Patterns: {patterns}
Sentiment: {sentiment}

Red flags to check:
1. Persistent exhaustion or lack of motivation
2. Cynicism about career progress
3. Feeling stuck or directionless
4. Avoiding career tasks consistently
5. Physical symptoms mentioned (headaches, sleep issues)
6. Social withdrawal from networking
7. Diminished sense of accomplishment

If ANY red flags detected, return them with severity (mild/moderate/severe).
If none, return empty array.

Return as JSON: {{"signals": [], "severity": "none|mild|moderate|severe"}}
""")
        
        chain = burnout_prompt | self.llm
        response = await chain.ainvoke({
            "entry": state["entry_text"],
            "patterns": ", ".join(state.get("reflection_insights", [])),
            "sentiment": json.dumps(state["sentiment_analysis"])
        })
        
        try:
            burnout_data = json.loads(response.content)
            state["burnout_signals"] = burnout_data.get("signals", [])
            
            # If severe burnout detected, trigger supportive action
            if burnout_data.get("severity") in ["moderate", "severe"]:
                logger.warning(f"Burnout signals detected for user {state['user_id']}: {burnout_data['severity']}")
        except json.JSONDecodeError:
            state["burnout_signals"] = []
        
        state["messages"].append(response)
        return state
    
    async def persist_journal_entry(self, state: JournalState) -> JournalState:
        """Persist journal entry and analysis"""
        
        user_id = state["user_id"]
        
        # Create comprehensive entry text
        full_entry = f"""Journal Entry by {state['user_name']}
Date: {datetime.utcnow().isoformat()}
Mood: {state['mood']}
Entry: {state['entry_text']}
Sentiment: {state['sentiment_analysis'].get('primary_emotion', 'neutral')}
Insights: {', '.join(state.get('reflection_insights', []))}"""
        
        # Store in vector DB with high priority for semantic search
        vector_db.add_context(
            user_id=user_id,
            text=full_entry,
            metadata={
                "source": "journal_entry",
                "type": "reflection",
                "mood": state["mood"],
                "sentiment": state["sentiment_analysis"].get("primary_emotion"),
                "timestamp": datetime.utcnow().isoformat(),
                "burnout_signals": len(state.get("burnout_signals", []))
            }
        )
        
        logger.info(f"Persisted journal entry for user {user_id}")
        return state
    
    async def chat(
        self,
        user_id: str,
        user_name: str,
        message: str,
        mood: str = "neutral",
        context: dict = None,
        db: Session = None
    ) -> dict:
        """Main entry point for journal conversation"""
        
        initial_state = JournalState(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            user_name=user_name,
            entry_text=message,
            mood=mood,
            context=context or {},
            sentiment_analysis={},
            reflection_insights=[],
            motivational_message="",
            action_suggestions=[],
            burnout_signals=[],
            conversation_history=[],
            voice_command=""
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            # Extract response from messages
            reflection = [msg.content for msg in result["messages"] if isinstance(msg, AIMessage)]
            
            return {
                "success": True,
                "reflection": reflection[2] if len(reflection) > 2 else "Thank you for sharing.",
                "motivation": result["motivational_message"],
                "insights": result["reflection_insights"],
                "suggested_actions": result["action_suggestions"],
                "sentiment": result["sentiment_analysis"],
                "burnout_detected": len(result["burnout_signals"]) > 0,
                "burnout_signals": result["burnout_signals"],
                "voice_command": result.get("voice_command"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Journal chat error: {e}")
            return {
                "success": False,
                "error": str(e),
                "reflection": "I'm here to listen. Could you tell me more about how you're feeling?"
            }
    
    async def get_journey_summary(self, user_id: str, days: int = 30) -> dict:
        """Generate summary of journal journey over time period"""
        
        # Get entries from past N days
        entries = vector_db.semantic_search(
            query=f"journal entries for user {user_id}",
            user_id=user_id,
            n_results=50,
            filter_metadata={"source": "journal_entry"}
        )
        
        summary_prompt = ChatPromptTemplate.from_template("""
Create a meaningful summary of this person's career journal journey:

Entries over past {days} days:
{entries}

Provide:
1. Overall emotional arc
2. Key themes and recurring topics
3. Progress made
4. Ongoing challenges
5. Moments of growth
6. Patterns to be aware of

Write as a compassionate narrative (3-4 paragraphs) that helps them see their journey clearly.
""")
        
        chain = summary_prompt | self.llm
        response = await chain.ainvoke({
            "days": days,
            "entries": json.dumps([e["text"][:300] for e in entries[:20]])
        })
        
        return {
            "summary": response.content,
            "entry_count": len(entries),
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat()
        }

# Singleton instance
journal_agent = JournalAgent()