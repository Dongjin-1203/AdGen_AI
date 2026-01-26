"""
광고 캡션 생성 API 엔드포인트
GPT 기반 짧은 광고 캡션 생성 (1-2문장)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import uuid
import time

from app.db.base import get_db
from app.models.schemas import UserContent, GenerationHistory
from app.models.caption_system import AdCaption, CaptionCorrection
from app.api.routes.auth import get_current_user
from openai import OpenAI
from config import settings

router = APIRouter()

# OpenAI 클라이언트 (싱글톤)
_openai_client = None

def get_openai_client():
    """OpenAI 클라이언트 가져오기"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# ========== Request/Response Models ==========

class GenerateCaptionRequest(BaseModel):
    """캡션 생성 요청"""
    content_id: str
    generation_id: Optional[str] = None  # 없으면 최신 generation 사용
    user_request: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "uuid-here",
                "generation_id": "uuid-here",
                "user_request": "힙한 느낌으로"
            }
        }


class GenerateCaptionResponse(BaseModel):
    """캡션 생성 응답"""
    caption_id: str
    ai_caption: str
    ai_confidence: Optional[float] = None
    style: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "caption_id": "uuid-here",
                "ai_caption": "트렌디한 레트로 감성의 니트 카디건으로 일상에 빈티지 무드를 더하세요.",
                "ai_confidence": 0.95,
                "style": "retro"
            }
        }


class ConfirmCaptionRequest(BaseModel):
    """캡션 확정 요청"""
    caption_id: str
    final_caption: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "caption_id": "uuid-here",
                "final_caption": "트렌디한 레트로 스타일의 니트 카디건! 겨울 필수 아이템 🧶"
            }
        }


class ConfirmCaptionResponse(BaseModel):
    """캡션 확정 응답"""
    success: bool
    caption_id: str
    is_modified: bool
    reward_score: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "caption_id": "uuid-here",
                "is_modified": True,
                "reward_score": 0
            }
        }


# ========== API Endpoints ==========

@router.post("/caption", response_model=GenerateCaptionResponse)
async def generate_caption(
    request: GenerateCaptionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    광고 캡션 생성 (1-2문장)
    
    - Vision AI 분석 결과와 스타일 태그를 기반으로 짧은 광고 캡션 생성
    - 사용자 추가 요청 반영 가능
    - AdCaption 테이블에 저장
    
    **처리 시간:** ~2초 (GPT)
    """
    
    # 1. 콘텐츠 조회 및 권한 확인
    content = db.query(UserContent).filter(
        UserContent.content_id == request.content_id,
        UserContent.user_id == current_user.user_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="콘텐츠를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    # 2. Vision AI 분석 결과 확인
    if not content.category:
        raise HTTPException(
            status_code=400,
            detail="Vision AI 분석이 완료되지 않았습니다."
        )
    
    # 3. GenerationHistory 조회
    if request.generation_id:
        generation = db.query(GenerationHistory).filter(
            GenerationHistory.generation_id == request.generation_id,
            GenerationHistory.user_id == current_user.user_id
        ).first()
    else:
        # 최신 generation 사용
        generation = db.query(GenerationHistory).filter(
            GenerationHistory.content_id == request.content_id,
            GenerationHistory.user_id == current_user.user_id
        ).order_by(GenerationHistory.created_at.desc()).first()
    
    if not generation:
        raise HTTPException(
            status_code=400,
            detail="생성된 모델 이미지가 없습니다."
        )
    
    # 4. Vision AI 분석 결과 준비
    style_tags = content.style_tags
    if isinstance(style_tags, str):
        try:
            style_tags = json.loads(style_tags)
        except:
            style_tags = [tag.strip() for tag in style_tags.split(',') if tag.strip()]
    
    # 5. GPT로 캡션 생성
    try:
        client = get_openai_client()
        
        # 프롬프트 구성
        system_prompt = """당신은 패션 광고 카피라이터입니다.
제품 정보를 바탕으로 짧고 임팩트 있는 광고 캡션을 작성하세요.

⚠️ 중요 규칙:
1. 반드시 한글로만 작성
2. 1-2문장으로 간결하게 (최대 50자)
3. 감성적이고 트렌디한 표현 사용
4. 이모지 1-2개 활용 가능

응답 형식 (JSON):
{
  "caption": "광고 캡션 텍스트",
  "confidence": 0.95
}
"""
        
        user_message = f"""다음 정보로 광고 캡션을 작성하세요:

[상품 정보]
- 카테고리: {content.category}
- 서브카테고리: {content.sub_category or '없음'}
- 색상: {content.color or '없음'}
- 소재: {content.material or '없음'}
- 핏: {content.fit or '없음'}
- 스타일: {', '.join(style_tags) if style_tags else '없음'}

[스타일]
- {generation.style} (리조트/레트로/로맨틱)

[사용자 요청]
{request.user_request or '없음'}

⚠️ 반드시 한글로만 작성하고, 1-2문장으로 간결하게!
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-4o 유지
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,
            max_tokens=200,
            timeout=30.0,  # ✨ 30초 타임아웃 추가
            response_format={"type": "json_object"}
        )
        
        # JSON 파싱
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        ai_caption = result.get('caption', '').strip()
        ai_confidence = result.get('confidence', 0.9)
        
        if not ai_caption:
            raise ValueError("생성된 캡션이 비어있습니다.")
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"캡션 생성 중 오류가 발생했습니다: {str(e)}"
        )
    
    # 6. AdCaption 저장
    caption_id = str(uuid.uuid4())
    
    new_caption = AdCaption(
        caption_id=caption_id,
        content_id=request.content_id,
        user_id=current_user.user_id,
        generation_id=generation.generation_id,
        ai_caption=ai_caption,
        ai_confidence=ai_confidence,
        final_caption=ai_caption,  # 초기값은 AI 캡션과 동일
        is_modified=False,
        style=generation.style,
        user_request=request.user_request
    )
    
    db.add(new_caption)
    db.commit()
    db.refresh(new_caption)
    
    return GenerateCaptionResponse(
        caption_id=caption_id,
        ai_caption=ai_caption,
        ai_confidence=ai_confidence,
        style=generation.style
    )


