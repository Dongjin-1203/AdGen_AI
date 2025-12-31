from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # CORS
    allow_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # Database
    CLOUD_SQL_URL: str
    
    # App
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()