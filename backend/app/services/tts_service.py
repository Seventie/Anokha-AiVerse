# backend/app/services/tts_service.py

import os
from pathlib import Path
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class TTSService:
    """
    Text-to-Speech Service using Local Piper
    """
    
    def __init__(self):
        self.model_path = settings.PIPER_MODEL_PATH
        self.config_path = settings.PIPER_CONFIG_PATH
        self.voice = settings.PIPER_VOICE
        self.piper_model = None
        
        # Verify model files exist
        if not os.path.exists(self.model_path):
            logger.warning(f"⚠️ Piper model not found at: {self.model_path}")
            logger.warning("TTS will be disabled. Download model from:")
            logger.warning("https://huggingface.co/rhasspy/piper-voices")
            self.enabled = False
        else:
            logger.info(f"✅ Piper TTS ready with voice: {self.voice}")
            self.enabled = True
    
    def _load_model(self):
        """Lazy load Piper model"""
        if not self.enabled:
            return None
            
        if self.piper_model is None:
            try:
                # Import piper library
                from piper import PiperVoice
                
                logger.info(f"Loading Piper model: {self.model_path}")
                self.piper_model = PiperVoice.load(
                    self.model_path,
                    config_path=self.config_path,
                    use_cuda=False
                )
                logger.info("✅ Piper model loaded successfully")
            except ImportError:
                logger.error("❌ piper-tts package not installed correctly")
                logger.error("Try: pip uninstall piper-tts && pip install piper-tts")
                self.enabled = False
                return None
            except Exception as e:
                logger.error(f"❌ Failed to load Piper model: {e}")
                self.enabled = False
                return None
        
        return self.piper_model
    
    async def synthesize(self, text: str, output_path: str) -> str:
        """
        Convert text to speech using Piper
        
        Args:
            text: Text to convert to speech
            output_path: Where to save the audio file (.wav)
        
        Returns:
            Path to generated audio file (or empty string if failed)
        """
        if not self.enabled:
            logger.warning("⚠️ TTS disabled - returning empty audio")
            return ""
        
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Load model
            model = self._load_model()
            if model is None:
                return ""
            
            logger.info(f"Generating speech: {text[:50]}...")
            
            # Synthesize speech
            with open(output_path, 'wb') as f:
                model.synthesize(text, f)
            
            logger.info(f"✅ Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis error: {e}")
            return ""
    
    async def synthesize_stream(self, text: str) -> bytes:
        """
        Generate audio as bytes (for streaming to frontend)
        """
        if not self.enabled:
            return b""
        
        try:
            import io
            
            model = self._load_model()
            if model is None:
                return b""
            
            # Create in-memory buffer
            buffer = io.BytesIO()
            
            # Synthesize to buffer
            model.synthesize(text, buffer)
            
            # Get bytes
            audio_bytes = buffer.getvalue()
            buffer.close()
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"❌ TTS streaming error: {e}")
            return b""
    
    def get_available_voices(self) -> list:
        """List available Piper voices (if multiple downloaded)"""
        if not self.enabled:
            return []
        
        voices_dir = Path(self.model_path).parent
        voices = []
        
        for model_file in voices_dir.glob("*.onnx"):
            if model_file.stem != model_file.name:  # Has .onnx extension
                voices.append({
                    "name": model_file.stem,
                    "path": str(model_file)
                })
        
        return voices

# Singleton - but don't fail if Piper not available
try:
    tts_service = TTSService()
except Exception as e:
    logger.error(f"❌ Failed to initialize TTS service: {e}")
    # Create a dummy service
    class DummyTTSService:
        enabled = False
        async def synthesize(self, text: str, output_path: str) -> str:
            return ""
        async def synthesize_stream(self, text: str) -> bytes:
            return b""
    tts_service = DummyTTSService()
