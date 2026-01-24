"""
이미지 렌더링 API
HTML을 PNG 이미지로 변환 (Playwright)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
import io
from playwright.async_api import async_playwright

from app.db.base import get_db
from app.models.caption_system import AdCopyHistory
from app.api.routes.auth import get_current_user
from config import settings

router = APIRouter()


# ========== Request/Response Models ==========

class RenderImageRequest(BaseModel):
    """이미지 렌더링 요청"""
    ad_copy_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "ad_copy_id": "uuid-here"
            }
        }


class RenderImageResponse(BaseModel):
    """이미지 렌더링 응답"""
    success: bool
    ad_copy_id: str
    image_url: str
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ad_copy_id": "uuid-here",
                "image_url": "https://storage.googleapis.com/.../ad_minimal_uuid.png",
                "processing_time": 2.3
            }
        }


# ========== Helper Functions ==========

async def render_html_to_png(html_content: str, width: int = 1080, height: int = 1080) -> bytes:
    """
    HTML을 PNG 이미지로 변환
    
    Args:
        html_content: HTML 문자열
        width: 이미지 너비 (기본 1080px)
        height: 이미지 높이 (기본 1080px)
    
    Returns:
        PNG 이미지 바이트
    """
    
    async with async_playwright() as p:
        # Chromium 브라우저 실행
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        # 새 페이지 생성
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=2  # ✨ 고해상도 (Retina)
        )
        
        # HTML 로드
        await page.set_content(html_content, wait_until='networkidle')
        
        # 폰트 로딩 대기 (500ms)
        await page.wait_for_timeout(500)
        
        # PNG 스크린샷
        screenshot_bytes = await page.screenshot(
            type="png",
            full_page=False,
            omit_background=False
        )
        
        await browser.close()
        
        return screenshot_bytes


def upload_to_gcs(image_bytes: bytes, filename: str, user_id: str) -> str:
    """
    GCS에 이미지 업로드
    
    Args:
        image_bytes: 이미지 바이트
        filename: 파일명
        user_id: 사용자 ID
    
    Returns:
        GCS URL
    """
    from google.cloud import storage
    from google.oauth2 import service_account
    
    # GCS 클라이언트
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        )
        client = storage.Client(credentials=credentials)
    else:
        client = storage.Client()
    
    bucket_name = settings.GCS_BUCKET_NAME or "adgen-uploads-2026"
    bucket = client.bucket(bucket_name)
    
    # GCS 경로
    gcs_path = f"{user_id}/ads/{filename}"
    blob = bucket.blob(gcs_path)
    
    # 업로드
    blob.upload_from_string(image_bytes, content_type="image/png")
    
    # URL 생성
    image_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
    
    return image_url


# ========== API Endpoints ==========

@router.post("/render-image", response_model=RenderImageResponse)
async def render_ad_copy_to_image(
    request: RenderImageRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    저장된 광고를 PNG 이미지로 렌더링
    
    ✨ Playwright로 HTML → PNG 변환
    - 1080x1080 해상도 (2x Retina)
    - GCS에 저장
    - AdCopyHistory.final_image_url 업데이트
    
    **처리 시간:** ~2-3초 (Playwright)
    """
    
    import time
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🖼️  이미지 렌더링 시작")
    print(f"{'='*60}")
    print(f"Ad Copy ID: {request.ad_copy_id}")
    
    # 1. AdCopyHistory 조회
    ad_copy = db.query(AdCopyHistory).filter(
        AdCopyHistory.ad_copy_id == request.ad_copy_id,
        AdCopyHistory.user_id == current_user.user_id
    ).first()
    
    if not ad_copy:
        raise HTTPException(
            status_code=404,
            detail="광고를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    # 이미 렌더링된 경우
    if ad_copy.final_image_url:
        print(f"ℹ️  이미 렌더링된 이미지 존재: {ad_copy.final_image_url}")
        return RenderImageResponse(
            success=True,
            ad_copy_id=request.ad_copy_id,
            image_url=ad_copy.final_image_url,
            processing_time=0
        )
    
    # 2. HTML 가져오기
    html_content = ad_copy.html_content
    
    if not html_content:
        raise HTTPException(
            status_code=400,
            detail="HTML 내용이 없습니다."
        )
    
    # 3. HTML → PNG 변환
    try:
        print(f"🎨 Playwright로 렌더링 중...")
        image_bytes = await render_html_to_png(html_content, 1080, 1080)
        print(f"✅ 렌더링 완료: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"❌ Playwright 렌더링 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"이미지 렌더링 실패: {str(e)}"
        )
    
    # 4. GCS에 업로드
    try:
        filename = f"ad_{ad_copy.template_used}_{uuid.uuid4()}.png"
        image_url = upload_to_gcs(image_bytes, filename, current_user.user_id)
        print(f"☁️  GCS 업로드 완료: {image_url}")
    except Exception as e:
        print(f"❌ GCS 업로드 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이미지 저장 실패: {str(e)}"
        )
    
    # 5. AdCopyHistory 업데이트
    ad_copy.final_image_url = image_url
    db.commit()
    db.refresh(ad_copy)
    
    # 6. 처리 시간 계산
    processing_time = time.time() - start_time
    print(f"⏱️  총 처리 시간: {processing_time:.2f}초")
    print(f"{'='*60}\n")
    
    return RenderImageResponse(
        success=True,
        ad_copy_id=request.ad_copy_id,
        image_url=image_url,
        processing_time=processing_time
    )


@router.post("/render-html-direct")
async def render_html_direct(
    html_content: str,
    current_user = Depends(get_current_user)
):
    """
    HTML을 직접 PNG로 변환 (저장 안 함)
    
    테스트 또는 미리보기 용도
    
    Args:
        html_content: HTML 문자열
    
    Returns:
        PNG 이미지 바이트 (base64)
    """
    
    import time
    import base64
    
    start_time = time.time()
    
    try:
        # HTML → PNG
        image_bytes = await render_html_to_png(html_content, 1080, 1080)
        
        # Base64 인코딩
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "image_base64": image_base64,
            "size_bytes": len(image_bytes),
            "processing_time": processing_time
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"렌더링 실패: {str(e)}"
        )


@router.post("/test-playwright")
async def test_playwright(
    current_user = Depends(get_current_user)
):
    """
    Playwright 설치 테스트
    
    간단한 HTML을 렌더링하여 Playwright가 정상 작동하는지 확인
    """
    
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                width: 1080px;
                height: 1080px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: Arial, sans-serif;
            }
            .box {
                background: white;
                padding: 60px;
                border-radius: 30px;
                text-align: center;
            }
            h1 {
                font-size: 48px;
                color: #333;
                margin-bottom: 20px;
            }
            p {
                font-size: 24px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>🎉 Playwright Test</h1>
            <p>이미지 렌더링 성공!</p>
        </div>
    </body>
    </html>
    """
    
    try:
        import time
        import base64
        
        start_time = time.time()
        
        # 렌더링
        image_bytes = await render_html_to_png(test_html, 1080, 1080)
        
        # Base64 인코딩
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        processing_time = time.time() - start_time
        
        return {
            "status": "success",
            "message": "Playwright가 정상적으로 작동합니다.",
            "image_base64": image_base64,
            "size_bytes": len(image_bytes),
            "processing_time": processing_time
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }