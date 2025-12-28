# backend/app/services/interview_service.py

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import logging
import json

# Settings
from app.config.settings import settings

# Database Models
from app.models.database import (
    Interview,
    InterviewRound,
    InterviewConversation,
    InterviewEvaluation,
    InterviewRecording,
    InterviewType,
    RoundType,
    InterviewStatus,
    RoundStatus
)

# Schemas
from app.schemas.interview_schemas import (
    InterviewCreate,
    InterviewResponse,
    RoundResponse,
    QuestionResponse,
    AnswerSubmit,
    AnswerFeedback,
    EvaluationResponse,
    InterviewHistoryItem,
    InterviewAnalytics
)

# Services
from app.services.interview_llm_service import InterviewLLMService
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service

logger = logging.getLogger(__name__)

class InterviewService:
    """
    Core interview orchestration service
    Coordinates: Whisper (STT) → Groq (LLM) → Piper (TTS)
    """
    
    def __init__(self):
        self.audio_path = Path(settings.INTERVIEW_AUDIO_PATH)
        self.audio_path.mkdir(parents=True, exist_ok=True)
        
        # ✅ Initialize InterviewLLMService
        self.interview_llm = InterviewLLMService()
        
        logger.info("✅ Interview Service initialized")
    
    async def create_interview(
        self,
        user_id: str,
        data: InterviewCreate,
        db: Session
    ) -> InterviewResponse:
        """Create new interview session"""
        
        # Validate data
        if data.interview_type == "company_specific" and not data.company_name:
            raise ValueError("Company name required for company-specific interviews")
        
        if data.interview_type == "custom_topic" and not data.custom_topics:
            raise ValueError("Custom topics required for custom interviews")
        
        # Create interview
        interview = Interview(
            id=str(uuid.uuid4()),
            user_id=user_id,
            interview_type=data.interview_type,
            company_name=data.company_name,
            job_description=data.job_description,
            custom_topics=data.custom_topics,
            total_rounds=data.total_rounds,
            current_round=1,
            status="not_started",
            created_at=datetime.utcnow()
        )
        db.add(interview)
        
        # Create rounds
        for i, round_config in enumerate(data.round_configs):
            round_obj = InterviewRound(
                id=str(uuid.uuid4()),
                interview_id=interview.id,
                round_number=i + 1,
                round_type=round_config["type"],
                difficulty=round_config.get("difficulty", "medium"),
                status="unlocked" if i == 0 else "locked",  # First round unlocked
                pass_threshold=round_config.get("pass_threshold", 70.0)
            )
            db.add(round_obj)
        
        db.commit()
        db.refresh(interview)
        
        logger.info(f"✅ Created interview {interview.id} for user {user_id}")
        return InterviewResponse.from_orm(interview)
    
    async def start_interview(
        self,
        interview_id: str,
        user_id: str,
        db: Session
    ) -> dict:
        """Start the interview"""
        
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.user_id == user_id
        ).first()
        
        if not interview:
            raise ValueError("Interview not found")
        
        if interview.status != "not_started":
            raise ValueError("Interview already started")
        
        # Update status
        interview.status = "in_progress"
        interview.started_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Interview started", "interview_id": interview_id}
    
    async def start_round(
        self,
        interview_id: str,
        round_id: str,
        user_id: str,
        db: Session
    ) -> QuestionResponse:
        """
        Start a round and get first question with audio
        
        Flow: Groq generates question → Piper speaks it
        """
        
        # Get interview and round
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.user_id == user_id
        ).first()
        
        round_obj = db.query(InterviewRound).filter(
            InterviewRound.id == round_id,
            InterviewRound.interview_id == interview_id
        ).first()
        
        if not interview or not round_obj:
            raise ValueError("Interview or round not found")
        
        if round_obj.status not in ["unlocked", "in_progress"]:
            raise ValueError(f"Round is {round_obj.status}")
        
        # Update statuses
        round_obj.status = "in_progress"
        round_obj.started_at = datetime.utcnow()
        interview.status = "in_progress"
        interview.current_round = round_obj.round_number
        
        if not interview.started_at:
            interview.started_at = datetime.utcnow()
        
        db.commit()
        
        # ✅ FIX: Safely handle custom_topics (can be None, string, or list)
        custom_topics_list = interview.custom_topics
        
        if custom_topics_list is None:
            custom_topics_list = []
        elif isinstance(custom_topics_list, str):
            # If stored as JSON string in database
            try:
                custom_topics_list = json.loads(custom_topics_list)
                if not isinstance(custom_topics_list, list):
                    custom_topics_list = [custom_topics_list]
            except (json.JSONDecodeError, TypeError):
                # If it's a plain string, make it a list
                custom_topics_list = [custom_topics_list] if custom_topics_list.strip() else []
        elif not isinstance(custom_topics_list, list):
            # Convert any other type to list
            custom_topics_list = [str(custom_topics_list)]
        
        # Prepare context for question generation
        context = {
            "company_name": interview.company_name or "General Company",
            "job_title": "Software Engineer",
            "job_description": interview.job_description or "",
            "custom_topics": custom_topics_list,  # ✅ Now guaranteed to be a list
            "round_type": round_obj.round_type
        }
        
        # Get conversation history
        history = db.query(InterviewConversation).filter(
            InterviewConversation.round_id == round_id
        ).order_by(InterviewConversation.timestamp).all()
        
        history_list = [
            {"speaker": conv.speaker, "message": conv.message_text}
            for conv in history
        ]
        
        # 🔥 Step 1: Generate question using Groq
        logger.info("🤖 Generating question with Groq...")
        question_data = await self.interview_llm.generate_interview_question(
            context=context,
            conversation_history=history_list,
            round_type=round_obj.round_type,
            difficulty=round_obj.difficulty
        )
        
        # Save question to database
        conversation = InterviewConversation(
            interview_id=interview_id,
            round_id=round_id,
            speaker="ai",
            message_text=question_data["question"],
            question_category=question_data.get("category", "general"),
            expected_answer_points=question_data.get("sample_answer_points", []),
            timestamp=datetime.utcnow()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # 🔥 Step 2: Generate audio using Piper TTS
        logger.info("🔊 Generating audio with Piper TTS...")
        audio_filename = f"question_{conversation.id}.wav"
        audio_path = self.audio_path / audio_filename
        
        await tts_service.synthesize(
            text=question_data["question"],
            output_path=str(audio_path)
        )
        
        # Update conversation with audio URL
        conversation.audio_url = f"/interview_audio/{audio_filename}"
        db.commit()
        
        logger.info(f"✅ Question ready: {question_data['question'][:50]}...")
        
        return QuestionResponse(
            question_id=conversation.id,
            question_text=question_data["question"],
            category=question_data.get("category", "general"),
            what_to_look_for=question_data.get("what_to_look_for", []),
            audio_url=conversation.audio_url
        )
    
    async def submit_answer(
        self,
        data: AnswerSubmit,
        user_id: str,
        db: Session,
        audio_file_path: str = None
    ) -> AnswerFeedback:
        """
        Submit answer (text or audio) and get feedback + next question
        
        Flow: Whisper transcribes → Groq evaluates → Piper speaks feedback
        """
        
        # Get the question
        question = db.query(InterviewConversation).filter(
            InterviewConversation.id == data.question_id
        ).first()
        
        if not question:
            raise ValueError("Question not found")
        
        # 🔥 Step 1: Transcribe audio if provided
        answer_text = data.answer_text
        
        if audio_file_path:
            logger.info("🎤 Transcribing answer with Whisper...")
            transcription = await stt_service.transcribe(audio_file_path)
            answer_text = transcription["text"]
            logger.info(f"📝 Transcribed: {answer_text[:100]}...")
        
        if not answer_text or not answer_text.strip():
            raise ValueError("Answer cannot be empty")
        
        # Save answer to database
        answer_record = InterviewConversation(
            interview_id=data.interview_id,
            round_id=data.round_id,
            speaker="user",
            message_text=answer_text,
            audio_url=data.audio_url,
            timestamp=datetime.utcnow()
        )
        db.add(answer_record)
        db.commit()
        db.refresh(answer_record)
        
        # 🔥 Step 2: Evaluate answer using Groq
        logger.info("🧠 Evaluating answer with Groq...")
        round_obj = db.query(InterviewRound).filter(
            InterviewRound.id == data.round_id
        ).first()
        
        evaluation = await self.interview_llm.evaluate_answer(
            question=question.message_text,
            answer=answer_text,
            expected_points=question.expected_answer_points or [],
            round_type=round_obj.round_type
        )
        
        # Update answer record with scores
        answer_record.answer_score = evaluation["score"]
        answer_record.sentiment_score = 0.0
        answer_record.confidence_detected = evaluation.get("confidence_level", "medium")
        
        db.commit()
        
        logger.info(f"✅ Answer evaluated: {evaluation['score']}/100")
        
        # Check if we should generate next question or end round
        MAX_QUESTIONS_PER_ROUND = 5
        
        question_count = db.query(InterviewConversation).filter(
            InterviewConversation.round_id == data.round_id,
            InterviewConversation.speaker == "ai"
        ).count()
        
        next_question = None
        
        if question_count < MAX_QUESTIONS_PER_ROUND:
            # Generate next question
            logger.info("Generating next question...")
            next_question = await self.start_round(
                interview_id=data.interview_id,
                round_id=data.round_id,
                user_id=user_id,
                db=db
            )
        else:
            # End round
            await self._complete_round(data.round_id, db)
        
        return AnswerFeedback(
            score=evaluation["score"],
            feedback=evaluation["feedback"],
            strengths=evaluation.get("strengths", []),
            improvements=evaluation.get("improvements", []),
            next_question=next_question
        )
    
    async def _complete_round(self, round_id: str, db: Session):
        """Complete a round and calculate scores"""
        
        round_obj = db.query(InterviewRound).filter(
            InterviewRound.id == round_id
        ).first()
        
        if not round_obj:
            raise ValueError("Round not found")
        
        # Calculate average score from all answers
        answers = db.query(InterviewConversation).filter(
            InterviewConversation.round_id == round_id,
            InterviewConversation.speaker == "user"
        ).all()
        
        scores = [a.answer_score for a in answers if a.answer_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Update round
        round_obj.status = "passed" if avg_score >= round_obj.pass_threshold else "failed"
        round_obj.score = avg_score
        round_obj.pass_status = avg_score >= round_obj.pass_threshold
        round_obj.completed_at = datetime.utcnow()
        
        if round_obj.started_at:
            round_obj.duration_seconds = int(
                (round_obj.completed_at - round_obj.started_at).total_seconds()
            )
        
        # Generate round feedback
        round_obj.feedback_summary = f"Average score: {avg_score:.1f}/100"
        
        # Unlock next round if passed
        if round_obj.pass_status:
            interview = db.query(Interview).filter(
                Interview.id == round_obj.interview_id
            ).first()
            
            next_round = db.query(InterviewRound).filter(
                InterviewRound.interview_id == round_obj.interview_id,
                InterviewRound.round_number == round_obj.round_number + 1
            ).first()
            
            if next_round:
                next_round.status = "unlocked"
                interview.current_round = next_round.round_number
            else:
                # This was the last round
                await self.complete_interview(round_obj.interview_id, interview.user_id, db)
        
        db.commit()
        logger.info(f"✅ Round {round_obj.round_number} completed: {avg_score:.1f}/100")
    
    async def complete_interview(
        self,
        interview_id: str,
        user_id: str,
        db: Session
    ) -> dict:
        """Complete entire interview and generate final evaluation"""
        
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.user_id == user_id
        ).first()
        
        if not interview:
            raise ValueError("Interview not found")
        
        # Get all rounds
        rounds = db.query(InterviewRound).filter(
            InterviewRound.interview_id == interview_id
        ).order_by(InterviewRound.round_number).all()
        
        round_scores = [r.score for r in rounds if r.score is not None]
        overall_score = sum(round_scores) / len(round_scores) if round_scores else 0
        
        # Get all conversations
        conversations = db.query(InterviewConversation).filter(
            InterviewConversation.interview_id == interview_id
        ).order_by(InterviewConversation.timestamp).all()
        
        conv_list = [
            {"speaker": c.speaker, "message": c.message_text}
            for c in conversations
        ]
        
        # 🔥 Generate final evaluation using Groq
        logger.info("📊 Generating final evaluation with Groq...")
        final_eval = await self.interview_llm.generate_final_evaluation(
            all_conversations=conv_list,
            round_scores=round_scores,
            interview_type=interview.interview_type,
            company_name=interview.company_name or "General"
        )
        
        # Save evaluation
        evaluation = InterviewEvaluation(
            interview_id=interview_id,
            technical_score=final_eval.get("technical_score", overall_score),
            communication_score=final_eval.get("communication_score", overall_score),
            problem_solving_score=final_eval.get("problem_solving_score", overall_score),
            confidence_score=final_eval.get("confidence_score", overall_score),
            overall_score=final_eval.get("overall_score", overall_score),
            strengths=final_eval.get("strengths", []),
            weaknesses=final_eval.get("weaknesses", []),
            recommendations=final_eval.get("recommendations", []),
            suggested_topics=final_eval.get("suggested_topics", []),
            next_interview_date=datetime.utcnow() + timedelta(days=7)
        )
        db.add(evaluation)
        
        # Update interview
        interview.status = "completed"
        interview.completed_at = datetime.utcnow()
        
        if interview.started_at:
            interview.duration_seconds = int(
                (interview.completed_at - interview.started_at).total_seconds()
            )
        
        interview.overall_score = overall_score
        interview.pass_fail_status = "pass" if final_eval.get("pass", False) else "fail"
        interview.completed_rounds = len(rounds)
        
        db.commit()
        
        logger.info(f"✅ Interview completed: {overall_score:.1f}/100")
        
        return {
            "message": "Interview completed",
            "overall_score": overall_score,
            "evaluation_id": evaluation.id
        }
    
    async def get_evaluation(
        self,
        interview_id: str,
        user_id: str,
        db: Session
    ) -> EvaluationResponse:
        """Get full interview evaluation"""
        
        evaluation = db.query(InterviewEvaluation).filter(
            InterviewEvaluation.interview_id == interview_id
        ).first()
        
        if not evaluation:
            raise ValueError("Evaluation not found")
        
        return EvaluationResponse.from_orm(evaluation)
    
    async def get_history(
        self,
        user_id: str,
        db: Session,
        limit: int = 10
    ) -> List[InterviewHistoryItem]:
        """Get user's interview history"""
        
        interviews = db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.status == "completed"
        ).order_by(Interview.completed_at.desc()).limit(limit).all()
        
        return [
            InterviewHistoryItem(
                id=i.id,
                company_name=i.company_name,
                custom_topics=i.custom_topics,
                overall_score=i.overall_score or 0,
                pass_fail_status=i.pass_fail_status or "pending",
                created_at=i.created_at
            )
            for i in interviews
        ]
    
    async def get_analytics(
        self,
        user_id: str,
        db: Session
    ) -> InterviewAnalytics:
        """Get performance analytics"""
        
        interviews = db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.status == "completed"
        ).all()
        
        if not interviews:
            return InterviewAnalytics(
                total_interviews=0,
                pass_rate=0.0,
                average_score=0.0,
                score_trend=[],
                category_scores={}
            )
        
        total = len(interviews)
        passed = sum(1 for i in interviews if i.pass_fail_status == "pass")
        avg_score = sum(i.overall_score or 0 for i in interviews) / total
        
        # Score trend
        trend = [
            {
                "date": i.completed_at.strftime("%Y-%m-%d"),
                "score": i.overall_score or 0
            }
            for i in sorted(interviews, key=lambda x: x.completed_at)
        ]
        
        return InterviewAnalytics(
            total_interviews=total,
            pass_rate=round(passed / total * 100, 1),
            average_score=round(avg_score, 1),
            score_trend=trend,
            category_scores={}
        )


# Singleton
interview_service = InterviewService()
