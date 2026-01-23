"""
Models package
모든 SQLAlchemy 모델을 import하여 Alembic이 인식할 수 있도록 설정
"""
from .schemas import (
    User,
    Shop,
    Product,
    UserContent,
    GenerationHistory
)

from .reward_system import (
    AIPrediction,
    UserCorrection,
    RewardScore
)

__all__ = [
    # 기존 모델
    "User",
    "Shop",
    "Product",
    "UserContent",
    "GenerationHistory",
    # 보상 기반 학습 모델
    "AIPrediction",
    "UserCorrection",
    "RewardScore",
]