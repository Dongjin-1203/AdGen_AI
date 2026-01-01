from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

print("=" * 50)
print("🚀 FastAPI 앱 초기화 시작")
print(f"PORT: {os.getenv('PORT', 'NOT SET')}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'NOT SET')}")
print("=" * 50)

app = FastAPI(
    title="AdGen AI API",
    description="소규모 패션 쇼핑몰을 위한 AI 광고 자동 생성 서비스",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 일단 전체 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "AdGen AI Backend - Cloud Run!",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "0.1.0"
    }

print("✅ FastAPI 앱 초기화 완료")