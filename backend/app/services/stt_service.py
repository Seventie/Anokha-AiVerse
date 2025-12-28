# backend/app/services/stt_service.py

import whisper
import torch
from app.config.settings import settings
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text Service using Local Whisper
    """
    
    def __init__(self):
        self.model = None
        self.model_size = settings.WHISPER_MODEL_SIZE  # tiny, base, small, medium, large
        self.device = settings.WHISPER_DEVICE  # cpu or cuda
        self.model_path = settings.WHISPER_MODEL_PATH
        
        # Create model directory
        Path(self.model_path).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing Whisper {self.model_size} on {self.device}")
    
    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            
            # Check if CUDA is available and requested
            if self.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                self.device = "cpu"
            
            # Load model
            self.model = whisper.load_model(
                self.model_size,
                device=self.device,
                download_root=self.model_path
            )
            logger.info(f"✅ Whisper model loaded on {self.device}")
    
    async def transcribe(self, audio_file_path: str, language: str = "en") -> dict:
        """
        Transcribe audio to text using local Whisper
        
        Args:
            audio_file_path: Path to audio file (wav, mp3, m4a, etc.)
            language: Language code (default: "en")
        
        Returns:
            {
                "text": "transcribed text",
                "confidence": 0.95,
                "duration": 5.2,
                "language": "en",
                "segments": [...]  # Detailed segments with timestamps
            }
        """
        try:
            # Lazy load model
            self._load_model()
            
            # Transcribe
            logger.info(f"Transcribing: {audio_file_path}")
            result = self.model.transcribe(
                audio_file_path,
                language=language,
                task="transcribe",
                fp16=False,  # Set to True if using CUDA
                verbose=False
            )
            
            # Calculate average confidence from segments
            avg_confidence = sum(
                segment.get("no_speech_prob", 0) 
                for segment in result.get("segments", [])
            ) / max(len(result.get("segments", [])), 1)
            avg_confidence = 1 - avg_confidence  # Invert no_speech_prob
            
            return {
                "text": result["text"].strip(),
                "confidence": round(avg_confidence, 2),
                "duration": result.get("duration", 0),
                "language": result.get("language", language),
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Whisper transcription error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def transcribe_with_timestamps(self, audio_file_path: str) -> list:
        """
        Transcribe with detailed timestamps for each segment
        Useful for showing real-time captions during interview
        """
        self._load_model()
        
        result = self.model.transcribe(
            audio_file_path,
            task="transcribe",
            verbose=False,
            word_timestamps=True  # Word-level timestamps
        )
        
        segments = []
        for segment in result["segments"]:
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "words": segment.get("words", [])
            })
        
        return segments

# Singleton
stt_service = STTService()
