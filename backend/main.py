"""
AdGen AI - 통합 백엔드 서버
소규모 패션 쇼핑몰을 위한 AI 광고 자동 생성 서비스
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import logging

from config import settings
from app.api.routes import auth, contents, ai_generate
from app.api.routes import processing as image

# ===== 로깅 설정 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 50)
print("🚀 FastAPI 앱 초기화 시작")
print(f"PORT: {os.getenv('PORT', 'NOT SET')}")
print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"DB_NAME: {settings.DB_NAME}")
print("=" * 50)

# ===== 디렉토리 생성 =====
UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# ===== Lifespan 컨텍스트 매니저 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """비동기 컨텍스트 매니저"""
    logger.info("🚀 서버 시작")
    logger.info(f"📍 환경: {settings.ENVIRONMENT}")
    
    yield
    
    logger.info("👋 서버 종료")

# ===== FastAPI 앱 생성 =====
app = FastAPI(
    title="AdGen AI - 통합 API",
    description="소규모 패션 쇼핑몰을 위한 AI 광고 자동 생성 서비스 (인증 + 콘텐츠 관리 + 이미지 처리)",
    version="1.0.0",
    lifespan=lifespan
)

# ===== CORS 설정 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://adgen-frontend-613605394208.asia-northeast3.run.app",
        "https://*.run.app",
        "*"  # 개발 편의상 추가 (프로덕션에서는 제거 권장)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 정적 파일 제공 =====
# /uploads - 사용자 업로드 파일 (조건부)
if os.path.exists(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    logger.info("✅ 정적 파일 제공: /uploads")

# /static - 웹 UI 정적 파일
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
logger.info("✅ 정적 파일 제공: /static")

# ===== 라우터 등록 =====
app.include_router(auth.router)
app.include_router(contents.router)
app.include_router(image.router, prefix="/api/v1", tags=["Image Processing"])
app.include_router(ai_generate.router, prefix="/api/v1", tags=["ai"])

logger.info("✅ 라우터 등록 완료: auth, contents, image")

# ===== 루트 엔드포인트 =====
@app.get("/")
async def root():
    """
    루트 엔드포인트
    - index.html이 있으면 웹 UI 제공
    - 없으면 API 정보 반환
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {
            "message": "AdGen AI - 통합 백엔드 API",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "status": "active",
            "endpoints": {
                "authentication": {
                    "signup": "/api/auth/signup",
                    "login": "/api/auth/login",
                    "me": "/api/auth/me"
                },
                "contents": {
                    "upload": "/api/contents/upload",
                    "list": "/api/contents",
                    "detail": "/api/contents/{id}"
                },
                "image_processing": {
                    "remove_background": "/api/v1/remove-background",
                    "image_info": "/api/v1/image-info",
                    "health": "/api/v1/health"
                },
                "docs": "/docs",
                "health": "/health"
            }
        }

# ===== 헬스체크 엔드포인트 =====
@app.get("/health")
async def health_check():
    """통합 헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "auth": "active",
            "contents": "active",
            "image_processing": "active"
        }
    }

# ===== OPTIONS 메서드 처리 (CORS 디버깅용) =====
@app.options("/{path:path}")
async def options_handler(path: str):
    return {"message": "OK"}

logger.info("✅ FastAPI 앱 초기화 완료")
logger.info(f"📍 문서: http://localhost:{os.getenv('PORT', '8080')}/docs")