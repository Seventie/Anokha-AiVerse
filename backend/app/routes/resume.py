# backend/app/routes/resume.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import shutil
from pathlib import Path
import os
import jwt

from app.config.database import get_db
from app.config.settings import settings
from app.services.resume_parser_service import resume_parser_service
from app.models.database import UserResume


router = APIRouter(prefix="/api/resume", tags=["Resume"])

UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ✅ TEMPORARY AUTH HELPER (until we find your actual one)
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


# Rest of your resume.py code stays the same...
@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    jd_text: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload and parse resume PDF"""
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    user_id = current_user["user_id"]
    
    # Save file
    file_path = UPLOAD_DIR / f"{user_id}_{file.filename}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
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
        
        return {
            "message": "Resume uploaded and parsed successfully",
            "resume_id": resume_record.id,
            "data": parsed_data
        }
    
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(500, f"Failed to parse resume: {str(e)}")


@router.get("/current")
async def get_current_resume(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the user's active resume"""
    
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
        "uploaded_at": resume.created_at
    }


@router.get("/history")
async def get_resume_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all uploaded resumes for user"""
    
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
            "uploaded_at": r.created_at,
            "match_score": r.match_score
        }
        for r in resumes
    ]


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume"""
    
    user_id = current_user["user_id"]
    
    resume = db.query(UserResume).filter(
        UserResume.id == resume_id,
        UserResume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(404, "Resume not found")
    
    # Delete file
    if resume.file_path and Path(resume.file_path).exists():
        Path(resume.file_path).unlink()
    
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume deleted successfully"}
