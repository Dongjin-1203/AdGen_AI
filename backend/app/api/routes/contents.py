"""
콘텐츠 API 라우터
/api/contents/upload - 이미지 업로드
/api/contents - 콘텐츠 목록
/api/contents/{id} - 콘텐츠 상세
/api/contents/{id}/generate-background - 배경 생성
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import os
from pathlib import Path
from PIL import Image
import io
from google.cloud import storage
from google.oauth2 import service_account
import json
import tempfile
import time
import requests
import httpx

from app.db.base import get_db
from app.models.schemas import UserContent, User
from app.schemas.content import ContentResponse, GenerateBackgroundRequest, GenerateBackgroundResponse
from app.api.routes.auth import get_current_user
from config import settings
from app.services.vision.product_analyzer import ProductAnalyzer
# from app.services.generation import HybridGenerator  # GPU 서버 사용으로 비활성화
from app.services.img_processing.background_removal import BackgroundRemovalService

router = APIRouter(prefix="/api/contents", tags=["Contents"])

# 허용된 이미지 확장자
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ===== GCS 클라이언트 (Lazy Initialization) =====
_storage_client = None
_bucket = None

def get_gcs_bucket():
    """GCS 버킷 가져오기 (Lazy Initialization)"""
    global _storage_client, _bucket
    
    if _storage_client is None:
        # credentials 로드
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            _storage_client = storage.Client(credentials=credentials)
        else:
            # 환경 변수 기반 (배포 환경)
            _storage_client = storage.Client()
        
        # 버킷 설정
        bucket_name = settings.GCS_BUCKET_NAME or "adgen-uploads-2026"
        _bucket = _storage_client.bucket(bucket_name)
        
        print(f"✅ GCS 클라이언트 초기화 완료: {bucket_name}")
    
    return _bucket


# ===== AI Services (Lazy Initialization) =====
# _background_generator = None  # GPU 서버 사용으로 비활성화
_background_remover = None

# def get_background_generator():
#     """배경 생성기 가져오기 (Lazy Initialization)"""
#     global _background_generator
#     if _background_generator is None:
#         _background_generator = HybridGenerator()
#         print(f"✅ Background Generator initialized: {_background_generator.get_mode()}")
#     return _background_generator

def get_background_remover():
    """배경 제거 서비스 가져오기"""
    global _background_remover
    if _background_remover is None:
        _background_remover = BackgroundRemovalService()
        print("✅ Background Remover initialized")
    return _background_remover


# ===== 기존 엔드포인트 (업로드, 목록, 상세, 수정) =====

@router.post("/upload", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def upload_content(
    file: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """이미지 업로드 및 콘텐츠 생성 (GCS 저장 + Vision AI)"""
    
    bucket = get_gcs_bucket()
    
    # ===== 1. 파일 검증 =====
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only image files are allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    try:
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )
    
    # ===== 2. GCS에 업로드 =====
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    thumbnail_filename = f"thumb_{unique_filename}"
    
    gcs_path = f"{current_user.user_id}/{unique_filename}"
    gcs_thumb_path = f"{current_user.user_id}/{thumbnail_filename}"
    
    # 원본 업로드
    try:
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(contents, content_type=f"image/{file_ext[1:]}")
        print(f"✅ Uploaded: {gcs_path}")
    except Exception as e:
        print(f"❌ GCS Upload Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image to storage"
        )
    
    # 썸네일 업로드
    try:
        thumb_image = image.copy()
        thumb_image.thumbnail((300, 300))
        thumb_buffer = io.BytesIO()
        thumb_image.save(thumb_buffer, format=image.format or 'JPEG')
        thumb_buffer.seek(0)
        
        thumb_blob = bucket.blob(gcs_thumb_path)
        thumb_blob.upload_from_string(
            thumb_buffer.read(),
            content_type=f"image/{file_ext[1:]}"
        )
        print(f"✅ Uploaded thumbnail: {gcs_thumb_path}")
    except Exception as e:
        print(f"❌ Thumbnail Upload Error: {e}")
    
    # ===== 3. Vision AI 분석 =====
    vision_data = {}

    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        print(f"\n{'='*60}")
        print(f"🔍 Vision AI 분석 시작")
        print(f"{'='*60}")
        print(f"임시 파일: {tmp_path}")

        # Vision AI 분석
        analyzer = ProductAnalyzer(provider="gemini")
        vision_result = await analyzer.analyze(tmp_path)
        
        # 임시 파일 삭제
        os.unlink(tmp_path)
        
        print(f"📊 Vision AI 결과: {vision_result}")
        
        if vision_result.get('success'):
            vision_data = {
                'category': vision_result.get('category'),
                'sub_category': vision_result.get('sub_category'),
                'color': vision_result.get('color'),
                'material': vision_result.get('material'),
                'fit': vision_result.get('fit'),
                'style_tags': json.dumps(vision_result.get('style_tags', []), ensure_ascii=False),
                'ai_confidence': vision_result.get('confidence')
            }
            print(f"✅ Vision AI 분석 완료: {vision_data['category']}, {vision_data['color']}")
        else:
            print(f"⚠️ Vision AI 분석 실패: {vision_result.get('error')}")

    except Exception as e:
        print(f"⚠️ Vision AI 오류 (계속 진행): {e}")
        import traceback
        traceback.print_exc()
    
    # 확인용 로그 출력
    print(f"\n📝 DB 저장 직전 vision_data:")
    print(f"vision_data = {vision_data}")
    print(f"type = {type(vision_data)}")
    print(f"len = {len(vision_data)}")
    print(f"keys = {vision_data.keys() if vision_data else 'None'}")

    # ===== 4. DB 저장 =====
    bucket_name = settings.GCS_BUCKET_NAME or "adgen-uploads-2026"
    image_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
    thumbnail_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_thumb_path}"
    
    # UserContent 객체 생성
    new_content = UserContent(
        content_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        
        # 기본 정보 (수동 입력 우선)
        product_name=product_name,
        category=category or vision_data.get('category'),  # Vision AI 결과 활용
        color=color or vision_data.get('color'),
        price=price,
        
        # Vision AI 결과
        sub_category=vision_data.get('sub_category'),
        material=vision_data.get('material'),
        fit=vision_data.get('fit'),
        style_tags=vision_data.get('style_tags'),
        ai_confidence=vision_data.get('ai_confidence'),
        confirmed=False,  # 사용자 확인 필요
        
        # 메타데이터
        file_size=file_size,
        width=width,
        height=height
    )
    
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    
    print(f"✅ Content saved: {new_content.content_id}")
    
    return new_content


@router.get("", response_model=List[ContentResponse])
async def get_my_contents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 콘텐츠 목록 조회
    최신순 정렬
    """
    contents = db.query(UserContent)\
        .filter(UserContent.user_id == current_user.user_id)\
        .order_by(UserContent.created_at.desc())\
        .all()
    
    return contents


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 상세 조회
    """
    content = db.query(UserContent)\
        .filter(
            UserContent.content_id == content_id,
            UserContent.user_id == current_user.user_id  # 본인 것만
        )\
        .first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return content

@router.patch("/{content_id}")
async def update_content(
    content_id: str,
    product_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    sub_category: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    fit: Optional[str] = Form(None),
    style_tags: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    confirmed: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 정보 수정 (Vision AI 결과 확인/수정 후)
    """
    # 본인 콘텐츠 확인
    content = db.query(UserContent).filter(
        UserContent.content_id == content_id,
        UserContent.user_id == current_user.user_id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # 수정
    if product_name is not None:
        content.product_name = product_name
    if category is not None:
        content.category = category
    if sub_category is not None:
        content.sub_category = sub_category
    if color is not None:
        content.color = color
    if material is not None:
        content.material = material
    if fit is not None:
        content.fit = fit
    if style_tags is not None:
        content.style_tags = style_tags
    if price is not None:
        content.price = float(price)
    
    # 확인 완료 처리
    content.confirmed = confirmed
    
    db.commit()
    db.refresh(content)
    
    return {
        "success": True,
        "content_id": content.content_id,
        "message": "Content updated successfully"
    }


# ===== 신규: 배경 생성 엔드포인트 =====

@router.post("/{content_id}/generate-background", response_model=GenerateBackgroundResponse)
async def generate_background(
    content_id: str,
    request: GenerateBackgroundRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    배경 생성
    
    프로세스:
    1. 원본 이미지 다운로드
    2. 배경 제거
    3. 배경 생성
    4. 결과 저장 및 반환
    """
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🎨 배경 생성 시작")
    print(f"{'='*60}")
    print(f"Content ID: {content_id}")
    print(f"Prompt: {request.prompt}")
    print(f"Style: {request.style}")
    print(f"Aspect Ratio: {request.aspect_ratio}")
    
    # ===== 1. 콘텐츠 조회 =====
    content = db.query(UserContent).filter(
        UserContent.content_id == content_id,
        UserContent.user_id == current_user.user_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # ===== 2. 원본 이미지 다운로드 =====
    try:
        print(f"📥 Downloading image: {content.image_url}")
        response = requests.get(content.image_url)
        response.raise_for_status()
        
        original_image = Image.open(io.BytesIO(response.content))
        print(f"✅ Image downloaded: {original_image.size}")
        
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download image: {str(e)}"
        )
    
    # ===== 3. 배경 제거 =====
    try:
        print(f"🖼️ Removing background...")
        bg_remover = get_background_remover()
        
        # ✅ PIL Image를 직접 전달 (bytes 변환 불필요)
        removed_bg_image = await bg_remover.remove_background(original_image)
        
        print(f"✅ Background removed: {removed_bg_image.size}, mode: {removed_bg_image.mode}")
        
    except Exception as e:
        print(f"❌ Background removal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Background removal failed: {str(e)}"
        )
    
    # ===== 4. GPU 서버에 배경 생성 요청 =====
    try:
        print(f"🎨 Calling GPU server for background generation...")
        print(f"GPU Server URL: {settings.GPU_SERVER_URL}")
        
        # PIL Image를 bytes로 변환
        img_bytes = io.BytesIO()
        removed_bg_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # GPU 서버에 POST 요청
        async with httpx.AsyncClient(timeout=settings.GPU_SERVER_TIMEOUT) as client:
            files = {"image": ("image.png", img_bytes, "image/png")}
            data = {
                "prompt": request.prompt,
                "style": request.style,
                "aspect_ratio": request.aspect_ratio,
                "num_inference_steps": request.num_inference_steps
            }
            
            response = await client.post(
                f"{settings.GPU_SERVER_URL}/generate",
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"GPU server error: {response.text}"
                )
            
            # 생성된 이미지 로드
            result_image = Image.open(io.BytesIO(response.content))
            mode_used = "gpu_server"
            print(f"✅ Background generated using GPU server: {result_image.size}")
        
    except httpx.TimeoutException:
        print(f"❌ GPU server timeout")
        raise HTTPException(
            status_code=504,
            detail="GPU server timeout - image generation took too long"
        )
    except Exception as e:
        print(f"❌ Background generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Background generation failed: {str(e)}"
        )

    # ===== 5. 결과를 GCS에 저장 =====
    try:
        bucket = get_gcs_bucket()
        
        # 결과 이미지 저장
        result_filename = f"generated_{uuid.uuid4()}.png"
        result_gcs_path = f"{current_user.user_id}/generated/{result_filename}"
        
        result_buffer = io.BytesIO()
        result_image.save(result_buffer, format='PNG')
        result_buffer.seek(0)
        
        result_blob = bucket.blob(result_gcs_path)
        result_blob.upload_from_string(
            result_buffer.read(),
            content_type="image/png"
        )
        
        bucket_name = settings.GCS_BUCKET_NAME or "adgen-uploads-2026"
        result_url = f"https://storage.googleapis.com/{bucket_name}/{result_gcs_path}"
        print(f"✅ Result uploaded: {result_url}")
        
        # 썸네일 저장
        thumb_filename = f"thumb_{result_filename}"
        thumb_gcs_path = f"{current_user.user_id}/generated/{thumb_filename}"
        
        thumb_image = result_image.copy()
        thumb_image.thumbnail((300, 300))
        thumb_buffer = io.BytesIO()
        thumb_image.save(thumb_buffer, format='PNG')
        thumb_buffer.seek(0)
        
        thumb_blob = bucket.blob(thumb_gcs_path)
        thumb_blob.upload_from_string(
            thumb_buffer.read(),
            content_type="image/png"
        )
        
        thumbnail_url = f"https://storage.googleapis.com/{bucket_name}/{thumb_gcs_path}"
        print(f"✅ Thumbnail uploaded: {thumbnail_url}")
        
    except Exception as e:
        print(f"❌ Failed to upload result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save result: {str(e)}"
        )
    
    # ===== 6. 처리 시간 계산 =====
    processing_time = time.time() - start_time
    print(f"⏱️ Total processing time: {processing_time:.2f}s")
    print(f"{'='*60}\n")
    
    # ===== 7. 결과 반환 =====
    return GenerateBackgroundResponse(
        success=True,
        content_id=content_id,
        result_url=result_url,
        thumbnail_url=thumbnail_url,
        mode=mode_used,
        prompt_used=request.prompt,
        style=request.style,
        processing_time=processing_time
    )

@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 삭제
    """
    # 본인 콘텐츠 확인
    content = db.query(UserContent).filter(
        UserContent.content_id == content_id,
        UserContent.user_id == current_user.user_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # 삭제
    db.delete(content)
    db.commit()
    
    return {
        "success": True,
        "content_id": content_id,
        "message": "Content deleted successfully"
    }