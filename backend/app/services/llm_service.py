# backend/app/services/llm_service.py - FIXED

from groq import Groq
from typing import List, Dict, Any, Optional, Union
from app.config.settings import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM Service using Groq (FREE API)
    Models available: llama-3.3-70b-versatile, llama-3.1-8b-instant
    """
    
    def __init__(self):
        # Try GROQ_API_KEY first, then fallback to GROQ_API_KEY_INTERVIEW
        api_key = settings.GROQ_API_KEY_JOURNAL or settings.GROQ_API_KEY or settings.GROQ_API_KEY_INTERVIEW
        
        if not api_key:
            raise ValueError("GROQ_API_KEY or GROQ_API_KEY_INTERVIEW must be set in .env")
        
        self.client = Groq(api_key=api_key)
        self.default_model = "llama-3.3-70b-versatile"  # Fast and capable
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> str:
        """
        Generate text completion
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else {"type": "text"}
            )
            
            content = response.choices[0].message.content
            logger.debug(f"LLM response length: {len(content)} chars")
            return content
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return ""
    
    def _extract_json_from_response(self, response: str) -> Union[Dict, List, None]:
        """Extract JSON from response with markdown code block handling"""
        if not response or not response.strip():
            logger.error("Empty response received")
            return None
        
        try:
            # Try direct JSON parse first
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        code_block_pattern = re.compile(
            r"``````",
            re.DOTALL | re.IGNORECASE
        )
        
        match = code_block_pattern.search(response)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Last resort: try to find JSON-like structure
        # Look for array
        array_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Look for object
        object_match = re.search(r'\{\s*".*?\}\s*', response, re.DOTALL)
        if object_match:
            try:
                return json.loads(object_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Could not extract JSON from response: {response[:500]}")
        return None
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Generate JSON output (can return dict or list)
        """
        system = system_prompt or "You are a helpful assistant that responds in JSON format."
        
        # Add explicit JSON instruction to prompt
        if "Return ONLY valid JSON" not in prompt:
            prompt = prompt + "\n\nReturn ONLY valid JSON. No markdown, no explanations."
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=system,
            model=model,
            json_mode=True,  # Force JSON mode
            temperature=0.3  # Lower temp for more consistent JSON
        )
        
        if not response:
            logger.error("Empty response from LLM")
            return {}
        
        # Log raw response for debugging
        logger.debug(f"Raw LLM JSON response (first 500 chars): {response[:500]}")
        
        # Extract and parse JSON
        parsed = self._extract_json_from_response(response)
        
        if parsed is None:
            logger.error(f"Failed to parse JSON from response")
            return {}
        
        logger.debug(f"Successfully parsed JSON of type: {type(parsed)}")
        return parsed
    
    # ==================== ROADMAP GENERATION ====================
    
    async def generate_roadmap(
        self,
        user_profile: Dict[str, Any],
        target_role: str,
        timeline: str
    ) -> Dict[str, Any]:
        """
        Generate career roadmap - FIXED to handle None values
        """
        # SAFE extraction with defaults
        current_skills = user_profile.get('current_skills', [])
        missing_skills = user_profile.get('missing_skills', [])
        experience = user_profile.get('experience', 'Beginner - Starting career journey')
        timeline_weeks = user_profile.get('timeline_weeks', 12)
        
        # Ensure experience is a string
        if not isinstance(experience, str):
            experience = 'Beginner - Starting career journey'
        
        # Build skills summary
        skills_summary = ', '.join(current_skills) if current_skills else 'No skills listed yet'
        missing_summary = ', '.join(missing_skills) if missing_skills else 'Will be determined based on target role'
        
        prompt = f"""
User Profile:
- Current Skills: {skills_summary}
- Missing Skills for Target Role: {missing_summary}
- Experience Level: {experience}
- Target Role: {target_role}
- Timeline: {timeline} ({timeline_weeks} weeks)

Generate a detailed, actionable career roadmap with:

1. **Milestones**: Monthly breakdown of phases (Foundation → Intermediate → Advanced → Specialization)
2. **Learning Path**: Prioritized skills to learn with estimated hours
3. **Projects**: Hands-on projects to build portfolio
4. **Resources**: Specific courses, tutorials, documentation links

Return ONLY valid JSON with this EXACT structure:
{{
  "milestones": [
    {{
      "month": 1,
      "phase_name": "Foundation Phase",
      "goals": ["Master JavaScript fundamentals", "Learn HTML/CSS"],
      "tasks": ["Complete JavaScript course", "Build 3 small projects"],
      "skills": ["JavaScript", "HTML", "CSS"],
      "duration_weeks": 4
    }}
  ],
  "learning_path": [
    {{
      "skill": "JavaScript",
      "priority": "high",
      "category": "Programming Language",
      "resources": [
        "https://javascript.info",
        "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures"
      ],
      "estimated_hours": 40,
      "prerequisites": ["HTML", "CSS"]
    }},
    {{
      "skill": "React",
      "priority": "high",
      "category": "Frontend Framework",
      "resources": [
        "https://react.dev",
        "https://www.udemy.com/course/react-the-complete-guide"
      ],
      "estimated_hours": 50,
      "prerequisites": ["JavaScript"]
    }}
  ],
  "projects": [
    {{
      "title": "Personal Portfolio Website",
      "description": "Responsive website showcasing your skills and projects",
      "skills_used": ["HTML", "CSS", "JavaScript"],
      "timeline": "1 week"
    }},
    {{
      "title": "Todo App with React",
      "description": "Full CRUD application with local storage",
      "skills_used": ["React", "JavaScript", "CSS"],
      "timeline": "2 weeks"
    }}
  ]
}}
"""

        system_prompt = f"""You are an expert career strategist and learning path designer. 
Create comprehensive, realistic roadmaps for transitioning to {target_role}.
Focus on practical, achievable steps with real resources.
Prioritize in-demand skills and hands-on projects.
Always return valid JSON without markdown formatting."""

        try:
            result = await self.generate_json(prompt, system_prompt)
            
            # Validate result
            if not result or not isinstance(result, dict):
                logger.error("Invalid result from LLM, using fallback")
                return self._get_fallback_roadmap(target_role, timeline_weeks)
            
            # Ensure required fields exist
            if 'learning_path' not in result or not result['learning_path']:
                logger.warning("No learning path in result, generating basic one")
                result['learning_path'] = self._generate_basic_learning_path(
                    target_role, 
                    current_skills, 
                    missing_skills
                )
            
            if 'milestones' not in result or not result['milestones']:
                logger.warning("No milestones in result, generating basic ones")
                result['milestones'] = self._generate_basic_milestones(timeline_weeks)
            
            if 'projects' not in result:
                result['projects'] = []
            
            logger.info(f"✅ Generated roadmap with {len(result['learning_path'])} skills, {len(result['milestones'])} milestones")
            return result
            
        except Exception as e:
            logger.error(f"Error generating roadmap: {e}", exc_info=True)
            return self._get_fallback_roadmap(target_role, timeline_weeks)
    
    def _generate_basic_learning_path(
        self, 
        target_role: str, 
        current_skills: List[str],
        missing_skills: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate a basic learning path if LLM fails"""
        
        # Common skills for different roles
        role_skills = {
            "full stack": [
                ("JavaScript", "high", 40, "Programming Language"),
                ("React", "high", 50, "Frontend Framework"),
                ("Node.js", "high", 40, "Backend Runtime"),
                ("Python", "medium", 40, "Programming Language"),
                ("FastAPI", "medium", 30, "Backend Framework"),
                ("PostgreSQL", "high", 30, "Database"),
                ("Git", "high", 20, "Version Control"),
                ("Docker", "low", 25, "DevOps"),
                ("AWS", "low", 35, "Cloud Platform")
            ],
            "data scientist": [
                ("Python", "high", 40, "Programming Language"),
                ("Pandas", "high", 30, "Data Analysis"),
                ("NumPy", "high", 25, "Scientific Computing"),
                ("Scikit-learn", "high", 40, "Machine Learning"),
                ("SQL", "high", 30, "Database"),
                ("Machine Learning", "high", 60, "Core Skill"),
                ("Deep Learning", "medium", 60, "Advanced ML"),
                ("TensorFlow", "medium", 45, "ML Framework"),
                ("Data Visualization", "medium", 25, "Visualization")
            ],
            "backend": [
                ("Python", "high", 40, "Programming Language"),
                ("FastAPI", "high", 35, "Web Framework"),
                ("PostgreSQL", "high", 30, "Database"),
                ("Redis", "medium", 20, "Caching"),
                ("Docker", "high", 30, "Containerization"),
                ("Kubernetes", "low", 40, "Orchestration"),
                ("AWS", "medium", 40, "Cloud Platform"),
                ("Microservices", "low", 40, "Architecture")
            ],
            "frontend": [
                ("JavaScript", "high", 40, "Programming Language"),
                ("TypeScript", "high", 30, "Programming Language"),
                ("React", "high", 50, "Framework"),
                ("Next.js", "medium", 35, "Meta-framework"),
                ("Tailwind CSS", "medium", 20, "CSS Framework"),
                ("State Management", "high", 30, "Architecture"),
                ("Web APIs", "medium", 25, "Browser APIs"),
                ("Testing", "medium", 30, "Quality Assurance")
            ]
        }
        
        # Match target role to skill set
        target_role_lower = target_role.lower()
        skills_list = role_skills.get("full stack")  # default
        
        for role_key in role_skills.keys():
            if role_key in target_role_lower:
                skills_list = role_skills[role_key]
                break
        
        # Filter out skills user already has
        current_skills_lower = [s.lower() for s in current_skills]
        learning_path = []
        
        for skill_name, priority, hours, category in skills_list:
            if skill_name.lower() not in current_skills_lower:
                learning_path.append({
                    "skill": skill_name,
                    "priority": priority,
                    "category": category,
                    "estimated_hours": hours,
                    "resources": [
                        f"https://www.youtube.com/results?search_query={skill_name.replace(' ', '+')}+tutorial",
                        f"https://www.coursera.org/search?query={skill_name.replace(' ', '+')}"
                    ],
                    "prerequisites": []
                })
        
        return learning_path
    
    def _generate_basic_milestones(self, timeline_weeks: int) -> List[Dict[str, Any]]:
        """Generate basic milestones based on timeline"""
        num_phases = min(4, max(2, timeline_weeks // 4))
        weeks_per_phase = timeline_weeks // num_phases
        
        phase_names = ["Foundation", "Intermediate", "Advanced", "Specialization"]
        milestones = []
        
        for i in range(num_phases):
            milestones.append({
                "month": i + 1,
                "phase_name": f"{phase_names[i]} Phase",
                "goals": [
                    "Learn core concepts",
                    "Build practical projects",
                    "Practice regularly"
                ],
                "tasks": [
                    "Complete online courses",
                    "Work on hands-on exercises",
                    "Build portfolio projects"
                ],
                "skills": ["Technical skills", "Problem solving", "Best practices"],
                "duration_weeks": weeks_per_phase
            })
        
        return milestones
    
    def _get_fallback_roadmap(self, target_role: str, timeline_weeks: int) -> Dict[str, Any]:
        """Return a fallback roadmap if generation fails"""
        return {
            "milestones": self._generate_basic_milestones(timeline_weeks),
            "learning_path": self._generate_basic_learning_path(target_role, [], []),
            "projects": [
                {
                    "title": "Personal Portfolio Website",
                    "description": "Showcase your skills and projects with a professional website",
                    "skills_used": ["HTML", "CSS", "JavaScript"],
                    "timeline": "1 week"
                },
                {
                    "title": "Full Stack Application",
                    "description": "Complete CRUD application with backend and frontend",
                    "skills_used": ["React", "Node.js", "Database"],
                    "timeline": "3 weeks"
                },
                {
                    "title": "Open Source Contribution",
                    "description": "Contribute to a real-world open source project",
                    "skills_used": ["Git", "Code review", "Collaboration"],
                    "timeline": "Ongoing"
                }
            ]
        }
    
    # ==================== OTHER METHODS ====================
    
    async def analyze_resume(
        self,
        resume_text: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze resume against job description"""
        prompt = f"""
Analyze this resume:

{resume_text}
"""
        
        if job_description:
            prompt += f"""

Job Description:
{job_description}

Compare the resume to the job description and identify:
1. Matching skills and experience
2. Missing skills (gaps)
3. Compatibility score (0-100)
4. Specific recommendations to improve the resume
"""
        else:
            prompt += """

Provide:
1. Overall quality score (0-100)
2. Key strengths
3. Areas for improvement
4. Missing sections or details
"""
        
        system_prompt = """You are an expert career advisor and resume reviewer. 
Provide detailed, actionable feedback in JSON format with the following structure:
{
  "score": 85,
  "strengths": ["list of strengths"],
  "weaknesses": ["list of weaknesses"],
  "gaps": ["missing skills or experience"],
  "recommendations": ["specific improvement suggestions"]
}"""
        
        return await self.generate_json(prompt, system_prompt)
    
    async def score_job_compatibility(
        self,
        user_skills: List[str],
        user_experience: str,
        job_description: str,
        job_requirements: str
    ) -> Dict[str, Any]:
        """Score compatibility between user and job"""
        prompt = f"""
User Skills: {', '.join(user_skills)}
User Experience: {user_experience}

Job Description:
{job_description}

Requirements:
{job_requirements}

Calculate:
1. Compatibility score (0-100)
2. Matching skills
3. Missing skills (gaps)
4. Experience match
5. Recommendations for application
"""
        
        system_prompt = """You are a job matching expert. Return JSON:
{
  "compatibility_score": 75,
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "experience_match": "good|partial|poor",
  "recommendations": ["rec1", "rec2"],
  "should_apply": true
}"""
        
        return await self.generate_json(prompt, system_prompt)
    
    async def generate_interview_questions(
        self,
        role: str,
        company: str,
        job_description: str,
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Generate interview questions for practice"""
        prompt = f"""
Generate {difficulty} difficulty interview questions for:
Role: {role}
Company: {company}
Job Description: {job_description}

Create 10 questions covering:
- Technical skills
- Behavioral scenarios
- Problem-solving
- Company-specific
"""
        
        system_prompt = """You are an interview coach. Return JSON:
{
  "questions": [
    {
      "question": "Tell me about...",
      "category": "behavioral",
      "difficulty": "medium",
      "sample_answer": "A good answer would include...",
      "evaluation_criteria": ["criteria1", "criteria2"]
    }
  ]
}"""
        
        result = await self.generate_json(prompt, system_prompt)
        return result.get("questions", [])
    
    async def evaluate_interview_response(
        self,
        question: str,
        response: str,
        role: str
    ) -> Dict[str, Any]:
        """Evaluate interview response"""
        prompt = f"""
Interview Question: {question}
Candidate Response: {response}
Role: {role}

Evaluate the response on:
1. Content quality (0-100)
2. Clarity (0-100)
3. Relevance (0-100)
4. Confidence indicators
5. Areas for improvement
6. Overall score (0-100)
"""
        
        system_prompt = """You are an interview evaluator. Provide honest, constructive feedback in JSON:
{
  "content_score": 75,
  "clarity_score": 80,
  "relevance_score": 90,
  "overall_score": 82,
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"],
  "feedback": "Detailed feedback paragraph"
}"""
        
        return await self.generate_json(prompt, system_prompt)
    
    async def generate_motivational_message(
        self,
        user_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate personalized motivational message"""
        prompt = f"""
User: {user_name}
Recent Progress: {context.get('progress', 'Starting journey')}
Current Mood: {context.get('mood', 'neutral')}
Goals: {context.get('goals', 'Career growth')}

Generate a warm, encouraging, personalized message that:
- Acknowledges their progress
- Provides motivation
- Offers specific encouragement
- Keeps it concise (2-3 sentences)
"""
        
        system_prompt = "You are a supportive career coach who provides genuine, warm encouragement."
        
        return await self.generate(prompt, system_prompt, temperature=0.9)
def get_llm_service() -> LLMService:
    """Factory function to get LLM service instance"""
    return LLMService()

# Singleton instance
llm_service = LLMService()
