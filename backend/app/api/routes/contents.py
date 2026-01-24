"""
콘텐츠 API 라우터 (보상 기반 학습 시스템 통합)
/api/contents/upload - 이미지 업로드 + AI 예측 저장
/api/contents - 콘텐츠 목록
/api/contents/{id} - 콘텐츠 상세
/api/contents/{id} (PATCH) - 콘텐츠 수정 + 보상 점수 계산
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
# ⭐ 보상 기반 학습 모델 추가
from app.models.reward_system import AIPrediction, UserCorrection, RewardScore
from app.schemas.content import ContentResponse, GenerateBackgroundRequest, GenerateBackgroundResponse
from app.api.routes.auth import get_current_user
from config import settings
from app.services.vision.product_analyzer import ProductAnalyzer
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
_background_remover = None

def get_background_remover():
    """배경 제거 서비스 가져오기"""
    global _background_remover
    if _background_remover is None:
        _background_remover = BackgroundRemovalService()
        print("✅ Background Remover initialized")
    return _background_remover


# ===== 업로드 엔드포인트 (보상 기반 학습 통합) =====

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
    """
    이미지 업로드 및 콘텐츠 생성 (GCS 저장 + Vision AI + AI 예측 저장)
    
    ⭐ 보상 기반 학습 시스템 통합:
    1. Vision AI 분석
    2. AIPrediction 저장 (AI 초기 예측)
    3. UserContent 저장 (예측 결과 포함)
    """
    
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
                'style_tags': vision_result.get('style_tags', []),  # List 유지
                'ai_confidence': vision_result.get('confidence')
            }
            print(f"✅ Vision AI 분석 완료: {vision_data['category']}, {vision_data['color']}")
        else:
            print(f"⚠️ Vision AI 분석 실패: {vision_result.get('error')}")

    except Exception as e:
        print(f"⚠️ Vision AI 오류 (계속 진행): {e}")
        import traceback
        traceback.print_exc()
    
    # ===== 4. DB 저장 (UserContent 먼저 저장) =====
    bucket_name = settings.GCS_BUCKET_NAME or "adgen-uploads-2026"
    image_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
    thumbnail_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_thumb_path}"
    
    content_id = str(uuid.uuid4())
    
    # UserContent 객체 생성
    new_content = UserContent(
        content_id=content_id,
        user_id=current_user.user_id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        
        # 기본 정보 (수동 입력 우선)
        product_name=product_name,
        category=category or vision_data.get('category'),
        color=color or vision_data.get('color'),
        price=price,
        
        # Vision AI 결과
        sub_category=vision_data.get('sub_category'),
        material=vision_data.get('material'),
        fit=vision_data.get('fit'),
        style_tags=json.dumps(vision_data.get('style_tags', []), ensure_ascii=False) if vision_data.get('style_tags') else None,
        ai_confidence=vision_data.get('ai_confidence'),
        confirmed=False,  # 사용자 확인 필요
        
        # 메타데이터
        file_size=file_size,
        width=width,
        height=height
    )
    
    db.add(new_content)
    db.flush()  # content_id 생성 완료
    
    print(f"✅ Content saved: {new_content.content_id}")
    
    # ===== 5. ⭐ AIPrediction 저장 (보상 기반 학습) =====
    if vision_data:
        try:
            ai_prediction = AIPrediction(
                prediction_id=str(uuid.uuid4()),
                content_id=content_id,  # ⭐ content_id 포함
                predicted_category=vision_data.get('category'),
                predicted_sub_category=vision_data.get('sub_category'),
                predicted_material=vision_data.get('material'),
                predicted_fit=vision_data.get('fit'),
                predicted_color=vision_data.get('color'),
                predicted_style_tags=vision_data.get('style_tags'),  # JSON 자동 변환
                prediction_confidence=vision_data.get('ai_confidence')
            )
            
            db.add(ai_prediction)
            print(f"✅ AIPrediction 저장 완료: {ai_prediction.prediction_id}")
            
        except Exception as e:
            print(f"⚠️ AIPrediction 저장 실패: {e}")
            import traceback
            traceback.print_exc()
    
    # ===== 6. 최종 커밋 =====
    db.commit()
    db.refresh(new_content)
    
    return new_content


# ===== 콘텐츠 목록 조회 =====

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


# ===== 콘텐츠 수정 (보상 기반 학습 통합) =====

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
    
    ⭐ 보상 기반 학습 시스템 통합:
    1. 6개 필드 비교 (category, sub_category, material, fit, color, style_tags)
    2. 수정된 필드 UserCorrection에 저장
    3. 보상 점수 계산 (6 - 수정 개수)
    4. RewardScore에 저장
    """
    
    # ===== 1. 본인 콘텐츠 확인 =====
    content = db.query(UserContent).filter(
        UserContent.content_id == content_id,
        UserContent.user_id == current_user.user_id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # ===== 2. 원본 AI 예측 조회 =====
    prediction = db.query(AIPrediction).filter(
        AIPrediction.content_id == content_id
    ).first()
    
    if not prediction:
        print(f"⚠️ No prediction found for content {content_id}, skipping reward calculation")
    
    # ===== 3. 6개 필드 비교 및 수정 기록 =====
    corrections = []
    
    if prediction:
        # 필드 매핑 (Form 입력 → DB 필드 → AI 예측 필드)
        field_mapping = [
            ('category', category, content.category, prediction.predicted_category),
            ('sub_category', sub_category, content.sub_category, prediction.predicted_sub_category),
            ('material', material, content.material, prediction.predicted_material),
            ('fit', fit, content.fit, prediction.predicted_fit),
            ('color', color, content.color, prediction.predicted_color),
            ('style_tags', style_tags, content.style_tags, json.dumps(prediction.predicted_style_tags, ensure_ascii=False) if prediction.predicted_style_tags else None)
        ]
        
        for field_name, new_value, current_value, predicted_value in field_mapping:
            # 새 값이 입력되었고, 현재 값과 다른 경우
            if new_value is not None and str(new_value) != str(current_value):
                # UserCorrection 생성
                correction = UserCorrection(
                    correction_id=str(uuid.uuid4()),
                    content_id=content_id,
                    prediction_id=prediction.prediction_id,
                    user_id=current_user.user_id,
                    field_name=field_name,
                    original_value=str(predicted_value) if predicted_value else None,
                    corrected_value=str(new_value)
                )
                
                corrections.append(correction)
                db.add(correction)
                
                print(f"✏️ Correction: {field_name} = '{predicted_value}' → '{new_value}'")
    
    # ===== 4. 콘텐츠 업데이트 =====
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
    
    # ===== 5. ⭐ 보상 점수 계산 및 저장 =====
    if prediction and corrections:
        corrected_fields_count = len(corrections)
        reward_score_value = 6 - corrected_fields_count
        
        reward_score = RewardScore(
            score_id=str(uuid.uuid4()),
            content_id=content_id,
            prediction_id=prediction.prediction_id,
            total_fields=6,
            corrected_fields=corrected_fields_count,
            reward_score=reward_score_value,
            used_for_training=False
        )
        
        db.add(reward_score)
        
        print(f"🎯 Reward Score: {reward_score_value} (corrected {corrected_fields_count}/6 fields)")
    
    db.commit()
    db.refresh(content)
    
    # ===== 6. 응답 =====
    response = {
        "success": True,
        "content_id": content.content_id,
        "message": "Content updated successfully"
    }
    
    # 보상 정보 추가
    if prediction and corrections:
        response["reward_info"] = {
            "corrected_fields": corrected_fields_count,
            "reward_score": reward_score_value,
            "corrections": [
                {
                    "field": c.field_name,
                    "from": c.original_value,
                    "to": c.corrected_value
                }
                for c in corrections
            ]
        }
    
    return response


# ===== 통계 API (보상 기반 학습) =====

@router.get("/stats/rewards")
async def get_reward_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    보상 기반 학습 통계
    
    Returns:
        - 총 예측 수
        - 총 수정 수
        - 평균 보상 점수
        - 필드별 오류 빈도
    """
    from sqlalchemy import func
    
    # 총 예측 수
    total_predictions = db.query(func.count(AIPrediction.prediction_id))\
        .join(UserContent, AIPrediction.content_id == UserContent.content_id)\
        .filter(UserContent.user_id == current_user.user_id)\
        .scalar()
    
    # 총 수정 수
    total_corrections = db.query(func.count(UserCorrection.correction_id))\
        .filter(UserCorrection.user_id == current_user.user_id)\
        .scalar()
    
    # 평균 보상 점수
    avg_reward_score = db.query(func.avg(RewardScore.reward_score))\
        .join(UserContent, RewardScore.content_id == UserContent.content_id)\
        .filter(UserContent.user_id == current_user.user_id)\
        .scalar()
    
    # 필드별 오류 빈도
    field_errors = db.query(
        UserCorrection.field_name,
        func.count(UserCorrection.correction_id).label('count')
    ).filter(
        UserCorrection.user_id == current_user.user_id
    ).group_by(
        UserCorrection.field_name
    ).order_by(
        func.count(UserCorrection.correction_id).desc()
    ).all()
    
    return {
        "total_predictions": total_predictions or 0,
        "total_corrections": total_corrections or 0,
        "average_reward_score": round(float(avg_reward_score), 2) if avg_reward_score else 6.0,
        "field_errors": [
            {
                "field": field_name,
                "error_count": count
            }
            for field_name, count in field_errors
        ],
        "accuracy": {
            "overall": round((1 - (total_corrections / (total_predictions * 6))) * 100, 2) if total_predictions else 100.0
        }
    }


# ===== 배경 생성 엔드포인트 (기존 유지) =====

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


@router.delete("/api/contents/{content_id}")
async def delete_content(
    content_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    콘텐츠 삭제 (관련 데이터 모두 삭제)
    
    삭제 순서:
    1. AdCopyHistory (최종 광고)
    2. CaptionCorrection (캡션 수정)
    3. AdCaption (광고 캡션)
    4. RewardScore (보상 점수)
    5. UserCorrection (사용자 수정)
    6. AIPrediction (AI 예측)
    7. GenerationHistory (생성 히스토리)
    8. UserContent (콘텐츠)
    """
    
    # 1. 콘텐츠 조회 및 권한 확인
    content = db.query(UserContent).filter(
        UserContent.content_id == content_id,
        UserContent.user_id == current_user.user_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="콘텐츠를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    try:
        # 2. AdCopyHistory 삭제
        from app.models.caption_system import AdCopyHistory
        db.query(AdCopyHistory).filter(
            AdCopyHistory.content_id == content_id
        ).delete(synchronize_session=False)
        
        # 3. CaptionCorrection 삭제 (AdCaption을 통해)
        from app.models.caption_system import AdCaption, CaptionCorrection
        caption_ids = [c.caption_id for c in db.query(AdCaption).filter(
            AdCaption.content_id == content_id
        ).all()]
        
        if caption_ids:
            db.query(CaptionCorrection).filter(
                CaptionCorrection.caption_id.in_(caption_ids)
            ).delete(synchronize_session=False)
        
        # 4. AdCaption 삭제
        db.query(AdCaption).filter(
            AdCaption.content_id == content_id
        ).delete(synchronize_session=False)
        
        # 5. RewardScore 삭제
        from app.models.reward_system import RewardScore
        db.query(RewardScore).filter(
            RewardScore.content_id == content_id
        ).delete(synchronize_session=False)
        
        # 6. UserCorrection 삭제
        from app.models.reward_system import UserCorrection
        db.query(UserCorrection).filter(
            UserCorrection.content_id == content_id
        ).delete(synchronize_session=False)
        
        # 7. AIPrediction 삭제
        from app.models.reward_system import AIPrediction
        db.query(AIPrediction).filter(
            AIPrediction.content_id == content_id
        ).delete(synchronize_session=False)
        
        # 8. GenerationHistory 삭제
        from app.models.schemas import GenerationHistory
        db.query(GenerationHistory).filter(
            GenerationHistory.content_id == content_id
        ).delete(synchronize_session=False)
        
        # 9. 마지막으로 UserContent 삭제
        db.delete(content)
        
        # 10. 커밋
        db.commit()
        
        return {
            "success": True,
            "message": "콘텐츠가 성공적으로 삭제되었습니다.",
            "deleted_content_id": content_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"삭제 중 오류가 발생했습니다: {str(e)}"
        )