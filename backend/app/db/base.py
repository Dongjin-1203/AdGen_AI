"""
Database configuration
Supports both SQLite and Cloud SQL based on DATABASE_URL
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# DATABASE_URL 읽기
DATABASE_URL = os.getenv("DATABASE_URL")

logger.info(f"🔧 DATABASE_URL: {DATABASE_URL[:50] if DATABASE_URL else 'Not set'}...")

# SQLite vs PostgreSQL 판단
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    # ===== SQLite 설정 =====
    logger.info("📁 Using SQLite database")
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
elif DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    # ===== PostgreSQL 직접 연결 =====
    logger.info("🐘 Using PostgreSQL (direct connection)")
    
    engine = create_engine(
        DATABASE_URL,
        echo=False
    )
    
else:
    # ===== Cloud SQL Connector 사용 (환경 변수 기반) =====
    logger.info("☁️ Using Cloud SQL Connector")
    
    from google.cloud.sql.connector import Connector
    from config import settings
    
    connector = Connector()
    
    def getconn():
        """Cloud SQL 연결 생성"""
        conn = connector.connect(
            settings.CLOUD_SQL_CONNECTION_NAME,
            "pg8000",
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME
        )
        return conn
    
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        echo=False
    )

# Base 클래스 생성
Base = declarative_base()

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

logger.info("✅ Database configuration loaded")