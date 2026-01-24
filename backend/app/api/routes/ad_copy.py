"""
광고 페이지 생성 API 엔드포인트
캡션 기반 광고 카피 생성 및 HTML 렌더링
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict
import json
import uuid
import time

from app.db.base import get_db
from app.models.schemas import UserContent, GenerationHistory
from app.models.caption_system import AdCaption, AdCopyHistory
from app.services.html.ad_generator import AdGenerator
from app.api.routes.auth import get_current_user

router = APIRouter()  # tags는 main.py에서 지정


# ========== Request/Response Models ==========

class GenerateAdCopyRequest(BaseModel):
    """광고 카피 생성 요청"""
    caption_id: str  # ✨ 캡션 기반
    user_request: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "caption_id": "uuid-here",
                "user_request": "더 강렬한 느낌으로"
            }
        }


class AdCopyResponse(BaseModel):
    """광고 카피 응답"""
    ad_copy_id: str
    content_id: str
    caption_id: str
    ad_copy: Dict
    html_preview: str
    template_used: str
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "ad_copy_id": "uuid-here",
                "content_id": "uuid-here",
                "caption_id": "uuid-here",
                "ad_copy": {
                    "headline": "WINTER ESSENTIALS",
                    "discount": "60% OFF",
                    "period": "1.24 - 2.10",
                    "brand": "TRENDY"
                },
                "html_preview": "<!DOCTYPE html>...",
                "template_used": "bold",
                "processing_time": 2.5
            }
        }


# ========== API Endpoints ==========

@router.post("/ad-copy", response_model=AdCopyResponse)
async def generate_ad_copy(
    request: GenerateAdCopyRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    최종 광고 페이지 생성 (캡션 기반)
    
    - 확정된 캡션을 기반으로 완전한 광고 카피 생성
    - Vision AI 분석 + 캡션 → GPT → HTML
    - AdCopyHistory에 저장
    
    **처리 시간:** ~2-3초 (GPT)
    """
    start_time = time.time()
    
    # 1. ⭐ AdCaption 조회 및 권한 확인
    caption = db.query(AdCaption).filter(
        AdCaption.caption_id == request.caption_id,
        AdCaption.user_id == current_user.user_id
    ).first()
    
    if not caption:
        raise HTTPException(
            status_code=404,
            detail="캡션을 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    # 2. UserContent 조회
    content = db.query(UserContent).filter(
        UserContent.content_id == caption.content_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="콘텐츠를 찾을 수 없습니다."
        )
    
    # 3. GenerationHistory 조회
    generation = db.query(GenerationHistory).filter(
        GenerationHistory.history_id == caption.generation_id
    ).first()
    
    if not generation:
        raise HTTPException(
            status_code=404,
            detail="생성된 이미지를 찾을 수 없습니다."
        )
    
    generated_image_url = generation.result_url
    
    # 4. Vision AI 분석 결과 준비
    style_tags = content.style_tags
    if isinstance(style_tags, str):
        try:
            style_tags = json.loads(style_tags)
        except:
            style_tags = [tag.strip() for tag in style_tags.split(',') if tag.strip()]
    
    vision_result = {
        "category": content.category,
        "sub_category": content.sub_category,
        "color": content.color,
        "material": content.material,
        "fit": content.fit,
        "style_tags": style_tags or []
    }
    
    # 5. ⭐ 광고 HTML 생성 (캡션 포함)
    try:
        generator = AdGenerator()
        result = generator.generate_html(
            vision_result=vision_result,
            image_url=generated_image_url,
            caption=caption.final_caption,  # ✨ 확정된 캡션 사용
            user_request=request.user_request
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"광고 카피 생성 중 오류가 발생했습니다: {str(e)}"
        )
    
    processing_time = time.time() - start_time
    
    # 6. ⭐ AdCopyHistory 저장
    ad_copy_id = str(uuid.uuid4())
    
    new_ad_copy = AdCopyHistory(
        ad_copy_id=ad_copy_id,
        content_id=caption.content_id,
        user_id=current_user.user_id,
        caption_id=request.caption_id,
        generation_id=caption.generation_id,
        ad_copy_data=result['ad_copy'],
        template_used=result['template_used'],
        html_content=result['html'],
        processing_time=processing_time
    )
    
    db.add(new_ad_copy)
    db.commit()
    db.refresh(new_ad_copy)
    
    # 7. 응답 반환
    return AdCopyResponse(
        ad_copy_id=ad_copy_id,
        content_id=caption.content_id,
        caption_id=request.caption_id,
        ad_copy=result['ad_copy'],
        html_preview=result['html'],
        template_used=result['template_used'],
        processing_time=round(processing_time, 2)
    )


@router.get("/templates")
async def list_templates():
    """
    사용 가능한 템플릿 목록 조회
    
    Returns:
        템플릿 정보 리스트
    """
    from app.templates.ad_templates import AD_TEMPLATES
    
    templates = []
    for template_name, template_info in AD_TEMPLATES.items():
        templates.append({
            "name": template_name,
            "display_name": template_info['name'],
            "description": template_info['description'],
            "best_for": template_info['best_for'],
            "colors": template_info['colors']
        })
    
    return {
        "total": len(templates),
        "templates": templates
    }


@router.get("/ad-copy/{ad_copy_id}")
async def get_ad_copy(
    ad_copy_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    생성된 광고 카피 조회
    
    ad_copy_id로 저장된 광고 정보 조회
    """
    
    ad_copy = db.query(AdCopyHistory).filter(
        AdCopyHistory.ad_copy_id == ad_copy_id,
        AdCopyHistory.user_id == current_user.user_id
    ).first()
    
    if not ad_copy:
        raise HTTPException(
            status_code=404,
            detail="광고 카피를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    return {
        "ad_copy_id": ad_copy.ad_copy_id,
        "content_id": ad_copy.content_id,
        "caption_id": ad_copy.caption_id,
        "ad_copy_data": ad_copy.ad_copy_data,
        "template_used": ad_copy.template_used,
        "html_content": ad_copy.html_content,
        "final_image_url": ad_copy.final_image_url,
        "created_at": ad_copy.created_at
    }


@router.post("/test-ad-copy")
async def test_ad_copy_generation(
    current_user = Depends(get_current_user)
):
    """
    광고 카피 생성 테스트 (개발용)
    
    실제 DB 없이 샘플 데이터로 테스트
    """
    
    # 테스트 데이터
    test_vision_result = {
        "category": "아우터",
        "sub_category": "코트",
        "material": "울",
        "fit": "오버사이즈",
        "color": "블랙",
        "style_tags": ["미니멀", "모던"]
    }
    
    test_caption = "클래식한 블랙 울 코트로 겨울 스타일을 완성하세요 ❄️"
    test_image_url = "https://storage.googleapis.com/adgen-storage/test/sample.jpg"
    
    try:
        generator = AdGenerator()
        result = generator.generate_html(
            vision_result=test_vision_result,
            image_url=test_image_url,
            caption=test_caption,
            user_request="세련된 느낌으로"
        )
        
        return {
            "status": "success",
            "ad_copy": result['ad_copy'],
            "html_length": len(result['html']),
            "template_used": result['template_used']
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"테스트 실패: {str(e)}"
        )