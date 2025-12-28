# backend/app/services/llm_service.py

from groq import Groq
from typing import List, Dict, Any, Optional
from app.config.settings import settings
import json
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM Service using Groq (FREE API)
    Models available: llama3-70b-8192, mixtral-8x7b-32768, gemma-7b-it
    """
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.default_model = "llama3-70b-8192"  # Fast and capable
        
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
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return ""
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON output
        """
        system = system_prompt or "You are a helpful assistant that responds in JSON format."
        response = await self.generate(
            prompt=prompt,
            system_prompt=system,
            model=model,
            json_mode=True
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {response}")
            return {}
    
    async def analyze_resume(
        self,
        resume_text: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze resume against job description
        """
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
    
    async def generate_roadmap(
        self,
        user_profile: Dict[str, Any],
        target_role: str,
        timeline: str
    ) -> Dict[str, Any]:
        """
        Generate career roadmap
        """
        prompt = f"""
User Profile:
- Current Status: {user_profile.get('currentStatus', 'Unknown')}
- Skills: {', '.join(user_profile.get('skills', {}).get('technical', []))}
- Experience: {len(user_profile.get('experience', []))} positions
- Education: {len(user_profile.get('education', []))} degrees
- Target Role: {target_role}
- Timeline: {timeline}

Generate a detailed career roadmap with:
1. Milestones (monthly breakdown)
2. Skills to learn (priority ordered)
3. Projects to build
4. Certifications to get
5. Networking activities
6. Application strategy
"""
        
        system_prompt = """You are a career strategist. Create a comprehensive roadmap in JSON:
{
  "milestones": [
    {
      "month": 1,
      "title": "Foundation Phase",
      "goals": ["goal1", "goal2"],
      "tasks": ["task1", "task2"],
      "skills": ["skill1", "skill2"]
    }
  ],
  "learning_path": [
    {
      "skill": "React",
      "priority": "high",
      "resources": ["resource1", "resource2"],
      "estimated_hours": 40
    }
  ],
  "projects": [
    {
      "title": "Project Name",
      "description": "Brief description",
      "skills_used": ["skill1", "skill2"],
      "timeline": "2 weeks"
    }
  ]
}"""
        
        return await self.generate_json(prompt, system_prompt)
    
    async def score_job_compatibility(
        self,
        user_skills: List[str],
        user_experience: str,
        job_description: str,
        job_requirements: str
    ) -> Dict[str, Any]:
        """
        Score compatibility between user and job
        """
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
        """
        Generate interview questions for practice
        """
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
        """
        Evaluate interview response
        """
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
        """
        Generate personalized motivational message
        """
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

# Singleton instance
llm_service = LLMService()