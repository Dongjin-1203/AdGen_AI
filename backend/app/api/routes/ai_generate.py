"""
/api/v1/generate-ad 엔드포인트
이미 업로드된 콘텐츠(content_id)로 AI 광고 생성
"""

from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from PIL import Image
import io
import time
import uuid
import logging
from typing import Optional

from app.db.base import get_db
from app.schemas.content import ContentResponse
from app.services.ai.replicate_generator import ReplicateBackgroundGenerator
from app.services.ai.style_prompts import StylePrompts
from app.core.storage import download_from_gcs, upload_to_gcs

logger = logging.getLogger(__name__)

# Replicate Generator (싱글톤)
replicate_generator = None

def get_replicate_generator() -> ReplicateBackgroundGenerator:
    """Get or create Replicate generator instance"""
    global replicate_generator
    if replicate_generator is None:
        from config import settings
        logger.info("Initializing ReplicateBackgroundGenerator...")
        api_token = settings.REPLICATE_API_TOKEN
        replicate_generator = ReplicateBackgroundGenerator(api_token=api_token)
    return replicate_generator


router = APIRouter()


@router.post("/generate-ad")
async def generate_ad_from_content(
    content_id: str = Form(..., description="업로드된 콘텐츠 ID"),
    style: str = Form(default="minimal", description="스타일: vintage, modern, minimal, natural, luxury"),
    db: Session = Depends(get_db)
):
    """
    이미 업로드된 콘텐츠로 AI 광고 생성
    
    Flow:
    1. content_id로 콘텐츠 조회
    2. GCS에서 원본 이미지 다운로드
    3. 스타일에 맞는 프롬프트 생성
    4. AI 배경 생성 (Replicate SDXL)
    5. 결과를 GCS에 저장
    6. URL 반환
    
    Args:
        content_id: 업로드된 콘텐츠 ID
        style: AI 스타일 (vintage/modern/minimal/natural/luxury)
    
    Returns:
        result_url: 생성된 이미지 GCS URL
        processing_time: 처리 시간 (초)
    """
    start_time = time.time()
    
    try:
        # 1. 콘텐츠 조회
        content = db.query(ContentResponse).filter(ContentResponse.content_id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        logger.info(f"[AI Generate] Starting for content_id={content_id}, style={style}")
        
        # 2. GCS에서 원본 이미지 다운로드
        # image_url 예: https://storage.googleapis.com/bucket-name/uploads/xxx.jpg
        # 또는 /uploads/xxx.jpg (로컬)
        
        image_url = content.image_url
        if not image_url:
            raise HTTPException(status_code=400, detail="No image URL in content")
        
        # GCS 경로 추출
        if image_url.startswith('http'):
            # https://storage.googleapis.com/bucket-name/uploads/xxx.jpg
            # → uploads/xxx.jpg
            gcs_path = '/'.join(image_url.split('/')[-2:])
        else:
            # /uploads/xxx.jpg → uploads/xxx.jpg
            gcs_path = image_url.lstrip('/')
        
        logger.info(f"[AI Generate] Downloading from GCS: {gcs_path}")
        
        # GCS에서 다운로드
        image_bytes = download_from_gcs(gcs_path)
        original_image = Image.open(io.BytesIO(image_bytes))
        
        logger.info(f"[AI Generate] Image loaded: {original_image.size}")
        
        # 3. 스타일 프롬프트 생성
        # 스타일 매핑 (프론트엔드 → 백엔드)
        style_map = {
            'minimal': 'minimal',
            'vintage': 'emotional',
            'modern': 'street',
            'natural': 'emotional',
            'luxury': 'minimal'
        }
        
        mapped_style = style_map.get(style.lower(), 'minimal')
        prompt_dict = StylePrompts.get_prompt(mapped_style)
        prompt = prompt_dict.get('positive', '')
        
        logger.info(f"[AI Generate] Style: {style} → {mapped_style}")
        logger.info(f"[AI Generate] Prompt: {prompt}")
        
        # 4. AI 배경 생성
        generator = get_replicate_generator()
        
        # 스타일에 맞는 프롬프트로 생성
        result_image = generator.generate_background(
            product_image=original_image,
            prompt_text=prompt,
            aspect_ratio='square',
            style=mapped_style
        )
        
        logger.info(f"[AI Generate] Background generated: {result_image.size}")
        
        # 5. GCS에 업로드
        # 파일명: ai_generated/style_contentid_timestamp.jpg
        timestamp = int(time.time())
        filename = f"ai_generated/{style}_{content_id}_{timestamp}.jpg"
        
        # 이미지를 바이트로 변환
        img_byte_arr = io.BytesIO()
        result_image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        # GCS 업로드
        result_url = upload_to_gcs(
            file_data=img_byte_arr.getvalue(),
            destination_path=filename,
            content_type='image/jpeg'
        )
        
        # 처리 시간
        processing_time = time.time() - start_time
        
        logger.info(f"[AI Generate] Completed in {processing_time:.2f}s")
        logger.info(f"[AI Generate] Result URL: {result_url}")
        
        return {
            "success": True,
            "result_url": result_url,
            "processing_time": round(processing_time, 2),
            "style": style,
            "content_id": content_id,
            "prompt": prompt,
            "dimensions": {
                "width": result_image.width,
                "height": result_image.height
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI Generate] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI 생성 중 오류 발생: {str(e)}"
        )