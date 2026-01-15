from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class ContentCreate(BaseModel):
    """콘텐츠 생성 요청"""
    product_name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    price: Optional[Decimal] = None

class ContentResponse(BaseModel):
    """콘텐츠 응답"""
    content_id: str
    user_id: str
    image_url: str
    thumbnail_url: str
    
    # 기본 정보
    product_name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    price: Optional[float] = None
    
    # Vision AI 필드 추가
    sub_category: Optional[str] = None
    material: Optional[str] = None
    fit: Optional[str] = None
    style_tags: Optional[str] = None  # JSON 문자열
    ai_confidence: Optional[float] = None
    confirmed: Optional[bool] = False
    caption: Optional[str] = None  # AI 캡션 (추후)
    
    # 메타데이터
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # SQLAlchemy 객체 → Pydantic 자동 변환