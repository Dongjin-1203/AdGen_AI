"""
광고 카피 생성 API 엔드포인트 (단일 템플릿 생성 + 즉시 저장)

✨ 변경: Minimal 템플릿만 생성하고 DB에 즉시 저장
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, Dict, List
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

class AdCopyHistoryItem(BaseModel):
    """광고 카피 히스토리 단일 항목"""
    ad_copy_id: str
    template_used: str
    ad_copy_data: dict
    final_image_url: Optional[str]
    created_at: str
    
    # 추가 정보
    product_name: Optional[str]
    category: Optional[str]
    model_image_url: Optional[str]
    
    class Config:
        from_attributes = True


class AdCopyHistoryResponse(BaseModel):
    """광고 카피 히스토리 응답"""
    results: List[AdCopyHistoryItem]
    total: int
    page: int
    total_pages: int

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
    
@router.get("/ad-copy-history", response_model=AdCopyHistoryResponse)
async def get_ad_copy_history(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(12, ge=1, le=50, description="페이지당 항목 수"),
    template: Optional[str] = Query(None, description="템플릿 필터 (minimal, bold, vintage)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    광고 카피 히스토리 조회
    
    - 페이지네이션 지원
    - 템플릿별 필터링 가능
    - 최신순 정렬
    
    Args:
        page: 페이지 번호 (1부터 시작)
        limit: 페이지당 항목 수 (기본 12개)
        template: 템플릿 필터 (optional)
    
    Returns:
        AdCopyHistoryResponse
    """
    
    print(f"\n📋 광고 카피 히스토리 조회 - Page: {page}, Limit: {limit}")
    
    offset = (page - 1) * limit
    
    # 기본 쿼리
    query = db.query(AdCopyHistory)\
        .join(UserContent, AdCopyHistory.content_id == UserContent.content_id)\
        .join(GenerationHistory, AdCopyHistory.generation_id == GenerationHistory.history_id)\
        .filter(AdCopyHistory.user_id == current_user.user_id)
    
    # 템플릿 필터
    if template:
        query = query.filter(AdCopyHistory.template_used == template)
    
    # 총 개수
    total = query.count()
    
    # 데이터 조회 (최신순)
    ad_copies = query\
        .order_by(AdCopyHistory.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    # 응답 데이터 구성
    results = []
    for ad_copy in ad_copies:
        results.append(AdCopyHistoryItem(
            ad_copy_id=ad_copy.ad_copy_id,
            template_used=ad_copy.template_used,
            ad_copy_data=ad_copy.ad_copy_data,
            final_image_url=ad_copy.final_image_url,
            created_at=ad_copy.created_at.isoformat(),
            # 추가 정보
            product_name=ad_copy.content.product_name,
            category=ad_copy.content.category,
            model_image_url=ad_copy.generation.result_url
        ))
    
    total_pages = (total + limit - 1) // limit
    
    print(f"✅ 조회 완료: {len(results)}개 (전체 {total}개)")
    
    return AdCopyHistoryResponse(
        results=results,
        total=total,
        page=page,
        total_pages=total_pages
    )


@router.get("/ad-copy-history/{ad_copy_id}")
async def get_ad_copy_detail(
    ad_copy_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    광고 카피 상세 조회
    
    Args:
        ad_copy_id: AdCopyHistory ID
    
    Returns:
        상세 정보 (HTML 포함)
    """
    
    ad_copy = db.query(AdCopyHistory)\
        .join(UserContent, AdCopyHistory.content_id == UserContent.content_id)\
        .join(GenerationHistory, AdCopyHistory.generation_id == GenerationHistory.history_id)\
        .filter(
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
        "created_at": ad_copy.created_at.isoformat(),
        "processing_time": ad_copy.processing_time,
        # 추가 정보
        "product_name": ad_copy.content.product_name,
        "category": ad_copy.content.category,
        "color": ad_copy.content.color,
        "model_image_url": ad_copy.generation.result_url,
        "style": ad_copy.generation.style
    }


@router.get("/ad-copy-history/{ad_copy_id}/download")
async def download_ad_copy_image(
    ad_copy_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    광고 카피 최종 이미지 다운로드
    
    Args:
        ad_copy_id: AdCopyHistory ID
    
    Returns:
        PNG 이미지 파일
    """
    from urllib.parse import quote
    
    print(f"\n📥 광고 이미지 다운로드 요청: {ad_copy_id}")
    
    # AdCopyHistory 조회
    ad_copy = db.query(AdCopyHistory).filter(
        AdCopyHistory.ad_copy_id == ad_copy_id,
        AdCopyHistory.user_id == current_user.user_id
    ).first()
    
    if not ad_copy:
        raise HTTPException(status_code=404, detail="Not found")
    
    if not ad_copy.final_image_url:
        raise HTTPException(
            status_code=400,
            detail="최종 이미지가 아직 생성되지 않았습니다."
        )
    
    # GCS에서 이미지 다운로드
    from app.api.routes.history import download_from_gcs
    
    try:
        image_bytes = download_from_gcs(ad_copy.final_image_url)
        print(f"✅ 이미지 다운로드 완료: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"❌ GCS 다운로드 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이미지 다운로드 실패: {str(e)}"
        )
    
    # ✅ 파일명 생성 (영문만 사용)
    created_date = ad_copy.created_at.strftime("%Y%m%d")
    template = ad_copy.template_used
    ad_id_short = ad_copy_id[:8]
    
    # ASCII-safe 파일명 (영문, 숫자, 언더스코어만)
    filename = f"ad_{template}_{created_date}_{ad_id_short}.png"
    
    print(f"📦 다운로드 파일명: {filename}")
    
    # ✅ Response 헤더 (URL 인코딩 없이 ASCII만)
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(image_bytes))
        }
    )

