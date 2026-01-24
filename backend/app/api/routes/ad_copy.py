"""
광고 카피 생성 API 엔드포인트 (단일 템플릿 생성 + 즉시 저장)

✨ 변경: Minimal 템플릿만 생성하고 DB에 즉시 저장
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
from app.api.routes.auth import get_current_user
from app.services.html.ad_generator import AdGenerator
from app.templates.ad_templates import AD_TEMPLATES

router = APIRouter()


# ========== Request/Response Models ==========

class GenerateAdCopyRequest(BaseModel):
    """광고 카피 생성 요청"""
    caption_id: str
    user_request: Optional[str] = None


class AdCopyResponse(BaseModel):
    """단일 템플릿 응답"""
    ad_copy_id: str
    caption_id: str
    content_id: str
    generation_id: str
    template_used: str
    ad_copy: Dict
    html_content: str
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "ad_copy_id": "uuid-here",
                "caption_id": "uuid-here",
                "content_id": "uuid-here",
                "generation_id": "uuid-here",
                "template_used": "minimal",
                "ad_copy": {
                    "headline": "베이지의 따뜻함",
                    "discount": "40% OFF",
                    "period": "11.01 - 11.08",
                    "brand": "FALL SPECIAL"
                },
                "html_content": "<!DOCTYPE html>...",
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
    광고 카피 + HTML 생성 (Minimal 템플릿 단일 생성 + 즉시 저장)
    
    워크플로우:
    1. AdCaption 조회
    2. Vision AI 결과 준비
    3. Minimal 템플릿 생성
    4. DB에 즉시 저장 (AdCopyHistory)
    5. ad_copy_id 반환
    
    **처리 시간:** ~2-3초
    """
    
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🎨 광고 카피 생성 시작 (Minimal 템플릿)")
    print(f"{'='*60}")
    print(f"Caption ID: {request.caption_id}")
    
    # 1. AdCaption 조회 및 권한 확인
    caption = db.query(AdCaption).filter(
        AdCaption.caption_id == request.caption_id,
        AdCaption.user_id == current_user.user_id
    ).first()
    
    if not caption:
        raise HTTPException(
            status_code=404,
            detail="캡션을 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    # 2. UserContent, GenerationHistory 조회
    content = db.query(UserContent).filter(
        UserContent.content_id == caption.content_id
    ).first()
    
    generation = db.query(GenerationHistory).filter(
        GenerationHistory.history_id == caption.generation_id
    ).first()
    
    if not content or not generation:
        raise HTTPException(
            status_code=404,
            detail="관련 데이터를 찾을 수 없습니다."
        )
    
    generated_image_url = generation.result_url
    
    # 3. Vision AI 분석 결과 준비
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
    
    # 4. ✨ Minimal 템플릿 생성
    generator = AdGenerator()
    template_name = "minimal"
    
    try:
        print(f"\n📝 {template_name} 템플릿 생성 중...")
        
        result = generator.generate_html_with_template(
            vision_result=vision_result,
            image_url=generated_image_url,
            template_name=template_name,
            caption=caption.final_caption,
            user_request=request.user_request
        )
        
        print(f"✅ {template_name} 템플릿 생성 완료")
        
    except Exception as e:
        print(f"❌ 템플릿 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"템플릿 생성 실패: {str(e)}"
        )
    
    # 5. ✨ DB에 즉시 저장
    ad_copy_id = str(uuid.uuid4())
    
    new_ad_copy = AdCopyHistory(
        ad_copy_id=ad_copy_id,
        content_id=caption.content_id,
        user_id=current_user.user_id,
        caption_id=request.caption_id,
        generation_id=caption.generation_id,
        ad_copy_data=result['ad_copy'],
        template_used=template_name,
        html_content=result['html'],
        processing_time=0
    )
    
    db.add(new_ad_copy)
    db.commit()
    db.refresh(new_ad_copy)
    
    processing_time = time.time() - start_time
    
    print(f"✅ AdCopyHistory 저장 완료: {ad_copy_id} ({template_name})")
    print(f"⏱️  총 처리 시간: {processing_time:.2f}초")
    print(f"{'='*60}\n")
    
    # 6. 응답 반환
    return AdCopyResponse(
        ad_copy_id=ad_copy_id,
        caption_id=request.caption_id,
        content_id=caption.content_id,
        generation_id=caption.generation_id,
        template_used=template_name,
        ad_copy=result['ad_copy'],
        html_content=result['html'],
        processing_time=processing_time
    )


@router.get("/ad-copy/{ad_copy_id}")
async def get_ad_copy(
    ad_copy_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    저장된 광고 조회
    
    ad_copy_id로 저장된 광고 정보 조회
    """
    
    ad_copy = db.query(AdCopyHistory).filter(
        AdCopyHistory.ad_copy_id == ad_copy_id,
        AdCopyHistory.user_id == current_user.user_id
    ).first()
    
    if not ad_copy:
        raise HTTPException(
            status_code=404,
            detail="광고를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    return {
        "ad_copy_id": ad_copy.ad_copy_id,
        "template_used": ad_copy.template_used,
        "ad_copy_data": ad_copy.ad_copy_data,
        "html_content": ad_copy.html_content,
        "final_image_url": ad_copy.final_image_url,
        "created_at": ad_copy.created_at
    }


@router.get("/templates")
async def get_available_templates():
    """
    사용 가능한 템플릿 목록 조회
    
    프론트엔드에서 템플릿 정보를 미리 알 수 있도록
    """
    
    templates = []
    for template_name, template_info in AD_TEMPLATES.items():
        templates.append({
            "template_name": template_name,
            "template_display_name": template_info['name'],
            "description": template_info.get('description', '')
        })
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/test-ad-copy")
async def test_ad_copy_generation(
    current_user = Depends(get_current_user)
):
    """
    광고 카피 생성 테스트 (개발용)
    
    실제 DB 없이 샘플 데이터로 Minimal 템플릿 테스트
    """
    
    # 샘플 데이터
    vision_result = {
        "category": "아우터",
        "sub_category": "코트",
        "color": "블랙",
        "material": "울",
        "fit": "오버사이즈",
        "style_tags": ["미니멀", "모던"]
    }
    
    image_url = "https://via.placeholder.com/1080x1080"
    caption = "트렌디한 블랙 코트로 겨울 스타일 완성 🖤"
    
    # Minimal 템플릿 생성
    generator = AdGenerator()
    template_name = "minimal"
    
    try:
        result = generator.generate_html_with_template(
            vision_result=vision_result,
            image_url=image_url,
            template_name=template_name,
            caption=caption
        )
        
        return {
            "status": "success",
            "template_name": template_name,
            "template_display_name": AD_TEMPLATES[template_name]['name'],
            "ad_copy": result['ad_copy'],
            "html_length": len(result['html'])
        }
    except Exception as e:
        return {
            "status": "error",
            "template_name": template_name,
            "error": str(e)
        }