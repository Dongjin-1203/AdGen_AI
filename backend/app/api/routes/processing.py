"""
Image Processing API Endpoints
Handles background removal and image processing requests
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from PIL import Image
import io
import time
import logging
from typing import Optional
import uuid
from google.cloud import storage
from google.oauth2 import service_account


from app.services.ai.replicate_generator import ReplicateBackgroundGenerator
from config import settings
from app.services.ai.background import BackgroundRemovalService
from app.services.ai.img_processing import (
    resize_to_instagram_ratio,
    add_background_color,
    get_image_info
)
from app.services.ai.styles import StyleProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services (singleton)
bg_removal_service = None
style_processor = None


def get_bg_removal_service() -> BackgroundRemovalService:
    """Get or create background removal service instance"""
    global bg_removal_service
    if bg_removal_service is None:
        logger.info("Initializing BackgroundRemovalService...")
        bg_removal_service = BackgroundRemovalService()
    return bg_removal_service


def get_style_processor() -> StyleProcessor:
    """Get or create style processor instance"""
    global style_processor
    if style_processor is None:
        logger.info("Initializing StyleProcessor...")
        style_processor = StyleProcessor()
    return style_processor


@router.post("/remove-background")
async def remove_background(
    file: UploadFile = File(...),
    ratio: str = Form(default="4:5"),
    background_color: Optional[str] = Form(default=None),
    style: str = Form(default="minimal"),
    enhance_color: bool = Form(default=True),
    remove_wrinkles: bool = Form(default=False)
):
    """
    Remove background from uploaded image with advanced processing
    
    Args:
        file: Image file to process
        ratio: Instagram aspect ratio ("4:5", "1:1", "16:9")
        background_color: Optional hex color for background (e.g., "#FFFFFF")
        style: Processing style ("minimal", "mood", "street")
        enhance_color: Apply automatic color correction
        remove_wrinkles: Apply wrinkle smoothing
    
    Returns:
        Processed image with background removed and style applied
    """
    start_time = time.time()
    timing = {}
    
    try:
        # Read uploaded file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        logger.info(f"Processing image: {file.filename}, size: {image.size}, mode: {image.mode}")
        logger.info(f"Options: ratio={ratio}, style={style}, enhance_color={enhance_color}, remove_wrinkles={remove_wrinkles}")
        
        # Get services
        bg_service = get_bg_removal_service()
        
        # 1. Remove background
        step_start = time.time()
        result = await bg_service.remove_background(image)
        timing['background_removal'] = time.time() - step_start
        
        # 2. Apply style processing
        step_start = time.time()
        processor = get_style_processor()
        result = processor.process_with_style(result, style=style)
        timing['style_processing'] = time.time() - step_start
        
        # 3. Resize to Instagram ratio
        step_start = time.time()
        result = resize_to_instagram_ratio(result, ratio=ratio)
        timing['resize'] = time.time() - step_start
        
        # 4. Add background color if specified
        if background_color:
            step_start = time.time()
            # Parse hex color
            bg_color = tuple(int(background_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            result = add_background_color(result, background_color=bg_color)
            timing['background_color'] = time.time() - step_start
            output_format = "JPEG"
        else:
            output_format = "PNG"
        
        # Convert to bytes
        step_start = time.time()
        output_buffer = io.BytesIO()
        result.save(output_buffer, format=output_format, quality=95)
        output_buffer.seek(0)
        timing['encoding'] = time.time() - step_start
        
        processing_time = time.time() - start_time
        timing['total'] = processing_time
        
        logger.info(f"Processing completed in {processing_time:.2f}s")
        logger.info(f"Timing breakdown: {timing}")
        
        # Return image response
        media_type = f"image/{output_format.lower()}"
        return Response(
            content=output_buffer.getvalue(),
            media_type=media_type,
            headers={
                "X-Processing-Time": str(processing_time),
                "X-Processing-Style": style,
                "X-Output-Format": output_format,
                "X-Timing-Background": str(timing.get('background_removal', 0)),
                "X-Timing-Style": str(timing.get('style_processing', 0)),
                "Content-Disposition": f'attachment; filename="processed_{file.filename}"'
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/image-info")
async def get_image_metadata(file: UploadFile = File(...)):
    """
    Get metadata about uploaded image
    
    Args:
        file: Image file
        
    Returns:
        Image metadata (size, dimensions, format, etc.)
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        info = get_image_info(image)
        info["filename"] = file.filename
        info["content_type"] = file.content_type
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading image: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for image processing service"""
    try:
        service = get_bg_removal_service()
        return {
            "status": "healthy",
            "model_loaded": True,
            "styles_available": ["minimal", "mood", "street"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
    
# ===== Replicate Generator 초기화 (Lazy) =====
replicate_generator = None

def get_replicate_generator() -> ReplicateBackgroundGenerator:
    """Get or create Replicate generator instance"""
    global replicate_generator
    if replicate_generator is None:
        logger.info("Initializing ReplicateBackgroundGenerator...")
        api_token = settings.REPLICATE_API_TOKEN  # 환경 변수에서 로드
        replicate_generator = ReplicateBackgroundGenerator(api_token=api_token)
    return replicate_generator


# ===== GCS 클라이언트 (기존 contents.py 패턴) =====
_storage_client = None

def get_storage_client():
    """GCS 클라이언트 가져오기"""
    global _storage_client
    
    if _storage_client is None:
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            _storage_client = storage.Client(credentials=credentials)
        else:
            _storage_client = storage.Client()
        
        logger.info("GCS Storage 클라이언트 초기화 완료")
    
    return _storage_client


# ===== 새로운 엔드포인트 =====
@router.post("/generate-ad")
async def generate_ad(
    file: UploadFile = File(...),
    prompt: str = Form(..., description="배경 생성 프롬프트 (예: on a wooden table, soft lighting)"),
    product_name: Optional[str] = Form(None),
    style: str = Form(default="minimal", description="스타일: minimal, emotional, street"),
    ratio: str = Form(default="square", description="비율: square, portrait, landscape"),
    enhance_color: bool = Form(default=True),
    remove_wrinkles: bool = Form(default=False)
):
    """
    전체 AI 광고 생성 파이프라인
    
    Flow:
    1. 이미지 업로드
    2. 배경 제거 (rembg)
    3. 색상/주름 보정
    4. AI 배경 생성 (Replicate SDXL)
    5. GCS 저장
    
    Returns:
        생성된 광고 이미지 URL 및 메타데이터
    """
    start_time = time.time()
    timing = {}
    
    try:
        # 1. 이미지 로드
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        original_size = image.size
        
        logger.info(f"Starting ad generation: {file.filename}, size: {image.size}")
        
        # 2. 배경 제거
        step_start = time.time()
        bg_service = get_bg_removal_service()
        no_bg_image = await bg_service.remove_background(image)
        timing['background_removal'] = time.time() - step_start
        logger.info(f"Background removed in {timing['background_removal']:.2f}s")
        
        # 3. 스타일 처리 (색상/주름 보정)
        step_start = time.time()
        processor = get_style_processor()
        processed_image = processor.process_with_style(no_bg_image, style=style)
        timing['style_processing'] = time.time() - step_start
        logger.info(f"Style processed in {timing['style_processing']:.2f}s")
        
        # 4. AI 배경 생성 (Replicate)
        step_start = time.time()
        generator = get_replicate_generator()
        final_image = generator.generate_background(
            product_image=processed_image,
            prompt_text=prompt,
            aspect_ratio=ratio,
            style=style
        )
        timing['background_generation'] = time.time() - step_start
        logger.info(f"Background generated in {timing['background_generation']:.2f}s")
        
        # 5. GCS 업로드
        step_start = time.time()
        
        # 파일명 생성
        file_ext = ".jpg"  # AI 생성은 항상 JPG
        unique_filename = f"ai_generated_{uuid.uuid4()}{file_ext}"
        
        # GCS 경로 (ai_generated 폴더에 저장)
        gcs_path = f"ai_generated/{unique_filename}"
        
        # 이미지를 바이트로 변환
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        # GCS 업로드
        bucket_name = settings.GCS_BUCKET_NAME or "adgen-ai-storage"
        storage_client = get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        
        blob.upload_from_string(
            img_byte_arr.getvalue(),
            content_type="image/jpeg"
        )
        
        timing['gcs_upload'] = time.time() - step_start
        
        # GCS 공개 URL
        image_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
        
        # 총 처리 시간
        total_time = time.time() - start_time
        timing['total'] = total_time
        
        logger.info(f"Ad generation completed in {total_time:.2f}s")
        logger.info(f"Timing breakdown: {timing}")
        
        # 응답
        return {
            "success": True,
            "image_url": image_url,
            "product_name": product_name,
            "style": style,
            "ratio": ratio,
            "prompt": prompt,
            "dimensions": {
                "width": final_image.width,
                "height": final_image.height
            },
            "original_dimensions": {
                "width": original_size[0],
                "height": original_size[1]
            },
            "processing_time": {
                "total": round(total_time, 2),
                "background_removal": round(timing['background_removal'], 2),
                "style_processing": round(timing['style_processing'], 2),
                "background_generation": round(timing['background_generation'], 2),
                "gcs_upload": round(timing['gcs_upload'], 2)
            },
            "message": "Ad generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating ad: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating ad: {str(e)}"
        )