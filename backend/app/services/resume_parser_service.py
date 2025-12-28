# backend/app/services/resume_parser_service.py

import json
import re
import os
from datetime import datetime
from typing import Dict, Any, Optional
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
                # Import Groq lazily to avoid heavy imports at module import time
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
        # If client not initialized, return empty (fallback to basic parsing)
        if not self.client:
            logger.debug("LLM client not available — skipping LLM calls")
            return ""

        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a precise resume parser. Always return valid JSON when asked."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
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
    
    def safe_json_loads(self, text: str):
        """Safely parse JSON from LLM response"""
        if not text or not text.strip():
            return []
        
        text = re.sub(r"``````", "", text).strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
        return text

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(docx_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text]
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
    
    def parse_personal_info(self, text: str) -> Dict[str, Any]:
        """Parse personal info from LLM output"""
        result = {
            "fullName": None, "email": None, "phone": None,
            "location": None, "linkedin": None, "github": None,
            "portfolio": None, "summary": None
        }

        if not text:
            return result

        for line in text.splitlines():
            line = line.strip()
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            value = value.strip()
            key = key.lower()

            if "name" in key:
                result["fullName"] = value
            elif "email" in key:
                result["email"] = value
            elif "phone" in key:
                result["phone"] = value
            elif "location" in key:
                result["location"] = value
            elif "linkedin" in key:
                result["linkedin"] = value
            elif "github" in key:
                result["github"] = value
            elif "portfolio" in key:
                result["portfolio"] = value
            elif "summary" in key:
                result["summary"] = value

        return result
    
    def parse_skill_sections(self, text: str) -> Dict[str, list]:
        """Parse skill sections"""
        result = {"technical": [], "non_technical": []}
        section = None

        for line in text.splitlines():
            line = line.strip()
            if line == "TECHNICAL:":
                section = "technical"
            elif line == "NON_TECHNICAL:":
                section = "non_technical"
            elif line.startswith("-") and section:
                result[section].append(line[1:].strip())

        return result
    
    async def extract_personal_info(self, resume_text: str) -> Dict[str, Any]:
        """Extract personal information"""
        prompt = f"""
Extract personal information from the resume.
Return EXACTLY in this format (one per line):

Full Name: ...
Email: ...
Phone: ...
Location: ...
LinkedIn: ...
GitHub: ...
Portfolio: ...
Summary: ...

Resume:
{resume_text[:2000]}
"""
        
        raw = await self.call_llm(prompt)
        return self.parse_personal_info(raw)
    
    async def extract_education(self, resume_text: str) -> list:
        """Extract education"""
        prompt = f"""
Extract ALL education entries from the resume.
Return ONLY a JSON array like this:
[
    {{
        "degree": "Bachelor of Science in Computer Science",
        "institution": "University Name",
        "year": "2020",
        "gpa": "3.8"
    }}
]

Resume:
{resume_text[:3000]}
"""
        
        raw = await self.call_llm(prompt)
        education = self.safe_json_loads(raw)
        return education if isinstance(education, list) else []
    
    async def extract_experience(self, resume_text: str) -> list:
        """Extract work experience"""
        prompt = f"""
Extract ALL work experience from the resume.
Return ONLY a JSON array like this:
[
    {{
        "title": "Software Engineer",
        "company": "Company Name",
        "duration": "Jan 2020 - Dec 2022",
        "responsibilities": ["Built APIs", "Led team"]
    }}
]

Resume:
{resume_text[:4000]}
"""
        
        raw = await self.call_llm(prompt)
        experience = self.safe_json_loads(raw)
        return experience if isinstance(experience, list) else []
    
    async def extract_projects(self, resume_text: str) -> list:
        """Extract projects"""
        prompt = f"""
Extract ALL projects from the resume.
Return ONLY a JSON array like this:
[
    {{
        "name": "Project Name",
        "description": "What it does",
        "technologies": ["Python", "React"],
        "link": "github.com/user/repo"
    }}
]

Resume:
{resume_text[:3000]}
"""
        
        raw = await self.call_llm(prompt)
        projects = self.safe_json_loads(raw)
        return projects if isinstance(projects, list) else []
    
    async def extract_skills(self, resume_text: str) -> Dict[str, list]:
        """Extract and classify skills"""
        prompt = f"""
Extract ALL skills from the resume and classify them.

Return in EXACTLY this format:

TECHNICAL:
- Python
- JavaScript
- React

NON_TECHNICAL:
- Leadership
- Communication

Resume:
{resume_text[:3000]}
"""
        
        raw = await self.call_llm(prompt)
        return self.parse_skill_sections(raw)
    
    async def parse_resume(
        self,
        file_path: str,
        jd_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main parsing function
        
        Args:
            file_path: Path to PDF resume
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
        personal_info = await self.extract_personal_info(resume_text)
        await asyncio.sleep(1)  # Rate limit buffer
        
        education = await self.extract_education(resume_text)
        await asyncio.sleep(1)
        
        experience = await self.extract_experience(resume_text)
        await asyncio.sleep(1)
        
        projects = await self.extract_projects(resume_text)
        await asyncio.sleep(1)
        
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
        
        # If JD provided, calculate match score
        if jd_text:
            # TODO: Add JD matching logic
            pass
        
        logger.info("✅ Resume parsed successfully")
        return resume_json


# Singleton
resume_parser_service = ResumeParserService()