@router.delete("/ad-copy-history/{ad_copy_id}")
async def delete_ad_copy(
    ad_copy_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    광고 카피 삭제
    
    Args:
        ad_copy_id: AdCopyHistory ID
    
    Returns:
        삭제 성공 메시지
    """
    
    # AdCopyHistory 조회
    ad_copy = db.query(AdCopyHistory).filter(
        AdCopyHistory.ad_copy_id == ad_copy_id,
        AdCopyHistory.user_id == current_user.user_id
    ).first()
    
    if not ad_copy:
        raise HTTPException(status_code=404, detail="Not found")
    
    # 삭제
    db.delete(ad_copy)
    db.commit()
    
    print(f"🗑️  광고 카피 삭제 완료: {ad_copy_id}")
    
    return {
        "success": True,
        "message": "광고가 삭제되었습니다.",
        "ad_copy_id": ad_copy_id
    }


@router.get("/ad-copy-statistics")
async def get_ad_copy_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    광고 카피 통계
    
    - 총 생성 개수
    - 템플릿별 개수
    - 최근 7일 생성 개수
    
    Returns:
        통계 정보
    """
    from datetime import datetime, timedelta
    
    # 총 개수
    total_count = db.query(func.count(AdCopyHistory.ad_copy_id))\
        .filter(AdCopyHistory.user_id == current_user.user_id)\
        .scalar()
    
    # 템플릿별 개수
    template_counts = db.query(
        AdCopyHistory.template_used,
        func.count(AdCopyHistory.ad_copy_id)
    ).filter(
        AdCopyHistory.user_id == current_user.user_id
    ).group_by(
        AdCopyHistory.template_used
    ).all()
    
    # 최근 7일
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_count = db.query(func.count(AdCopyHistory.ad_copy_id))\
        .filter(
            AdCopyHistory.user_id == current_user.user_id,
            AdCopyHistory.created_at >= seven_days_ago
        ).scalar()
    
    return {
        "total_count": total_count,
        "template_counts": {
            template: count for template, count in template_counts
        },
        "recent_7days_count": recent_count,
        "average_per_day": round(recent_count / 7, 1) if recent_count > 0 else 0
    }