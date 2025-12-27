"""Resource Recommender Agent - Recommends learning resources and platforms"""

from typing import Any, Dict, List
from .base_agent import BaseAgent
from datetime import datetime


class ResourceRecommenderAgent(BaseAgent):
    """Agent that recommends learning resources and platforms"""
    
    async def execute(
        self,
        user_id: str,
        target_skills: List[str],
        learning_style: str = "mixed",
        budget_tier: str = "flexible",
        preferred_languages: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Recommend learning resources for target skills
        
        Args:
            user_id: User identifier
            target_skills: Skills to learn
            learning_style: Preferred learning style
            budget_tier: Budget level (free, budget, premium, flexible)
            preferred_languages: Programming languages or natural languages preferred
            
        Returns:
            Dict containing resource recommendations
        """
        self.log_execution(f"Resource Recommendation", "processing")
        
        skills_text = ", ".join(target_skills) if target_skills else "General skill development"
        lang_text = ", ".join(preferred_languages) if preferred_languages else "Any"
        
        system_prompt = """You are an expert resource curator with deep knowledge of online learning platforms, 
courses, books, and tools. Provide comprehensive, well-researched resource recommendations.
Respond ONLY with valid JSON, no other text."""
        
        user_message = f"""Recommend the best learning resources for developing these skills: {skills_text}

User Preferences:
- Learning Style: {learning_style}
- Budget Tier: {budget_tier}
- Programming Languages: {lang_text}

Provide a JSON response with this EXACT structure:
{{
    "resource_recommendations": {{
        "online_courses": [
            {{
                "rank": 1,
                "title": "Course Title",
                "platform": "Platform Name",
                "instructor": "Instructor Name",
                "url": "https://course.url",
                "duration_hours": 30,
                "cost": "Free",
                "difficulty_level": "beginner",
                "skills_covered": ["skill1", "skill2"],
                "rating": 4.8,
                "why_recommended": "Detailed explanation",
                "prerequisites": ["basic programming"],
                "certification": true
            }}
        ],
        "youtube_channels": [
            {{
                "rank": 1,
                "channel_name": "Channel Name",
                "url": "https://youtube.com/channel",
                "focus_area": "Skill focus",
                "content_quality": "high",
                "update_frequency": "weekly",
                "subscribers": "1M+",
                "why_recommended": "Reason for recommendation"
            }}
        ],
        "books": [
            {{
                "rank": 1,
                "title": "Book Title",
                "author": "Author Name",
                "published_year": 2024,
                "pages": 300,
                "format": ["pdf", "kindle", "physical"],
                "difficulty": "intermediate",
                "skills_covered": ["skill1"],
                "cost": "$25",
                "why_recommended": "Recommendation reason"
            }}
        ],
        "tools_and_platforms": [
            {{
                "name": "Tool/Platform Name",
                "type": "IDE/Playground/Editor",
                "free_tier": true,
                "url": "https://tool.url",
                "primary_use": "Practice/Build",
                "why_recommended": "How it helps"
            }}
        ],
        "communities": [
            {{
                "name": "Community Name",
                "type": "Discord/Reddit/Forum",
                "url": "https://community.url",
                "activity_level": "high",
                "why_recommended": "Community benefits"
            }}
        ]
    }},
    "learning_path_by_resource_type": {{
        "phase_1": "Start with X course, watch Y channel",
        "phase_2": "Practice with Z tool, read A book",
        "phase_3": "Join community, build projects"
    }},
    "estimated_total_cost": "$50-100 or Free",
    "time_investment": "120-150 hours total",
    "next_steps": ["Step 1", "Step 2", "Step 3"]
}}"""
        
        try:
            result = self.call_claude_json(
                system_prompt,
                user_message,
                temperature=0.6,
                max_tokens=3500
            )
            
            self.log_execution(
                "Resource Recommendation",
                "success",
                {
                    "courses_count": len(result.get('resource_recommendations', {}).get('online_courses', [])),
                    "books_count": len(result.get('resource_recommendations', {}).get('books', []))
                }
            )
            
            return {
                "user_id": user_id,
                "recommendations": result,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.log_execution("Resource Recommendation", "error", {"error": str(e)})
            raise
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current ISO timestamp"""
        return datetime.utcnow().isoformat()
