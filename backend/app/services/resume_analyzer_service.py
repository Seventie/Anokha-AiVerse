# backend/app/services/resume_analyzer_service.py - FIXED VERSION

from app.services.llm_service import llm_service
from typing import Dict, Any, List, Optional
import logging
import json
import re

logger = logging.getLogger(__name__)

class ResumeAnalyzerService:
    """AI-powered resume analysis using Groq LLM"""
    
    async def analyze_resume(
        self,
        parsed_resume: Dict[str, Any],
        user_goals: List[str] = None,
        jd_text: str = None
    ) -> Dict[str, Any]:
        """
        Comprehensive resume analysis with:
        - ATS score
        - Strengths & weaknesses
        - Project suggestions
        - JD comparison (if provided)
        """
        
        try:
            logger.info("🔍 Starting comprehensive resume analysis...")
            
            # 1. Calculate ATS Score
            ats_score = self._calculate_ats_score(parsed_resume)
            
            # 2. Get AI-powered suggestions
            suggestions = await self._get_improvement_suggestions(
                parsed_resume, 
                user_goals or []
            )
            
            # 3. Get project recommendations
            project_suggestions = await self._suggest_projects(
                parsed_resume,
                user_goals or []
            )
            
            # 4. JD-specific analysis (if provided)
            jd_analysis = None
            if jd_text:
                jd_analysis = await self._analyze_against_jd(
                    parsed_resume,
                    jd_text
                )
            
            logger.info("✅ Resume analysis complete")
            
            return {
                "ats_score": ats_score,
                "suggestions": suggestions,
                "project_suggestions": project_suggestions,
                "jd_analysis": jd_analysis
            }
        
        except Exception as e:
            logger.error(f"❌ Resume analysis error: {e}", exc_info=True)
            return {
                "ats_score": self._get_default_ats_score(),
                "suggestions": self._get_default_suggestions(),
                "project_suggestions": [],
                "jd_analysis": None
            }
    
    def _calculate_ats_score(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate ATS-friendliness score based on parsed data"""
        
        scores = {
            "contact_info": 0,
            "skills": 0,
            "experience": 0,
            "education": 0,
            "projects": 0,
            "formatting": 0
        }
        
        # Contact Info (15 points)
        personal = resume.get("personal_info", {})
        contact_fields = sum([
            1 for field in ["email", "phone", "fullName"]
            if personal.get(field)
        ])
        scores["contact_info"] = min(15, contact_fields * 5)
        
        # Skills (25 points)
        skills = resume.get("skills", {})
        tech_skills = skills.get("technical", [])
        non_tech = skills.get("non_technical", [])
        total_skills = len(tech_skills) + len(non_tech)
        
        if total_skills >= 15:
            scores["skills"] = 25
        elif total_skills >= 10:
            scores["skills"] = 20
        elif total_skills >= 5:
            scores["skills"] = 15
        elif total_skills >= 3:
            scores["skills"] = 10
        
        # Experience (25 points)
        experience = resume.get("experience", [])
        exp_count = len(experience)
        if exp_count >= 3:
            scores["experience"] = 25
        elif exp_count >= 2:
            scores["experience"] = 20
        elif exp_count >= 1:
            scores["experience"] = 15
        
        # Check for quantifiable achievements
        has_metrics = any(
            any(char.isdigit() for resp in exp.get("responsibilities", []) for char in resp)
            for exp in experience
        )
        if has_metrics:
            scores["experience"] = min(25, scores["experience"] + 5)
        
        # Education (15 points)
        education = resume.get("education", [])
        if len(education) >= 2:
            scores["education"] = 15
        elif len(education) >= 1:
            scores["education"] = 12
        
        # Projects (15 points)
        projects = resume.get("projects", [])
        project_count = len(projects)
        if project_count >= 4:
            scores["projects"] = 15
        elif project_count >= 3:
            scores["projects"] = 12
        elif project_count >= 2:
            scores["projects"] = 10
        elif project_count >= 1:
            scores["projects"] = 6
        
        # Formatting (5 points) - Links and profile completeness
        profile_links = sum([
            1 for field in ["linkedin", "github", "portfolio"]
            if personal.get(field)
        ])
        scores["formatting"] = min(5, profile_links * 2)
        
        # Summary bonus
        if personal.get("summary"):
            scores["formatting"] = min(5, scores["formatting"] + 2)
        
        overall = sum(scores.values())
        
        return {
            "overall_score": overall,
            "breakdown": scores,
            "grade": self._get_grade(overall),
            "message": self._get_score_message(overall)
        }
    
    def _get_grade(self, score: int) -> str:
        """Get letter grade from score"""
        if score >= 90: return "A+"
        if score >= 85: return "A"
        if score >= 80: return "A-"
        if score >= 75: return "B+"
        if score >= 70: return "B"
        if score >= 65: return "B-"
        if score >= 60: return "C+"
        if score >= 55: return "C"
        return "D"
    
    def _get_score_message(self, score: int) -> str:
        """Get human-readable message"""
        if score >= 85:
            return "🎉 Excellent! Your resume is highly ATS-friendly and well-structured."
        elif score >= 70:
            return "👍 Good! Your resume should pass most ATS systems with minor improvements."
        elif score >= 60:
            return "⚠️ Fair. Add more details and structure to improve ATS compatibility."
        else:
            return "❌ Needs work. Add more sections and details to increase ATS pass rate."
    
    async def _get_improvement_suggestions(
        self, 
        resume: Dict[str, Any],
        goals: List[str]
    ) -> Dict[str, List[str]]:
        """Get AI-powered improvement suggestions using Groq"""
        
        # Build resume summary for LLM
        personal = resume.get("personal_info", {})
        skills = resume.get("skills", {})
        experience = resume.get("experience", [])
        projects = resume.get("projects", [])
        education = resume.get("education", [])
        
        tech_skills = skills.get("technical", [])
        soft_skills = skills.get("non_technical", [])
        
        resume_summary = f"""
**Personal Info:**
- Name: {personal.get('fullName', 'Not provided')}
- Email: {'✓' if personal.get('email') else '✗'}
- Phone: {'✓' if personal.get('phone') else '✗'}
- LinkedIn: {'✓' if personal.get('linkedin') else '✗'}
- GitHub: {'✓' if personal.get('github') else '✗'}
- Summary: {'✓' if personal.get('summary') else '✗'}

**Skills:**
- Technical: {', '.join(tech_skills[:15]) if tech_skills else 'None listed'}
- Soft Skills: {', '.join(soft_skills[:10]) if soft_skills else 'None listed'}

**Experience:** {len(experience)} positions
{self._format_experience_summary(experience)}

**Projects:** {len(projects)} projects
{self._format_projects_summary(projects)}

**Education:** {len(education)} entries
{self._format_education_summary(education)}

**Career Goals:** {', '.join(goals) if goals else 'Not specified'}
"""
        
        prompt = f"""Analyze this resume and provide actionable improvements.

{resume_summary}

Provide a critical analysis with:
1. **3 Strengths** - What's working well
2. **3 Weaknesses** - What needs improvement
3. **5 Specific Improvements** - Actionable changes to make

Be specific and actionable. Focus on ATS optimization, quantifiable achievements, and keyword usage.

Return ONLY valid JSON in this exact format:
{{
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "improvements": ["improvement1", "improvement2", "improvement3", "improvement4", "improvement5"]
}}"""
        
        try:
            # ✅ FIXED: Use correct llm_service method
            response = await llm_service.generate(
                prompt=prompt,
                system_prompt="You are an expert resume analyzer and career coach. Provide honest, actionable feedback.",
                model="llama-3.3-70b-versatile",
                temperature=0.7
            )
            
            logger.debug(f"LLM suggestions response: {response[:200]}")
            
            # Extract JSON from response
            suggestions = self._extract_json_from_response(response)
            
            # Validate structure
            if not isinstance(suggestions, dict):
                raise ValueError("Invalid JSON structure")
            
            required_keys = ["strengths", "weaknesses", "improvements"]
            if not all(k in suggestions for k in required_keys):
                raise ValueError("Missing required keys")
            
            # Ensure lists and limit length
            suggestions["strengths"] = suggestions.get("strengths", [])[:3]
            suggestions["weaknesses"] = suggestions.get("weaknesses", [])[:3]
            suggestions["improvements"] = suggestions.get("improvements", [])[:5]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get AI suggestions: {e}", exc_info=True)
            return self._get_default_suggestions()

    async def _calculate_ats_score_with_llm(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate ATS score using LLM analysis"""
        
        prompt = f"""Analyze this resume and provide an ATS (Applicant Tracking System) compatibility score.

    **Resume Data:**
    - Contact Info: {resume.get('personal_info', {})}
    - Skills: {resume.get('skills', {})}
    - Experience: {len(resume.get('experience', []))} positions
    - Education: {len(resume.get('education', []))} entries
    - Projects: {len(resume.get('projects', []))} projects

    Provide detailed scoring on a 100-point scale:
    - Contact Info (15 points) - Email, phone, LinkedIn, GitHub
    - Skills (25 points) - Technical skills breadth and relevance
    - Experience (25 points) - Work history with quantifiable achievements
    - Education (15 points) - Degrees and institutions
    - Projects (15 points) - Portfolio projects with tech stack
    - Formatting (5 points) - Links, summary, consistency

    Return ONLY valid JSON:
    {{
    "overall_score": 85,
    "breakdown": {{
        "contact_info": 15,
        "skills": 22,
        "experience": 20,
        "education": 12,
        "projects": 12,
        "formatting": 4
    }},
    "grade": "A",
    "message": "Brief assessment message"
    }}"""

        try:
            response = await llm_service.generate_json(
                prompt=prompt,
                system_prompt="You are an ATS scoring expert. Provide accurate, fair assessments.",
                model="llama-3.3-70b-versatile"
            )
            
            if isinstance(response, dict) and "overall_score" in response:
                return response
            
            # Fallback to rule-based
            return self._calculate_ats_score(resume)
            
        except Exception as e:
            logger.error(f"LLM ATS scoring failed: {e}")
            return self._calculate_ats_score(resume)

    
    async def _suggest_projects(
        self,
        resume: Dict[str, Any],
        goals: List[str]
    ) -> List[Dict[str, Any]]:
        """Suggest projects to build based on skills and goals using Groq"""
        
        skills = resume.get("skills", {}).get("technical", [])
        current_projects = resume.get("projects", [])
        
        logger.info(f"🚀 Suggesting projects for skills: {skills[:10]}")
        
        # Wrap in projects key to ensure JSON object mode works
        prompt = f"""Based on these skills and goals, suggest 3 impactful portfolio projects.

    **Current Skills:** {', '.join(skills[:20]) if skills else 'Beginner level'}
    **Current Projects:** {len(current_projects)} projects
    **Career Goals:** {', '.join(goals) if goals else 'Software Engineering'}

    Suggest 3 projects that will strengthen this resume. For each project provide:
    - name: Project title
    - description: 2-3 sentence description of what to build
    - technologies: Array of 3-5 technologies to use
    - value: Why recruiters value this project

    Return in this EXACT JSON format:
    {{
    "projects": [
        {{
        "name": "Project Name",
        "description": "Detailed description",
        "technologies": ["Tech1", "Tech2", "Tech3"],
        "value": "Why this matters to recruiters"
        }}
    ]
    }}"""
        
        try:
            response = await llm_service.generate_json(
                prompt=prompt,
                system_prompt="You are a technical project advisor. Suggest realistic, impressive projects that demonstrate real-world skills.",
                model="llama-3.3-70b-versatile"
            )
            
            logger.debug(f"Project response type: {type(response)}, content: {response}")
            
            # Handle both list and dict responses
            if isinstance(response, dict):
                projects = response.get("projects", [])
            elif isinstance(response, list):
                projects = response
            else:
                projects = []
            
            logger.info(f"✅ Received {len(projects)} project suggestions")
            
            if isinstance(projects, list) and len(projects) > 0:
                return projects[:3]
            
            logger.warning("⚠️ LLM returned invalid projects, using defaults")
            return self._get_default_projects()
            
        except Exception as e:
            logger.error(f"Failed to get project suggestions: {e}", exc_info=True)
            return self._get_default_projects()

    
    async def _analyze_against_jd(
        self,
        resume: Dict[str, Any],
        jd_text: str
    ) -> Dict[str, Any]:
        """Compare resume against job description using Groq"""
        
        # Extract resume details
        skills = resume.get("skills", {})
        tech_skills = skills.get("technical", [])
        soft_skills = skills.get("non_technical", [])
        all_skills = tech_skills + soft_skills
        
        experience = resume.get("experience", [])
        projects = resume.get("projects", [])
        
        # Build experience summary
        exp_summary = []
        for exp in experience[:3]:
            exp_summary.append(f"- {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
        
        prompt = f"""Compare this resume against the job description and provide specific ATS optimization advice.

**Job Description:**
{jd_text[:2500]}

**Resume Skills:** {', '.join(all_skills[:30]) if all_skills else 'Limited skills listed'}

**Experience:**
{chr(10).join(exp_summary) if exp_summary else 'No experience listed'}

**Projects:** {len(projects)} projects

Provide:
1. **Match Score** (0-100) - How well resume matches JD
2. **Matching Keywords** - Skills/terms found in BOTH resume and JD
3. **Missing Keywords** - Critical terms from JD NOT in resume
4. **5 Recommended Changes** - Specific edits to improve match
5. **10 ATS Keywords** - Most important keywords to add for this JD

Return ONLY valid JSON:
{{
  "match_score": 75,
  "matching_keywords": ["Python", "React", "AWS"],
  "missing_keywords": ["Docker", "Kubernetes", "CI/CD"],
  "recommended_changes": ["Add Docker experience", "Quantify achievements", "..."],
  "ats_keywords": ["Python", "JavaScript", "AWS", "Docker", "..."]
}}"""
        
        try:
            # ✅ FIXED: Use generate_json method
            analysis = await llm_service.generate_json(
                prompt=prompt,
                system_prompt="You are an ATS expert. Analyze resume-JD match and provide keyword optimization.",
                model="llama-3.3-70b-versatile"
            )
            
            # Validate
            if not isinstance(analysis, dict):
                raise ValueError("Invalid response")
            
            # Set defaults for missing fields
            analysis.setdefault("match_score", 50)
            analysis.setdefault("matching_keywords", all_skills[:10])
            analysis.setdefault("missing_keywords", ["Specific JD keywords"])
            analysis.setdefault("recommended_changes", ["Review JD carefully"])
            analysis.setdefault("ats_keywords", ["Keywords from JD"])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed JD analysis: {e}", exc_info=True)
            return {
                "match_score": 50,
                "matching_keywords": all_skills[:10],
                "missing_keywords": ["Review job description"],
                "recommended_changes": [
                    "Add keywords from job description",
                    "Quantify achievements with metrics",
                    "Tailor experience bullets to JD",
                    "Include relevant technical skills",
                    "Add industry-specific terminology"
                ],
                "ats_keywords": tech_skills[:10] if tech_skills else ["Python", "JavaScript", "SQL"]
            }
    
    # Helper methods

    
    def _format_experience_summary(self, experience: List[Dict]) -> str:
        """Format experience for prompt"""
        if not experience:
            return "- No experience listed"
        
        lines = []
        for exp in experience[:3]:
            title = exp.get("title", "N/A")
            company = exp.get("company", "N/A")
            duration = exp.get("duration", "N/A")
            lines.append(f"- {title} at {company} ({duration})")
        
        return "\n".join(lines)
    
    def _format_projects_summary(self, projects: List[Dict]) -> str:
        """Format projects for prompt"""
        if not projects:
            return "- No projects listed"
        
        lines = []
        for proj in projects[:3]:
            name = proj.get("name", "N/A")
            techs = proj.get("technologies", [])
            tech_str = ', '.join(techs[:5]) if techs else "N/A"
            lines.append(f"- {name} ({tech_str})")
        
        return "\n".join(lines)
    
    def _format_education_summary(self, education: List[Dict]) -> str:
        """Format education for prompt"""
        if not education:
            return "- No education listed"
        
        lines = []
        for edu in education:
            degree = edu.get("degree", "N/A")
            institution = edu.get("institution", "N/A")
            lines.append(f"- {degree} from {institution}")
        
        return "\n".join(lines)
    
    # backend/app/services/resume_analyzer_service.py - FIX LINE 464

    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from LLM response with markdown code blocks"""
        try:
            if not response or not response.strip():
                logger.error("Empty LLM response received")
                raise ValueError("Empty LLM response")

            cleaned = response.strip()

            # 🔹 Log raw response
            logger.debug(f"Raw LLM response (first 500 chars):\n{cleaned[:500]}")

            # 🔹 Extract JSON inside markdown code fences if present
            code_block_pattern = re.compile(
                r"```(?:json)?\s*(.*?)\s*```",
                re.DOTALL | re.IGNORECASE
            )

            match = code_block_pattern.search(cleaned)
            if match:
                cleaned = match.group(1)

            logger.debug(f"Cleaned JSON (first 500 chars):\n{cleaned[:500]}")

            parsed = json.loads(cleaned)

            logger.debug(f"Successfully parsed JSON of type: {type(parsed)}")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Response was:\n{response[:1000]}")
            raise

    
    def _get_default_ats_score(self) -> Dict[str, Any]:
        """Fallback ATS score"""
        return {
            "overall_score": 60,
            "breakdown": {
                "contact_info": 10,
                "skills": 15,
                "experience": 15,
                "education": 10,
                "projects": 5,
                "formatting": 5
            },
            "grade": "C+",
            "message": "Unable to analyze - upload resume to get detailed score"
        }
    
    def _get_default_suggestions(self) -> Dict[str, List[str]]:
        """Fallback suggestions"""
        return {
            "strengths": [
                "Resume structure appears organized",
                "Contact information is present",
                "Some technical skills listed"
            ],
            "weaknesses": [
                "Limited quantifiable achievements",
                "Could use more specific technical keywords",
                "Experience section needs more detail"
            ],
            "improvements": [
                "Add metrics to experience bullets (e.g., 'Reduced load time by 40%')",
                "Include more industry-specific technical keywords",
                "Add a professional summary highlighting key achievements",
                "Ensure all dates are consistently formatted",
                "Add links to GitHub, LinkedIn, or portfolio projects"
            ]
        }
    
    def _get_default_projects(self) -> List[Dict[str, Any]]:
        """Fallback project suggestions"""
        return [
            {
                "name": "Full-Stack E-Commerce Platform",
                "description": "Build a scalable online marketplace with payment integration, user authentication, admin dashboard, and real-time inventory management",
                "technologies": ["React", "Node.js", "PostgreSQL", "Redis", "Stripe API"],
                "value": "Demonstrates full-stack capabilities, database design, payment integration, and production-ready architecture"
            },
            {
                "name": "AI-Powered Chatbot Application",
                "description": "Create an intelligent chatbot using LLMs with context-aware responses, conversation history, and multi-turn dialogue capabilities",
                "technologies": ["Python", "LangChain", "OpenAI API", "FastAPI", "PostgreSQL"],
                "value": "Shows modern AI/ML skills, API integration, and understanding of NLP technologies"
            },
            {
                "name": "DevOps CI/CD Pipeline",
                "description": "Set up automated testing, deployment, and monitoring infrastructure for a microservices application with container orchestration",
                "technologies": ["Docker", "Kubernetes", "GitHub Actions", "AWS/GCP", "Terraform"],
                "value": "Proves understanding of modern DevOps practices, cloud infrastructure, and automation"
            }
        ]


# Singleton
resume_analyzer = ResumeAnalyzerService()
