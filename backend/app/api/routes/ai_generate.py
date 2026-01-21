"""
/api/v1/generate-ad 엔드포인트
GPU 서버 전용
"""

from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from PIL import Image
import io
import time
import uuid
import logging
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.base import get_db
from app.models.schemas import UserContent, User, GenerationHistory  
from app.api.routes.auth import get_current_user  
from app.services.gpu_client import GPUServerClient
from app.core.storage import download_from_gcs, upload_to_gcs
from config import settings

logger = logging.getLogger(__name__)

# ===== 스타일별 프롬프트 정의 (GPU_server에서 복사) =====
STYLE_PROMPTS = {
    'resort': {
        'positive': (
            "professional resort fashion photography, commercial shoot, "
            "bright beach atmosphere, tropical vibes, vacation style, "
            "natural sunlight, ocean background, sandy beach, palm trees, "
            "safe for work, relaxed elegant mood, summer fashion, "
            "8k quality, clean composition, travel magazine style, "
            "professional commercial advertisement"
        ),
        'negative': (
            "nsfw, inappropriate content, adult content, nudity, "
            "dark, gloomy, winter, urban, city, indoor, "
            "cluttered, messy, low quality, grainy, blurry, "
            "amateur, unprofessional, distorted"
        )
    },
    'retro': {
        'positive': (
            "professional retro fashion photography, commercial shoot, "
            "vintage aesthetic, 70s 80s style, nostalgic atmosphere, "
            "film camera quality, analog colors, classic poses, "
            "safe for work, retro color grading, timeless fashion, "
            "8k quality, vintage vibe, editorial style, "
            "professional commercial advertisement"
        ),
        'negative': (
            "nsfw, inappropriate content, adult content, nudity, "
            "modern, futuristic, neon, digital, overly saturated, "
            "low quality, grainy, distorted, blurry, "
            "amateur, unprofessional, contemporary"
        )
    },
    'romantic': {
        'positive': (
            "professional romantic fashion photography, commercial shoot, "
            "soft feminine aesthetic, dreamy atmosphere, pastel colors, "
            "flowing fabrics, gentle lighting, floral elements, "
            "safe for work, elegant mood, graceful poses, "
            "8k quality, delicate composition, ethereal style, "
            "professional commercial advertisement"
        ),
        'negative': (
            "nsfw, inappropriate content, adult content, nudity, "
            "harsh, aggressive, dark, masculine, street style, "
            "low quality, grainy, distorted, blurry, "
            "amateur, unprofessional, rough"
        )
    }
}

# ===== Request Model 추가 =====
class FashionAdRequest(BaseModel):
    """패션 광고 생성 요청"""
    product_id: str
    style: str  # minimal, vintage, modern, natural, luxury
    garment_description: Optional[str] = None
    aspect_ratio: str = "square"  # square, portrait, landscape
    prompt: Optional[str] = None
    num_inference_steps: int = 30
    model_index: Optional[int] = None

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
        # 스타일 검증 (resort, retro, romantic만 허용)
        if style.lower() not in STYLE_PROMPTS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid style. Available styles: {list(STYLE_PROMPTS.keys())}"
            )
        
        mapped_style = style.lower()
        
        # 백엔드에 정의된 프롬프트 딕셔너리 사용
        prompt_dict = STYLE_PROMPTS.get(mapped_style, STYLE_PROMPTS['minimal'])
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
                "id": "resort",
                "name": "리조트",
                "description": "밝고 경쾌한 휴양지 분위기"
            },
            {
                "id": "retro",
                "name": "레트로",
                "description": "빈티지하고 복고적인 감성"
            },
            {
                "id": "romantic",
                "name": "로맨틱",
                "description": "부드럽고 여성스러운 분위기"
            }
        ],
        "aspect_ratios": [
            {"id": "square", "name": "정사각형 (1:1)"},
            {"id": "portrait", "name": "세로형 (3:4)"},
            {"id": "landscape", "name": "가로형 (4:3)"}
        ]
    }

