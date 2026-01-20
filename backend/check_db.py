import sqlite3

# DB 연결
conn = sqlite3.connect('adgen.db')
cursor = conn.cursor()

# 테이블 목록 조회
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📋 테이블 목록:")
for table in tables:
    print(f"  - {table[0]}")

# user_contents 구조 확인
print("\n📊 user_contents 테이블 구조:")
cursor.execute("PRAGMA table_info(user_contents);")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()