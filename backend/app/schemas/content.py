from pydantic import BaseModel, Field
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

class GenerateBackgroundRequest(BaseModel):
    """배경 생성 요청"""
    prompt: str = Field(..., description="배경 생성 프롬프트 (필수)")
    style: str = Field(default="minimal", description="스타일: minimal, emotional, street, instagram")
    aspect_ratio: str = Field(default="square", description="비율: square, portrait, landscape")
    num_inference_steps: int = Field(default=30, ge=10, le=50, description="생성 스텝 (10-50)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "white minimal studio background with soft shadows",
                "style": "minimal",
                "aspect_ratio": "square",
                "num_inference_steps": 30
            }
        }

class GenerateBackgroundResponse(BaseModel):
    """배경 생성 응답"""
    success: bool
    content_id: str
    result_url: str
    thumbnail_url: str
    mode: str = Field(..., description="사용된 생성 모드: local or replicate")
    prompt_used: str
    style: str
    processing_time: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "content_id": "123e4567-e89b-12d3-a456-426614174000",
                "result_url": "https://storage.googleapis.com/bucket/result.png",
                "thumbnail_url": "https://storage.googleapis.com/bucket/thumb_result.png",
                "mode": "replicate",
                "prompt_used": "white minimal studio background",
                "style": "minimal",
                "processing_time": 12.5
            }
        }