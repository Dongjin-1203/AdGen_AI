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
    original_image_url: str
    thumbnail_url: Optional[str]
    product_name: Optional[str]
    caption: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True