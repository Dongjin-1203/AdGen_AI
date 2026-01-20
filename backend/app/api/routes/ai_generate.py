"""
/api/v1/generate-ad 엔드포인트
GPU 서버 전용 (Replicate 제거)
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
from app.services.gpu_client import GPUServerClient
from GPU_server.generation.prompts.style_prompts import StylePrompts
from app.core.storage import download_from_gcs, upload_to_gcs
from config import settings

logger = logging.getLogger(__name__)

# ===== GPU Client (싱글톤) ===== 
gpu_client = None

def get_gpu_client() -> GPUServerClient:
    """GPU 서버 클라이언트 가져오기"""
    global gpu_client
    
    # GPU 서버 URL 미설정
    if not settings.GPU_SERVER_URL:
        raise RuntimeError("GPU_SERVER_URL not configured")
    
    # 이미 생성됨
    if gpu_client is not None:
        return gpu_client
    
    # 클라이언트 생성
    try:
        logger.info("Initializing GPUServerClient...")
        gpu_client = GPUServerClient()
        logger.info("✅ GPUServerClient initialized")
        return gpu_client
    except Exception as e:
        logger.error(f"Failed to initialize GPU client: {e}")
        raise RuntimeError(f"GPU 클라이언트 초기화 실패: {e}")

router = APIRouter()

@router.post("/generate-ad")
async def generate_ad_from_content(
    content_id: str = Form(..., description="업로드된 콘텐츠 ID"),
    style: str = Form(default="minimal", description="스타일: vintage, modern, minimal, natural, luxury"),
    prompt: Optional[str] = Form(None, description="사용자 추가 요청"), 
    current_user: User = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    """이미 업로드된 콘텐츠로 AI 광고 생성 (GPU 서버 사용)"""
    start_time = time.time()
    generation_method = "gpu_server"
    
    try:
        # ===== 1. 콘텐츠 조회 및 권한 확인 =====
        content = db.query(UserContent).filter(UserContent.content_id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        if content.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        logger.info(f"[AI Generate] Starting for content_id={content_id}, style={style}")
        
        # ===== 2. GCS에서 이미지 다운로드 =====
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
        
        # ===== 3. 프롬프트 생성 =====
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
        logger.info(f"[AI Generate] Prompt: {final_prompt[:100]}...")
        
        # ===== 4. GPU 서버로 배경 생성 =====
        client = get_gpu_client()
        
        logger.info("[AI Generate] Requesting GPU server generation...")
        
        # GPU 서버 헬스체크
        if not await client.health_check():
            raise HTTPException(
                status_code=503,
                detail="GPU 서버가 현재 사용 불가능합니다. 잠시 후 다시 시도해주세요."
            )
        
        # 이미지 생성 요청
        result_image = await client.generate_background(
            product_image=original_image,
            prompt_text=final_prompt,
            style=mapped_style,
            aspect_ratio='square'
        )
        
        logger.info(f"[AI Generate] ✅ GPU server generation succeeded")
        logger.info(f"[AI Generate] Background generated: {result_image.size}")
        
        # ===== 5. GCS에 업로드 =====
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
        
        # ===== 6. 히스토리 저장 ===== 
        new_history = GenerationHistory(
            history_id=str(uuid.uuid4()),
            content_id=content_id,
            user_id=current_user.user_id, 
            style=style,
            prompt=prompt,
            result_url=result_url,
            processing_time=round(processing_time, 2)
        )
        
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        
        logger.info(f"[AI Generate] Completed in {processing_time:.2f}s (via {generation_method})")
        logger.info(f"[AI Generate] History saved: {new_history.history_id}")
        logger.info(f"[AI Generate] Result URL: {result_url}")
        
        return {
            "success": True,
            "history_id": new_history.history_id,  
            "result_url": result_url,
            "processing_time": round(processing_time, 2),
            "generation_method": generation_method,
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


@router.get("/gpu-status")
async def check_gpu_status():
    """GPU 서버 상태 확인"""
    try:
        client = get_gpu_client()
        is_healthy = await client.health_check()
        
        if is_healthy:
            return {
                "status": "available",
                "message": "GPU 서버 정상 작동 중",
                "gpu_server_url": settings.GPU_SERVER_URL
            }
        else:
            return {
                "status": "unavailable",
                "message": "GPU 서버 응답 없음",
                "gpu_server_url": settings.GPU_SERVER_URL
            }
    except Exception as e:
        logger.error(f"GPU status check failed: {e}")
        return {
            "status": "error",
            "message": f"GPU 서버 상태 확인 실패: {str(e)}",
            "gpu_server_url": settings.GPU_SERVER_URL
        }


@router.get("/styles")
async def get_available_styles():
    """사용 가능한 스타일 목록"""
    return {
        "styles": [
            {
                "id": "minimal",
                "name": "미니멀",
                "description": "깔끔하고 단순한 배경",
                "mapped_to": "minimal"
            },
            {
                "id": "vintage",
                "name": "빈티지",
                "description": "감성적이고 따뜻한 배경",
                "mapped_to": "emotional"
            },
            {
                "id": "modern",
                "name": "모던",
                "description": "현대적이고 세련된 배경",
                "mapped_to": "street"
            },
            {
                "id": "natural",
                "name": "내추럴",
                "description": "자연스럽고 편안한 배경",
                "mapped_to": "emotional"
            },
            {
                "id": "luxury",
                "name": "럭셔리",
                "description": "고급스럽고 우아한 배경",
                "mapped_to": "minimal"
            }
        ],
        "aspect_ratios": [
            {"id": "square", "name": "정사각형 (1:1)"},
            {"id": "portrait", "name": "세로형 (3:4)"},
            {"id": "landscape", "name": "가로형 (4:3)"}
        ]
    }