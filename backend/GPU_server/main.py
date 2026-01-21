"""
AdGen AI - GPU 전용 배경 생성 서버
AI 배경 생성만 담당하는 독립 API 서버
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from PIL import Image
import torch
import io
import logging
import os

from config import settings
from generation.local_generator import SDXLGenerator
from generation.fashion_ad_pipeline import FashionAdPipeline

# ===== 로깅 설정 =====
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== 전역 Generator =====
generator = None
fashion_pipeline = None

# ===== Lifespan 컨텍스트 매니저 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 실행"""
    global generator, fashion_pipeline  # fashion_pipeline 추가
    
    logger.info("=" * 60)
    logger.info("🚀 GPU 서버 시작")
    # ... 기존 코드 ...
    
    # ===== 모델 로드 =====
    try:
        logger.info("📦 SDXL 모델 로딩 중...")
        generator = SDXLGenerator(device="cuda" if torch.cuda.is_available() else "cpu")
        generator.load_model()
        logger.info("✅ SDXL 모델 로드 완료")
        
        # Fashion Pipeline 초기화 (SDXL generator 재사용)
        logger.info("📦 Fashion Ad Pipeline 초기화 중...")
        fashion_pipeline = FashionAdPipeline(
            sdxl_generator=generator,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        logger.info("✅ Fashion Ad Pipeline 초기화 완료")
        
    except Exception as e:
        logger.error(f"❌ 모델 로드 실패: {e}")
        logger.exception(e)
        if settings.FORCE_CUDA:
            raise
    
    logger.info("=" * 60)
    
    yield
    
    # Cleanup
    if fashion_pipeline:
        fashion_pipeline.cleanup()
    
    logger.info("👋 GPU 서버 종료")

# ===== FastAPI 앱 생성 =====
app = FastAPI(
    title="AdGen AI - GPU 서버",
    description="AI 배경 생성 전용 서버 (RealVisXL V4.0 + ControlNet)",
    version="1.0.0",
    lifespan=lifespan
)

# ===== CORS 설정 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 루트 엔드포인트 =====
@app.get("/")
async def root():
    """API 정보"""
    return {
        "service": "AdGen AI - GPU Server",
        "version": "1.0.0",
        "status": "active",
        "cuda_available": torch.cuda.is_available(),
        "model_loaded": generator is not None,
        "fashion_pipeline_loaded": fashion_pipeline is not None,
        "endpoints": {
            "generate": "POST /generate (배경 생성)",
            "generate_fashion_ad": "POST /generate-fashion-ad (패션 광고 생성)",
            "fashion_styles": "GET /fashion-ad/styles (스타일 목록)",
            "health": "GET /health",
            "gpu_info": "GET /gpu/info"
        }
    }

# ===== 헬스체크 =====
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    cuda_available = torch.cuda.is_available()
    
    health_status = {
        "status": "healthy" if (cuda_available and generator) else "degraded",
        "cuda_available": cuda_available,
        "model_loaded": generator is not None,
        "environment": settings.ENVIRONMENT
    }
    
    if cuda_available:
        health_status["gpu"] = {
            "name": torch.cuda.get_device_name(0),
            "memory_allocated_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 2),
            "memory_reserved_gb": round(torch.cuda.memory_reserved(0) / (1024**3), 2),
            "memory_total_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        }
    
    return health_status

# ===== GPU 정보 =====
@app.get("/gpu/info")
async def gpu_info():
    """GPU 상세 정보"""
    if not torch.cuda.is_available():
        raise HTTPException(status_code=503, detail="CUDA not available")
    
    props = torch.cuda.get_device_properties(0)
    
    return {
        "device_name": torch.cuda.get_device_name(0),
        "compute_capability": f"{props.major}.{props.minor}",
        "total_memory_gb": round(props.total_memory / (1024**3), 2),
        "allocated_memory_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 2),
        "reserved_memory_gb": round(torch.cuda.memory_reserved(0) / (1024**3), 2),
        "free_memory_gb": round((props.total_memory - torch.cuda.memory_reserved(0)) / (1024**3), 2),
        "multi_processor_count": props.multi_processor_count
    }

# ===== 배경 생성 API =====
@app.post("/generate")
async def generate_background(
    image: UploadFile = File(..., description="배경 제거된 제품 이미지 (PNG)"),
    prompt: str = Form(..., description="배경 생성 프롬프트"),
    style: str = Form(default=settings.DEFAULT_STYLE, description="스타일 (minimal/emotional/street/instagram)"),
    aspect_ratio: str = Form(default=settings.DEFAULT_ASPECT_RATIO, description="비율 (square/portrait/landscape)"),
    num_inference_steps: int = Form(default=settings.DEFAULT_NUM_INFERENCE_STEPS, description="생성 스텝 (20-50)"),
    controlnet_scale: float = Form(default=settings.DEFAULT_CONTROLNET_SCALE, description="ControlNet 강도 (0.5-1.5)"),
    padding_percent: float = Form(default=0.7, description="이미지 패딩 비율 (0.5-0.9)"),
    vertical_alignment: str = Form(default="center", description="수직 정렬 (top/center/bottom)"),
    use_ip_adapter: bool = Form(default=True, description="IP-Adapter 사용 여부")
):
    """
    AI 배경 생성
    
    Returns:
        생성된 이미지 (image/png)
    """
    # 모델 로드 확인
    if generator is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # 이미지 로드
        image_data = await image.read()
        input_image = Image.open(io.BytesIO(image_data))
        
        logger.info(f"🎨 배경 생성 시작: style={style}, ratio={aspect_ratio}")
        logger.info(f"   Prompt: {prompt}")
        
        # 배경 생성
        result_image = generator.generate_background(
            product_image=input_image,
            prompt_text=prompt,
            aspect_ratio=aspect_ratio,
            style=style,
            num_inference_steps=num_inference_steps,
            controlnet_conditioning_scale=controlnet_scale,
            padding_percent=padding_percent,
            vertical_alignment=vertical_alignment,
            use_ip_adapter=use_ip_adapter
        )
        
        # PNG로 변환
        output_buffer = io.BytesIO()
        result_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        
        logger.info(f"✅ 배경 생성 완료: {result_image.size}")
        
        return Response(
            content=output_buffer.getvalue(),
            media_type="image/png",
            headers={
                "X-Image-Width": str(result_image.width),
                "X-Image-Height": str(result_image.height)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 배경 생성 실패: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
@app.post("/generate-fashion-ad")
async def generate_fashion_ad(
    garment: UploadFile = File(..., description="옷 이미지 (JPG/PNG)"),
    style: str = Form(..., description="스타일 (minimal/vintage/modern/natural/luxury)"),
    garment_description: str = Form(default=None, description="옷 설명 (선택)"),
    aspect_ratio: str = Form(default="square", description="비율 (square/portrait/landscape)"),
    prompt: str = Form(default=None, description="배경 프롬프트 (선택)"),
    num_inference_steps: int = Form(default=30, description="생성 스텝 (20-50)"),
    model_index: int = Form(default=None, description="특정 모델 인덱스 (선택)")
):
    """
    패션 광고 생성 (IDM-VTON + SDXL)
    
    워크플로우:
    1. K-Fashion 모델 자동 선택
    2. 의류 마스크 + DensePose 생성
    3. IDM-VTON 가상 착장
    4. SDXL 배경 생성
    
    Returns:
        생성된 광고 이미지 (image/png)
    """
    # 모델 로드 확인
    if fashion_pipeline is None:
        raise HTTPException(status_code=503, detail="Fashion pipeline not loaded")
    
    try:
        # 이미지 로드
        garment_data = await garment.read()
        garment_image = Image.open(io.BytesIO(garment_data)).convert("RGB")
        
        logger.info("=" * 60)
        logger.info("🎨 Fashion Ad Generation Request")
        logger.info(f"   Style: {style}")
        logger.info(f"   Aspect Ratio: {aspect_ratio}")
        logger.info(f"   Garment Image: {garment_image.size}")
        if model_index is not None:
            logger.info(f"   Model Index: {model_index}")
        logger.info("=" * 60)
        
        # 광고 생성
        result_image = fashion_pipeline.generate(
            garment_image=garment_image,
            style=style,
            garment_description=garment_description,
            aspect_ratio=aspect_ratio,
            prompt_text=prompt,
            num_inference_steps=num_inference_steps,
            model_index=model_index
        )
        
        # PNG로 변환
        output_buffer = io.BytesIO()
        result_image.save(output_buffer, format="PNG", quality=95)
        output_buffer.seek(0)
        
        logger.info(f"✅ Fashion ad generation complete: {result_image.size}")
        
        return Response(
            content=output_buffer.getvalue(),
            media_type="image/png",
            headers={
                "X-Image-Width": str(result_image.width),
                "X-Image-Height": str(result_image.height),
                "X-Style": style,
                "X-Processing-Type": "idm-vton+sdxl"
            }
        )
        
    except ValueError as e:
        # 스타일 오류 등
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"❌ Fashion ad generation failed: {e}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/fashion-ad/styles")
async def get_fashion_styles():
    """
    사용 가능한 스타일 목록 반환
    """
    if fashion_pipeline is None:
        raise HTTPException(status_code=503, detail="Fashion pipeline not loaded")
    
    try:
        available_styles = fashion_pipeline.model_selector.get_available_styles()
        model_counts = fashion_pipeline.model_selector.get_all_models_info()
        
        return {
            "styles": available_styles,
            "model_counts": model_counts,
            "style_mapping": fashion_pipeline.model_selector.STYLE_MAPPING
        }
    except Exception as e:
        logger.error(f"Failed to get fashion styles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 서버 시작 로그 =====
logger.info("✅ FastAPI 앱 초기화 완료")
logger.info(f"📍 서버 주소: http://{settings.HOST}:{settings.PORT}")
logger.info(f"📍 문서: http://{settings.HOST}:{settings.PORT}/docs")