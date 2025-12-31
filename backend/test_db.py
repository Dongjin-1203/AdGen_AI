from app.db.base import engine
from sqlalchemy import text

try:
    # 연결 테스트
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("✅ Cloud SQL 연결 성공!")
        print(f"PostgreSQL 버전: {version}")
        
except Exception as e:
    print(f"❌ 연결 실패: {e}")