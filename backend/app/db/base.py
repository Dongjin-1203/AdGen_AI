from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from config import settings

# 엔진 생성
engine = create_engine(
    settings.CLOUD_SQL_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

# 세션 팩토리
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Base 클래스
Base = declarative_base()

# 의존성 주입
def get_db() -> Generator:
    """FastAPI Depends()에서 사용"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()