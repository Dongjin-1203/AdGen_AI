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

from app.db.base import get_db
from app.models.schemas import UserContent, User
from app.schemas.content import ContentResponse
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/api/contents", tags=["Contents"])

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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
    """이미지 업로드 및 콘텐츠 생성"""
    
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
    
    # ===== 2. 파일 저장 =====
    
    # 2-1. 사용자별 디렉토리 생성
    user_dir = UPLOAD_DIR / current_user.user_id
    user_dir.mkdir(exist_ok=True)
    
    # 2-2. 고유한 파일명 생성 (UUID + 원본 확장자)
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = user_dir / unique_filename
    
    # 2-3. 원본 이미지 저장
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # 2-4. 썸네일 생성 (300x300)
    thumbnail_filename = f"thumb_{unique_filename}"
    thumbnail_path = user_dir / thumbnail_filename
    
    # 이미지 리사이즈 (비율 유지)
    image.thumbnail((300, 300))
    image.save(thumbnail_path)
    
    # ===== 3. DB 저장 =====
    
    # 3-1. 상대 경로 (URL로 사용)
    image_url = f"/uploads/{current_user.user_id}/{unique_filename}"  # ← 수정!
    thumbnail_url = f"/uploads/{current_user.user_id}/{thumbnail_filename}"
    
    # 3-2. UserContent 객체 생성
    new_content = UserContent(
        content_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        image_url=image_url,  # ← 수정!
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