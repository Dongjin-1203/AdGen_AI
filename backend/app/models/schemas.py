from sqlalchemy import Column, String, Integer, DateTime, Numeric, Text, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base

class User(Base):
    """사용자 모델"""
    __tablename__ = 'users'
    
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User {self.email}>"
    

class Shop(Base):
    __tablename__ = 'shops'
    
    shop_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    shop_name = Column(String(200), nullable=False)
    location = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    owner = relationship("User", backref="shops")

class Product(Base):
    __tablename__ = 'products'
    
    product_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shop_id = Column(String(36), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(300), nullable=False)
    category = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    original_image_url = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    shop = relationship("Shop", backref="products")

class UserContent(Base):
    """사용자 업로드 콘텐츠 (갤러리)"""
    __tablename__ = 'user_contents'
    
    content_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.user_id"))
    
    # 이미지
    image_url = Column(String(1000), nullable=False)
    thumbnail_url = Column(String(1000), nullable=True)
    
    # 기본 정보
    product_name = Column(String(300), nullable=True)
    category = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    
    # Vision AI 필드
    sub_category = Column(String(100), nullable=True)
    material = Column(String(100), nullable=True)
    fit = Column(String(50), nullable=True)
    style_tags = Column(Text, nullable=True)
    ai_confidence = Column(Numeric(3, 2), nullable=True)
    confirmed = Column(Boolean, default=False)
    
    # AI 캡션
    caption = Column(Text, nullable=True)
    
    # 광고 생성 필드
    final_ad_url = Column(String(1000), nullable=True)      # 최종 광고 이미지 URL
    ad_copy_data = Column(JSON, nullable=True)             # 광고 카피 데이터
    
    # 메타데이터
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    owner = relationship("User", backref="contents")

class GenerationHistory(Base):
    """AI 광고 생성 기록 (히스토리)"""
    __tablename__ = 'generation_history'
    
    history_id = Column(String(36), primary_key=True)
    content_id = Column(
        String(36), 
        ForeignKey("user_contents.content_id", ondelete="CASCADE"), 
        nullable=False
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # 생성 정보
    style = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=True)
    result_url = Column(String(1000), nullable=False)
    
    # 메타데이터
    processing_time = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    content = relationship("UserContent", backref="generations")
    user = relationship("User", backref="generation_history")
    
    def __repr__(self):
        return f"<GenerationHistory(history_id={self.history_id}, style={self.style})>"