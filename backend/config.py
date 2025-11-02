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
    GEMINI_API_KEY_1: str = "AIzaSyCl7ZBH5Vp2izkC5uNVArZ2arh_DEFF9Zs"
    GEMINI_API_KEY_2: str = "AIzaSyAdsybf3VEN00pFqhOdhtKvIcrmGS7ksrE"
    
    # LLM Configuration
    LLM_PROVIDER: str = "gemini"  # Options: "gemini", "ollama"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # CORS Settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

