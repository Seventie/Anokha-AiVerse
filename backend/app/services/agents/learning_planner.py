"""Learning Planner Agent - Creates personalized learning paths"""

from typing import Any, Dict, List
from .base_agent import BaseAgent
from datetime import datetime


class LearningPlannerAgent(BaseAgent):
    """Agent that creates personalized learning plans"""
    
    async def execute(
        self,
        user_id: str,
        skill_gaps: List[Dict[str, Any]],
        learning_style: str = "mixed",
        time_commitment_hours_per_week: int = 10,
        target_completion_months: int = 6,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a personalized learning plan based on skill gaps
        
        Args:
            user_id: User identifier
            skill_gaps: List of skill gaps to address
            learning_style: User's learning preference (visual, hands-on, reading, mixed)
            time_commitment_hours_per_week: Hours available per week
            target_completion_months: Desired completion timeline
            
        Returns:
            Dict containing learning plan
        """
        self.log_execution(f"Learning Plan Generation", "processing")
        
        gaps_text = self._format_gaps(skill_gaps)
        
        system_prompt = f"""You are an expert learning design specialist with deep knowledge of curriculum design, 
metacognition, and skill development. Create detailed, practical learning plans that are adaptive and evidence-based.
Respond ONLY with valid JSON, no other text."""
        
        user_message = f"""Create a detailed learning plan for the following skill gaps:
{gaps_text}

Learning Profile:
- Learning Style: {learning_style}
- Time Commitment: {time_commitment_hours_per_week} hours/week
- Target Timeline: {target_completion_months} months

Provide a JSON response with this EXACT structure:
{{
    "learning_plan": {{
        "title": "Customized Learning Path",
        "total_duration_months": {target_completion_months},
        "weekly_commitment_hours": {time_commitment_hours_per_week},
        "phases": [
            {{
                "phase_number": 1,
                "phase_name": "Foundation Phase",
                "duration_weeks": 4,
                "skills_covered": ["skill1", "skill2"],
                "learning_objectives": ["objective1", "objective2"],
                "resources": [
                    {{
                        "type": "course",
                        "title": "Course Title",
                        "platform": "Platform Name",
                        "duration_hours": 20,
                        "difficulty": "beginner",
                        "reasoning": "Why this resource"
                    }}
                ],
                "milestones": [
                    {{
                        "week": 1,
                        "milestone": "Complete module 1",
                        "success_criteria": "80% quiz score"
                    }}
                ],
                "practice_activities": ["activity1", "activity2"],
                "estimated_hours": 40
            }}
        ],
        "learning_styles_addressed": ["visual", "hands-on", "reading"],
        "total_estimated_hours": 120,
        "success_metrics": ["metric1", "metric2"],
        "adaptation_points": ["checkpoint1", "checkpoint2"],
        "recommended_schedule": "Sample weekly schedule example"
    }},
    "recommendations": {{
        "pacing": "Recommended pacing notes",
        "prerequisites": ["prerequisite1"],
        "supporting_habits": ["habit1", "habit2"],
        "community_resources": ["resource1"],
        "mentoring_opportunities": ["opportunity1"]
    }}
}}"""
        
        try:
            result = self.call_claude_json(
                system_prompt,
                user_message,
                temperature=0.6,
                max_tokens=4000
            )
            
            self.log_execution(
                "Learning Plan Generation",
                "success",
                {"phases_count": len(result.get('learning_plan', {}).get('phases', []))}
            )
            
            return {
                "user_id": user_id,
                "learning_plan": result,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.log_execution("Learning Plan Generation", "error", {"error": str(e)})
            raise
    
    def _format_gaps(self, gaps: List[Dict[str, Any]]) -> str:
        """Format skill gaps for Claude"""
        lines = []
        for gap in gaps:
            lines.append(
                f"- {gap.get('skill')}: Proficiency needed {gap.get('required', 7)}/10, "
                f"Current {gap.get('current', 0)}/10 (Severity: {gap.get('severity', 'medium')})"
            )
        return "\n".join(lines) if lines else "No gaps specified"
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current ISO timestamp"""
        return datetime.utcnow().isoformat()
