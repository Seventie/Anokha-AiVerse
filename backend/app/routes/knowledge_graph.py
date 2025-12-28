# backend/app/routes/knowledge_graph.py

"""
Knowledge Graph API Routes
Provides access to all graph queries and hybrid computations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.config.database import get_db
from app.services.hybrid_graph_service import get_hybrid_graph_service
from app.services.user_graph_sync import get_user_graph_sync
from app.services.graph_db import get_graph_db
from app.schemas.graph_schemas import (
    SkillGapResponse,
    ReadinessResponse,
    LearningPlanResponse,
    CareerPathResponse,
    SkillRecommendationsResponse,
    MarketInsightResponse,
    SyncResponse,
    GraphStatsResponse,
    SkillInfo,
    JobRoleInfo,
    LearningPathItem
)
from app.utils.graph_queries import CypherQueries
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])

# ========================
# STATIC DATA ENDPOINTS
# ========================

@router.get("/skills", response_model=List[SkillInfo])
async def get_all_skills(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all skills from the knowledge graph"""
    graph_db = get_graph_db()
    queries = CypherQueries()
    
    with graph_db.driver.session() as session:
        if category:
            result = session.run(
                """
                MATCH (s:Skill {category: $category})
                RETURN s.name as name, s.category as category, s.description as description
                ORDER BY s.name
                LIMIT $limit
                """,
                category=category,
                limit=limit
            )
        else:
            result = session.run(queries.GET_ALL_SKILLS)
        
        skills = [
            SkillInfo(
                name=record["name"],
                category=record["category"],
                description=record.get("description")
            )
            for record in result
        ]
    
    return skills


@router.get("/roles", response_model=List[JobRoleInfo])
async def get_all_roles(
    industry: Optional[str] = Query(None, description="Filter by industry")
):
    """Get all job roles from the knowledge graph"""
    graph_db = get_graph_db()
    queries = CypherQueries()
    
    with graph_db.driver.session() as session:
        if industry:
            result = session.run(
                """
                MATCH (j:JobRole {industry: $industry})
                RETURN j.name as name, j.industry as industry, j.seniority_levels as seniority_levels
                ORDER BY j.name
                """,
                industry=industry
            )
        else:
            result = session.run(queries.GET_ALL_JOB_ROLES)
        
        roles = [
            JobRoleInfo(
                name=record["name"],
                industry=record["industry"],
                seniority_levels=record["seniority_levels"]
            )
            for record in result
        ]
    
    return roles


@router.get("/role/{role_name}/skills")
async def get_role_skills(role_name: str):
    """Get all skills required for a specific role"""
    graph_db = get_graph_db()
    
    with graph_db.driver.session() as session:
        # Core skills
        core_result = session.run(
            """
            MATCH (j:JobRole {name: $role_name})-[:REQUIRES]->(s:Skill)
            RETURN s.name as skill, s.category as category
            ORDER BY s.category, s.name
            """,
            role_name=role_name
        )
        core_skills = [{"skill": r["skill"], "category": r["category"]} for r in core_result]
        
        # Nice-to-have skills
        optional_result = session.run(
            """
            MATCH (j:JobRole {name: $role_name})-[:NICE_TO_HAVE]->(s:Skill)
            RETURN s.name as skill, s.category as category
            ORDER BY s.category, s.name
            """,
            role_name=role_name
        )
        optional_skills = [{"skill": r["skill"], "category": r["category"]} for r in optional_result]
    
    return {
        "role": role_name,
        "core_skills": core_skills,
        "nice_to_have_skills": optional_skills,
        "total_core": len(core_skills),
        "total_optional": len(optional_skills)
    }


# ========================
# HYBRID GRAPH ENDPOINTS
# ========================

@router.get("/skill-gaps/{user_id}", response_model=SkillGapResponse)
async def get_skill_gaps(
    user_id: str,
    target_role: str = Query(..., description="Target job role")
):
    """
    Analyze skill gaps for a user targeting a specific role.
    Shows what skills they have, what's missing, and recommendations.
    """
    hybrid_service = get_hybrid_graph_service()
    
    try:
        result = hybrid_service.analyze_skill_gaps(user_id, target_role)
        
        return SkillGapResponse(
            user_id=result.user_id,
            target_role=result.target_role,
            has_skills=result.has_skills,
            missing_skills=result.missing_skills,
            learning_skills=result.learning_skills,
            match_percentage=result.match_percentage,
            recommendations=result.recommendations
        )
    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze skill gaps: {str(e)}"
        )


