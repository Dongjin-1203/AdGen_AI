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
import time

from config import settings
from app.core.storage import upload_to_gcs

logger = logging.getLogger(__name__)


class ReplicateVTONService:
    """Replicate IDM-VTON을 사용한 광고 생성"""
    
    def __init__(self):
        """Replicate 클라이언트 초기화"""
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN not found in settings")
        
        self.api_token = settings.REPLICATE_API_TOKEN
        
        # GCS 버킷 이름 (fallback 포함)
        bucket_name = settings.GCS_BUCKET_NAME or "adgen-ai-storage"
        
        # K-Fashion 모델 이미지 URL (스타일별 10개씩) - Public URL 사용
        self.K_FASHION_MODELS = {
            'resort': [
                f"https://storage.googleapis.com/{bucket_name}/k-fashion-models/resort/resort_{i:02d}.jpg"
                for i in range(10)
            ],
            'retro': [
                f"https://storage.googleapis.com/{bucket_name}/k-fashion-models/retro/retro_{i:02d}.jpg"
                for i in range(10)
            ],
            'romantic': [
                f"https://storage.googleapis.com/{bucket_name}/k-fashion-models/romantic/romantic_{i:02d}.jpg"
                for i in range(10)
            ]
        }
        
        logger.info("✅ Replicate VTON Service initialized")
        logger.info(f"   Bucket: {bucket_name}")
        logger.info(f"   Models loaded: {sum(len(v) for v in self.K_FASHION_MODELS.values())} images")
        logger.info(f"   Sample resort URL: {self.K_FASHION_MODELS['resort'][0]}")
    
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
        temp_garment_url = None
        
        try:
            logger.info(f"🎨 [VTON] Starting generation")
            logger.info(f"   [VTON] Style: {style}")
            logger.info(f"   [VTON] Model index: {model_index}")
            logger.info(f"   [VTON] Garment size: {garment_image.size}")
            
            # 1. 의류 이미지를 GCS에 임시 업로드
            timestamp = int(time.time())
            temp_filename = f"temp/garment_{timestamp}.png"
            
            garment_bytes = io.BytesIO()
            garment_image.save(garment_bytes, format='PNG')
            garment_bytes.seek(0)
            
            logger.info(f"[VTON] Step 1: Uploading garment to GCS: {temp_filename}")
            temp_garment_url = upload_to_gcs(
                file_data=garment_bytes.getvalue(),
                destination_path=temp_filename,
                content_type='image/png'
            )
            logger.info(f"[VTON] Step 1: ✅ Garment uploaded: {temp_garment_url}")
            
            # URL이 None인지 체크
            if not temp_garment_url:
                raise ValueError("❌ Garment upload failed: temp_garment_url is None")
            
            # 2. K-Fashion 모델 선택 (스타일별)
            logger.info(f"[VTON] Step 2: Selecting K-Fashion model...")
            model_image_url = self._get_model_image(style, model_index)
            logger.info(f"[VTON] Step 2: Model URL returned: {model_image_url}")
            
            # URL이 None인지 체크
            if not model_image_url:
                raise ValueError(f"❌ Model URL is None for style={style}, model_index={model_index}")
            
            logger.info(f"[VTON] Step 2: ✅ Selected model: {model_image_url}")
            
            # 3. 양쪽 URL 검증
            logger.info(f"[VTON] Step 3: Validating URLs...")
            logger.info(f"   [VTON] garm_img type: {type(temp_garment_url)}, value: {temp_garment_url[:100] if temp_garment_url else 'None'}...")
            logger.info(f"   [VTON] human_img type: {type(model_image_url)}, value: {model_image_url[:100] if model_image_url else 'None'}...")
            
            # 4. Replicate IDM-VTON API 호출
            logger.info("[VTON] Step 4: Calling Replicate API...")
            logger.info(f"   [VTON] Model: cuuupid/idm-vton")
            logger.info(f"   [VTON] Parameters:")
            logger.info(f"      - garm_img: {temp_garment_url}")
            logger.info(f"      - human_img: {model_image_url}")
            logger.info(f"      - category: upper_body")
            logger.info(f"      - steps: 30")
            logger.info(f"      - seed: 42")
            
            output = replicate.run(
                "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
                input={
                    "garm_img": temp_garment_url,
                    "human_img": model_image_url,
                    "category": "upper_body",
                    "steps": 30,
                    "seed": 42
                }
            )
            
            logger.info(f"[VTON] Step 4: ✅ API response received: {type(output)}")
            
            # 5. 결과 이미지 다운로드
            if isinstance(output, str):
                result_url = output
            elif isinstance(output, list) and len(output) > 0:
                result_url = output[0]
            else:
                raise Exception(f"Unexpected output format: {type(output)}")
            
            logger.info(f"[VTON] Step 5: Downloading result from: {result_url}")
            
            response = requests.get(result_url, timeout=60)
            response.raise_for_status()
            
            result_image = Image.open(io.BytesIO(response.content))
            
            logger.info(f"✅ [VTON] Generation completed successfully")
            logger.info(f"   [VTON] Result size: {result_image.size}")
            
            return result_image
            
        except Exception as e:
            logger.error(f"❌ [VTON] Generation failed at some step", exc_info=True)
            logger.error(f"   [VTON] Error type: {type(e).__name__}")
            logger.error(f"   [VTON] Error message: {str(e)}")
            raise Exception(f"Replicate 가상 피팅 실패: {str(e)}")
        
        finally:
            if temp_garment_url:
                logger.info(f"[VTON] Temp file created: {temp_garment_url}")
    
    def _get_model_image(self, style: str, model_index: Optional[int] = None) -> str:
        """
        스타일에 맞는 K-Fashion 모델 이미지 가져오기
        
        Args:
            style: 'resort', 'retro', 'romantic'
            model_index: 0-9 사이의 인덱스 (None이면 랜덤)
        
        Returns:
            GCS 모델 이미지 URL
        """
        logger.info(f"   [_get_model_image] Input: style={style}, model_index={model_index}")
        
        # 스타일 검증
        if style not in self.K_FASHION_MODELS:
            logger.warning(f"   [_get_model_image] ⚠️ Unknown style '{style}', defaulting to 'resort'")
            style = 'resort'
        
        models = self.K_FASHION_MODELS[style]
        logger.info(f"   [_get_model_image] Available models for '{style}': {len(models)} images")
        
        # 인덱스 처리
        if model_index is None:
            model_index = random.randint(0, len(models) - 1)
            logger.info(f"   [_get_model_image] Random index selected: {model_index}")
        else:
            original_index = model_index
            model_index = model_index % len(models)
            if original_index != model_index:
                logger.info(f"   [_get_model_image] Index normalized: {original_index} → {model_index}")
        
        model_url = models[model_index]
        
        logger.info(f"   [_get_model_image] ✅ Returning URL: {model_url}")
        logger.info(f"   [_get_model_image] URL type: {type(model_url)}")
        logger.info(f"   [_get_model_image] URL length: {len(model_url) if model_url else 0}")
        
        return model_url
    
    def health_check(self) -> bool:
        """Replicate API 상태 확인"""
        try:
            # API 토큰 체크
            if not self.api_token or not self.api_token.startswith('r8_'):
                logger.error("Invalid Replicate API token format")
                return False
            
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