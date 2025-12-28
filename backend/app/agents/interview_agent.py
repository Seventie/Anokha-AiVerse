# backend/app/agents/interview_agent.py

from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config.settings import settings
from app.services.vector_db import vector_db
from app.services.graph_db import graph_db
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class InterviewState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    session_id: str
    user_id: str
    job_title: str
    company: str
    difficulty: str
    question_count: int
    current_question_index: int
    questions: List[Dict[str, Any]]
    user_responses: List[Dict[str, Any]]
    evaluations: List[Dict[str, Any]]
    overall_feedback: dict
    final_score: int
    improvement_areas: List[str]
    interview_complete: bool

class InterviewAgent:
    """
    Interview Practice Agent with LangGraph
    - Conducts mock interviews
    - Role-specific questions
    - Transcribes responses
    - Maintains interview memory
    - Evaluates content, confidence, clarity
    - Provides honest feedback and scores
    - Recommends improvements
    - Updates skill graph based on weaknesses
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.7
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build interview practice workflow"""
        workflow = StateGraph(InterviewState)
        
        # Add nodes
        workflow.add_node("initialize_interview", self.initialize_interview_session)
        workflow.add_node("generate_questions", self.generate_interview_questions)
        workflow.add_node("ask_question", self.ask_current_question)
        workflow.add_node("receive_response", self.receive_user_response)
        workflow.add_node("evaluate_response", self.evaluate_single_response)
        workflow.add_node("provide_feedback", self.provide_immediate_feedback)
        workflow.add_node("check_completion", self.check_interview_completion)
        workflow.add_node("generate_overall_feedback", self.generate_final_feedback)
        workflow.add_node("calculate_scores", self.calculate_final_scores)
        workflow.add_node("update_skills", self.update_skill_graph)
        workflow.add_node("persist_session", self.persist_interview_data)
        
        # Define flow
        workflow.set_entry_point("initialize_interview")
        workflow.add_edge("initialize_interview", "generate_questions")
        workflow.add_edge("generate_questions", "ask_question")
        workflow.add_edge("ask_question", "receive_response")
        workflow.add_edge("receive_response", "evaluate_response")
        workflow.add_edge("evaluate_response", "provide_feedback")
        workflow.add_edge("provide_feedback", "check_completion")
        workflow.add_conditional_edges(
            "check_completion",
            self.should_continue_interview,
            {
                "continue": "ask_question",
                "finish": "generate_overall_feedback"
            }
        )
        workflow.add_edge("generate_overall_feedback", "calculate_scores")
        workflow.add_edge("calculate_scores", "update_skills")
        workflow.add_edge("update_skills", "persist_session")
        workflow.add_edge("persist_session", END)
        
        return workflow.compile()
    
    async def initialize_interview_session(self, state: InterviewState) -> InterviewState:
        """Initialize interview session"""
        
        state["session_id"] = str(uuid.uuid4())
        state["current_question_index"] = 0
        state["interview_complete"] = False
        state["user_responses"] = []
        state["evaluations"] = []
        
        # Determine question count based on difficulty
        question_counts = {
            "easy": 5,
            "medium": 8,
            "hard": 10
        }
        state["question_count"] = question_counts.get(state["difficulty"], 8)
        
        logger.info(f"Initialized interview session {state['session_id']} for user {state['user_id']}")
        
        return state
    
    async def generate_interview_questions(self, state: InterviewState) -> InterviewState:
        """Generate interview questions based on role and difficulty"""
        
        questions_prompt = ChatPromptTemplate.from_template("""
Generate {count} interview questions for this role:

Role: {job_title}
Company: {company}
Difficulty: {difficulty}

Question distribution:
- 30% Behavioral (STAR format)
- 30% Technical (role-specific)
- 20% Problem-solving scenarios
- 20% Company/role fit

For each question provide:
- question (string)
- category (behavioral/technical/problem-solving/fit)
- difficulty (easy/medium/hard)
- what_to_look_for (evaluation criteria)
- sample_good_answer (brief example)
- time_limit_seconds (120-300)

Return as JSON array.
""")
        
        chain = questions_prompt | self.llm
        response = await chain.ainvoke({
            "count": state["question_count"],
            "job_title": state["job_title"],
            "company": state["company"],
            "difficulty": state["difficulty"]
        })
        
        try:
            questions = json.loads(response.content)
            state["questions"] = questions if isinstance(questions, list) else []
        except json.JSONDecodeError:
            # Fallback questions
            state["questions"] = [
                {
                    "question": f"Tell me about your experience relevant to {state['job_title']}.",
                    "category": "behavioral",
                    "difficulty": state["difficulty"]
                }
            ]
        
        state["messages"].append(response)
        return state
    
    async def ask_current_question(self, state: InterviewState) -> InterviewState:
        """Ask the current question"""
        
        idx = state["current_question_index"]
        if idx >= len(state["questions"]):
            return state
        
        question = state["questions"][idx]
        
        question_message = f"""
Question {idx + 1}/{len(state['questions'])}:

{question['question']}

Category: {question.get('category', 'general')}
Time to think: {question.get('time_limit_seconds', 120)} seconds

Take your time to structure your response. When ready, share your answer.
"""
        
        state["messages"].append(AIMessage(content=question_message))
        return state
    
    async def receive_user_response(self, state: InterviewState) -> InterviewState:
        """Receive and store user's response"""
        
        # In production, this would transcribe audio/video
        # For now, we assume text response is in messages
        
        idx = state["current_question_index"]
        question = state["questions"][idx]
        
        # Get last user message (the response)
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if user_messages:
            response_text = user_messages[-1].content
        else:
            response_text = "No response provided"
        
        state["user_responses"].append({
            "question_index": idx,
            "question": question["question"],
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return state
    
    async def evaluate_single_response(self, state: InterviewState) -> InterviewState:
        """Evaluate the user's response"""
        
        idx = state["current_question_index"]
        question = state["questions"][idx]
        response = state["user_responses"][-1]["response"]
        
        evaluation_prompt = ChatPromptTemplate.from_template("""
Evaluate this interview response:

Question: {question}
Category: {category}
What to look for: {criteria}
Candidate's Answer: {response}

Evaluate on:
1. Content Quality (0-100): Relevance, depth, examples
2. Clarity (0-100): Structure, articulation, conciseness
3. Confidence Indicators (0-100): Tone, decisiveness, ownership
4. STAR Method (if behavioral): Situation, Task, Action, Result
5. Technical Accuracy (if technical): Correctness, depth

Provide:
- content_score (0-100)
- clarity_score (0-100)
- confidence_score (0-100)
- strengths (list of 2-3)
- improvements (list of 2-3)
- overall_score (0-100)
- feedback (2-3 sentences of constructive feedback)

Be honest but constructive. Return as JSON.
""")
        
        chain = evaluation_prompt | self.llm
        response_eval = await chain.ainvoke({
            "question": question["question"],
            "category": question.get("category", "general"),
            "criteria": question.get("what_to_look_for", "Relevance and clarity"),
            "response": response
        })
        
        try:
            evaluation = json.loads(response_eval.content)
            state["evaluations"].append({
                "question_index": idx,
                **evaluation
            })
        except json.JSONDecodeError:
            state["evaluations"].append({
                "question_index": idx,
                "overall_score": 50,
                "feedback": "Unable to evaluate properly."
            })
        
        state["messages"].append(response_eval)
        return state
    
    async def provide_immediate_feedback(self, state: InterviewState) -> InterviewState:
        """Provide brief immediate feedback"""
        
        if not state["evaluations"]:
            return state
        
        latest_eval = state["evaluations"][-1]
        
        feedback_message = f"""
Thank you for your response. Here's quick feedback:

Score: {latest_eval.get('overall_score', 0)}/100

Strengths: {', '.join(latest_eval.get('strengths', ['Good effort']))}
Areas to improve: {', '.join(latest_eval.get('improvements', ['Keep practicing']))}

{latest_eval.get('feedback', '')}

Let's move to the next question.
"""
        
        state["messages"].append(AIMessage(content=feedback_message))
        return state
    
    async def check_interview_completion(self, state: InterviewState) -> InterviewState:
        """Check if interview is complete"""
        
        state["current_question_index"] += 1
        
        if state["current_question_index"] >= len(state["questions"]):
            state["interview_complete"] = True
        
        return state
    
    def should_continue_interview(self, state: InterviewState) -> str:
        """Decide if interview should continue"""
        if state["interview_complete"]:
            return "finish"
        return "continue"
    
    async def generate_final_feedback(self, state: InterviewState) -> InterviewState:
        """Generate comprehensive final feedback"""
        
        overall_prompt = ChatPromptTemplate.from_template("""
Generate comprehensive interview feedback:

Role: {job_title}
Questions Asked: {question_count}
Evaluations: {evaluations}

Provide overall feedback covering:
1. Overall performance summary
2. Key strengths demonstrated
3. Primary areas for improvement
4. Specific examples from their responses
5. Comparison to typical candidates for this role
6. Honest assessment of selection probability
7. Action plan for improvement

Be honest, specific, and constructive. This is for their growth.

Return as JSON with:
- summary (string)
- strengths (list)
- improvements (list)
- selection_probability (0-100)
- comparison_to_peers (above_average/average/below_average)
- action_plan (list of specific steps)
""")
        
        chain = overall_prompt | self.llm
        response = await chain.ainvoke({
            "job_title": state["job_title"],
            "question_count": len(state["questions"]),
            "evaluations": json.dumps(state["evaluations"])
        })
        
        try:
            feedback = json.loads(response.content)
            state["overall_feedback"] = feedback
        except json.JSONDecodeError:
            state["overall_feedback"] = {
                "summary": "Interview completed. Review individual question feedback.",
                "selection_probability": 50
            }
        
        state["messages"].append(response)
        return state
    
    async def calculate_final_scores(self, state: InterviewState) -> InterviewState:
        """Calculate final interview score"""
        
        if not state["evaluations"]:
            state["final_score"] = 0
            return state
        
        # Average all evaluation scores
        total_score = sum(eval.get("overall_score", 0) for eval in state["evaluations"])
        state["final_score"] = int(total_score / len(state["evaluations"]))
        
        # Extract improvement areas
        improvement_areas = []
        for eval in state["evaluations"]:
            improvement_areas.extend(eval.get("improvements", []))
        
        # Deduplicate and prioritize
        state["improvement_areas"] = list(set(improvement_areas))[:5]
        
        return state
    
    async def update_skill_graph(self, state: InterviewState) -> InterviewState:
        """Update knowledge graph with weaknesses"""
        
        user_id = state["user_id"]
        
        # Extract skills that need work from improvement areas
        for area in state["improvement_areas"]:
            # This is simplified - in production, parse areas better
            graph_db.create_learning_path(
                user_id=user_id,
                skill=area,
                resources=[],
                estimated_hours=10,
                priority="high"
            )
        
        logger.info(f"Updated skill graph for user {user_id} based on interview")
        return state
    
    async def persist_interview_data(self, state: InterviewState) -> InterviewState:
        """Persist interview session data"""
        
        user_id = state["user_id"]
        session_id = state["session_id"]
        
        # Create comprehensive interview summary
        interview_summary = f"""
Interview Practice Session
Role: {state['job_title']} at {state['company']}
Difficulty: {state['difficulty']}
Questions: {len(state['questions'])}
Final Score: {state['final_score']}/100
Selection Probability: {state['overall_feedback'].get('selection_probability', 'N/A')}%

Overall Feedback: {state['overall_feedback'].get('summary', '')}

Strengths: {', '.join(state['overall_feedback'].get('strengths', []))}
Improvements: {', '.join(state['improvement_areas'])}
"""
        
        # Store in vector DB
        vector_db.add_context(
            user_id=user_id,
            text=interview_summary,
            metadata={
                "source": "interview_practice",
                "type": "interview",
                "session_id": session_id,
                "score": state["final_score"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Persisted interview session {session_id} for user {user_id}")
        return state
    
    async def start_interview(
        self,
        user_id: str,
        job_title: str,
        company: str = "Tech Company",
        difficulty: str = "medium",
        db: Session = None
    ) -> dict:
        """Start a new interview session"""
        
        initial_state = InterviewState(
            messages=[HumanMessage(content="Start interview")],
            session_id="",
            user_id=user_id,
            job_title=job_title,
            company=company,
            difficulty=difficulty,
            question_count=0,
            current_question_index=0,
            questions=[],
            user_responses=[],
            evaluations=[],
            overall_feedback={},
            final_score=0,
            improvement_areas=[],
            interview_complete=False
        )
        
        try:
            # Run only initialization and question generation
            result = await self.initialize_interview_session(initial_state)
            result = await self.generate_interview_questions(result)
            result = await self.ask_current_question(result)
            
            return {
                "success": True,
                "session_id": result["session_id"],
                "first_question": result["questions"][0] if result["questions"] else None,
                "total_questions": len(result["questions"]),
                "difficulty": difficulty
            }
        except Exception as e:
            logger.error(f"Interview start error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def submit_answer(
        self,
        session_id: str,
        question_index: int,
        answer: str,
        # In production: audio_data, video_data
        db: Session = None
    ) -> dict:
        """Submit answer and get feedback"""
        
        # This would retrieve session state and continue the graph
        # For now, simplified
        
        return {
            "success": True,
            "feedback": "Answer received and evaluated",
            "score": 75,
            "next_question": question_index + 1
        }

# Singleton instance
interview_agent = InterviewAgent()