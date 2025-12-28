# backend/app/routes/profile.py

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import jwt
import logging
from datetime import datetime

from app.config.database import get_db
from app.config.settings import settings
from app.models.database import (
    User, Education, Skill, Project, Experience, 
    CareerGoal, CareerIntent, Link, Availability,
    PreferredLocation, UserResume
)
from app.services.llm_service import llm_service
from app.services.resume_parser_service import resume_parser_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profile", tags=["Profile"])

# ==================== AUTH ====================
async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authentication token")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        return {"user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# ==================== SCHEMAS ====================
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    location: Optional[str] = None
    target_role: Optional[str] = None
    timeline: Optional[str] = None
    vision_statement: Optional[str] = None

class EducationItem(BaseModel):
    institution: str
    degree: str
    major: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None

class ExperienceItem(BaseModel):
    role: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class ProjectItem(BaseModel):
    title: str
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    link: Optional[str] = None

class SkillItem(BaseModel):
    skill: str
    category: str = "technical"
    level: str = "intermediate"

# ==================== ENDPOINTS ====================

@router.get("/complete")
async def get_complete_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """📋 Get complete user profile with all data"""
    try:
        user_id = current_user["user_id"]
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User not found")
        
        # Get all related data
        education = db.query(Education).filter(Education.user_id == user_id).all()
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        projects = db.query(Project).filter(Project.user_id == user_id).all()
        experience = db.query(Experience).filter(Experience.user_id == user_id).all()
        career_goal = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
        career_intent = db.query(CareerIntent).filter(CareerIntent.user_id == user_id).first()
        links = db.query(Link).filter(Link.user_id == user_id).all()
        availability = db.query(Availability).filter(Availability.user_id == user_id).first()
        preferred_locs = db.query(PreferredLocation).filter(PreferredLocation.user_id == user_id).all()
        resume = db.query(UserResume).filter(
            UserResume.user_id == user_id,
            UserResume.is_active == True
        ).first()
        
        # ✅ FIX: Handle both fullname and full_name attributes
        full_name = getattr(user, 'fullname', None) or getattr(user, 'full_name', None) or user.email.split('@')[0]
        
        # Calculate completeness
        completeness = 0
        total_sections = 10
        
        if full_name: completeness += 1
        if user.location: completeness += 1
        if education: completeness += 1
        if skills: completeness += 1
        if experience: completeness += 1
        if projects: completeness += 1
        if career_goal and career_goal.target_roles: completeness += 1
        if career_intent and career_intent.intent_text: completeness += 1
        if links: completeness += 1
        if resume: completeness += 1
        
        completeness_score = int((completeness / total_sections) * 100)
        
        # Missing sections
        missing = []
        if not education: missing.append("Education - Add your academic background")
        if not experience: missing.append("Experience - Add work experience")
        if not projects: missing.append("Projects - Showcase your work")
        if not skills or len(skills) < 5: missing.append("Skills - Add at least 5 skills")
        if not career_intent or not career_intent.intent_text: missing.append("Vision Statement - Define your career vision")
        if not links: missing.append("Links - Add your GitHub, LinkedIn profiles")
        if not resume: missing.append("Resume - Upload your resume")
        
        return {
            "success": True,
            "profile": {
                "id": user.id,
                "email": user.email,
                "full_name": full_name,
                "location": user.location or "",
                "readiness_level": user.readiness_level.value if user.readiness_level else "beginner",
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "career_goals": {
                "target_roles": career_goal.target_roles if career_goal and career_goal.target_roles else [],
                "timeline": career_goal.target_timeline if career_goal else "",
                "vision_statement": career_intent.intent_text if career_intent else ""
            },
            "education": [
                {
                    "id": e.id,
                    "institution": e.institution,
                    "degree": e.degree,
                    "major": e.major or "",
                    "location": e.location or "",
                    "start_date": e.start_date or "",
                    "end_date": e.end_date or "",
                    "grade": e.grade or ""
                }
                for e in education
            ],
            "experience": [
                {
                    "id": e.id,
                    "role": e.role,
                    "company": e.company,
                    "location": e.location or "",
                    "start_date": e.start_date or "",
                    "end_date": e.end_date or "",
                    "description": e.description or ""
                }
                for e in experience
            ],
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description or "",
                    "tech_stack": p.tech_stack or "",
                    "link": p.link or ""
                }
                for p in projects
            ],
            "skills": [
                {
                    "id": s.id,
                    "skill": s.skill,
                    "category": s.category.value if s.category else "technical",
                    "level": s.level.value if s.level else "intermediate"
                }
                for s in skills
            ],
            "links": [
                {
                    "id": l.id,
                    "type": l.type.value if l.type else "other",
                    "url": l.url
                }
                for l in links
            ],
            "availability": {
                "free_time": availability.free_time if availability else "",
                "study_days": availability.study_days if availability else []
            } if availability else None,
            "preferred_locations": [loc.location for loc in preferred_locs],
            "resume": {
                "id": resume.id,
                "filename": resume.original_filename,
                "uploaded_at": resume.created_at.isoformat() if resume.created_at else None
            } if resume else None,
            "completeness_score": completeness_score,
            "missing_sections": missing
        }
    
    except Exception as e:
        logger.error(f"Failed to get complete profile: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.patch("/basic")
async def update_basic_profile(
    updates: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """✏️ Update basic profile information"""
    try:
        user_id = current_user["user_id"]
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User not found")
        
        # ✅ FIX: Handle both fullname and full_name
        if updates.full_name:
            if hasattr(user, 'fullname'):
                user.fullname = updates.full_name
            elif hasattr(user, 'full_name'):
                user.full_name = updates.full_name
        
        if updates.location:
            user.location = updates.location
        
        # Update career goals
        if updates.target_role or updates.timeline:
            career_goal = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
            if not career_goal:
                career_goal = CareerGoal(user_id=user_id)
                db.add(career_goal)
            
            if updates.target_role:
                career_goal.target_roles = [updates.target_role]
            if updates.timeline:
                career_goal.target_timeline = updates.timeline
        
        # Update vision statement
        if updates.vision_statement:
            career_intent = db.query(CareerIntent).filter(CareerIntent.user_id == user_id).first()
            if not career_intent:
                career_intent = CareerIntent(user_id=user_id, intent_text=updates.vision_statement)
                db.add(career_intent)
            else:
                career_intent.intent_text = updates.vision_statement
        
        db.commit()
        
        return {"message": "Profile updated successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(500, str(e))


# Similar endpoints for Experience, Projects, Skills...
# (I'll include a few more for completeness)

@router.post("/experience")
async def add_experience(
    item: ExperienceItem,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """➕ Add experience entry"""
    user_id = current_user["user_id"]
    
    exp = Experience(
        user_id=user_id,
        role=item.role,
        company=item.company,
        location=item.location,
        start_date=item.start_date,
        end_date=item.end_date,
        description=item.description,
        is_confirmed=True
    )
    
    db.add(exp)
    db.commit()
    db.refresh(exp)
    
    return {"success": True, "id": exp.id}

@router.delete("/experience/{exp_id}")
async def delete_experience(
    exp_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    user_id = current_user["user_id"]
    
    exp = db.query(Experience).filter(
        Experience.id == exp_id,
        Experience.user_id == user_id
    ).first()
    
    if not exp:
        raise HTTPException(404, "Experience not found")
    
    db.delete(exp)
    db.commit()
    
    return {"message": "Deleted successfully"}

@router.post("/project")
async def add_project(
    item: ProjectItem,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    user_id = current_user["user_id"]
    
    proj = Project(
        user_id=user_id,
        title=item.title,
        description=item.description,
        tech_stack=item.tech_stack,
        link=item.link,
        is_confirmed=True
    )
    
    db.add(proj)
    db.commit()
    db.refresh(proj)
    
    return {"success": True, "id": proj.id}

@router.delete("/project/{proj_id}")
async def delete_project(
    proj_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    user_id = current_user["user_id"]
    
    proj = db.query(Project).filter(
        Project.id == proj_id,
        Project.user_id == user_id
    ).first()
    
    if not proj:
        raise HTTPException(404, "Project not found")
    
    db.delete(proj)
    db.commit()
    
    return {"message": "Deleted successfully"}

@router.post("/skill")
async def add_skill(
    item: SkillItem,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    from app.models.database import SkillCategory, SkillLevel
    
    user_id = current_user["user_id"]
    
    skill = Skill(
        user_id=user_id,
        skill=item.skill,
        category=SkillCategory(item.category),
        level=SkillLevel(item.level),
        is_confirmed=True
    )
    
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    return {"success": True, "id": skill.id}

@router.delete("/skill/{skill_id}")
async def delete_skill(
    skill_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    user_id = current_user["user_id"]
    
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == user_id
    ).first()
    
    if not skill:
        raise HTTPException(404, "Skill not found")
    
    db.delete(skill)
    db.commit()
    
    return {"message": "Deleted successfully"}

@router.get("/skills")
async def get_skills(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    user_id = current_user["user_id"]
    
    skills = db.query(Skill).filter(Skill.user_id == user_id).all()
    
    return [
        {
            "id": s.id,
            "skill": s.skill,
            "category": s.category.value,
            "level": s.level.value
        }
        for s in skills
    ]
