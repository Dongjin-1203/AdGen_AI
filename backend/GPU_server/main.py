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

# ===== 로깅 설정 =====
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== 전역 Generator =====
generator = None

# ===== Lifespan 컨텍스트 매니저 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 실행"""
    global generator
    
    logger.info("=" * 60)
    logger.info("🚀 GPU 서버 시작")
    logger.info(f"📍 환경: {settings.ENVIRONMENT}")
    logger.info(f"🎮 CUDA 사용 가능: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        logger.info(f"🎮 GPU: {gpu_name}")
        logger.info(f"💾 GPU 메모리: {gpu_memory:.1f} GB")
    else:
        logger.error("❌ CUDA를 사용할 수 없습니다!")
        if settings.FORCE_CUDA:
            raise RuntimeError("GPU가 필요하지만 CUDA를 사용할 수 없습니다.")
    
    # ===== 모델 로드 =====
    try:
        logger.info("📦 SDXL 모델 로딩 중...")
        generator = SDXLGenerator(device="cuda" if torch.cuda.is_available() else "cpu")
        generator.load_model()
        logger.info("✅ 모델 로드 완료")
    except Exception as e:
        logger.error(f"❌ 모델 로드 실패: {e}")
        logger.exception(e)
        if settings.FORCE_CUDA:
            raise
    
    logger.info("=" * 60)
    
    yield
    
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
        "endpoints": {
            "generate": "POST /generate",
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

# ===== 서버 시작 로그 =====
logger.info("✅ FastAPI 앱 초기화 완료")
logger.info(f"📍 서버 주소: http://{settings.HOST}:{settings.PORT}")
logger.info(f"📍 문서: http://{settings.HOST}:{settings.PORT}/docs")