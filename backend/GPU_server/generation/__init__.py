"""
AI 배경 생성 모듈

로컬 GPU 및 Replicate API를 사용한 배경 생성
하이브리드 모드로 자동 선택 가능
"""

from .local_generator import SDXLGenerator

__all__ = [
    "SDXLGenerator",
]

__version__ = "1.0.0"