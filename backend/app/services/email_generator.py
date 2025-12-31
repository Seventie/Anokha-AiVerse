# backend/app/services/email_generator.py

from typing import Dict, List
import logging
from sqlalchemy.orm import Session
from app.models.database import User, Skill, Experience, Project
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

class EmailGenerator:
    """Generate personalized cold emails using AI"""
    
    def generate_cold_email(
        self,
        user_id: str,
        recipient_name: str,
        recipient_title: str,
        company_name: str,
        company_info: Dict,
        db: Session
    ) -> Dict[str, str]:
        """
        Generate personalized cold email
        
        Returns: {"subject": "...", "body": "..."}
        """
        try:
            # Get user profile
            user = db.query(User).filter(User.id == user_id).first()
            skills = db.query(Skill).filter(Skill.user_id == user_id).limit(5).all()
            experiences = db.query(Experience).filter(Experience.user_id == user_id).limit(2).all()
            projects = db.query(Project).filter(Project.user_id == user_id).limit(2).all()
            
            # Build context
            skills_text = ", ".join([s.skill for s in skills])
            
            experience_text = ""
            if experiences:
                exp = experiences[0]
                experience_text = f"{exp.role} at {exp.company}"
            
            project_text = ""
            if projects:
                proj = projects[0]
                project_text = f"{proj.title}: {proj.description[:100]}"
            
            # Company context
            tech_stack = company_info.get("tech_stack", "")
            recent_news = company_info.get("recent_news", "")
            
            # Generate email
            prompt = f"""Generate a professional cold email for a job opportunity.

**Sender Profile:**
- Name: {user.full_name}
- Skills: {skills_text}
- Recent Experience: {experience_text}
- Notable Project: {project_text}
- Target Role: {user.readiness_level or 'Software Engineer'}

**Recipient:**
- Name: {recipient_name}
- Title: {recipient_title}
- Company: {company_name}

**Company Info:**
- Tech Stack: {tech_stack}
- Recent News: {recent_news}

**Requirements:**
1. Keep it under 150 words
2. Personalize based on company tech stack
3. Highlight relevant skills/experience
4. Professional but friendly tone
5. Clear call-to-action (15-min chat)
6. No generic templates

Generate:
1. Subject line (under 60 characters)
2. Email body (HTML format with proper formatting)

Format as JSON:
{{
  "subject": "...",
  "body": "<p>...</p>"
}}
"""
            
            llm = get_llm_service()
            response = llm.generate(prompt)
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response)
                return {
                    "subject": result.get("subject", f"Interested in {recipient_title} opportunities at {company_name}"),
                    "body": result.get("body", self._fallback_email(user, recipient_name, company_name))
                }
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON, using fallback")
                return {
                    "subject": f"Interested in {recipient_title} opportunities at {company_name}",
                    "body": self._fallback_email(user, recipient_name, company_name)
                }
                
        except Exception as e:
            logger.error(f"Failed to generate email: {e}", exc_info=True)
            return {
                "subject": f"Interested in opportunities at {company_name}",
                "body": self._fallback_email(user, recipient_name, company_name)
            }
    
    def _fallback_email(self, user: User, recipient_name: str, company_name: str) -> str:
        """Fallback email template"""
        return f"""<p>Hi {recipient_name},</p>

<p>I'm {user.full_name}, a software engineer interested in opportunities at {company_name}.</p>

<p>I've been following {company_name}'s work and I'm impressed by your team's innovations. 
I believe my skills could add value to your engineering team.</p>

<p>Would you be open to a brief 15-minute chat to discuss potential opportunities?</p>

<p>Best regards,<br>
{user.full_name}</p>
"""

email_generator = EmailGenerator()
