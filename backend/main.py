from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from config import settings
from app.api.routes import auth, contents

print("=" * 50)
print("🚀 FastAPI 앱 초기화 시작")
print(f"PORT: {os.getenv('PORT', 'NOT SET')}")
print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"DB_NAME: {settings.DB_NAME}")
print("=" * 50)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """비동기 컨텍스트 매니저"""
    print("🚀 서버 시작")
    print(f"📍 환경: {settings.ENVIRONMENT}")
    
    yield
    
    print("👋 서버 종료")

app = FastAPI(
    title="AdGen AI API",
    description="소규모 패션 쇼핑몰을 위한 AI 광고 자동 생성 서비스",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 제공 (uploads 폴더가 있을 때만)
if os.path.exists("uploads"):
    from fastapi.staticfiles import StaticFiles
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    print("✅ 정적 파일 제공: /uploads")

# 라우터 등록
app.include_router(auth.router)
app.include_router(contents.router)

@app.get("/")
def read_root():
    return {
        "message": "AdGen AI Backend - Cloud Run!",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }

print("✅ FastAPI 앱 초기화 완료")