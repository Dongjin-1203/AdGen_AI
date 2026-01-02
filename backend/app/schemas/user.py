"""
Pydantic 스키마 - API 입출력
SQLAlchemy 모델과 분리
"""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


# ===== 회원가입 요청 =====
class UserCreate(BaseModel):  # ← BaseModel 상속 추가
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호 (최소 8자)")
    name: str = Field(..., min_length=1, max_length=100, description="사용자 이름")
    phone: Optional[str] = Field(None, max_length=20, description="전화번호")


# ===== 로그인 요청 =====
class UserLogin(BaseModel):  # ← BaseModel 상속 추가
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., description="비밀번호")


# ===== 사용자 응답 (비밀번호 제외) =====
class UserResponse(BaseModel):  # ← BaseModel 상속 추가
    user_id: str
    email: str
    name: str
    phone: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemy 모델 → Pydantic


# ===== JWT 토큰 응답 =====
class Token(BaseModel):  # ← BaseModel 상속 추가
    access_token: str
    token_type: str = "bearer"


# ===== 토큰 데이터 =====
class TokenData(BaseModel):  # ← BaseModel 상속 추가
    email: Optional[str] = None