# backend/app/config/settings.py

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute base directory -> /backend
BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # =========================
    # Environment
    # =========================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # =========================
    # Server
    # =========================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # =========================
    # Database (PostgreSQL)
    # =========================
    DATABASE_URL: str

    # =========================
    # Auth / JWT
    # =========================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200

    # =========================
    # Vector DB (Chroma)
    # =========================
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "career_memory"

    # =========================
    # Embeddings
    # =========================
    HUGGINGFACE_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # =========================
    # Neo4j (Knowledge Graph)
    # =========================
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # =========================
    # Redis / Celery
    # =========================
    REDIS_URL: str

    # =========================
    # LLM Providers
    # =========================
    GROQ_API_KEY: Optional[str] = None
    OLLAMA_HOST: Optional[str] = None

    # =========================
    # Google OAuth / Calendar
    # =========================
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    # =========================
    # Scheduler / Agents
    # =========================
    SUPERVISOR_CHECK_INTERVAL: int = 300
    OPPORTUNITIES_CHECK_INTERVAL: int = 21600
    WEEKLY_SUMMARY_DAY: str = "Sunday"
    WEEKLY_SUMMARY_HOUR: int = 20

    # =========================
    # 🎤 INTERVIEW SYSTEM (NEW)
    # =========================
    
    # Interview LLM Provider
    GROQ_API_KEY_INTERVIEW: Optional[str] = None  # Separate key for interviews
    GOOGLE_API_KEY: Optional[str] = None  # Backup LLM (Gemini)
    
    # Whisper (Local STT - Speech-to-Text)
    WHISPER_MODEL_SIZE: str = "base"  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"  # cpu or cuda
    WHISPER_MODEL_PATH: str = "./models/whisper"
    
    # Piper TTS (Local Text-to-Speech)
    PIPER_MODEL_PATH: str = "./models/piper/en_US-lessac-medium.onnx"
    PIPER_CONFIG_PATH: str = "./models/piper/en_US-lessac-medium.onnx.json"
    PIPER_VOICE: str = "en_US-lessac-medium"
    
    # Interview Service Providers
    INTERVIEW_STT_PROVIDER: str = "whisper_local"  # whisper_local | deepgram
    INTERVIEW_TTS_PROVIDER: str = "piper_local"  # piper_local | elevenlabs
    INTERVIEW_LLM_PROVIDER: str = "groq"  # groq | openai | gemini
    
    # Interview Storage
    INTERVIEW_STORAGE_TYPE: str = "local"  # local | s3
    INTERVIEW_STORAGE_PATH: str = "./interview_recordings"
    INTERVIEW_AUDIO_PATH: str = "./interview_audio"
    
    # AWS S3 (Optional - for production)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET_NAME: Optional[str] = None
    AWS_REGION: Optional[str] = None

    # =========================
    # Helpers
    # =========================
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # =========================
    # Pydantic v2 Config
    # =========================
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # ✅ CHANGED FROM "forbid" to "allow"
    )


settings = Settings()
