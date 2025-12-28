# backend/app/agents/opportunities_agent.py

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

class OpportunitiesState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    user_skills: List[str]
    user_experience: str
    target_roles: List[str]
    location_preferences: List[str]
    scraped_jobs: List[Dict[str, Any]]
    filtered_jobs: List[Dict[str, Any]]
    scored_jobs: List[Dict[str, Any]]
    top_opportunities: List[Dict[str, Any]]

class OpportunitiesAgent:
    """
    Opportunities Agent with LangGraph
    - Scrapes job/internship platforms
    - Filters by skills, goals, location
    - Scores compatibility
    - Identifies skill gaps
    - Suggests resume modifications
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.3  # Lower temperature for factual matching
        )
        self.graph = self._build_graph()
        
        # Job platforms to scrape
        self.job_platforms = [
            "https://www.linkedin.com/jobs",
            "https://www.indeed.com",
            "https://www.glassdoor.com",
            "https://angel.co",
            "https://www.wellfound.com"
        ]
    
    def _build_graph(self) -> StateGraph:
        """Build opportunities workflow"""
        workflow = StateGraph(OpportunitiesState)
        
        # Add nodes
        workflow.add_node("scrape_jobs", self.scrape_job_platforms)
        workflow.add_node("filter_jobs", self.filter_by_criteria)
        workflow.add_node("score_compatibility", self.score_job_compatibility)
        workflow.add_node("identify_gaps", self.identify_skill_gaps)
        workflow.add_node("rank_opportunities", self.rank_and_prioritize)
        workflow.add_node("suggest_actions", self.suggest_application_actions)
        workflow.add_node("persist_opportunities", self.persist_to_databases)
        
        # Define flow
        workflow.set_entry_point("scrape_jobs")
        workflow.add_edge("scrape_jobs", "filter_jobs")
        workflow.add_edge("filter_jobs", "score_compatibility")
        workflow.add_edge("score_compatibility", "identify_gaps")
        workflow.add_edge("identify_gaps", "rank_opportunities")
        workflow.add_edge("rank_opportunities", "suggest_actions")
        workflow.add_edge("suggest_actions", "persist_opportunities")
        workflow.add_edge("persist_opportunities", END)
        
        return workflow.compile()
    
    async def scrape_job_platforms(self, state: OpportunitiesState) -> OpportunitiesState:
        """Scrape job platforms for opportunities"""
        
        # In production, use Selenium/Playwright for actual scraping
        # For now, we'll simulate with LLM-generated sample data
        
        scrape_prompt = ChatPromptTemplate.from_template("""
Generate 10 realistic job postings for:
Target Roles: {target_roles}
Locations: {locations}

For each job, provide:
- job_id (unique)
- title
- company
- location
- description (brief)
- requirements (list of skills)
- experience_level
- salary_range
- posted_date
- application_url

Return as JSON array.
""")
        
        chain = scrape_prompt | self.llm
        response = await chain.ainvoke({
            "target_roles": ", ".join(state["target_roles"]),
            "locations": ", ".join(state["location_preferences"])
        })
        
        try:
            jobs = json.loads(response.content)
            state["scraped_jobs"] = jobs
        except json.JSONDecodeError:
            state["scraped_jobs"] = []
            logger.error("Failed to parse scraped jobs")
        
        state["messages"].append(response)
        logger.info(f"Scraped {len(state['scraped_jobs'])} jobs")
        
        return state
    
    async def filter_by_criteria(self, state: OpportunitiesState) -> OpportunitiesState:
        """Filter jobs by user criteria"""
        
        filtered_jobs = []
        
        for job in state["scraped_jobs"]:
            # Filter by location
            if state["location_preferences"]:
                job_location = job.get("location", "")
                if not any(pref.lower() in job_location.lower() for pref in state["location_preferences"]):
                    continue
            
            # Filter by experience level
            # Add more sophisticated filtering here
            
            filtered_jobs.append(job)
        
        state["filtered_jobs"] = filtered_jobs
        logger.info(f"Filtered to {len(filtered_jobs)} relevant jobs")
        
        return state
    
    async def score_job_compatibility(self, state: OpportunitiesState) -> OpportunitiesState:
        """Score each job for compatibility"""
        
        scored_jobs = []
        
        for job in state["filtered_jobs"]:
            scoring_prompt = ChatPromptTemplate.from_template("""
Score this job compatibility:

Job: {job_title} at {company}
Requirements: {requirements}
Description: {description}

User Profile:
Skills: {user_skills}
Experience: {user_experience}

Provide:
1. compatibility_score (0-100)
2. matching_skills (list)
3. missing_skills (list)
4. experience_match (good/partial/poor)
5. should_apply (true/false)
6. reason (brief explanation)

Return as JSON.
""")
            
            chain = scoring_prompt | self.llm
            response = await chain.ainvoke({
                "job_title": job.get("title", ""),
                "company": job.get("company", ""),
                "requirements": ", ".join(job.get("requirements", [])),
                "description": job.get("description", ""),
                "user_skills": ", ".join(state["user_skills"]),
                "user_experience": state["user_experience"]
            })
            
            try:
                score_data = json.loads(response.content)
                job["compatibility_score"] = score_data.get("compatibility_score", 0)
                job["matching_skills"] = score_data.get("matching_skills", [])
                job["missing_skills"] = score_data.get("missing_skills", [])
                job["should_apply"] = score_data.get("should_apply", False)
                job["application_reason"] = score_data.get("reason", "")
                
                scored_jobs.append(job)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse score for job {job.get('job_id')}")
        
        state["scored_jobs"] = scored_jobs
        return state
    
    async def identify_skill_gaps(self, state: OpportunitiesState) -> OpportunitiesState:
        """Identify skill gaps for top opportunities"""
        
        # Get top 5 jobs
        top_jobs = sorted(
            state["scored_jobs"], 
            key=lambda x: x.get("compatibility_score", 0), 
            reverse=True
        )[:5]
        
        for job in top_jobs:
            missing_skills = job.get("missing_skills", [])
            
            if missing_skills:
                gap_prompt = ChatPromptTemplate.from_template("""
