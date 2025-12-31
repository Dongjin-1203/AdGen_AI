"""
보안 관련 함수
- 비밀번호 해싱/검증
- JWT 토큰 생성/검증
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from config import settings

# CryptContext 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== 비밀번호 해싱 =====
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ===== JWT 토큰 =====
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # 1. 데이터 복사
    to_encode = data.copy()
    
    # 2. 만료 시간 설정
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 3. 만료 시간 추가
    to_encode.update({"exp": expire})
    
    # 4. JWT 토큰 생성
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None