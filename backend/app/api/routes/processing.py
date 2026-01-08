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

# ===== 구버전 /generate-ad 엔드포인트 제거됨 =====
# AI 광고 생성은 ai_generate.py에서 처리합니다.
# (content_id 기반, UserContent 모델 사용)