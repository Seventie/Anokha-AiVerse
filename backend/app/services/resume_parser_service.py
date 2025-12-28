# backend/app/services/resume_parser_service.py - FIXED VERSION

import json
import re
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
from pathlib import Path
import pdfplumber
from docx import Document

from app.config.settings import settings

import logging
logger = logging.getLogger(__name__)


class ResumeParserService:
    """
    Resume parsing service using Groq LLM
    Extracts structured data from resume PDFs
    """
    
    def __init__(self):
        # Initialize Groq client only if API key is provided
        self.client = None
        self.model = None
        if settings.GROQ_API_KEY:
            try:
                from groq import Groq
                self.client = Groq(api_key=settings.GROQ_API_KEY)
                self.model = "llama-3.3-70b-versatile"
                logger.info("✅ Resume Parser Service initialized with Groq")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")
                self.client = None
                self.model = None
        else:
            logger.info("⚠️ GROQ_API_KEY not set — running parser in offline/basic mode")
    
    async def call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """Call Groq LLM with retry logic"""
        import time
        
        if not self.client:
            logger.debug("LLM client not available — skipping LLM calls")
            return ""

        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a precise resume parser. Always return valid JSON when asked. Extract ALL information accurately."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1  # Lower temperature for more accurate extraction
                )
                return response.choices[0].message.content

            except Exception as e:
                error_str = str(e)

                if "rate_limit" in error_str or "429" in error_str:
                    wait_match = re.search(r"try again in ([\d.]+)s", error_str)
                    wait_time = float(wait_match.group(1)) if wait_match else 10

                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit. Waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time + 1)
                        continue

                logger.error(f"LLM Error: {e}")
                return ""

        return ""
    
    # backend/app/services/resume_parser_service.py - FIX LINE 87

    def safe_json_loads(self, text: str):
        """Safely parse JSON from LLM response"""
        
        if not text or not text.strip():
            return []

        text = text.strip()

        # 🔹 Remove markdown code blocks (```json ... ``` or ``` ... ```)
        code_block_pattern = re.compile(
            r"```(?:json)?\s*(.*?)\s*```",
            re.DOTALL | re.IGNORECASE
        )

        match = code_block_pattern.search(text)
        if match:
            text = match.group(1)

        # 🔹 Try parsing JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Failed to parse JSON text:\n{text[:500]}")
            return []


    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
        return text

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(docx_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Error reading DOCX: {e}")
            return ""

    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading TXT: {e}")
            return ""

    def extract_text(self, file_path: str) -> str:
        """Extract text from supported resume files"""
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return self.extract_text_from_pdf(file_path)
        if suffix == ".docx":
            return self.extract_text_from_docx(file_path)
        if suffix == ".txt":
            return self.extract_text_from_txt(file_path)
        return ""
    
    def extract_urls_regex(self, text: str) -> Dict[str, Optional[str]]:
        """Fallback: Extract URLs using regex patterns"""
        result = {
            "linkedin": None,
            "github": None,
            "portfolio": None
        }
        
        # LinkedIn patterns
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'linkedin\.com/pub/[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+'
        ]
        for pattern in linkedin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["linkedin"] = match.group(0)
                if not result["linkedin"].startswith("http"):
                    result["linkedin"] = "https://" + result["linkedin"]
                break
        
        # GitHub patterns
        github_patterns = [
            r'github\.com/[\w-]+',
            r'www\.github\.com/[\w-]+'
        ]
        for pattern in github_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["github"] = match.group(0)
                if not result["github"].startswith("http"):
                    result["github"] = "https://" + result["github"]
                break
        
        # Portfolio/website patterns
        portfolio_patterns = [
            r'https?://[\w\.-]+\.[\w]{2,}/?[\w\.-]*',
            r'www\.[\w\.-]+\.[\w]{2,}'
        ]
        for pattern in portfolio_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Skip if it's linkedin or github
                if 'linkedin' not in match.lower() and 'github' not in match.lower():
                    result["portfolio"] = match
                    if not result["portfolio"].startswith("http"):
                        result["portfolio"] = "https://" + result["portfolio"]
                    break
            if result["portfolio"]:
                break
        
        return result
    
    async def extract_personal_info(self, resume_text: str) -> Dict[str, Any]:
        """Extract personal information with better URL extraction"""
        
        prompt = f"""Extract personal information from this resume.

Return ONLY valid JSON in this exact format:
{{
  "fullName": "John Doe",
  "email": "john@email.com",
  "phone": "+1234567890",
  "location": "City, State",
  "linkedin": "https://linkedin.com/in/johndoe",
  "github": "https://github.com/johndoe",
  "portfolio": "https://johndoe.com",
  "summary": "Professional summary or objective"
}}

Extract ALL links carefully. Include full URLs with https://.
If any field is not found, use null.

Resume:
{resume_text[:3000]}"""
        
        raw = await self.call_llm(prompt)
        personal_info = self.safe_json_loads(raw)
        
        # If parsing failed or returned a list, create empty dict
        if not isinstance(personal_info, dict):
            personal_info = {}
        
        # Fallback: Use regex to extract URLs if LLM missed them
        if not personal_info.get("linkedin") or not personal_info.get("github"):
            regex_urls = self.extract_urls_regex(resume_text)
            if not personal_info.get("linkedin"):
                personal_info["linkedin"] = regex_urls["linkedin"]
            if not personal_info.get("github"):
                personal_info["github"] = regex_urls["github"]
            if not personal_info.get("portfolio"):
                personal_info["portfolio"] = regex_urls["portfolio"]
        
        # Ensure all expected fields exist
        default_fields = {
            "fullName": None, "email": None, "phone": None,
            "location": None, "linkedin": None, "github": None,
            "portfolio": None, "summary": None
        }
        for key, default_value in default_fields.items():
            if key not in personal_info:
                personal_info[key] = default_value
        
        return personal_info
    
    async def extract_education(self, resume_text: str) -> list:
        """Extract education"""
        prompt = f"""Extract ALL education entries from this resume.

Return ONLY a valid JSON array like this:
[
  {{
    "degree": "Bachelor of Science in Computer Science",
    "institution": "University Name",
    "year": "2020-2024",
    "gpa": "3.8"
  }}
]

If no education found, return empty array: []

Resume:
{resume_text[:3000]}"""
        
        raw = await self.call_llm(prompt)
        education = self.safe_json_loads(raw)
        return education if isinstance(education, list) else []
    
    async def extract_experience(self, resume_text: str) -> list:
        """Extract work experience"""
        prompt = f"""Extract ALL work experience from this resume.

Return ONLY a valid JSON array like this:
[
  {{
    "title": "Software Engineer",
    "company": "Company Name",
    "duration": "Jan 2020 - Dec 2022",
    "responsibilities": [
      "Built REST APIs using Python and FastAPI",
      "Reduced query time by 40% through optimization"
    ]
  }}
]

Include ALL bullet points and achievements. Use metrics when available.
If no experience found, return empty array: []

Resume:
{resume_text[:4000]}"""
        
        raw = await self.call_llm(prompt)
        experience = self.safe_json_loads(raw)
        return experience if isinstance(experience, list) else []
    
    async def extract_projects(self, resume_text: str) -> list:
        """Extract projects"""
        prompt = f"""Extract ALL projects from this resume.

Return ONLY a valid JSON array like this:
[
  {{
    "name": "E-Commerce Platform",
    "description": "Full-stack web app with payment integration",
    "technologies": ["React", "Node.js", "PostgreSQL", "Stripe"],
    "link": "https://github.com/user/project"
  }}
]

Extract ALL technologies used. Include GitHub/live demo links if present.
If no projects found, return empty array: []

Resume:
{resume_text[:4000]}"""
        
        raw = await self.call_llm(prompt)
        projects = self.safe_json_loads(raw)
        return projects if isinstance(projects, list) else []
    
    def extract_skills_regex(self, text: str) -> Dict[str, List[str]]:
        """Fallback: Extract skills using keyword matching"""
        technical_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node', 'express', 'django', 'flask', 'fastapi', 'spring', 'sql', 'nosql',
            'mongodb', 'postgresql', 'mysql', 'redis', 'aws', 'azure', 'gcp', 'docker',
            'kubernetes', 'git', 'ci/cd', 'jenkins', 'terraform', 'html', 'css',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas',
            'numpy', 'scikit-learn', 'rest api', 'graphql', 'microservices'
        ]
        
        soft_keywords = [
            'leadership', 'communication', 'teamwork', 'problem solving',
            'critical thinking', 'time management', 'agile', 'scrum',
            'project management', 'collaboration', 'adaptability'
        ]
        
        text_lower = text.lower()
        
        technical = []
        for keyword in technical_keywords:
            if keyword in text_lower:
                # Capitalize properly
                technical.append(keyword.title())
        
        soft = []
        for keyword in soft_keywords:
            if keyword in text_lower:
                soft.append(keyword.title())
        
        return {
            "technical": list(set(technical)),  # Remove duplicates
            "non_technical": list(set(soft))
        }
    
    async def extract_skills(self, resume_text: str) -> Dict[str, list]:
        """Extract and classify skills with improved extraction"""
        prompt = f"""Extract ALL skills from this resume and classify them.

Return ONLY valid JSON in this format:
{{
  "technical": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "AWS"],
  "non_technical": ["Leadership", "Communication", "Agile", "Project Management"]
}}

Extract EVERY skill mentioned. Include:
- Programming languages
- Frameworks and libraries
- Tools and platforms
- Databases
- Cloud services
- Soft skills

If no skills found, return empty arrays.

Resume:
{resume_text[:4000]}"""
        
        raw = await self.call_llm(prompt)
        skills = self.safe_json_loads(raw)
        
        # If parsing failed or returned a list, use regex fallback
        if not isinstance(skills, dict):
            skills = self.extract_skills_regex(resume_text)
        else:
            # Ensure required fields exist
            if "technical" not in skills:
                skills["technical"] = []
            if "non_technical" not in skills:
                skills["non_technical"] = []
            
            # If LLM returned empty, try regex fallback
            if not skills["technical"] and not skills["non_technical"]:
                regex_skills = self.extract_skills_regex(resume_text)
                skills["technical"].extend(regex_skills["technical"])
                skills["non_technical"].extend(regex_skills["non_technical"])
        
        return skills
    
    async def parse_resume(
        self,
        file_path: str,
        jd_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main parsing function
        
        Args:
            file_path: Path to resume file (PDF, DOCX, TXT)
            jd_text: Optional job description for matching
            
        Returns:
            Parsed resume JSON
        """
        
        logger.info(f"📄 Parsing resume: {file_path}")
        
        # Extract text
        resume_text = self.extract_text(file_path)
        if not resume_text:
            raise ValueError("Could not extract text from file")
        
        logger.info(f"✅ Extracted {len(resume_text)} characters")
        
        # Run all extraction tasks sequentially to avoid rate limits
        logger.info("🔍 Extracting personal info...")
        personal_info = await self.extract_personal_info(resume_text)
        await asyncio.sleep(1.5)  # Rate limit buffer
        
        logger.info("🎓 Extracting education...")
        education = await self.extract_education(resume_text)
        await asyncio.sleep(1.5)
        
        logger.info("💼 Extracting experience...")
        experience = await self.extract_experience(resume_text)
        await asyncio.sleep(1.5)
        
        logger.info("🚀 Extracting projects...")
        projects = await self.extract_projects(resume_text)
        await asyncio.sleep(1.5)
        
        logger.info("⚡ Extracting skills...")
        skills = await self.extract_skills(resume_text)
        
        # Build final JSON
        resume_json = {
            "personal_info": personal_info,
            "education": education,
            "experience": experience,
            "projects": projects,
            "skills": skills,
            "certifications": [],
            "achievements": [],
            "languages": [],
            "metadata": {
                "parsed_at": datetime.utcnow().isoformat(),
                "confidence_score": 0.85,
                "source_file": Path(file_path).name
            }
        }
        
        logger.info("✅ Resume parsed successfully")
        logger.debug(f"Found: {len(skills.get('technical', []))} technical skills, "
                    f"{len(skills.get('non_technical', []))} soft skills, "
                    f"{len(experience)} experiences, {len(projects)} projects")
        
        return resume_json


# Singleton
resume_parser_service = ResumeParserService()
