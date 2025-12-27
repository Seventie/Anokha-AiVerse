"""Project Generator Agent - Generates resume-worthy project ideas"""

from typing import Any, Dict, List
from .base_agent import BaseAgent
from datetime import datetime


class ProjectGeneratorAgent(BaseAgent):
    """Agent that generates project ideas aligned with career goals"""
    
    async def execute(
        self,
        user_id: str,
        target_skills: List[str],
        target_role: str,
        experience_level: str = "intermediate",
        project_timeline_weeks: int = 8,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate project ideas for resume building
        
        Args:
            user_id: User identifier
            target_skills: Skills to demonstrate
            target_role: Target job role
            experience_level: User's current level (beginner, intermediate, advanced)
            project_timeline_weeks: Weeks available for project
            
        Returns:
            Dict containing project recommendations
        """
        self.log_execution(f"Project Generation for {target_role}", "processing")
        
        skills_text = ", ".join(target_skills) if target_skills else "Various skills"
        
        system_prompt = """You are an expert technical project mentor with experience in portfolio building, 
resume optimization, and demonstrating technical expertise. Generate practical, achievable projects that showcase skills.
Respond ONLY with valid JSON, no other text."""
        
        user_message = f"""Generate 3-5 resume-worthy project ideas for someone targeting a {target_role} role.

Project Context:
- Skills to Demonstrate: {skills_text}
- Experience Level: {experience_level}
- Timeline Available: {project_timeline_weeks} weeks

Provide a JSON response with this EXACT structure:
{{
    "projects": [
        {{
            "project_id": 1,
            "title": "Project Name",
            "description": "Brief description",
            "difficulty_level": "intermediate",
            "skills_demonstrated": ["skill1", "skill2"],
            "tech_stack": ["tech1", "tech2"],
            "estimated_duration_weeks": 6,
            "estimated_hours_per_week": 10,
            "project_objectives": [
                {{
                    "objective": "Build X functionality",
                    "why_matters": "Demonstrates Y skill for Z role"
                }}
            ],
            "scope": {{
                "features": ["feature1", "feature2"],
                "out_of_scope": ["feature3"],
                "mvp_timeline_weeks": 4,
                "extended_features": ["advanced_feature1"]
            }},
            "why_recruiters_love_it": "Specific explanation",
            "portfolio_impact": "How it strengthens resume",
            "learning_outcomes": ["outcome1", "outcome2"],
            "github_repo_structure": {
                "setup_complexity": "moderate",
                "documentation_needs": ["README", "API docs"],
                "deployment_example": "Example deployment setup"
            }},
            "variations_for_different_levels": {{
                "beginner": "Simplified scope",
                "intermediate": "Standard scope",
                "advanced": "Extended scope with additional features"
            }},
            "interview_talking_points": [
                "Technical decision #1",
                "Challenge overcome: ...",
                "Architectural choice: ..."
            ]
        }}
    ],
    "portfolio_strategy": {{
        "overall_approach": "How these projects work together",
        "timeline_for_all_projects": "Suggested order and timing",
        "complementary_skills": ["skill1", "skill2"],
        "github_profile_setup": "Tips for profile optimization",
        "blog_articles_to_write": ["Article 1", "Article 2"],
        "open_source_contributions": "Suggested open source projects to contribute to"
    }},
    "success_metrics": {{
        "recruiter_interview_signal": "What will trigger recruiter interest",
        "technical_interview_prep": "How this prepares for interviews",
        "compensation_impact": "Expected impact on offers"
    }},
    "next_steps": ["Step 1", "Step 2", "Step 3"]
}}"""
        
        try:
            result = self.call_claude_json(
                system_prompt,
                user_message,
                temperature=0.7,
                max_tokens=4500
            )
            
            self.log_execution(
                f"Project Generation for {target_role}",
                "success",
                {"projects_count": len(result.get('projects', []))}
            )
            
            return {
                "user_id": user_id,
                "projects": result,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.log_execution(f"Project Generation for {target_role}", "error", {"error": str(e)})
            raise
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current ISO timestamp"""
        return datetime.utcnow().isoformat()