@router.post("/caption/confirm", response_model=ConfirmCaptionResponse)
async def confirm_caption(
    request: ConfirmCaptionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    캡션 확정 (수정 여부 기록)
    
    - 사용자가 캡션을 확정하면 is_modified 업데이트
    - 수정된 경우 CaptionCorrection에 기록 (보상 학습용)
    - 보상 점수: 0 (수정됨), 1 (그대로 사용)
    
    **처리 시간:** ~0.1초
    """
    
    # 1. AdCaption 조회 및 권한 확인
    caption = db.query(AdCaption).filter(
        AdCaption.caption_id == request.caption_id,
        AdCaption.user_id == current_user.user_id
    ).first()
    
    if not caption:
        raise HTTPException(
            status_code=404,
            detail="캡션을 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    # 2. 수정 여부 확인
    is_modified = (request.final_caption.strip() != caption.ai_caption.strip())
    
    # 3. 수정된 경우 CaptionCorrection 저장
    reward_score = 0 if is_modified else 1
    
    if is_modified:
        correction = CaptionCorrection(
            correction_id=str(uuid.uuid4()),
            caption_id=request.caption_id,
            user_id=current_user.user_id,
            original_caption=caption.ai_caption,
            corrected_caption=request.final_caption,
            reward_score=reward_score,
            edit_type="user_edit"  # 향후 분석 가능
        )
        db.add(correction)
    
    # 4. AdCaption 업데이트
    caption.final_caption = request.final_caption
    caption.is_modified = is_modified
    
    db.commit()
    db.refresh(caption)
    
    return ConfirmCaptionResponse(
        success=True,
        caption_id=request.caption_id,
        is_modified=is_modified,
        reward_score=reward_score
    )


@router.post("/caption/test")
async def test_caption_generation(
    current_user = Depends(get_current_user)
):
    """
    캡션 생성 테스트 (개발용)
    
    실제 DB 없이 샘플 데이터로 테스트
    """
    
    try:
        client = get_openai_client()
        
        system_prompt = """당신은 패션 광고 카피라이터입니다.
제품 정보를 바탕으로 짧고 임팩트 있는 광고 캡션을 작성하세요.

⚠️ 중요 규칙:
1. 반드시 한글로만 작성
2. 1-2문장으로 간결하게 (최대 50자)
3. 감성적이고 트렌디한 표현 사용
4. 이모지 1-2개 활용 가능

응답 형식 (JSON):
{
  "caption": "광고 캡션 텍스트",
  "confidence": 0.95
}
"""
        
        user_message = """다음 정보로 광고 캡션을 작성하세요:

[상품 정보]
- 카테고리: 아우터
- 서브카테고리: 코트
- 색상: 블랙
- 소재: 울
- 핏: 오버사이즈
- 스타일: 미니멀, 모던

[스타일]
- retro (레트로)

⚠️ 반드시 한글로만 작성하고, 1-2문장으로 간결하게!
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-4o 유지
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,
            max_tokens=200,
            timeout=30.0,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        return {
            "status": "success",
            "caption": result.get('caption'),
            "confidence": result.get('confidence'),
            "raw_response": result_text
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"테스트 실패: {str(e)}"
        )


@router.get("/caption/{caption_id}")
async def get_caption(
    caption_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    캡션 조회
    
    caption_id로 캡션 정보 조회
    """
    
    caption = db.query(AdCaption).filter(
        AdCaption.caption_id == caption_id,
        AdCaption.user_id == current_user.user_id
    ).first()
    
    if not caption:
        raise HTTPException(
            status_code=404,
            detail="캡션을 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    return {
        "caption_id": caption.caption_id,
        "ai_caption": caption.ai_caption,
        "final_caption": caption.final_caption,
        "is_modified": caption.is_modified,
        "style": caption.style,
        "created_at": caption.created_at
    }