# backend/app/agents/resume_agent.py

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
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ResumeState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    resume_text: str
    job_description: str
    user_profile: dict
    resume_score: int
    strengths: List[str]
    weaknesses: List[str]
    keyword_gaps: List[str]
    ats_analysis: dict
    optimization_suggestions: List[dict]
    tailored_resume: str
    gap_to_roadmap: List[dict]

class ResumeAgent:
    """
    Resume Intelligence Agent with LangGraph
    - Scores resume against target roles
    - Compares resume vs job descriptions
    - Detects gaps (skills, experience, keywords)
    - Suggests precise edits
    - Auto-generates improved resume versions
    - Converts gaps to roadmap tasks
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.3
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build resume analysis workflow"""
        workflow = StateGraph(ResumeState)
        
        # Add nodes
        workflow.add_node("parse_resume", self.parse_resume_content)
        workflow.add_node("score_resume", self.score_overall_quality)
        workflow.add_node("analyze_ats", self.analyze_ats_compatibility)
        workflow.add_node("compare_job", self.compare_with_job_description)
        workflow.add_node("identify_gaps", self.identify_keyword_gaps)
        workflow.add_node("suggest_improvements", self.generate_improvements)
        workflow.add_node("optimize_resume", self.optimize_for_job)
        workflow.add_node("create_roadmap_tasks", self.convert_gaps_to_tasks)
        workflow.add_node("persist_analysis", self.persist_resume_data)
        
        # Define flow
        workflow.set_entry_point("parse_resume")
        workflow.add_edge("parse_resume", "score_resume")
        workflow.add_edge("score_resume", "analyze_ats")
        workflow.add_conditional_edges(
            "analyze_ats",
            self.should_compare_job,
            {
                "compare": "compare_job",
                "skip": "suggest_improvements"
            }
        )
        workflow.add_edge("compare_job", "identify_gaps")
        workflow.add_edge("identify_gaps", "suggest_improvements")
        workflow.add_edge("suggest_improvements", "optimize_resume")
        workflow.add_edge("optimize_resume", "create_roadmap_tasks")
        workflow.add_edge("create_roadmap_tasks", "persist_analysis")
        workflow.add_edge("persist_analysis", END)
        
        return workflow.compile()
    
    async def parse_resume_content(self, state: ResumeState) -> ResumeState:
        """Parse and extract key sections from resume"""
        
        parse_prompt = ChatPromptTemplate.from_template("""
Parse this resume and extract key information:

Resume:
{resume_text}

Extract:
1. Contact information
2. Summary/Objective
3. Work experience (with dates, roles, companies)
4. Education
5. Skills (technical and soft)
6. Projects
7. Certifications
8. Keywords present

Return as structured JSON.
""")
        
        chain = parse_prompt | self.llm
        response = await chain.ainvoke({
            "resume_text": state["resume_text"]
        })
        
        state["messages"].append(response)
        logger.info(f"Parsed resume for user {state['user_id']}")
        
        return state
    
    async def score_overall_quality(self, state: ResumeState) -> ResumeState:
        """Score resume quality (0-100)"""
        
        scoring_prompt = ChatPromptTemplate.from_template("""
Evaluate this resume on a scale of 0-100:

Resume:
{resume_text}

Criteria:
1. Format and readability (20 points)
2. Content quality (30 points)
3. Achievement quantification (20 points)
4. Keywords and industry terms (15 points)
5. Grammar and professionalism (15 points)

Provide:
- overall_score (0-100)
- category_scores (dict)
- top_3_strengths (list)
- top_3_weaknesses (list)
- immediate_fixes (list)

Return as JSON.
""")
        
        chain = scoring_prompt | self.llm
        response = await chain.ainvoke({
            "resume_text": state["resume_text"]
        })
        
        try:
            score_data = json.loads(response.content)
            state["resume_score"] = score_data.get("overall_score", 0)
            state["strengths"] = score_data.get("top_3_strengths", [])
            state["weaknesses"] = score_data.get("top_3_weaknesses", [])
        except json.JSONDecodeError:
            state["resume_score"] = 50
            state["strengths"] = []
            state["weaknesses"] = []
        
        state["messages"].append(response)
        return state
    
    async def analyze_ats_compatibility(self, state: ResumeState) -> ResumeState:
        """Analyze ATS (Applicant Tracking System) compatibility"""
        
        ats_prompt = ChatPromptTemplate.from_template("""
Analyze this resume for ATS (Applicant Tracking System) compatibility:

Resume:
{resume_text}

Check:
1. Formatting issues (tables, columns, headers/footers)
2. Font readability
3. Section headers clarity
4. Keyword density
5. File format compatibility
6. Contact information parseability

Provide:
- ats_score (0-100)
- format_issues (list)
- parsing_warnings (list)
- optimization_tips (list)

Return as JSON.
""")
        
        chain = ats_prompt | self.llm
        response = await chain.ainvoke({
            "resume_text": state["resume_text"]
        })
        
        try:
            ats_data = json.loads(response.content)
            state["ats_analysis"] = ats_data
        except json.JSONDecodeError:
            state["ats_analysis"] = {"ats_score": 50}
        
        state["messages"].append(response)
        return state
    
    def should_compare_job(self, state: ResumeState) -> str:
        """Decide if we should compare with job description"""
        if state.get("job_description"):
            return "compare"
        return "skip"
    
    async def compare_with_job_description(self, state: ResumeState) -> ResumeState:
        """Compare resume against specific job description"""
        
        comparison_prompt = ChatPromptTemplate.from_template("""
Compare this resume with the job description:

Resume:
{resume_text}

Job Description:
{job_description}

Analyze:
1. Matching skills and experience
2. Missing required qualifications
3. Keyword alignment
4. Experience level match
5. Cultural fit indicators
6. Relevance score (0-100)

Provide detailed comparison as JSON.
""")
        
        chain = comparison_prompt | self.llm
        response = await chain.ainvoke({
            "resume_text": state["resume_text"],
            "job_description": state["job_description"]
        })
        
        state["messages"].append(response)
        return state
    
    async def identify_keyword_gaps(self, state: ResumeState) -> ResumeState:
        """Identify missing keywords from job description"""
        
        if not state.get("job_description"):
            state["keyword_gaps"] = []
            return state
        
        gap_prompt = ChatPromptTemplate.from_template("""
Identify missing keywords and phrases:

Job Description:
{job_description}

Current Resume:
{resume_text}

Find:
1. Critical keywords in job description but missing in resume
2. Skills mentioned in JD but not in resume
3. Industry terms and buzzwords to add
4. Action verbs to incorporate

Prioritize by importance (critical/important/nice-to-have).

Return as JSON array of:
{{
  "keyword": "string",
  "importance": "critical|important|nice-to-have",
  "suggestion": "how to incorporate"
}}
""")
        
        chain = gap_prompt | self.llm
        response = await chain.ainvoke({
            "job_description": state["job_description"],
            "resume_text": state["resume_text"]
        })
        
        try:
            gaps = json.loads(response.content)
            state["keyword_gaps"] = gaps if isinstance(gaps, list) else []
        except json.JSONDecodeError:
            state["keyword_gaps"] = []
        
        state["messages"].append(response)
        return state
    
    async def generate_improvements(self, state: ResumeState) -> ResumeState:
        """Generate specific improvement suggestions"""
        
        improvement_prompt = ChatPromptTemplate.from_template("""
Based on the analysis, provide specific improvements:

Current Resume Score: {score}/100
Weaknesses: {weaknesses}
ATS Issues: {ats_issues}
Keyword Gaps: {keyword_gaps}

For each improvement:
1. Section to modify
2. Current text (if applicable)
3. Suggested replacement
4. Reasoning
5. Impact (high/medium/low)

Provide 5-10 actionable improvements as JSON array.
""")
        
        chain = improvement_prompt | self.llm
        response = await chain.ainvoke({
            "score": state.get("resume_score", 0),
            "weaknesses": ", ".join(state.get("weaknesses", [])),
            "ats_issues": json.dumps(state.get("ats_analysis", {})),
            "keyword_gaps": json.dumps(state.get("keyword_gaps", []))
        })
        
        try:
            improvements = json.loads(response.content)
            state["optimization_suggestions"] = improvements if isinstance(improvements, list) else []
        except json.JSONDecodeError:
            state["optimization_suggestions"] = []
        
        state["messages"].append(response)
        return state
    
    async def optimize_for_job(self, state: ResumeState) -> ResumeState:
        """Generate optimized resume version"""
        
        if not state.get("job_description"):
            state["tailored_resume"] = state["resume_text"]
            return state
        
        optimization_prompt = ChatPromptTemplate.from_template("""
Rewrite this resume to optimize for the job description:

Original Resume:
{resume_text}

Job Description:
{job_description}

Improvements to Apply:
{improvements}

Guidelines:
1. Reorder bullets to prioritize relevant experience
2. Incorporate missing keywords naturally
3. Quantify achievements where possible
4. Highlight matching skills prominently
5. Maintain truthfulness - don't fabricate
6. Keep same overall structure
7. Optimize for ATS parsing

Generate the improved resume text.
""")
        
        chain = optimization_prompt | self.llm
        response = await chain.ainvoke({
            "resume_text": state["resume_text"],
            "job_description": state["job_description"],
            "improvements": json.dumps(state.get("optimization_suggestions", []))
        })
        
        state["tailored_resume"] = response.content
        state["messages"].append(response)
        
        return state
    
    async def convert_gaps_to_tasks(self, state: ResumeState) -> ResumeState:
        """Convert skill gaps into actionable roadmap tasks"""
        
        task_prompt = ChatPromptTemplate.from_template("""
Convert these gaps into learning tasks:

Keyword Gaps: {keyword_gaps}
Missing Skills: {weaknesses}

For each gap that represents a learnable skill:
1. Task title
2. Description
3. Estimated time to learn
4. Resources (courses, tutorials)
5. Priority
6. How it improves resume

Return as JSON array of tasks.
""")
        
        chain = task_prompt | self.llm
        response = await chain.ainvoke({
            "keyword_gaps": json.dumps(state.get("keyword_gaps", [])),
            "weaknesses": ", ".join(state.get("weaknesses", []))
        })
        
        try:
            tasks = json.loads(response.content)
            state["gap_to_roadmap"] = tasks if isinstance(tasks, list) else []
        except json.JSONDecodeError:
            state["gap_to_roadmap"] = []
        
        state["messages"].append(response)
        return state
    
    async def persist_resume_data(self, state: ResumeState) -> ResumeState:
        """Persist analysis to databases"""
        
        user_id = state["user_id"]
        
        # Store in vector DB for semantic search
        analysis_text = f"Resume analysis: Score {state['resume_score']}/100. Strengths: {', '.join(state['strengths'])}. Weaknesses: {', '.join(state['weaknesses'])}."
        
        vector_db.add_context(
            user_id=user_id,
            text=analysis_text,
            metadata={
                "source": "resume_analysis",
                "type": "resume",
                "score": state["resume_score"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Store tailored resume
        if state.get("tailored_resume"):
            vector_db.add_context(
                user_id=user_id,
                text=state["tailored_resume"],
                metadata={
                    "source": "optimized_resume",
                    "type": "resume",
                    "generated": True,
                    "confidence": 0.85
                }
            )
        
        # Add gap tasks to knowledge graph
        for task in state.get("gap_to_roadmap", []):
            if "skill" in task or "title" in task:
                skill_name = task.get("skill") or task.get("title", "Unknown")
                graph_db.create_learning_path(
                    user_id=user_id,
                    skill=skill_name,
                    resources=task.get("resources", []),
                    estimated_hours=task.get("estimated_time", 20),
                    priority="high"
                )
        
        logger.info(f"Persisted resume analysis for user {user_id}")
        return state
    
    async def analyze_resume(
        self,
        user_id: str,
        resume_text: str,
        user_profile: dict,
        job_description: str = None,
        db: Session = None
    ) -> dict:
        """Main entry point to analyze resume"""
        
        initial_state = ResumeState(
            messages=[],
            user_id=user_id,
            resume_text=resume_text,
            job_description=job_description or "",
            user_profile=user_profile,
            resume_score=0,
            strengths=[],
            weaknesses=[],
            keyword_gaps=[],
            ats_analysis={},
            optimization_suggestions=[],
            tailored_resume="",
            gap_to_roadmap=[]
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "resume_score": result["resume_score"],
                "strengths": result["strengths"],
                "weaknesses": result["weaknesses"],
                "ats_analysis": result["ats_analysis"],
                "keyword_gaps": result["keyword_gaps"],
                "suggestions": result["optimization_suggestions"],
                "optimized_resume": result["tailored_resume"],
                "learning_tasks": result["gap_to_roadmap"],
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Resume analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
resume_agent = ResumeAgent()