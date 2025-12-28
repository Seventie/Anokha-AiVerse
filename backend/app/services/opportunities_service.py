# backend/app/services/opportunities_service.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.database import (
    User, Skill, CareerGoal, JobOpportunity, Hackathon, 
    UserJobMatch, UserHackathonMatch, OpportunityStatus
)
from app.services.job_scraper_service import job_scraper, hackathon_scraper
from app.services.llm_service import llm_service
from typing import List, Dict, Any
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class OpportunitiesService:
    """Match users with jobs and hackathons using AI"""
    
    async def scan_and_match_opportunities(
        self, 
        user_id: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Main workflow:
        1. Get user profile (skills, goals, location)
        2. Scrape jobs from LinkedIn, Indeed, Glassdoor
        3. Scrape internships from Internshala
        4. Scrape hackathons from Devpost, Unstop, MLH
        5. Store unique opportunities in database
        6. Match and score using LLM
        7. Return top matches
        """
        
        try:
            # 1. Get user profile
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            user_skills_objs = db.query(Skill).filter(Skill.user_id == user_id).all()
            user_skills = [s.skill for s in user_skills_objs]
            
            career_goals = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
            target_role = "Software Engineer"  # Default
            if career_goals and career_goals.target_roles:
                target_role = career_goals.target_roles[0]
            
            location = user.location or "India"
            
            logger.info(f"👤 User Profile: {len(user_skills)} skills, targeting '{target_role}' in {location}")
            
            # 2. Scrape jobs (full-time)
            logger.info("🔍 Scraping full-time jobs...")
            fulltime_jobs = await job_scraper.scrape_jobs(
                search_term=target_role,
                location=location,
                results_wanted=30,
                job_type="fulltime"
            )
            
            # 3. Scrape internships
            logger.info("🔍 Scraping internships...")
            internships = await job_scraper.scrape_internships_india(domain="Technology")
            
            # Combine all jobs
            all_jobs = fulltime_jobs + internships
            logger.info(f"📊 Total jobs scraped: {len(all_jobs)}")
            
            # 4. Store unique jobs in database
            stored_jobs = []
            for job_data in all_jobs:
                try:
                    # Skip if no URL
                    if not job_data.get("url"):
                        continue
                    
                    # Check if already exists
                    existing = db.query(JobOpportunity).filter(
                        JobOpportunity.url == job_data["url"]
                    ).first()
                    
                    if not existing:
                        job = JobOpportunity(
                            id=str(uuid.uuid4()),
                            title=job_data["title"],
                            company=job_data["company"],
                            location=job_data["location"],
                            job_type=job_data["job_type"],
                            is_remote=job_data["is_remote"],
                            description=job_data.get("description", ""),
                            requirements=job_data.get("requirements", []),
                            salary_min=job_data.get("salary_min"),
                            salary_max=job_data.get("salary_max"),
                            salary_currency=job_data.get("salary_currency", "INR"),
                            experience_level=job_data.get("experience_level"),
                            url=job_data["url"],
                            source=job_data.get("source", "Unknown"),
                            posted_date=job_data.get("posted_date"),
                            scraped_at=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(job)
                        db.flush()
                        stored_jobs.append(job)
                        logger.debug(f"✅ Stored: {job.title} at {job.company}")
                
                except Exception as e:
                    logger.error(f"Failed to store job: {e}")
                    continue
            
            db.commit()
            logger.info(f"💾 Stored {len(stored_jobs)} new jobs in database")
            
            # 5. Match and score jobs
            logger.info("🤖 Matching jobs with user profile...")
            job_matches = await self._match_user_to_jobs(user_id, user_skills, stored_jobs, db)
            
            # 6. Scrape and match hackathons
            logger.info("🏆 Scraping hackathons...")
            hackathon_matches = await self._scan_hackathons(user_id, user_skills, db)
            
            return {
                "success": True,
                "jobs_found": len(all_jobs),
                "jobs_stored": len(stored_jobs),
                "job_matches": len(job_matches),
                "hackathon_matches": len(hackathon_matches),
                "top_jobs": job_matches[:10],
                "top_hackathons": hackathon_matches[:5]
            }
        
        except Exception as e:
            logger.error(f"❌ Scan and match error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "jobs_found": 0,
                "jobs_stored": 0,
                "job_matches": 0,
                "hackathon_matches": 0
            }
    
    async def _match_user_to_jobs(
        self,
        user_id: str,
        user_skills: List[str],
        jobs: List[JobOpportunity],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Use LLM to score job compatibility"""
        
        matches = []
        
        for job in jobs:
            try:
                # Use existing LLM service to score compatibility
                score_data = await llm_service.score_job_compatibility(
                    user_skills=user_skills,
                    user_experience="2 years",  # TODO: Get from user profile
                    job_description=job.description or "",
                    job_requirements=", ".join(job.requirements or [])
                )
                
                compatibility_score = score_data.get("compatibility_score", 0)
                matching_skills = score_data.get("matching_skills", [])
                missing_skills = score_data.get("missing_skills", [])
                should_apply = score_data.get("should_apply", False)
                
                # Only store matches above 50% compatibility
                if compatibility_score >= 50:
                    # Store match in database
                    match = UserJobMatch(
                        user_id=user_id,
                        job_id=job.id,
                        match_score=compatibility_score,
                        matching_skills=matching_skills,
                        missing_skills=missing_skills,
                        status=OpportunityStatus.RECOMMENDED,
                        recommended_at=datetime.utcnow(),
                        viewed=False
                    )
                    db.add(match)
                    
                    matches.append({
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "url": job.url,
                        "job_type": job.job_type,
                        "match_score": compatibility_score,
                        "matching_skills": matching_skills,
                        "missing_skills": missing_skills,
                        "should_apply": should_apply
                    })
                    
                    logger.debug(f"✓ {job.title} at {job.company}: {compatibility_score}%")
            
            except Exception as e:
                logger.error(f"Failed to match job {job.id}: {e}")
                continue
        
        db.commit()
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        logger.info(f"✅ Matched {len(matches)} jobs above 50% compatibility")
        return matches
    
    async def _scan_hackathons(
        self,
        user_id: str,
        user_skills: List[str],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Scrape and match hackathons"""
        
        all_hackathons = []
        
        try:
            # Scrape from multiple platforms
            devpost_hacks = await hackathon_scraper.scrape_devpost()
            unstop_hacks = await hackathon_scraper.scrape_unstop()
            mlh_hacks = await hackathon_scraper.scrape_mlh()
            
            all_hackathons = devpost_hacks + unstop_hacks + mlh_hacks
            logger.info(f"🏆 Found {len(all_hackathons)} hackathons across all platforms")
            
            # Store in database
            for hack_data in all_hackathons:
                try:
                    if not hack_data.get("url"):
                        continue
                    
                    existing = db.query(Hackathon).filter(
                        Hackathon.url == hack_data["url"]
                    ).first()
                    
                    if not existing:
                        hackathon = Hackathon(
                            id=str(uuid.uuid4()),
                            title=hack_data["title"],
                            organizer=hack_data["organizer"],
                            platform=hack_data["platform"],
                            description=hack_data.get("description", ""),
                            themes=hack_data.get("themes", []),
                            prize_pool=hack_data.get("prize_pool"),
                            start_date=hack_data.get("start_date"),
                            end_date=hack_data.get("end_date"),
                            registration_deadline=hack_data.get("registration_deadline"),
                            mode=hack_data.get("mode", "online"),
                            location=hack_data.get("location"),
                            url=hack_data["url"],
                            eligibility=hack_data.get("eligibility", "Open to all"),
                            scraped_at=datetime.utcnow(),
                            is_active=True
                        )
                        db.add(hackathon)
                        db.flush()
                        
                        # Create user match (simple scoring for now)
                        match_score = 75.0  # Default match score
                        
                        # Boost score if themes match user skills
                        themes_lower = [t.lower() for t in hack_data.get("themes", [])]
                        skills_lower = [s.lower() for s in user_skills]
                        matching_count = sum(1 for theme in themes_lower if any(skill in theme for skill in skills_lower))
                        
                        if matching_count > 0:
                            match_score = min(90.0, 75.0 + (matching_count * 5))
                        
                        match = UserHackathonMatch(
                            user_id=user_id,
                            hackathon_id=hackathon.id,
                            match_score=match_score,
                            relevant_skills=user_skills[:5],
                            reason="Matches your technical skills and interests",
                            status=OpportunityStatus.RECOMMENDED,
                            recommended_at=datetime.utcnow()
                        )
                        db.add(match)
                
                except Exception as e:
                    logger.error(f"Failed to store hackathon: {e}")
                    continue
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to scan hackathons: {e}")
        
        return all_hackathons
    
    def get_user_matches(
        self,
        user_id: str,
        db: Session,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get user's matched opportunities from database"""
        
        try:
            # Get job matches with job details
            job_matches = db.query(UserJobMatch, JobOpportunity).join(
                JobOpportunity, UserJobMatch.job_id == JobOpportunity.id
            ).filter(
                UserJobMatch.user_id == user_id,
                JobOpportunity.is_active == True
            ).order_by(UserJobMatch.match_score.desc()).limit(limit).all()
            
            # Get hackathon matches
            hackathon_matches = db.query(UserHackathonMatch, Hackathon).join(
                Hackathon, UserHackathonMatch.hackathon_id == Hackathon.id
            ).filter(
                UserHackathonMatch.user_id == user_id,
                Hackathon.is_active == True
            ).order_by(UserHackathonMatch.match_score.desc()).limit(10).all()
            
            return {
                "jobs": [
                    {
                        "id": job.id,
                        "match_id": match.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "job_type": job.job_type.value if hasattr(job.job_type, 'value') else job.job_type,
                        "is_remote": job.is_remote,
                        "description": job.description[:200] + "..." if job.description and len(job.description) > 200 else job.description,
                        "requirements": job.requirements,
                        "salary_min": job.salary_min,
                        "salary_max": job.salary_max,
                        "salary_currency": job.salary_currency,
                        "experience_level": job.experience_level,
                        "url": job.url,
                        "source": job.source,
                        "match_score": match.match_score,
                        "matching_skills": match.matching_skills,
                        "missing_skills": match.missing_skills,
                        "status": match.status.value if hasattr(match.status, 'value') else match.status,
                        "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                        "recommended_at": match.recommended_at.isoformat() if match.recommended_at else None
                    }
                    for match, job in job_matches
                ],
                "hackathons": [
                    {
                        "id": hack.id,
                        "title": hack.title,
                        "organizer": hack.organizer,
                        "platform": hack.platform,
                        "description": hack.description[:200] + "..." if hack.description and len(hack.description) > 200 else hack.description,
                        "themes": hack.themes,
                        "prize_pool": hack.prize_pool,
                        "mode": hack.mode,
                        "url": hack.url,
                        "match_score": match.match_score,
                        "relevant_skills": match.relevant_skills,
                        "reason": match.reason
                    }
                    for match, hack in hackathon_matches
                ]
            }
        
        except Exception as e:
            logger.error(f"Failed to get user matches: {e}", exc_info=True)
            return {"jobs": [], "hackathons": []}

# Singleton instance
opportunities_service = OpportunitiesService()