@router.get("/readiness/{user_id}", response_model=ReadinessResponse)
async def calculate_readiness(
    user_id: str,
    job_role: str = Query(..., description="Job role to check readiness for")
):
    """
    Calculate job readiness score for a user.
    Considers skills, projects, and experience.
    """
    hybrid_service = get_hybrid_graph_service()
    
    try:
        result = hybrid_service.calculate_readiness_score(user_id, job_role)
        
        return ReadinessResponse(
            user_id=result.user_id,
            job_role=result.job_role,
            overall_score=result.score,
            skill_coverage=result.skill_coverage,
            experience_match=result.experience_match,
            project_relevance=result.project_relevance,
            ready=result.ready,
            recommendations=result.recommendations
        )
    except Exception as e:
        logger.error(f"Error calculating readiness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate readiness: {str(e)}"
        )


@router.get("/learning-plan/{user_id}", response_model=LearningPlanResponse)
async def get_learning_plan(
    user_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Generate personalized learning plan based on career goals.
    Returns prioritized skills with resources and prerequisites.
    """
    hybrid_service = get_hybrid_graph_service()
    
    try:
        plan = hybrid_service.generate_learning_plan(user_id, limit)
        
        learning_path = [
            LearningPathItem(
                skill=item["skill"],
                category=item["category"],
                priority=item["priority"],
                prerequisites=item["prerequisites"],
                prerequisites_met=item["prerequisites_met"],
                resources=item["resources"],
                estimated_hours=item["estimated_hours"],
                can_start_now=item["can_start_now"]
            )
            for item in plan
        ]
        
        total_hours = sum(item["estimated_hours"] for item in plan)
        
        return LearningPlanResponse(
            user_id=user_id,
            learning_path=learning_path,
            total_estimated_hours=total_hours
        )
    except Exception as e:
        logger.error(f"Error generating learning plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning plan: {str(e)}"
        )


@router.get("/career-paths/{user_id}", response_model=CareerPathResponse)
async def explore_career_paths(user_id: str):
    """
    Explore possible career paths based on current skills.
    Shows roles user could transition to with minimal skill gaps.
    """
    hybrid_service = get_hybrid_graph_service()
    
    try:
        paths = hybrid_service.explore_career_paths(user_id)
        
        return CareerPathResponse(
            user_id=user_id,
            possible_paths=paths
        )
    except Exception as e:
        logger.error(f"Error exploring career paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explore career paths: {str(e)}"
        )


@router.get("/recommendations/{user_id}", response_model=SkillRecommendationsResponse)
async def get_skill_recommendations(
    user_id: str,
    limit: int = Query(5, ge=1, le=20)
):
    """
    Get personalized skill recommendations based on current skills and goals.
    """
    hybrid_service = get_hybrid_graph_service()
    
    try:
        recommendations = hybrid_service.recommend_next_skills(user_id, limit)
        
        return SkillRecommendationsResponse(
            user_id=user_id,
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/market-insights/{skill}", response_model=MarketInsightResponse)
async def get_market_insights(skill: str):
    """
    Get market insights for a specific skill.
    Shows which roles require it, related skills, and resources.
    """
    hybrid_service = get_hybrid_graph_service()
    
    try:
        insights = hybrid_service.get_market_insights(skill)
        
        return MarketInsightResponse(**insights)
    except Exception as e:
        logger.error(f"Error getting market insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market insights: {str(e)}"
        )


# ========================
# USER SYNC ENDPOINTS
# ========================

@router.post("/sync-user/{user_id}", response_model=SyncResponse)
async def sync_user_to_graph(
    user_id: str,
    force: bool = Query(False, description="Force re-sync even if already synced"),
    db: Session = Depends(get_db)
):
    """
    Synchronize user data from SQL to Neo4j.
    Creates user node and all relationships.
    """
    sync_service = get_user_graph_sync()
    
    try:
        results = sync_service.sync_complete_user(user_id, db)
        
        return SyncResponse(
            user_id=user_id,
            success=True,
            synced_entities=results,
            message=f"Successfully synced user {user_id}"
        )
    except Exception as e:
        logger.error(f"Error syncing user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync user: {str(e)}"
        )


@router.get("/stats", response_model=GraphStatsResponse)
async def get_graph_statistics():
    """Get overall graph statistics"""
    graph_db = get_graph_db()
    
    with graph_db.driver.session() as session:
        # Count nodes by type
        node_counts = {}
        for node_type in ["User", "JobRole", "Skill", "Resource", "Project", "Interview"]:
            result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
            node_counts[node_type] = result.single()["count"]
        
        # Count relationships
        rel_counts = {}
        for rel_type in ["REQUIRES", "HAS_SKILL", "ASPIRES_TO", "BUILT", "TEACHES"]:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
            rel_counts[rel_type] = result.single()["count"]
    
    return GraphStatsResponse(
        total_nodes=node_counts,
        total_relationships=rel_counts,
        user_nodes=node_counts.get("User", 0),
        static_nodes=node_counts.get("JobRole", 0) + node_counts.get("Skill", 0) + node_counts.get("Resource", 0)
    )