@router.post("/fashion-ad")
async def generate_fashion_ad(
    content_id: str = Form(..., description="업로드된 콘텐츠 ID"),
    style: str = Form(default="resort", description="스타일 (resort/retro/romantic)"),
    garment_description: str = Form(default=None, description="옷 설명 (선택)"),
    aspect_ratio: str = Form(default="square", description="비율 (square/portrait/landscape)"),
    prompt: str = Form(default=None, description="배경 프롬프트 (선택)"),
    num_inference_steps: int = Form(default=30, description="생성 스텝 (20-50)"),
    model_index: int = Form(default=None, description="특정 모델 인덱스 (선택)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    패션 광고 생성 (IDM-VTON + SDXL)
    
    워크플로우:
    1. 콘텐츠 이미지 로드 (GCS)
    2. GPU 서버로 광고 생성 요청
    3. 결과 이미지 GCS 업로드
    4. DB에 결과 저장
    """
    start_time = time.time()
    generation_method = "idm-vton+sdxl"
    
    try:
        # ===== 1. 콘텐츠 조회 및 권한 확인 =====
        content = db.query(UserContent).filter(UserContent.content_id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        if content.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        logger.info(f"[Fashion Ad] Starting for content_id={content_id}, style={style}")
        
        # ===== 2. GCS에서 이미지 다운로드 =====
        image_url = content.image_url
        if not image_url:
            raise HTTPException(status_code=400, detail="No image URL in content")
        
        if image_url.startswith('http'):
            gcs_path = '/'.join(image_url.split('/')[-2:])
        else:
            gcs_path = image_url.lstrip('/')
        
        logger.info(f"[Fashion Ad] Downloading from GCS: {gcs_path}")
        
        image_bytes = download_from_gcs(gcs_path)
        garment_image = Image.open(io.BytesIO(image_bytes))
        
        logger.info(f"[Fashion Ad] Garment image loaded: {garment_image.size}")
        
        # ===== 3. GPU 서버 상태 확인 =====
        client = get_gpu_client()
        
        if not await client.health_check():
            raise HTTPException(
                status_code=503,
                detail="GPU 서버가 현재 사용 불가능합니다. 잠시 후 다시 시도해주세요."
            )
        
        # ===== 4. GPU 서버로 패션 광고 생성 요청 =====
        logger.info("[Fashion Ad] Requesting fashion ad generation from GPU server...")
        
        # 이미지를 바이트로 변환
        img_byte_arr = io.BytesIO()
        garment_image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        garment_bytes = img_byte_arr.getvalue()
        
        # GPU 서버 호출
        result_image_bytes = await client.generate_fashion_ad(
            product_image=garment_bytes,
            style=style,
            garment_description=garment_description,
            aspect_ratio=aspect_ratio,
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            model_index=model_index
        )
        
        logger.info(f"[Fashion Ad] ✅ GPU server generation succeeded")
        
        # 결과 이미지 로드
        result_image = Image.open(io.BytesIO(result_image_bytes))
        logger.info(f"[Fashion Ad] Result image: {result_image.size}")
        
        # ===== 5. GCS에 업로드 =====
        timestamp = int(time.time())
        filename = f"fashion_ads/{style}_{content_id}_{timestamp}.png"
        
        result_url = upload_to_gcs(
            file_data=result_image_bytes,
            destination_path=filename,
            content_type='image/png'
        )
        
        processing_time = time.time() - start_time
        
        # ===== 6. 히스토리 저장 ===== 
        new_history = GenerationHistory(
            history_id=str(uuid.uuid4()),
            content_id=content_id,
            user_id=current_user.user_id, 
            style=style,
            prompt=prompt or garment_description or "fashion advertisement with virtual try-on",
            result_url=result_url,
            processing_time=round(processing_time, 2)
        )
        
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        
        logger.info(f"[Fashion Ad] Completed in {processing_time:.2f}s (via {generation_method})")
        logger.info(f"[Fashion Ad] History saved: {new_history.history_id}")
        logger.info(f"[Fashion Ad] Result URL: {result_url}")
        
        return {
            "success": True,
            "history_id": new_history.history_id,  
            "result_url": result_url,
            "processing_time": round(processing_time, 2),
            "generation_method": generation_method,
            "processing_type": "idm-vton+sdxl",
            "style": style,
            "content_id": content_id,
            "prompt": prompt,
            "dimensions": {
                "width": result_image.width,
                "height": result_image.height
            },
            "message": "Fashion ad with virtual try-on generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Fashion Ad] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"패션 광고 생성 중 오류 발생: {str(e)}"
        )

@router.get("/fashion-ad/styles")
async def get_fashion_ad_styles():
    """
    사용 가능한 패션 광고 스타일 목록
    """
    try:
        client = get_gpu_client()
        
        # GPU 서버에서 스타일 정보 가져오기
        styles_info = await client.get_fashion_styles()
        
        return {
            "success": True,
            "styles": styles_info.get("styles", []),
            "model_counts": styles_info.get("model_counts", {}),
            "style_mapping": styles_info.get("style_mapping", {}),
            "message": "Fashion styles retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get fashion styles: {e}")
        # GPU 서버 오류 시 기본값 반환
        return {
            "success": False,
            "styles": ["minimal", "vintage", "modern", "natural", "luxury"],
            "model_counts": {},
            "style_mapping": {
                "minimal": "resort",
                "vintage": "retro",
                "modern": "retro",
                "natural": "romantic",
                "luxury": "romantic"
            },
            "message": "Using fallback style list (GPU server unavailable)"
        }