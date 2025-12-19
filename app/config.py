"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Telegram API
    telegram_api_id: int
    telegram_api_hash: str
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "telegram_service"
    
    # Security
    api_secret_key: str
    
    # Session settings
    session_directory: str = "./sessions"
    qr_code_expires_in: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
