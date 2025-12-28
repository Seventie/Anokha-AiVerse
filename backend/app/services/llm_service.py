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
    
    # ... rest of your methods remain the same ...
    
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
