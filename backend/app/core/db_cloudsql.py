"""
Cloud SQL 연결 설정
DATABASE_URL 우선, 없으면 환경에 따라 Cloud SQL 또는 로컬 사용
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector
import pg8000
import logging

logger = logging.getLogger(__name__)

def get_cloud_sql_engine():
    """Cloud SQL Connector를 사용한 엔진 생성"""
    connector = Connector()

    def getconn():
        conn = connector.connect(
            os.getenv("CLOUD_SQL_CONNECTION_NAME"),
            "pg8000",
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return engine

def get_database_engine():
    """환경에 따라 적절한 엔진 반환"""
    
    # ===== 1순위: DATABASE_URL 체크 (최우선!) =====
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        logger.info(f"🔧 Using DATABASE_URL: {database_url[:50]}...")
        
        if database_url.startswith("sqlite"):
            # SQLite 사용
            logger.info("📁 Using SQLite database")
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False}
            )
            return engine
        
        elif database_url.startswith("postgresql"):
            # PostgreSQL 직접 연결
            logger.info("🐘 Using PostgreSQL (direct connection)")
            engine = create_engine(database_url)
            return engine
    
    # ===== 2순위: 환경 변수 기반 (DATABASE_URL 없을 때만) =====
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production" and os.getenv("CLOUD_SQL_CONNECTION_NAME"):
        # Cloud SQL 사용
        logger.info("☁️ Using Cloud SQL Connector")
        return get_cloud_sql_engine()
    else:
        # 로컬 PostgreSQL 사용
        logger.info("🔧 Using local database engine")
        from .database import engine
        return engine