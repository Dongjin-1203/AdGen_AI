from app.schemas.user import UserCreate

# 정상 케이스
user_data = UserCreate(
    email="test@example.com",
    password="password123",
    name="테스트"
)
print("✅ 정상 생성:", user_data)

# 에러 케이스 1: 비밀번호 짧음
try:
    UserCreate(
        email="test@example.com",
        password="short",  # 8자 미만
        name="테스트"
    )
except Exception as e:
    print("✅ 비밀번호 검증:", e)

# 에러 케이스 2: 이메일 누락
try:
    UserCreate(
        password="password123",
        name="테스트"
    )
except Exception as e:
    print("✅ 필수 필드 검증:", e)