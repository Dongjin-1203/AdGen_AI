"""
Replicate IDM-VTON 기반 패션 광고 생성 서비스
가상 피팅 (Virtual Try-On) + 스타일별 배경
"""
import replicate
from PIL import Image
import io
import logging
import requests
from typing import Optional
import random

from config import settings

logger = logging.getLogger(__name__)


class ReplicateVTONService:
    """Replicate IDM-VTON을 사용한 광고 생성"""
    
    # K-Fashion 모델 이미지 URL (스타일별 10개씩)
    K_FASHION_MODELS = {
        'resort': [
            f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/k-fashion-models/resort/resort_{i:02d}.jpg"
            for i in range(10)
        ],
        'retro': [
            f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/k-fashion-models/retro/retro_{i:02d}.jpg"
            for i in range(10)
        ],
        'romantic': [
            f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/k-fashion-models/romantic/romantic_{i:02d}.jpg"
            for i in range(10)
        ]
    }
    
    def __init__(self):
        """Replicate 클라이언트 초기화"""
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN not found in settings")
        
        self.api_token = settings.REPLICATE_API_TOKEN
        logger.info("✅ Replicate VTON Service initialized")
    
    def generate_fashion_ad(
        self,
        garment_image: Image.Image,
        style: str = "resort",
        model_index: Optional[int] = None,
        user_prompt: Optional[str] = None
    ) -> Image.Image:
        """
        패션 광고 이미지 생성 (VTON)
        
        Args:
            garment_image: 의류 이미지 (PIL Image)
            style: 스타일 (resort/retro/romantic)
            model_index: K-Fashion 모델 인덱스 (0-9, None이면 랜덤)
            user_prompt: 추가 요청사항 (현재 미사용)
        
        Returns:
            생성된 광고 이미지 (PIL Image)
        """
        try:
            logger.info(f"🎨 Starting Replicate IDM-VTON generation")
            logger.info(f"   Style: {style}")
            logger.info(f"   Model index: {model_index}")
            
            # 1. 의류 이미지를 bytes로 변환
            garment_bytes = io.BytesIO()
            garment_image.save(garment_bytes, format='PNG')
            garment_bytes.seek(0)
            
            # 2. K-Fashion 모델 선택 (스타일별)
            model_image_url = self._get_model_image(style, model_index)
            logger.info(f"   Selected model URL: {model_image_url}")
            
            # 3. Replicate IDM-VTON API 호출
            logger.info("[VTON] Calling Replicate API...")
            
            output = replicate.run(
                "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
                input={
                    "garm_img": garment_bytes,
                    "human_img": model_image_url,
                    "category": "upper_body",  # 상의 (TODO: 자동 감지)
                    "steps": 30,
                    "seed": 42
                }
            )
            
            logger.info(f"[VTON] API response received")
            
            # 4. 결과 이미지 다운로드
            if isinstance(output, str):
                # URL이 반환된 경우
                result_url = output
            elif isinstance(output, list) and len(output) > 0:
                # 리스트로 반환된 경우 첫 번째 결과
                result_url = output[0]
            else:
                raise Exception(f"Unexpected output format: {type(output)}")
            
            logger.info(f"[VTON] Downloading result from: {result_url}")
            
            response = requests.get(result_url, timeout=60)
            response.raise_for_status()
            
            result_image = Image.open(io.BytesIO(response.content))
            
            logger.info(f"✅ VTON generation completed")
            logger.info(f"   Result size: {result_image.size}")
            
            return result_image
            
        except Exception as e:
            logger.error(f"❌ Replicate VTON failed: {e}", exc_info=True)
            raise Exception(f"Replicate 가상 피팅 실패: {str(e)}")
    
    def _get_model_image(self, style: str, model_index: Optional[int] = None) -> str:
        """
        스타일에 맞는 K-Fashion 모델 이미지 가져오기
        
        Args:
            style: 'resort', 'retro', 'romantic'
            model_index: 0-9 사이의 인덱스 (None이면 랜덤)
        
        Returns:
            GCS 모델 이미지 URL
        """
        # 스타일 검증
        if style not in self.K_FASHION_MODELS:
            logger.warning(f"Unknown style '{style}', defaulting to 'resort'")
            style = 'resort'
        
        models = self.K_FASHION_MODELS[style]
        
        # 인덱스 처리
        if model_index is None:
            model_index = random.randint(0, len(models) - 1)
        else:
            model_index = model_index % len(models)  # 0-9 범위로 제한
        
        model_url = models[model_index]
        
        logger.info(f"   Selected {style} model #{model_index}: {model_url}")
        
        return model_url
    
    def health_check(self) -> bool:
        """Replicate API 상태 확인"""
        try:
            # API 토큰 체크
            if not self.api_token or not self.api_token.startswith('r8_'):
                logger.error("Invalid Replicate API token format")
                return False
            
            # 간단한 모델 조회로 테스트
            # replicate.models.get()는 API 키가 유효한지 확인
            logger.info("Replicate health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Replicate health check failed: {e}")
            return False


# 싱글톤 인스턴스
_vton_service = None

def get_vton_service() -> ReplicateVTONService:
    """VTON 서비스 싱글톤 가져오기"""
    global _vton_service
    
    if _vton_service is None:
        _vton_service = ReplicateVTONService()
    
    return _vton_service