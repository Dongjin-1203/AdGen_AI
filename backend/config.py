from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # ===== Environment =====
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # ===== Database (로컬 개발용) =====
    DATABASE_URL: Optional[str] = None
    
    # ===== Cloud SQL (배포용) =====
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = None
    DB_USER: str = "postgres"
    DB_PASSWORD: Optional[str] = None
    DB_NAME: str = "adgen_ai"
    
    # ===== JWT =====
    JWT_SECRET_KEY: str = "default-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ===== GCS =====
    GCS_BUCKET_NAME: Optional[str] = None
    
    # ===== CORS =====
    allow_origins: List[str] = [
        "http://localhost:3000",
        "https://*.run.app"
    ]
    
    @property
    def CLOUD_SQL_URL(self) -> str:
        """Cloud SQL 또는 로컬 DB URL 반환"""
        # Cloud Run 환경
        if self.ENVIRONMENT == "production" and self.CLOUD_SQL_CONNECTION_NAME:
            # Cloud SQL Connector는 별도 처리 (base.py에서)
            return f"postgresql+pg8000://{self.DB_USER}:{self.DB_PASSWORD}@/{self.DB_NAME}?unix_sock=/cloudsql/{self.CLOUD_SQL_CONNECTION_NAME}/.s.PGSQL.5432"
        # 로컬 환경
        else:
            return self.DATABASE_URL or "postgresql://postgres:password@localhost:5432/adgen_ai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

settings = Settings()