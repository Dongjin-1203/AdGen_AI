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
from app.models.schemas import UserContent, User, GenerationHistory  
from app.api.routes.auth import get_current_user  
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
    prompt: Optional[str] = Form(None, description="사용자 추가 요청"), 
    current_user: User = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    """이미 업로드된 콘텐츠로 AI 광고 생성"""
    start_time = time.time()
    
    try:
        # 1. 콘텐츠 조회
        content = db.query(UserContent).filter(UserContent.content_id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # 본인 콘텐츠인지 확인 ⭐ 추가!
        if content.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        logger.info(f"[AI Generate] Starting for content_id={content_id}, style={style}")
        
        # 2-4. 기존 로직 동일 (GCS 다운로드, 프롬프트, AI 생성, 업로드)
        # ... (기존 코드)
        
        image_url = content.image_url
        if not image_url:
            raise HTTPException(status_code=400, detail="No image URL in content")
        
        if image_url.startswith('http'):
            gcs_path = '/'.join(image_url.split('/')[-2:])
        else:
            gcs_path = image_url.lstrip('/')
        
        logger.info(f"[AI Generate] Downloading from GCS: {gcs_path}")
        
        image_bytes = download_from_gcs(gcs_path)
        original_image = Image.open(io.BytesIO(image_bytes))
        
        logger.info(f"[AI Generate] Image loaded: {original_image.size}")
        
        # 스타일 프롬프트 생성
        style_map = {
            'minimal': 'minimal',
            'vintage': 'emotional',
            'modern': 'street',
            'natural': 'emotional',
            'luxury': 'minimal'
        }
        
        mapped_style = style_map.get(style.lower(), 'minimal')
        prompt_dict = StylePrompts.get_prompt(mapped_style)
        base_prompt = prompt_dict.get('positive', '')
        
        # 사용자 프롬프트 추가 
        final_prompt = base_prompt
        if prompt:
            final_prompt = f"{base_prompt}, {prompt}"
        
        logger.info(f"[AI Generate] Style: {style} → {mapped_style}")
        logger.info(f"[AI Generate] Prompt: {final_prompt}")
        
        # AI 배경 생성
        generator = get_replicate_generator()
        result_image = generator.generate_background(
            product_image=original_image,
            prompt_text=final_prompt,
            aspect_ratio='square',
            style=mapped_style
        )
        
        logger.info(f"[AI Generate] Background generated: {result_image.size}")
        
        # GCS에 업로드
        timestamp = int(time.time())
        filename = f"ai_generated/{style}_{content_id}_{timestamp}.jpg"
        
        img_byte_arr = io.BytesIO()
        result_image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        result_url = upload_to_gcs(
            file_data=img_byte_arr.getvalue(),
            destination_path=filename,
            content_type='image/jpeg'
        )
        
        processing_time = time.time() - start_time
        
        # ===== 5. 히스토리 저장 ===== 
        new_history = GenerationHistory(
            history_id=str(uuid.uuid4()),
            content_id=content_id,
            user_id=current_user.user_id, 
            style=style,
            prompt=prompt,  # 사용자 입력 프롬프트
            result_url=result_url,
            processing_time=round(processing_time, 2)
        )
        
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        
        logger.info(f"[AI Generate] Completed in {processing_time:.2f}s")
        logger.info(f"[AI Generate] History saved: {new_history.history_id}")
        logger.info(f"[AI Generate] Result URL: {result_url}")
        
        return {
            "success": True,
            "history_id": new_history.history_id,  
            "result_url": result_url,
            "processing_time": round(processing_time, 2),
            "style": style,
            "content_id": content_id,
            "prompt": final_prompt,
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