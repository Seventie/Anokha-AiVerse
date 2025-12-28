# backend/app/services/job_scraper_service.py

from jobspy import scrape_jobs
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class JobScraperService:
    """Real job scraping using python-jobspy"""
    
    async def scrape_jobs(
        self, 
        search_term: str,
        location: str = "India",
        results_wanted: int = 20,
        job_type: str = "fulltime"
    ) -> List[Dict[str, Any]]:
        """
        Scrape jobs from LinkedIn, Indeed, Glassdoor
        
        Args:
            search_term: Job title/keyword (e.g., "Python Developer")
            location: Location (e.g., "India", "Bangalore")
            results_wanted: Number of jobs to fetch
            job_type: "fulltime", "parttime", "internship", "contract"
        
        Returns:
            List of job dictionaries
        """
        try:
            logger.info(f"🔍 Scraping {results_wanted} {job_type} jobs for '{search_term}' in {location}")
            
            jobs_df = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor"],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=72,  # Jobs posted in last 3 days
                country_indeed='India',
                linkedin_fetch_description=True,
                job_type=job_type
            )
            
            if jobs_df is None or len(jobs_df) == 0:
                logger.warning("No jobs found")
                return []
            
            jobs = []
            for _, row in jobs_df.iterrows():
                # Handle NaN values properly
                salary_min = row.get("min_amount")
                salary_max = row.get("max_amount")
                
                # Convert pandas NaN to None
                if pd.isna(salary_min):
                    salary_min = None
                else:
                    try:
                        salary_min = int(float(salary_min))
                    except (ValueError, TypeError):
                        salary_min = None
                
                if pd.isna(salary_max):
                    salary_max = None
                else:
                    try:
                        salary_max = int(float(salary_max))
                    except (ValueError, TypeError):
                        salary_max = None
                
                # Get description safely
                description = row.get("description")
                if pd.isna(description):
                    description = ""
                else:
                    description = str(description).strip()
                
                # Get currency safely
                currency = row.get("currency")
                if pd.isna(currency) or not currency:
                    currency = "INR"  # Default to INR for India
                else:
                    currency = str(currency).strip()
                
                # Get location safely
                location_val = row.get("location")
                if pd.isna(location_val):
                    location_val = location
                else:
                    location_val = str(location_val).strip()
                
                # Get posted date safely
                posted_date = row.get("date_posted")
                if pd.isna(posted_date):
                    posted_date = datetime.utcnow()
                
                jobs.append({
                    "title": str(row.get("title", "Unknown Position")).strip(),
                    "company": str(row.get("company", "Unknown Company")).strip(),
                    "location": location_val,
                    "job_type": job_type,
                    "is_remote": "remote" in location_val.lower(),
                    "description": description,
                    "requirements": self._extract_requirements(description),
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "salary_currency": currency,
                    "experience_level": self._extract_experience_level(description),
                    "url": str(row.get("job_url", "")).strip(),
                    "source": str(row.get("site", "Unknown")).strip(),
                    "posted_date": posted_date,
                })
            
            logger.info(f"✅ Scraped {len(jobs)} jobs successfully")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Job scraping error: {e}", exc_info=True)
            return []
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract tech skills from job description"""
        if not description or description == "nan":
            return []
        
        # Comprehensive tech skills list
        skills = [
            # Programming Languages
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
            "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB",
            
            # Web Frameworks
            "React", "Angular", "Vue", "Svelte", "Next.js", "Nuxt.js",
            "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring Boot",
            "ASP.NET", "Laravel", "Rails",
            
            # Mobile
            "React Native", "Flutter", "iOS", "Android", "Xamarin",
            
            # Databases
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "Cassandra", "DynamoDB", "Oracle", "SQL Server",
            
            # Cloud & DevOps
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI",
            
            # AI/ML
            "Machine Learning", "Deep Learning", "AI", "NLP", "GenAI",
            "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "OpenAI",
            "LangChain", "Transformers",
            
            # Data
            "Data Science", "Data Engineering", "ETL", "Spark", "Hadoop",
            "Kafka", "Airflow", "Pandas", "NumPy",
            
            # Other
            "Git", "REST API", "GraphQL", "Microservices", "Agile", "Scrum",
            "CI/CD", "Testing", "Linux", "Bash"
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        # Return unique skills, limit to 15
        return list(set(found_skills))[:15]
    
    def _extract_experience_level(self, description: str) -> str:
        """Determine experience level from description"""
        if not description or description == "nan":
            return "Mid-Level"
        
        description_lower = description.lower()
        
        # Check for experience level indicators
        if any(word in description_lower for word in [
            "senior", "lead", "principal", "staff", "architect", "director", "vp"
        ]):
            return "Senior"
        elif any(word in description_lower for word in [
            "junior", "entry", "entry-level", "graduate", "fresher", "trainee"
        ]):
            return "Entry Level"
        elif "intern" in description_lower:
            return "Internship"
        else:
            return "Mid-Level"
    
    async def scrape_internships_india(self, domain: str = "Technology") -> List[Dict[str, Any]]:
        """
        Scrape internships from Internshala
        
        Args:
            domain: Domain like "Technology", "Marketing", "Design"
        
        Returns:
            List of internship dictionaries
        """
        try:
            url = f"https://internshala.com/internships/{domain.lower()}-internship/"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
            
            if response.status_code != 200:
                logger.warning(f"Internshala returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            internships = []
            
            # Parse internship cards
            cards = soup.find_all("div", class_="internship_meta")
            
            for card in cards[:20]:
                try:
                    title_elem = card.find("h3")
                    company_elem = card.find("a", class_="link_display_like_text")
                    location_elem = card.find("span", class_="location_link")
                    link_elem = card.find("a")
                    
                    if title_elem and company_elem:
                        internships.append({
                            "title": title_elem.text.strip(),
                            "company": company_elem.text.strip(),
                            "location": location_elem.text.strip() if location_elem else "Remote",
                            "job_type": "internship",
                            "is_remote": False,
                            "description": "",
                            "requirements": [],
                            "salary_min": None,
                            "salary_max": None,
                            "salary_currency": "INR",
                            "experience_level": "Internship",
                            "url": "https://internshala.com" + link_elem["href"] if link_elem and link_elem.get("href") else "",
                            "source": "Internshala",
                            "posted_date": datetime.utcnow(),
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse internship card: {e}")
                    continue
            
            logger.info(f"✅ Scraped {len(internships)} internships from Internshala")
            return internships
            
        except Exception as e:
            logger.error(f"❌ Internshala scraping error: {e}", exc_info=True)
            return []


class HackathonScraperService:
    """Scrape hackathons from Devpost, Unstop, MLH, Devfolio"""
    
    async def scrape_devpost(self) -> List[Dict[str, Any]]:
        """Scrape live hackathons from Devpost"""
        try:
            url = "https://devpost.com/hackathons"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
            
            if response.status_code != 200:
                logger.warning(f"Devpost returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            hackathons = []
            
            # Find hackathon cards
            cards = soup.find_all("div", class_="hackathon-tile")
            
            for card in cards[:15]:
                try:
                    title_elem = card.find("h3")
                    link_elem = card.find("a")
                    prize_elem = card.find("div", class_="prize-amount")
                    themes_elem = card.find_all("span", class_="challenge-tag")
                    
                    if title_elem and link_elem:
                        href = link_elem.get("href", "")
                        if href and not href.startswith("http"):
                            href = "https://devpost.com" + href
                        
                        themes = [tag.text.strip() for tag in themes_elem] if themes_elem else []
                        
                        hackathons.append({
                            "title": title_elem.text.strip(),
                            "organizer": "Devpost",
                            "platform": "Devpost",
                            "description": "",
                            "themes": themes[:5],  # Limit to 5 themes
                            "prize_pool": prize_elem.text.strip() if prize_elem else "N/A",
                            "start_date": None,
                            "end_date": None,
                            "registration_deadline": None,
                            "mode": "online",
                            "location": None,
                            "url": href,
                            "eligibility": "Open to all"
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Devpost card: {e}")
                    continue
            
            logger.info(f"✅ Scraped {len(hackathons)} hackathons from Devpost")
            return hackathons
            
        except Exception as e:
            logger.error(f"❌ Devpost scraping error: {e}", exc_info=True)
            return []
    
    async def scrape_unstop(self) -> List[Dict[str, Any]]:
        """Scrape competitions from Unstop (formerly Dare2Compete)"""
        try:
            url = "https://unstop.com/hackathons"
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
            
            if response.status_code != 200:
                logger.warning(f"Unstop returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            hackathons = []
            
            # Parse competition cards
            cards = soup.find_all("div", class_="opportunity-card")[:15]
            
            for card in cards:
                try:
                    title_elem = card.find("h3") or card.find("h2")
                    link_elem = card.find("a")
                    prize_elem = card.find("span", class_="prize") or card.find("div", class_="prize")
                    
                    if title_elem:
                        href = link_elem.get("href", "") if link_elem else ""
                        if href and not href.startswith("http"):
                            href = "https://unstop.com" + href
                        
                        hackathons.append({
                            "title": title_elem.text.strip(),
                            "organizer": "Unstop",
                            "platform": "Unstop",
                            "description": "",
                            "themes": [],
                            "prize_pool": prize_elem.text.strip() if prize_elem else "N/A",
                            "start_date": None,
                            "end_date": None,
                            "registration_deadline": None,
                            "mode": "online",
                            "location": None,
                            "url": href,
                            "eligibility": "Students & Professionals"
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Unstop card: {e}")
                    continue
            
            logger.info(f"✅ Scraped {len(hackathons)} from Unstop")
            return hackathons
            
        except Exception as e:
            logger.error(f"❌ Unstop scraping error: {e}", exc_info=True)
            return []
    
    async def scrape_mlh(self) -> List[Dict[str, Any]]:
        """Scrape hackathons from Major League Hacking"""
        try:
            url = "https://mlh.io/seasons/2025/events"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
            
            if response.status_code != 200:
                logger.warning(f"MLH returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            hackathons = []
            
            # MLH event cards
            cards = soup.find_all("div", class_="event")[:10]
            
            for card in cards:
                try:
                    title_elem = card.find("h3")
                    link_elem = card.find("a")
                    date_elem = card.find("p", class_="event-date")
                    
                    if title_elem:
                        hackathons.append({
                            "title": title_elem.text.strip(),
                            "organizer": "MLH",
                            "platform": "Major League Hacking",
                            "description": "",
                            "themes": [],
                            "prize_pool": "N/A",
                            "start_date": None,
                            "end_date": None,
                            "registration_deadline": None,
                            "mode": "online",
                            "location": None,
                            "url": link_elem.get("href", "") if link_elem else "",
                            "eligibility": "Students"
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse MLH card: {e}")
                    continue
            
            logger.info(f"✅ Scraped {len(hackathons)} from MLH")
            return hackathons
            
        except Exception as e:
            logger.error(f"❌ MLH scraping error: {e}", exc_info=True)
            return []


# Singleton instances
job_scraper = JobScraperService()
hackathon_scraper = HackathonScraperService()
