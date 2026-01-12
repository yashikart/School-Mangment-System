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
    
    # Email Configuration (SMTP)
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@schoolmanagement.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "School Management System"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    
    # Frontend URL (for password setup links)
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Password token expiration (minutes)
    PASSWORD_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = [".env", "app/.env"]  # Check both root and app directory
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
