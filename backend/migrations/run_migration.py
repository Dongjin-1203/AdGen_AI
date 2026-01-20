import sqlite3
import os

# DB 경로
DB_PATH = "adgen.db"  # 또는 .env에서 읽기

# 연결
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# SQL 파일 읽기
with open('migrations/002_sqlite_vision_and_history.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# 실행
try:
    cursor.executescript(sql_script)
    conn.commit()
    print("✅ 마이그레이션 완료!")
except Exception as e:
    print(f"❌ 마이그레이션 실패: {e}")
    conn.rollback()
finally:
    conn.close()