"""
Configuration settings for LeadMate Backend
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb+srv://LeadMate_1:mvbuEfnYmKyCwPEM@cluster0.pslm64p.mongodb.net/"
    DATABASE_NAME: str = "leadmate_db"
    
    # JWT Configuration
    SECRET_KEY: str = "leadmate-secret-key-change-in-production-09876543210abcdef"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Application Settings
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "LeadMate API"
    
    # Gemini API Configuration (with fallbacks)
    # Primary/secondary (used if env vars are not set)
    GEMINI_API_KEY_1: str = "AIzaSyAdsybf3VEN00pFqhOdhtKvIcrmGS7ksrE"
    GEMINI_API_KEY_2: str = "AIzaSyCK60OPHxuDLrZIhZcsS_WSCgrC9de2_tw"
    # Optional: comma-separated list of keys loaded from .env; also used here as defaults
    GEMINI_API_KEYS: Optional[str] = (
        "AIzaSyAdsybf3VEN00pFqhOdhtKvIcrmGS7ksrE,"
        "AIzaSyCK60OPHxuDLrZIhZcsS_WSCgrC9de2_tw,"
        "AIzaSyDywSpFAeWIQ0HATUbss-ZhqzQ0alHaOf8,"
        "AIzaSyCl7ZBH5Vp2izkC5uNVArZ2arh_DEFF9Zs"
    )
    
    # LLM Configuration
    LLM_PROVIDER: str = "gemini"  # Options: "gemini", "ollama"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Feature Flags / Providers (to avoid extra field validation errors)
    FORCE_OLLAMA: bool = False
    USE_GEMINI: bool = False
    GOOGLE_API_KEY: Optional[str] = None
    
    # CORS Settings
    ALLOWED_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:3000").split(",")
    
    # Repository Analysis Configuration
    ALLOWED_REPO_DOMAINS: list = os.getenv("ALLOWED_REPO_DOMAINS", "github.com,gitlab.com").split(",")
    REPOS_DIR: str = os.getenv("REPOS_DIR", "./repositories")
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    MAX_COMMITS_ANALYSIS: int = int(os.getenv("MAX_COMMITS_ANALYSIS", "100"))

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

