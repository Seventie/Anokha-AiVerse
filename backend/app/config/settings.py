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
    # Helpers
    # =========================
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # =========================
    # Pydantic v2 Config
    # =========================
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",   # 🔥 absolute path fix
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid"               # strict & safe
    )


settings = Settings()
