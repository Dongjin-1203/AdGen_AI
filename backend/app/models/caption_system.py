"""
광고 캡션 시스템 모델
AI 캡션 생성, 사용자 수정, 최종 광고 페이지 관리
"""
from sqlalchemy import Column, String, Integer, Numeric, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class AdCaption(Base):
    """광고 캡션 생성 및 수정 기록"""
    __tablename__ = 'ad_captions'
    
    caption_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(
        String(36), 
        ForeignKey("user_contents.content_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    generation_id = Column(
        String(36), 
        ForeignKey("generation_history.generation_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # AI 생성 캡션
    ai_caption = Column(Text, nullable=False)
    ai_confidence = Column(Numeric(3, 2), nullable=True)
    
    # 최종 캡션 (수정 후 또는 그대로)
    final_caption = Column(Text, nullable=False)
    is_modified = Column(Boolean, default=False, index=True)
    
    # 메타데이터
    style = Column(String(50), nullable=True)  # resort, retro, romantic
    user_request = Column(Text, nullable=True)  # 사용자 추가 요청
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    content = relationship("UserContent", backref="ad_captions")
    user = relationship("User", backref="ad_captions")
    generation = relationship("GenerationHistory", backref="ad_caption", passive_deletes=True)
    
    def __repr__(self):
        return f"<AdCaption(caption_id={self.caption_id}, is_modified={self.is_modified})>"


class CaptionCorrection(Base):
    """캡션 수정 기록 (보상 기반 학습용)"""
    __tablename__ = 'caption_corrections'
    
    correction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    caption_id = Column(
        String(36), 
        ForeignKey("ad_captions.caption_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # 수정 전후
    original_caption = Column(Text, nullable=False)
    corrected_caption = Column(Text, nullable=False)
    
    # 보상 점수 (간단 버전)
    reward_score = Column(Integer, default=0, index=True)  # 0: 수정됨, 1: 그대로 사용
    
    # 메타데이터
    edit_type = Column(String(50), nullable=True)  # tone, length, content, style
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 관계
    caption = relationship("AdCaption", backref="corrections")
    user = relationship("User", backref="caption_corrections")
    
    def __repr__(self):
        return f"<CaptionCorrection(correction_id={self.correction_id}, reward_score={self.reward_score})>"


class AdCopyHistory(Base):
    """최종 광고 페이지 생성 기록"""
    __tablename__ = 'ad_copy_history'
    
    ad_copy_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(
        String(36), 
        ForeignKey("user_contents.content_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    caption_id = Column(
        String(36), 
        ForeignKey("ad_captions.caption_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    generation_id = Column(
        String(36), 
        ForeignKey("generation_history.generation_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # 광고 카피 데이터
    ad_copy_data = Column(JSON, nullable=False)  # headline, discount, period, brand 등
    template_used = Column(String(50), nullable=False, index=True)  # minimal, bold, vintage
    
    # 결과물
    html_content = Column(Text, nullable=False)
    final_image_url = Column(String(1000), nullable=True)  # PNG 렌더링 결과 (향후)
    
    # 메타데이터
    processing_time = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 관계
    content = relationship("UserContent", backref="ad_copies")
    user = relationship("User", backref="ad_copies")
    caption = relationship("AdCaption", backref="ad_copy")
    generation = relationship("GenerationHistory", backref="ad_copy", passive_deletes=True)
    
    def __repr__(self):
        return f"<AdCopyHistory(ad_copy_id={self.ad_copy_id}, template={self.template_used})>"