User is missing these skills for a {job_title} role:
{missing_skills}

For each skill:
1. How critical is it? (critical/important/nice-to-have)
2. How long to learn? (hours/weeks)
3. Best resources (free courses, tutorials)
4. Can they compensate with other skills?

Return as JSON array.
""")
                
                chain = gap_prompt | self.llm
                response = await chain.ainvoke({
                    "job_title": job.get("title", ""),
                    "missing_skills": ", ".join(missing_skills)
                })
                
                try:
                    gap_analysis = json.loads(response.content)
                    job["gap_analysis"] = gap_analysis
                except json.JSONDecodeError:
                    job["gap_analysis"] = []
        
        state["top_opportunities"] = top_jobs
        return state
    
    async def rank_and_prioritize(self, state: OpportunitiesState) -> OpportunitiesState:
        """Rank opportunities by overall value"""
        
        ranking_prompt = ChatPromptTemplate.from_template("""
Rank these job opportunities considering:
- Compatibility score
- Skill gaps
- Career growth potential
- Company reputation

Jobs: {jobs_summary}

Return ranked list with:
- rank (1-5)
- job_id
- priority_reason
- application_urgency (high/medium/low)

Return as JSON array.
""")
        
        jobs_summary = [
            {
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "score": job.get("compatibility_score")
            }
            for job in state["top_opportunities"]
        ]
        
        chain = ranking_prompt | self.llm
        response = await chain.ainvoke({
            "jobs_summary": json.dumps(jobs_summary)
        })
        
        try:
            rankings = json.loads(response.content)
            
            # Apply rankings to jobs
            for ranking in rankings:
                job_id = ranking.get("job_id")
                for job in state["top_opportunities"]:
                    if job.get("job_id") == job_id:
                        job["rank"] = ranking.get("rank")
                        job["priority_reason"] = ranking.get("priority_reason")
                        job["urgency"] = ranking.get("application_urgency")
        except json.JSONDecodeError:
            pass
        
        state["messages"].append(response)
        return state
    
    async def suggest_application_actions(self, state: OpportunitiesState) -> OpportunitiesState:
        """Suggest specific actions for each opportunity"""
        
        for job in state["top_opportunities"]:
            action_prompt = ChatPromptTemplate.from_template("""
For this job application:
Job: {job_title} at {company}
Compatibility: {score}%
Missing Skills: {missing_skills}

Suggest:
1. Resume modifications (which projects to highlight)
2. Cover letter key points
3. Skills to emphasize
4. How to address gaps
5. Interview prep topics

Return as JSON.
""")
            
            chain = action_prompt | self.llm
            response = await chain.ainvoke({
                "job_title": job.get("title", ""),
                "company": job.get("company", ""),
                "score": job.get("compatibility_score", 0),
                "missing_skills": ", ".join(job.get("missing_skills", []))
            })
            
            try:
                actions = json.loads(response.content)
                job["application_actions"] = actions
            except json.JSONDecodeError:
                job["application_actions"] = {}
        
        return state
    
    async def persist_to_databases(self, state: OpportunitiesState) -> OpportunitiesState:
        """Persist opportunities to databases"""
        
        user_id = state["user_id"]
        
        for job in state["top_opportunities"]:
            # Add to knowledge graph
            graph_db.add_job_opportunity(
                job_id=job.get("job_id", ""),
                title=job.get("title", ""),
                company=job.get("company", ""),
                required_skills=job.get("requirements", []),
                user_id=user_id,
                compatibility_score=job.get("compatibility_score", 0)
            )
            
            # Add to vector DB for semantic search
            job_text = f"{job.get('title')} at {job.get('company')}: {job.get('description', '')}"
            vector_db.add_context(
                user_id=user_id,
                text=job_text,
                metadata={
                    "source": "job_opportunity",
                    "type": "job",
                    "job_id": job.get("job_id"),
                    "compatibility": job.get("compatibility_score", 0)
                }
            )
        
        logger.info(f"Persisted {len(state['top_opportunities'])} opportunities for user {user_id}")
        return state
    
    async def scan_opportunities(self, user_id: str, user_profile: dict, db: Session) -> dict:
        """Main entry point to scan for opportunities"""
        
        initial_state = OpportunitiesState(
            messages=[],
            user_id=user_id,
            user_skills=user_profile.get("skills", {}).get("technical", []),
            user_experience=f"{len(user_profile.get('experience', []))} years",
            target_roles=[user_profile.get("targetRole", "Software Engineer")],
            location_preferences=user_profile.get("preferredLocations", []),
            scraped_jobs=[],
            filtered_jobs=[],
            scored_jobs=[],
            top_opportunities=[]
        )
        
        try:
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "opportunities": result["top_opportunities"],
                "total_found": len(result["scraped_jobs"]),
                "total_relevant": len(result["filtered_jobs"]),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Opportunities scan error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
opportunities_agent = OpportunitiesAgent()