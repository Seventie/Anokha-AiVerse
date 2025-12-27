"""Gap Analyzer Agent - Analyzes skill gaps between current and target roles"""

from typing import Any, Dict, List
from .base_agent import BaseAgent
import json


class GapAnalyzerAgent(BaseAgent):
    """Agent that identifies skill gaps for career progression"""
    
    async def execute(
        self,
        user_id: str,
        current_skills: List[Dict[str, Any]],
        target_role: str,
        job_requirements: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps between current and target role
        
        Args:
            user_id: User identifier
            current_skills: List of user's current skills with proficiency levels
            target_role: Target job role
            job_requirements: Required skills for target role
            
        Returns:
            Dict containing gap analysis results
        """
        self.log_execution(f"Gap Analysis for {target_role}", "processing")
        
        # Format current skills for analysis
        current_skills_text = self._format_skills(current_skills)
        job_requirements_text = self._format_requirements(job_requirements)
        
        system_prompt = f"""You are an expert career counselor and skill analyst. 
Your task is to identify skill gaps and create a structured analysis.
Be precise, actionable, and provide severity levels for each gap.
Respond ONLY with valid JSON, no other text."""
        
        user_message = f"""Analyze the skill gaps for a professional transitioning to {target_role}.

Current Skills (with proficiency 0-10):
{current_skills_text}

Target Role Requirements:
{job_requirements_text}

Provide a JSON response with this EXACT structure:
{{
    "target_role": "{target_role}",
    "critical_gaps": [
        {{
            "skill": "skill name",
            "required_proficiency": 8,
            "current_proficiency": 3,
            "gap_severity": "critical",
            "reasoning": "why this matters"
        }}
    ],
    "moderate_gaps": [
        {{
            "skill": "skill name",
            "required_proficiency": 7,
            "current_proficiency": 4,
            "gap_severity": "moderate",
            "reasoning": "why this matters"
        }}
    ],
    "minor_gaps": [],
    "strengths": ["skill1", "skill2"],
    "overall_readiness_score": 45,
    "months_to_readiness": 12,
    "summary": "Overall assessment"
}}"""
        
        try:
            result = self.call_claude_json(
                system_prompt,
                user_message,
                temperature=0.5,
                max_tokens=2000
            )
            
            self.log_execution(
                f"Gap Analysis for {target_role}",
                "success",
                {"critical_gaps_count": len(result.get('critical_gaps', []))}
            )
            
            return {
                "user_id": user_id,
                "analysis": result,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.log_execution(f"Gap Analysis for {target_role}", "error", {"error": str(e)})
            raise
    
    def _format_skills(self, skills: List[Dict[str, Any]]) -> str:
        """Format skills list for Claude"""
        lines = []
        for skill in skills:
            lines.append(f"- {skill.get('name')}: {skill.get('proficiency', 0)}/10 (Experience: {skill.get('experience_years', 0)} years)")
        return "\n".join(lines) if lines else "No skills recorded"
    
    def _format_requirements(self, requirements: List[Dict[str, Any]]) -> str:
        """Format job requirements for Claude"""
        lines = []
        for req in requirements:
            lines.append(f"- {req.get('skill')}: {req.get('required_level', 'intermediate')} level, {req.get('importance', 'medium')} importance")
        return "\n".join(lines) if lines else "No requirements specified"
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current ISO timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
