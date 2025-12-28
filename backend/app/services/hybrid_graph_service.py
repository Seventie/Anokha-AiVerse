# backend/app/services/hybrid_graph_service.py

"""
Hybrid Graph Service - Bridges user data with global knowledge
Computes on-demand queries for skill gaps, readiness, and learning paths
"""

import logging
from typing import Dict, Any, List, Optional
from app.services.graph_db import get_graph_db
from app.utils.graph_queries import CypherQueries
from app.models.graph_models import SkillGapResult, ReadinessScore

logger = logging.getLogger(__name__)


class HybridGraphService:
    """
    Provides on-demand hybrid graph computations.
    Combines user-specific data with global knowledge.
    """
    
    def __init__(self):
        self.graph_db = get_graph_db()
        self.queries = CypherQueries()
    
    # ========================
    # SKILL GAP ANALYSIS
    # ========================
    
    def analyze_skill_gaps(self, user_id: str, target_role: str) -> SkillGapResult:
        """
        Compute skill gaps for a user targeting a specific role.
        Returns what they have, what they're missing, and recommendations.
        """
        if not self.graph_db.driver:
            return SkillGapResult(
                user_id=user_id,
                target_role=target_role,
                has_skills=[],
                missing_skills=[],
                learning_skills=[],
                match_percentage=0.0,
                recommendations=[]
            )
        
        with self.graph_db.driver.session() as session:
            # Get skills user already has
            user_skills_result = session.run(
                self.queries.GET_USER_SKILLS_FOR_ROLE,
                user_id=user_id,
                job_role=target_role
            )
            has_skills = [
                {
                    "skill": record["skill"],
                    "level": record["level"],
                    "verified": record["verified"]
                }
                for record in user_skills_result
            ]
            
            # Get missing skills
            gap_result = session.run(
                self.queries.GET_SKILL_GAPS,
                user_id=user_id,
                job_role=target_role
            )
            missing_skills = [
                {
                    "skill": record["missing_skill"],
                    "category": record["category"],
                    "description": record["description"]
                }
                for record in gap_result
            ]
            
            # Get skills user is currently learning
            learning_result = session.run(
                """
                MATCH (u:User {id: $user_id})-[r:LEARNING_SKILL]->(s:Skill)
                RETURN s.name as skill, r.progress as progress
                """,
                user_id=user_id
            )
            learning_skills = [
                {
                    "skill": record["skill"],
                    "progress": record["progress"]
                }
                for record in learning_result
            ]
            
            # Get nice-to-have skills
            nice_to_have_result = session.run(
                self.queries.GET_NICE_TO_HAVE_SKILLS,
                job_role=target_role
            )
            nice_to_have = [record["skill"] for record in nice_to_have_result]
            
            # Calculate match percentage
            total_required = len(has_skills) + len(missing_skills)
            match_percentage = (len(has_skills) / total_required * 100) if total_required > 0 else 0
            
            # Generate recommendations
            recommendations = self._generate_skill_recommendations(
                missing_skills, learning_skills, nice_to_have
            )
        
        return SkillGapResult(
            user_id=user_id,
            target_role=target_role,
            has_skills=[s["skill"] for s in has_skills],
            missing_skills=[s["skill"] for s in missing_skills],
            learning_skills=[s["skill"] for s in learning_skills],
            match_percentage=round(match_percentage, 2),
            recommendations=recommendations
        )
    
    def _generate_skill_recommendations(
        self,
        missing_skills: List[Dict],
        learning_skills: List[Dict],
        nice_to_have: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized skill recommendations"""
        recommendations = []
        
        # Prioritize missing core skills
        for skill_info in missing_skills[:5]:  # Top 5 missing
            skill_name = skill_info["skill"]
            
            # Check if already learning
            is_learning = any(s["skill"] == skill_name for s in learning_skills)
            
            # Get prerequisites
            prerequisites = self._get_skill_prerequisites(skill_name)
            
            recommendations.append({
                "skill": skill_name,
                "category": skill_info["category"],
                "priority": "high",
                "reason": "Required for target role",
                "is_learning": is_learning,
                "prerequisites": prerequisites,
                "estimated_hours": self._estimate_learning_hours(skill_info["category"])
            })
        
        return recommendations
    
    def _get_skill_prerequisites(self, skill: str) -> List[str]:
        """Get prerequisites for a skill"""
        if not self.graph_db.driver:
            return []
        
        with self.graph_db.driver.session() as session:
            result = session.run(
                self.queries.GET_PREREQUISITE_CHAIN,
                skill=skill
            )
            return [record["prerequisite"] for record in result]
    
    def _estimate_learning_hours(self, category: str) -> int:
        """Estimate learning hours based on skill category"""
        estimates = {
            "Programming": 40,
            "Theory": 30,
            "Tools": 20,
            "Systems": 50,
            "ML": 60,
            "DevOps": 35,
            "Data": 45,
            "Soft": 15
        }
        return estimates.get(category, 30)
    
    # ========================
    # READINESS SCORING
    # ========================
    
    def calculate_readiness_score(self, user_id: str, job_role: str) -> ReadinessScore:
        """
        Calculate comprehensive readiness score for a job role.
        Considers skills, experience, projects, and more.
        """
        if not self.graph_db.driver:
            return ReadinessScore(
                user_id=user_id,
                job_role=job_role,
                score=0.0,
                skill_coverage=0.0,
                experience_match=0.0,
                project_relevance=0.0,
                recommendations=[],
                ready=False
            )
        
        with self.graph_db.driver.session() as session:
            # 1. Skill Coverage (50% weight)
            coverage_result = session.run(
                self.queries.CALCULATE_READINESS,
                user_id=user_id,
                job_role=job_role
            )
            coverage_record = coverage_result.single()
            
            if not coverage_record:
                skill_coverage = 0.0
                missing_count = 0
            else:
                skill_coverage = coverage_record["coverage_percentage"]
                missing_count = len(coverage_record.get("missing_skills", []))
            
            # 2. Project Relevance (30% weight)
            project_result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:BUILT]->(p:Project)-[:USES]->(s:Skill)
                MATCH (j:JobRole {name: $job_role})-[:REQUIRES]->(s)
                RETURN count(DISTINCT s) as relevant_projects
                """,
                user_id=user_id,
                job_role=job_role
            )
            project_record = project_result.single()
            project_relevance = min((project_record["relevant_projects"] * 10), 100) if project_record else 0
            
            # 3. Experience Match (20% weight)
            # Simplified: Check if user has any experience (can be enhanced)
            exp_result = session.run(
                """
                MATCH (u:User {id: $user_id})
                RETURN u.target_role as target_role
                """,
                user_id=user_id
            )
            exp_record = exp_result.single()
            experience_match = 50.0 if exp_record and exp_record["target_role"] else 30.0
            
            # Calculate weighted score
            total_score = (
                skill_coverage * 0.5 +
                project_relevance * 0.3 +
                experience_match * 0.2
            )
            
            # Generate recommendations
            recommendations = []
            if skill_coverage < 70:
                recommendations.append(f"Focus on building {missing_count} missing core skills")
            if project_relevance < 50:
                recommendations.append("Build more projects using required technologies")
            if experience_match < 40:
                recommendations.append("Gain relevant work experience or internships")
            
            ready = total_score >= 70
        
        return ReadinessScore(
            user_id=user_id,
            job_role=job_role,
            score=round(total_score, 2),
            skill_coverage=round(skill_coverage, 2),
            experience_match=round(experience_match, 2),
            project_relevance=round(project_relevance, 2),
            recommendations=recommendations,
            ready=ready
        )
    
    # ========================
    # LEARNING PATH GENERATION
    # ========================
    
    def generate_learning_plan(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate personalized learning plan based on career goals.
        Returns skills to learn with resources and prerequisites.
        """
        if not self.graph_db.driver:
            return []
        
        with self.graph_db.driver.session() as session:
            result = session.run(
                self.queries.GET_LEARNING_RECOMMENDATIONS,
                user_id=user_id
            )
            
            learning_plan = []
            for record in result:
                skill = record["skill"]
                category = record["category"]
                resources = record["resources"]
                
                # Get prerequisites
                prerequisites = self._get_skill_prerequisites(skill)
                
                # Check if prerequisites are met
                prereqs_met = self._check_prerequisites_met(user_id, prerequisites)
                
                learning_plan.append({
                    "skill": skill,
                    "category": category,
                    "priority": "high" if len(prerequisites) == 0 else "medium",
                    "prerequisites": prerequisites,
                    "prerequisites_met": prereqs_met,
                    "resources": resources[:3],  # Top 3 resources
                    "estimated_hours": self._estimate_learning_hours(category),
                    "can_start_now": prereqs_met
                })
            
            # Sort by priority (prerequisites met first)
            learning_plan.sort(key=lambda x: (not x["prerequisites_met"], len(x["prerequisites"])))
        
        return learning_plan[:limit]
    
    def _check_prerequisites_met(self, user_id: str, prerequisites: List[str]) -> bool:
        """Check if user has all prerequisites"""
        if not prerequisites:
            return True
        
        if not self.graph_db.driver:
            return False
        
        with self.graph_db.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:HAS_SKILL]->(s:Skill)
                WHERE s.name IN $prerequisites
                RETURN count(s) as count
                """,
                user_id=user_id,
                prerequisites=prerequisites
            )
            record = result.single()
            return record["count"] == len(prerequisites) if record else False
    
    # ========================
    # CAREER PATH EXPLORATION
    # ========================
    
    def explore_career_paths(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Explore possible career paths from current skills.
        Shows roles user could transition to with minimal skill gaps.
        """
        if not self.graph_db.driver:
            return []
        
        with self.graph_db.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:HAS_SKILL]->(s:Skill)
                MATCH (j:JobRole)-[:REQUIRES]->(s)
                WITH j, count(s) as matched_skills
                MATCH (j)-[:REQUIRES]->(all_skills:Skill)
                WITH j, matched_skills, count(all_skills) as total_required
                WHERE matched_skills * 100.0 / total_required >= 30
                RETURN j.name as role,
                       j.industry as industry,
                       matched_skills,
                       total_required,
                       matched_skills * 100.0 / total_required as match_percentage
                ORDER BY match_percentage DESC
                LIMIT 10
                """,
                user_id=user_id
            )
            
            paths = []
            for record in result:
                role = record["role"]
                
                # Get missing skills for this role
                gap_result = self.analyze_skill_gaps(user_id, role)
                
                paths.append({
                    "role": role,
                    "industry": record["industry"],
                    "match_percentage": round(record["match_percentage"], 2),
                    "matched_skills": record["matched_skills"],
                    "total_required": record["total_required"],
                    "missing_skills_count": len(gap_result.missing_skills),
                    "missing_skills": gap_result.missing_skills[:5],  # Top 5 gaps
                    "feasibility": "high" if record["match_percentage"] >= 70 else "medium"
                })
        
        return paths
    
    # ========================
    # SKILL RECOMMENDATION ENGINE
    # ========================
    
    def recommend_next_skills(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend next skills to learn based on:
        - Current skills
        - Career goals
        - Market demand
        - Prerequisites met
        """
        if not self.graph_db.driver:
            return []
        
        with self.graph_db.driver.session() as session:
            # Get skills related to what user already knows
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:HAS_SKILL]->(current:Skill)
                MATCH (current)-[:RELATED_TO]->(related:Skill)
                WHERE NOT EXISTS {
                    MATCH (u)-[:HAS_SKILL]->(related)
                }
                WITH related, count(*) as relevance_score
                
                // Check if user has prerequisites
                OPTIONAL MATCH (prereq:Skill)-[:PREREQUISITE_OF]->(related)
                OPTIONAL MATCH (u)-[:HAS_SKILL]->(prereq)
                WITH related, relevance_score, 
                     collect(prereq.name) as prereqs,
                     count(prereq) as total_prereqs
                
                // Get resources
                OPTIONAL MATCH (r:Resource)-[:TEACHES]->(related)
                WITH related, relevance_score, prereqs, total_prereqs,
                     collect({title: r.title, type: r.resource_type, url: r.url}) as resources
                
                RETURN related.name as skill,
                       related.category as category,
                       related.description as description,
                       relevance_score,
                       prereqs,
                       total_prereqs,
                       resources
                ORDER BY relevance_score DESC, total_prereqs ASC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit
            )
            
            recommendations = []
            for record in result:
                recommendations.append({
                    "skill": record["skill"],
                    "category": record["category"],
                    "description": record["description"],
                    "relevance_score": record["relevance_score"],
                    "prerequisites": record["prereqs"],
                    "resources": record["resources"][:3],
                    "estimated_hours": self._estimate_learning_hours(record["category"])
                })
        
        return recommendations
    
    # ========================
    # MARKET INSIGHTS
    # ========================
    
    def get_market_insights(self, skill: str) -> Dict[str, Any]:
        """
        Get market insights for a skill:
        - Which roles require it
        - Related skills
        - Learning resources
        """
        if not self.graph_db.driver:
            return {}
        
        with self.graph_db.driver.session() as session:
            # Roles requiring this skill
            roles_result = session.run(
                """
                MATCH (j:JobRole)-[:REQUIRES]->(s:Skill {name: $skill})
                RETURN j.name as role, j.industry as industry
                """,
                skill=skill
            )
            roles = [{"role": r["role"], "industry": r["industry"]} for r in roles_result]
            
            # Related skills
            related_result = session.run(
                """
                MATCH (s:Skill {name: $skill})-[:RELATED_TO]->(related:Skill)
                RETURN related.name as skill
                LIMIT 10
                """,
                skill=skill
            )
            related_skills = [r["skill"] for r in related_result]
            
            # Prerequisites
            prereq_result = session.run(
                """
                MATCH (prereq:Skill)-[:PREREQUISITE_OF]->(s:Skill {name: $skill})
                RETURN prereq.name as skill
                """,
                skill=skill
            )
            prerequisites = [r["skill"] for r in prereq_result]
            
            # Resources
            resource_result = session.run(
                """
                MATCH (r:Resource)-[:TEACHES]->(s:Skill {name: $skill})
                RETURN r.title as title, r.resource_type as type, r.url as url
                """,
                skill=skill
            )
            resources = [
                {"title": r["title"], "type": r["type"], "url": r["url"]}
                for r in resource_result
            ]
        
        return {
            "skill": skill,
            "roles_requiring": roles,
            "related_skills": related_skills,
            "prerequisites": prerequisites,
            "resources": resources,
            "demand_level": "high" if len(roles) >= 5 else "medium"
        }


# Singleton instance
_hybrid_graph_service: Optional[HybridGraphService] = None

def get_hybrid_graph_service() -> HybridGraphService:
    """Get singleton HybridGraphService instance"""
    global _hybrid_graph_service
    if _hybrid_graph_service is None:
        _hybrid_graph_service = HybridGraphService()
    return _hybrid_graph_service
