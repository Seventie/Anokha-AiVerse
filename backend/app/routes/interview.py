# backend/app/routes/interview.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.interview_schemas import *
from app.services.interview_service import interview_service
from app.utils.auth import get_current_user
from app.models.database import User
from typing import List
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interview", tags=["Interview"])

# ==================== INTERVIEW LIFECYCLE ====================

@router.post("/create", response_model=InterviewResponse)
async def create_interview(
    data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new interview session
    
    Example payload:
    {
        "interview_type": "company_specific",
        "company_name": "Google",
        "job_description": "Senior SWE role...",
        "total_rounds": 2,
        "round_configs": [
            {"type": "technical", "difficulty": "medium"},
            {"type": "hr", "difficulty": "easy"}
        ]
    }
    """
    try:
        return await interview_service.create_interview(
            user_id=current_user.id,
            data=data,
            db=db
        )
    except Exception as e:
        logger.error(f"Create interview error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# 🔥 FIX: Added missing GET endpoint for fetching interview details
@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get interview details by ID
    
    Returns:
    - Interview metadata (company, type, status)
    - Current round information
    - Progress indicators
    """
    from app.models.database import Interview, InterviewRound
    
    try:
        # Fetch interview
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.user_id == current_user.id
        ).first()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Get current active round
        current_round = db.query(InterviewRound).filter(
            InterviewRound.interview_id == interview_id,
            InterviewRound.status.in_(["in_progress", "unlocked"])
        ).order_by(InterviewRound.round_number).first()
        
        # Build response
        return InterviewResponse(
            id=interview.id,
            interview_type=interview.interview_type,
            company_name=interview.company_name,
            job_description=interview.job_description,
            custom_topics=interview.custom_topics,
            total_rounds=interview.total_rounds,
            current_round=current_round.round_number if current_round else 0,
            status=interview.status,
            created_at=interview.created_at,
            current_round_data={
                "id": current_round.id,
                "round_number": current_round.round_number,
                "round_type": current_round.round_type,
                "difficulty": current_round.difficulty,
                "status": current_round.status,
                "question": getattr(current_round, 'current_question', None)
            } if current_round else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get interview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{interview_id}/start")
async def start_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start the interview (changes status to in_progress)"""
    try:
        return await interview_service.start_interview(
            interview_id=interview_id,
            user_id=current_user.id,
            db=db
        )
    except Exception as e:
        logger.error(f"Start interview error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{interview_id}/pause")
async def pause_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause interview"""
    from app.models.database import Interview
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview.status = "paused"
    db.commit()
    
    return {"message": "Interview paused", "interview_id": interview_id}


@router.post("/{interview_id}/complete")
async def complete_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete interview and generate final evaluation"""
    try:
        return await interview_service.complete_interview(
            interview_id=interview_id,
            user_id=current_user.id,
            db=db
        )
    except Exception as e:
        logger.error(f"Complete interview error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{interview_id}")
async def delete_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete interview (only if not completed)"""
    from app.models.database import Interview
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot delete completed interview")
    
    db.delete(interview)
    db.commit()
    
    return {"message": "Interview deleted"}


# ==================== ROUND MANAGEMENT ====================

@router.get("/{interview_id}/rounds", response_model=List[RoundResponse])
async def get_rounds(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all rounds for an interview"""
    from app.models.database import InterviewRound, Interview
    
    # Verify ownership
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    rounds = db.query(InterviewRound).filter(
        InterviewRound.interview_id == interview_id
    ).order_by(InterviewRound.round_number).all()
    
    return [RoundResponse.from_orm(r) for r in rounds]


@router.post("/{interview_id}/round/{round_id}/start", response_model=QuestionResponse)
async def start_round(
    interview_id: str,
    round_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a round and get the first question (with audio)
    
    Response includes:
    - question_id: ID to use when submitting answer
    - question_text: The question text
    - category: "technical" | "behavioral" | "problem_solving"
    - what_to_look_for: Array of key points
    - audio_url: URL to play the question audio
    """
    try:
        return await interview_service.start_round(
            interview_id=interview_id,
            round_id=round_id,
            user_id=current_user.id,
            db=db
        )
    except Exception as e:
        logger.error(f"Start round error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== QUESTION & ANSWER ====================

@router.post("/answer", response_model=AnswerFeedback)
async def submit_answer_text(
    data: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit text answer and get feedback + next question
    
    Payload:
    {
        "interview_id": "uuid",
        "round_id": "uuid",
        "question_id": 123,
        "answer_text": "My answer is..."
    }
    
    Response:
    {
        "score": 85,
        "feedback": "Great answer! You covered...",
        "strengths": ["Clear explanation", "Good examples"],
        "improvements": ["Could add more detail on X"],
        "next_question": {...}  // or null if round complete
    }
    """
    try:
        return await interview_service.submit_answer(
            data=data,
            user_id=current_user.id,
            db=db,
            audio_file_path=None
        )
    except Exception as e:
        logger.error(f"Submit answer error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/answer/audio", response_model=AnswerFeedback)
async def submit_answer_audio(
    interview_id: str = Form(...),
    round_id: str = Form(...),
    question_id: int = Form(...),
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit audio answer (will be transcribed by Whisper)
    
    Frontend should send multipart/form-data with:
    - interview_id
    - round_id
    - question_id
    - audio: audio file (wav, mp3, m4a)
    
    Backend will:
    1. Save audio file
    2. Transcribe with Whisper
    3. Evaluate with Groq
    4. Return feedback + next question
    """
    try:
        # Save uploaded audio
        audio_dir = Path("./interview_audio/answers")
        audio_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(audio.filename or "").suffix.lower()
        if not suffix:
            content_type = (audio.content_type or "").lower()
            if "webm" in content_type:
                suffix = ".webm"
            elif "mpeg" in content_type or "mp3" in content_type:
                suffix = ".mp3"
            elif "mp4" in content_type or "m4a" in content_type:
                suffix = ".m4a"
            else:
                suffix = ".wav"

        audio_filename = f"answer_{question_id}_{current_user.id}{suffix}"
        audio_path = audio_dir / audio_filename
        
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        logger.info(f"📁 Saved audio: {audio_path}")
        
        # Create AnswerSubmit object
        data = AnswerSubmit(
            interview_id=interview_id,
            round_id=round_id,
            question_id=question_id,
            answer_text="",  # Will be filled by transcription
            audio_url=f"/interview_audio/answers/{audio_filename}"
        )
        
        # Process answer (includes Whisper transcription)
        return await interview_service.submit_answer(
            data=data,
            user_id=current_user.id,
            db=db,
            audio_file_path=str(audio_path)
        )
        
    except Exception as e:
        logger.error(f"Submit audio answer error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== RESULTS & ANALYTICS ====================

@router.get("/{interview_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive interview evaluation
    
    Returns:
    - overall_score: 0-100
    - technical_score, communication_score, etc.
    - strengths: Array of what went well
    - weaknesses: Array of areas to improve
    - recommendations: Specific action items
    """
    try:
        return await interview_service.get_evaluation(
            interview_id=interview_id,
            user_id=current_user.id,
            db=db
        )
    except Exception as e:
        logger.error(f"Get evaluation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history", response_model=List[InterviewHistoryItem])
async def get_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's interview history"""
    try:
        return await interview_service.get_history(
            user_id=current_user.id,
            db=db,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Get history error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics", response_model=InterviewAnalytics)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance analytics
    
    Returns:
    - total_interviews
    - pass_rate: percentage
    - average_score
    - score_trend: Array of {date, score}
    - category_scores: {technical: 80, communication: 90}
    """
    try:
        return await interview_service.get_analytics(
            user_id=current_user.id,
            db=db
        )
    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{interview_id}/conversation")
async def get_conversation(
    interview_id: str,
    round_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full conversation history for an interview or specific round"""
    from app.models.database import InterviewConversation, Interview
    
    # Verify ownership
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    query = db.query(InterviewConversation).filter(
        InterviewConversation.interview_id == interview_id
    )
    
    if round_id:
        query = query.filter(InterviewConversation.round_id == round_id)
    
    conversations = query.order_by(InterviewConversation.timestamp).all()
    
    return [
        {
            "id": c.id,
            "speaker": c.speaker,
            "message": c.message_text,
            "audio_url": c.audio_url,
            "timestamp": c.timestamp.isoformat(),
            "score": c.answer_score if c.speaker == "user" else None
        }
        for c in conversations
    ]


# ==================== RECORDING ====================

@router.post("/{interview_id}/recording/upload")
async def upload_recording(
    interview_id: str,
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload video recording of entire interview
    (Client-side recording via MediaRecorder API)
    """
    from app.models.database import Interview, InterviewRecording
    
    # Verify ownership
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    try:
        # Save video file
        video_dir = Path("./interview_recordings")
        video_dir.mkdir(parents=True, exist_ok=True)
        
        video_filename = f"{interview_id}.webm"
        video_path = video_dir / video_filename
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        file_size = video_path.stat().st_size
        
        # Create or update recording entry
        recording = db.query(InterviewRecording).filter(
            InterviewRecording.interview_id == interview_id
        ).first()
        
        if not recording:
            recording = InterviewRecording(
                interview_id=interview_id,
                video_url=f"/interview_recordings/{video_filename}",
                file_size_bytes=file_size,
                video_format="webm"
            )
            db.add(recording)
        else:
            recording.video_url = f"/interview_recordings/{video_filename}"
            recording.file_size_bytes = file_size
        
        db.commit()
        
        return {
            "message": "Recording uploaded successfully",
            "video_url": recording.video_url,
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Upload recording error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{interview_id}/recording")
async def get_recording(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recording URLs and transcript"""
    from app.models.database import InterviewRecording, Interview
    
    # Verify ownership
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    recording = db.query(InterviewRecording).filter(
        InterviewRecording.interview_id == interview_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return {
        "video_url": recording.video_url,
        "transcript_text": recording.transcript_text,
        "duration_seconds": recording.recording_duration,
        "file_size_mb": round(recording.file_size_bytes / (1024 * 1024), 2)
    }
