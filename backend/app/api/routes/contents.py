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

from app.db.base import get_db
from app.models.schemas import UserContent, User
from app.schemas.content import ContentResponse
from app.api.routes.auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/contents", tags=["Contents"])

# GCS 설정
storage_client = storage.Client()
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "adgen-uploads-2026")
bucket = storage_client.bucket(BUCKET_NAME)

# 허용된 이미지 확장자
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


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
    """이미지 업로드 및 콘텐츠 생성 (GCS 저장)"""
    
    # ===== 1. 파일 검증 =====
    
    # 1-1. 파일 확장자 확인
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only image files are allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 1-2. 파일 읽기
    contents = await file.read()
    file_size = len(contents)
    
    # 1-3. 파일 크기 확인
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # 1-4. 실제 이미지인지 확인 (Pillow로 열어보기)
    try:
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )
    
    # ===== 2. GCS에 업로드 =====
    
    # 2-1. 고유한 파일명 생성 (UUID + 원본 확장자)
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    thumbnail_filename = f"thumb_{unique_filename}"
    
    # 2-2. GCS 경로 (user_id/filename)
    gcs_path = f"{current_user.user_id}/{unique_filename}"
    gcs_thumb_path = f"{current_user.user_id}/{thumbnail_filename}"
    
    # 2-3. 원본 이미지 GCS 업로드
    try:
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(
            contents,
            content_type=f"image/{file_ext[1:]}"
        )
        blob.make_public()  # 공개 설정
        
        print(f"✅ Uploaded: {gcs_path}")
    except Exception as e:
        print(f"❌ GCS Upload Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image to storage"
        )
    
    # 2-4. 썸네일 생성 및 GCS 업로드
    try:
        # 썸네일 생성 (300x300, 비율 유지)
        thumb_image = image.copy()
        thumb_image.thumbnail((300, 300))
        
        # BytesIO로 변환
        thumb_buffer = io.BytesIO()
        thumb_image.save(thumb_buffer, format=image.format or 'JPEG')
        thumb_buffer.seek(0)
        
        # GCS 업로드
        thumb_blob = bucket.blob(gcs_thumb_path)
        thumb_blob.upload_from_string(
            thumb_buffer.read(),
            content_type=f"image/{file_ext[1:]}"
        )
        thumb_blob.make_public()
        
        print(f"✅ Uploaded thumbnail: {gcs_thumb_path}")
    except Exception as e:
        print(f"❌ Thumbnail Upload Error: {e}")
        # 썸네일 실패해도 원본은 저장되었으므로 계속 진행
    
    # ===== 3. DB 저장 =====
    
    # 3-1. GCS 공개 URL
    image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_path}"
    thumbnail_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_thumb_path}"
    
    # 3-2. UserContent 객체 생성
    new_content = UserContent(
        content_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        product_name=product_name,
        category=category,
        color=color,
        price=price,
        file_size=file_size,
        width=width,
        height=height
    )
    
    # 3-3. DB에 저장
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