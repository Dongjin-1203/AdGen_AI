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
    
    # JWT 설정
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()