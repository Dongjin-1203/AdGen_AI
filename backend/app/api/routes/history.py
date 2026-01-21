"""
히스토리 API 라우터
/api/v1/history/{user_id} - 사용자별 생성 히스토리 목록
/api/v1/history/{history_id} (DELETE) - 히스토리 삭제
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.base import get_db
from app.models.schemas import GenerationHistory, UserContent, User
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["History"])


# ===== Response Schema =====
from pydantic import BaseModel

class HistoryResponse(BaseModel):
    """히스토리 응답 스키마"""
    history_id: str
    content_id: str
    user_id: str
    
    # 생성 정보
    style: str
    prompt: str | None
    result_url: str
    
    # 메타데이터
    processing_time: float | None
    created_at: datetime
    
    # 원본 콘텐츠 정보 (Join)
    original_image_url: str | None = None
    product_name: str | None = None
    
    class Config:
        from_attributes = True


# ===== API 엔드포인트 =====

@router.get("/history/{user_id}", response_model=List[HistoryResponse])
async def get_user_history(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자별 생성 히스토리 목록 조회
    
    Args:
        user_id: 조회할 사용자 ID
        limit: 조회 개수 (기본 50)
        offset: 건너뛸 개수 (페이징)
    
    Returns:
        히스토리 목록 (최신순)
    """
    # 권한 확인: 본인의 히스토리만 조회 가능
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's history"
        )
    
    # GenerationHistory + UserContent JOIN
    histories = db.query(
        GenerationHistory,
        UserContent.image_url.label('original_image_url'),
        UserContent.product_name
    ).join(
        UserContent,
        GenerationHistory.content_id == UserContent.content_id
    ).filter(
        GenerationHistory.user_id == user_id
    ).order_by(
        GenerationHistory.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    # 결과 변환
    result = []
    for history, original_image_url, product_name in histories:
        history_dict = {
            "history_id": history.history_id,
            "content_id": history.content_id,
            "user_id": history.user_id,
            "style": history.style,
            "prompt": history.prompt,
            "result_url": history.result_url,
            "processing_time": float(history.processing_time) if history.processing_time else None,
            "created_at": history.created_at,
            "original_image_url": original_image_url,
            "product_name": product_name
        }
        result.append(HistoryResponse(**history_dict))
    
    return result


@router.delete("/history/{history_id}")
async def delete_history(
    history_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    히스토리 삭제
    
    Args:
        history_id: 히스토리 ID
    
    Returns:
        success 메시지
    """
    # 본인 히스토리 확인
    history = db.query(GenerationHistory).filter(
        GenerationHistory.history_id == history_id,
        GenerationHistory.user_id == current_user.user_id
    ).first()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History not found or not authorized"
        )
    
    # 삭제
    db.delete(history)
    db.commit()
    
    return {
        "success": True,
        "message": "History deleted successfully",
        "history_id": history_id
    }