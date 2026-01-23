"""
보상 기반 학습 시스템 모델
AI 예측, 사용자 수정, 보상 점수를 관리
"""
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class AIPrediction(Base):
    """AI 초기 예측 저장"""
    __tablename__ = 'ai_predictions'
    
    prediction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(
        String(36), 
        ForeignKey("user_contents.content_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # AI가 예측한 6개 필드
    predicted_category = Column(String(100), nullable=True)
    predicted_sub_category = Column(String(100), nullable=True)
    predicted_material = Column(String(100), nullable=True)
    predicted_fit = Column(String(50), nullable=True)
    predicted_color = Column(String(50), nullable=True)
    predicted_style_tags = Column(JSON, nullable=True)  # PostgreSQL JSON 타입
    
    # 신뢰도
    prediction_confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    content = relationship("UserContent", backref="ai_predictions")
    
    def __repr__(self):
        return f"<AIPrediction(prediction_id={self.prediction_id}, category={self.predicted_category})>"


class UserCorrection(Base):
    """사용자 수정 기록"""
    __tablename__ = 'user_corrections'
    
    correction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(
        String(36), 
        ForeignKey("user_contents.content_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    prediction_id = Column(
        String(36), 
        ForeignKey("ai_predictions.prediction_id", ondelete="CASCADE"), 
        nullable=False
    )
    user_id = Column(
        String(36), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # 어떤 필드를 수정했는지
    field_name = Column(String(50), nullable=False)  # 'category', 'material', 'color' 등
    original_value = Column(Text, nullable=True)     # AI 예측값
    corrected_value = Column(Text, nullable=True)    # 사용자 수정값
    
    corrected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 관계
    content = relationship("UserContent", backref="corrections")
    prediction = relationship("AIPrediction", backref="corrections")
    user = relationship("User", backref="corrections")
    
    def __repr__(self):
        return f"<UserCorrection(field={self.field_name}, {self.original_value} → {self.corrected_value})>"


class RewardScore(Base):
    """보상 점수"""
    __tablename__ = 'reward_scores'
    
    score_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(
        String(36), 
        ForeignKey("user_contents.content_id", ondelete="CASCADE"), 
        nullable=False
    )
    prediction_id = Column(
        String(36), 
        ForeignKey("ai_predictions.prediction_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    total_fields = Column(Integer, default=6)
    corrected_fields = Column(Integer, nullable=False)  # 수정한 필드 개수
    reward_score = Column(Integer, nullable=False, index=True)  # 6 - corrected_fields
    
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    used_for_training = Column(Boolean, default=False, index=True)
    
    # 관계
    content = relationship("UserContent", backref="reward_scores")
    prediction = relationship("AIPrediction", backref="reward_scores")
    
    def __repr__(self):
        return f"<RewardScore(score={self.reward_score}, corrected={self.corrected_fields}/6)>"