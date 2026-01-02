from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from config import settings
import os

def get_database_engine():
    """환경에 따라 DB 엔진 생성"""
    
    # Cloud Run (프로덕션) - Cloud SQL Connector 사용
    if settings.ENVIRONMENT == "production" and settings.CLOUD_SQL_CONNECTION_NAME:
        try:
            from google.cloud.sql.connector import Connector
            import pg8000
            
            connector = Connector()
            
            def getconn():
                conn = connector.connect(
                    settings.CLOUD_SQL_CONNECTION_NAME,
                    "pg8000",
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    db=settings.DB_NAME,
                )
                return conn
            
            engine = create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                echo=settings.DEBUG,
                pool_pre_ping=True
            )
            print("✅ Cloud SQL Connector 연결 성공")
            return engine
            
        except Exception as e:
            print(f"⚠️ Cloud SQL Connector 실패, 일반 연결 시도: {e}")
            # Fallback: 일반 연결
            engine = create_engine(
                settings.CLOUD_SQL_URL,
                echo=settings.DEBUG,
                pool_pre_ping=True
            )
            return engine
    
    # 로컬 개발
    else:
        if not settings.DATABASE_URL:
            print("⚠️ DATABASE_URL이 없습니다. 기본값 사용")
        
        engine = create_engine(
            settings.CLOUD_SQL_URL,  # 로컬은 DATABASE_URL 사용
            echo=settings.DEBUG,
            pool_pre_ping=True
        )
        print("✅ 로컬 PostgreSQL 연결 성공")
        return engine

# 엔진 생성
engine = get_database_engine()

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