# backend/app/routes/resume.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import shutil
from pathlib import Path
import os
import jwt
import logging

from app.config.database import get_db
from app.config.settings import settings
from app.services.resume_parser_service import resume_parser_service
from app.services.resume_analyzer_service import resume_analyzer
from app.models.database import UserResume, CareerGoal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["Resume"])

UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt"}

# ==================== AUTH HELPER ====================
async def get_current_user(authorization: str = Header(None)) -> dict:
    """Extract user from JWT token"""
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

# ==================== UPLOAD & PARSE ====================

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    jd_text: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    📤 Upload and parse resume
    
    Accepts PDF, DOCX, or TXT files.
    Automatically parses and stores in database.
    """
    
    # Validate file type
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, "Only PDF, DOCX, or TXT files are supported")
    
    user_id = current_user["user_id"]
    
    # Save file
    file_path = UPLOAD_DIR / f"{user_id}_{file.filename}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📄 Parsing resume for user {user_id}: {file.filename}")
        
        # Parse resume
        parsed_data = await resume_parser_service.parse_resume(
            str(file_path),
            jd_text=jd_text
        )
        
        # Deactivate old resumes
        db.query(UserResume).filter(
            UserResume.user_id == user_id,
            UserResume.is_active == True
        ).update({"is_active": False})
        
        # Save to database
        resume_record = UserResume(
            user_id=user_id,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=os.path.getsize(file_path),
            parsed_data=parsed_data,
            full_name=parsed_data.get("personal_info", {}).get("fullName"),
            email=parsed_data.get("personal_info", {}).get("email"),
            phone=parsed_data.get("personal_info", {}).get("phone"),
            technical_skills=parsed_data.get("skills", {}).get("technical", []),
            soft_skills=parsed_data.get("skills", {}).get("non_technical", []),
            last_jd_matched=jd_text,
            match_score=parsed_data.get("metadata", {}).get("confidence_score", 0.0),
            is_active=True
        )
        
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)
        
        logger.info(f"✅ Resume uploaded successfully: {resume_record.id}")
        
        return {
            "message": "Resume uploaded and parsed successfully",
            "resume_id": resume_record.id,
            "data": parsed_data
        }
    
    except Exception as e:
        logger.error(f"❌ Resume upload failed: {e}", exc_info=True)
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(500, f"Failed to parse resume: {str(e)}")

@router.post("/parse")
async def parse_resume_public(
    file: UploadFile = File(...),
    jd_text: str = None
) -> Dict[str, Any]:
    """
    📄 Parse a resume without authentication
    
    Used during onboarding or for quick analysis.
    Does not store in database.
    """
    
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, "Only PDF, DOCX, or TXT files are supported")
    
    temp_dir = Path("uploads/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = Path(file.filename).name
    temp_path = temp_dir / f"temp_{os.getpid()}_{safe_name}"
    
    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        parsed_data = await resume_parser_service.parse_resume(
            str(temp_path),
            jd_text=jd_text
        )
        
        return {
            "message": "Resume parsed successfully",
            "data": parsed_data
        }
    except Exception as e:
        logger.error(f"Parse error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to parse resume: {str(e)}")
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass

# ==================== ANALYSIS ENDPOINTS ====================

@router.post("/analyze")
async def analyze_resume(
    jd_text: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    🔍 Analyze current resume with AI
    
    Provides:
    - ATS score breakdown
    - Strengths & weaknesses
    - Project suggestions
    - JD-specific comparison (if JD provided)
    """
    try:
        user_id = current_user["user_id"]
        
        # Get current resume
        resume = db.query(UserResume).filter(
            UserResume.user_id == user_id,
            UserResume.is_active == True
        ).first()
        
        if not resume:
            raise HTTPException(404, "No resume found. Please upload one first.")
        
        # Get user goals
        goals = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
        target_roles = goals.target_roles if goals else []
        
        logger.info(f"🤖 Analyzing resume for user {user_id}")
        
        # Run analysis
        analysis = await resume_analyzer.analyze_resume(
            parsed_resume=resume.parsed_data,
            user_goals=target_roles,
            jd_text=jd_text
        )
        
        return {
            "success": True,
            "data": analysis
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.post("/analyze-uploaded")
async def analyze_uploaded_resume(
    file: UploadFile = File(...),
    jd_text: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    📄 Analyze a resume file without saving it
    
    Useful for quick checks before uploading.
    Returns parsed data + AI analysis.
    """
    try:
        # Validate file
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(400, "Only PDF, DOCX, or TXT files supported")
        
        # Save temp file
        temp_dir = Path("uploads/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"temp_{os.getpid()}_{file.filename}"
        
        try:
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Parse
            logger.info(f"📄 Parsing uploaded file: {file.filename}")
            parsed_data = await resume_parser_service.parse_resume(
                str(temp_path),
                jd_text=jd_text
            )
            
            # Get user goals
            user_id = current_user["user_id"]
            goals = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
            target_roles = goals.target_roles if goals else []
            
            # Analyze
            logger.info(f"🤖 Analyzing uploaded resume")
            analysis = await resume_analyzer.analyze_resume(
                parsed_resume=parsed_data,
                user_goals=target_roles,
                jd_text=jd_text
            )
            
            return {
                "success": True,
                "parsed_data": parsed_data,
                "analysis": analysis
            }
        
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload analysis error: {e}", exc_info=True)
        raise HTTPException(500, str(e))

# ==================== RETRIEVAL ENDPOINTS ====================

@router.get("/current")
async def get_current_resume(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    📋 Get the user's active resume
    """
    
    user_id = current_user["user_id"]
    
    resume = db.query(UserResume).filter(
        UserResume.user_id == user_id,
        UserResume.is_active == True
    ).first()
    
    if not resume:
        raise HTTPException(404, "No resume found. Please upload one.")
    
    return {
        "resume_id": resume.id,
        "filename": resume.original_filename,
        "parsed_data": resume.parsed_data,
        "uploaded_at": resume.created_at.isoformat() if resume.created_at else None,
        "match_score": resume.match_score
    }

@router.get("/history")
async def get_resume_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    📚 Get all uploaded resumes for user
    """
    
    user_id = current_user["user_id"]
    
    resumes = db.query(UserResume).filter(
        UserResume.user_id == user_id
    ).order_by(UserResume.created_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "filename": r.original_filename,
            "full_name": r.full_name,
            "is_active": r.is_active,
            "uploaded_at": r.created_at.isoformat() if r.created_at else None,
            "match_score": r.match_score
        }
        for r in resumes
    ]

# ==================== DELETE ====================

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    🗑️ Delete a resume
    """
    
    user_id = current_user["user_id"]
    
    resume = db.query(UserResume).filter(
        UserResume.id == resume_id,
        UserResume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(404, "Resume not found")
    
    # Delete file
    if resume.file_path and Path(resume.file_path).exists():
        try:
            Path(resume.file_path).unlink()
        except Exception as e:
            logger.warning(f"Failed to delete file: {e}")
    
    db.delete(resume)
    db.commit()
    
    logger.info(f"🗑️ Resume deleted: {resume_id}")
    
    return {"message": "Resume deleted successfully"}
# backend/app/routes/resume.py - ADD THIS ENDPOINT

@router.patch("/{resume_id}/set-active")
async def set_active_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    ✅ Set a resume as active
    """
    user_id = current_user["user_id"]
    
    # Verify resume exists and belongs to user
    resume = db.query(UserResume).filter(
        UserResume.id == resume_id,
        UserResume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(404, "Resume not found")
    
    # Deactivate all user's resumes
    db.query(UserResume).filter(
        UserResume.user_id == user_id
    ).update({"is_active": False})
    
    # Activate the selected resume
    resume.is_active = True
    db.commit()
    
    logger.info(f"✅ Set active resume: {resume_id} for user {user_id}")
    
    return {"message": "Active resume updated successfully"}


@router.post("/{resume_id}/analyze")
async def analyze_specific_resume(
    resume_id: str,
    jd_text: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    🔍 Analyze a specific resume by ID
    """
    try:
        user_id = current_user["user_id"]
        
        # Get the specific resume
        resume = db.query(UserResume).filter(
            UserResume.id == resume_id,
            UserResume.user_id == user_id
        ).first()
        
        if not resume:
            raise HTTPException(404, "Resume not found")
        
        # Get user goals
        goals = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
        target_roles = goals.target_roles if goals else []
        
        logger.info(f"🤖 Analyzing resume {resume_id} for user {user_id}")
        
        # Run analysis
        analysis = await resume_analyzer.analyze_resume(
            parsed_resume=resume.parsed_data,
            user_goals=target_roles,
            jd_text=jd_text
        )
        
        return {
            "success": True,
            "data": analysis
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")
