# backend/app/config/settings.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200
    
    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "career_memory"
    
    # Hugging Face
    HUGGINGFACE_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()