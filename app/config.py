from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/school_management_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = [".env", "app/.env"]  # Check both root and app directory
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
