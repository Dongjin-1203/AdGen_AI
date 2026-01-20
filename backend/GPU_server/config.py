"""
GPU 서버 전용 설정
AI 배경 생성에 필요한 최소 설정만 포함
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # ===== Environment =====
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # ===== Server =====
    HOST: str = "0.0.0.0"
    PORT: int = 8001  # 메인 서버와 구분
    
    # ===== CORS (메인 서버에서 호출) =====
    ALLOW_ORIGINS: List[str] = [
        "http://localhost:8000",  # 메인 백엔드
        "http://localhost:3000",  # 프론트엔드
        "https://*.run.app",      # Cloud Run
        "*"  # 개발용 (프로덕션에서는 제거)
    ]
    
    # ===== GPU 설정 =====
    FORCE_CUDA: bool = True  # GPU 강제 사용
    MODEL_CACHE_DIR: str = "./models"  # 모델 저장 경로
    
    # ===== 생성 기본값 =====
    DEFAULT_STYLE: str = "minimal"
    DEFAULT_ASPECT_RATIO: str = "square"
    DEFAULT_NUM_INFERENCE_STEPS: int = 30
    DEFAULT_CONTROLNET_SCALE: float = 1.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

settings = Settings()