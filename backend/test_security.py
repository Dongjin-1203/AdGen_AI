from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)

# 1. 비밀번호 해싱 테스트
password = "password123"
hashed = get_password_hash(password)
print(f"✅ 해싱: {hashed[:50]}...")

# 2. 비밀번호 검증 테스트
is_valid = verify_password(password, hashed)
print(f"✅ 검증 (올바른 비밀번호): {is_valid}")

is_invalid = verify_password("wrongpassword", hashed)
print(f"✅ 검증 (틀린 비밀번호): {is_invalid}")

# 3. JWT 토큰 생성 테스트
token = create_access_token(data={"sub": "user@example.com"})
print(f"✅ 토큰 생성: {token[:50]}...")

# 4. JWT 토큰 디코드 테스트
payload = decode_access_token(token)
print(f"✅ 토큰 디코드: {payload}")

# 5. 잘못된 토큰 테스트
invalid_payload = decode_access_token("invalid_token")
print(f"✅ 잘못된 토큰: {invalid_payload}")