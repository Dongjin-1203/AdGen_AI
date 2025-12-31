from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.api.routes import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    """비동기 컨텍스트 메니저"""

    # ===== 시작 시 실행 =====
    print("🚀 서버 시작")

    yield

    # ===== 종료 시 실행 =====
    print("👋 서버 종료")

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title = "AdGen AI API",
    description="소규모 패션 쇼핑몰을 위한 AI 광고 자동 생성 서비스",
    version= "0.1.0",
    lifespan = lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)

# 루트 엔드포인트
@app.get("/")
def read_root():
    return {
        "message": "AdGen AI API",  
        "version": "0.1.0",
        "status": "running"
    }

# 헬스 체크
@app.get("/health")
def health_check():
    return {"status": "healthy",
            "version": "0.1.0",
            }
