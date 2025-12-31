from sqlalchemy import Column, String, Text, Integer, DateTime, Numeric, ForeignKey
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
    __tablename__ = 'user_contents'
    
    content_id = Column(String(36), primary_key=True)  # image_id → content_id
    user_id = Column(String(36), ForeignKey("users.user_id"))
    
    # 이미지
    original_image_url = Column(String(1000), nullable=False)
    thumbnail_url = Column(String(1000), nullable=True)
    
    # 사용자 입력
    product_name = Column(String(300), nullable=True)
    category = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    
    # AI 생성 (나중에)
    caption = Column(Text, nullable=True)
    
    # 메타데이터
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    owner = relationship("User", backref="contents")  # images → contents