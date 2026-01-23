"""
광고 생성 API 엔드포인트
GPT-5 기반 광고 카피 생성 및 HTML 렌더링
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict
import json

from app.db.base import get_db
from app.models.schemas import UserContent
from app.models.reward_system import AIPrediction
from app.services.html.ad_generator import AdGenerator
from app.api.routes.auth import get_current_user

router = APIRouter(tags=["광고 카피 생성"])


# ========== Request/Response Models ==========

class GenerateAdCopyRequest(BaseModel):
    """광고 카피 생성 요청"""
    content_id: str
    user_request: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "uuid-here",
                "user_request": "힙한 느낌으로 MZ세대 타겟"
            }
        }


class AdCopyResponse(BaseModel):
    """광고 카피 응답"""
    content_id: str
    ad_copy: Dict
    html_preview: str
    template_used: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "uuid-here",
                "ad_copy": {
                    "headline": "STREET VIBES",
                    "discount": "60% OFF",
                    "caption": "🔥 스트릿 감성 아우터 초특가!"
                },
                "html_preview": "<!DOCTYPE html>...",
                "template_used": "bold"
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
    광고 카피 + HTML 생성 (이미지 렌더링 전)
    
    - Vision AI 분석 결과를 기반으로 GPT-5가 광고 카피 생성
    - 자동 선택된 템플릿과 카피를 결합하여 HTML 생성
    - 프론트엔드에서 HTML 미리보기 가능
    
    **처리 시간:** ~2초 (GPT-5)
    """
    
    # 1. 콘텐츠 조회 및 권한 확인
    content = db.query(UserContent).filter(
        UserContent.content_id == request.content_id,
        UserContent.user_id == current_user.user_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="콘텐츠를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    # 2. Vision AI 분석 결과 확인
    if not content.category:
        raise HTTPException(
            status_code=400,
            detail="Vision AI 분석이 완료되지 않았습니다. 먼저 이미지를 업로드하세요."
        )
    
    # 3. SDXL 생성 이미지 확인
    # Note: generated_image_url 필드가 UserContent에 있다고 가정
    # 없다면 이 부분은 제거하거나 수정 필요
    generated_image_url = getattr(content, 'generated_image_url', None)
    
    if not generated_image_url:
        raise HTTPException(
            status_code=400,
            detail="생성된 모델 이미지가 없습니다. 먼저 SDXL 이미지를 생성하세요."
        )
    
    # 4. Vision AI 분석 결과 준비
    # style_tags는 JSON 또는 문자열로 저장되어 있을 수 있음
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
    
    # 5. 광고 HTML 생성 (GPT-5 카피 + 템플릿)
    try:
        generator = AdGenerator()
        result = generator.generate_html(
            vision_result=vision_result,
            image_url=generated_image_url,
            user_request=request.user_request
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"광고 카피 생성 중 오류가 발생했습니다: {str(e)}"
        )
    
    # 6. 응답 반환
    return AdCopyResponse(
        content_id=request.content_id,
        ad_copy=result['ad_copy'],
        html_preview=result['html'],
        template_used=result['template_used']
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
    
    test_image_url = "https://storage.googleapis.com/adgen-storage/test/sample.jpg"
    
    try:
        generator = AdGenerator()
        result = generator.generate_html(
            vision_result=test_vision_result,
            image_url=test_image_url,
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