"""
Cloud SQL 연결 설정
개발 환경에서는 기존 DATABASE_URL 사용
배포 환경에서는 Cloud SQL Connector 사용
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector
import pg8000

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
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production" and os.getenv("CLOUD_SQL_CONNECTION_NAME"):
        # Cloud SQL 사용
        return get_cloud_sql_engine()
    else:
        # 로컬 PostgreSQL 사용
        from .database import engine
        return engine