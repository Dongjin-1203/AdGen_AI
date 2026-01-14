"""
콘텐츠 API 라우터
/api/contents/upload - 이미지 업로드
/api/contents - 콘텐츠 목록
/api/contents/{id} - 콘텐츠 상세
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
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

from app.db.base import get_db
from app.models.schemas import UserContent, User
from app.schemas.content import ContentResponse
from app.api.routes.auth import get_current_user
from config import settings
from app.services.ai.product_analyzer import ProductAnalyzer

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
    
    # ===== 3. Vision AI 분석 ===== ⭐ 수정!
    vision_data = {}
    
    try:
        # 임시 파일로 저장 (ProductAnalyzer는 로컬 파일 경로 필요)
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Vision AI 분석
        analyzer = ProductAnalyzer(provider="gemini")
        vision_result = await analyzer.analyze(tmp_path)
        
        # 임시 파일 삭제
        os.unlink(tmp_path)
        
        if vision_result.get('success'):
            vision_data = {
                'category': vision_result.get('category'),
                'color': vision_result.get('color'),
                'sub_category': vision_result.get('sub_category'),
                'material': vision_result.get('material'),
                'fit': vision_result.get('fit'),
                'style_tags': json.dumps(vision_result.get('style_tags', [])),
                'ai_confidence': vision_result.get('confidence')
            }
            print(f"✅ Vision AI 분석 완료: {vision_data['category']}, {vision_data['color']}")
        else:
            print(f"⚠️ Vision AI 분석 실패: {vision_result.get('error')}")
    
    except Exception as e:
        print(f"⚠️ Vision AI 오류 (계속 진행): {e}")
    
    # ===== 4. DB 저장 ===== ⭐ 수정!
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