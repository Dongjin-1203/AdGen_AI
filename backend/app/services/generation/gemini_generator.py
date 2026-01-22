"""
Gemini API 기반 패션 광고 이미지 생성 서비스
GPU 서버 없이 Google Gemini API로 이미지 생성
google-genai 최신 SDK + gemini-2.5-flash-image 모델 사용
"""
from google import genai
from google.genai import types
from PIL import Image
import io
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


class GeminiImageGenerator:
    """Gemini API를 사용한 이미지 생성 (최신 SDK)"""
    
    def __init__(self):
        """Gemini API 초기화"""
        if not settings.GOOGLE_MODEL_API_KEY:
            raise ValueError("GOOGLE_MODEL_API_KEY not found in settings")
        
        # 최신 SDK 클라이언트 생성
        self.client = genai.Client(api_key=settings.GOOGLE_MODEL_API_KEY)
        self.model = "gemini-2.5-flash-image"  # GA 모델
        logger.info(f"✅ Gemini Image Generator initialized (model: {self.model})")
    
    def generate_fashion_ad(
        self,
        product_image: Image.Image,
        style: str,
        user_prompt: Optional[str] = None
    ) -> Image.Image:
        """
        패션 광고 이미지 생성
        
        Args:
            product_image: 제품 이미지
            style: 스타일 (resort/retro/romantic)
            user_prompt: 사용자 추가 요청
        
        Returns:
            생성된 광고 이미지
        """
        try:
            # 스타일별 프롬프트
            style_prompts = {
                'resort': (
                    "Transform this clothing item into a professional resort-style fashion advertisement. "
                    "Place it in a bright, tropical beach setting with natural sunlight, ocean background, "
                    "and vacation vibes. Create a professional commercial photography style with high quality. "
                    "Keep the clothing item as the main focus but enhance the background and atmosphere."
                ),
                'retro': (
                    "Transform this clothing item into a professional retro-style fashion advertisement. "
                    "Place it in a vintage 70s-80s aesthetic setting with nostalgic atmosphere, "
                    "analog film quality look, and classic poses. Create an editorial photography style. "
                    "Keep the clothing item as the main focus but add retro elements and color grading."
                ),
                'romantic': (
                    "Transform this clothing item into a professional romantic-style fashion advertisement. "
                    "Place it in a soft, feminine setting with dreamy atmosphere, pastel colors, "
                    "and elegant mood. Create a luxury brand photography style with professional lighting. "
                    "Keep the clothing item as the main focus but enhance with romantic elements."
                )
            }
            
            base_prompt = style_prompts.get(style.lower(), style_prompts['resort'])
            
            # 사용자 프롬프트 추가
            if user_prompt:
                final_prompt = f"{base_prompt}\n\nAdditional requirements: {user_prompt}"
            else:
                final_prompt = base_prompt
            
            logger.info(f"🎨 Generating fashion ad with Gemini")
            logger.info(f"   Model: {self.model}")
            logger.info(f"   Style: {style}")
            logger.info(f"   Prompt length: {len(final_prompt)} chars")
            
            # 이미지를 bytes로 변환
            img_byte_arr = io.BytesIO()
            product_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            image_bytes = img_byte_arr.getvalue()
            
            # Gemini 2.5 Flash Image로 이미지 생성
            # 입력: 텍스트 프롬프트 + 제품 이미지
            # 출력: 변환된 광고 이미지
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    final_prompt,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/png'
                    )
                ],
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],  # 이미지만 출력
                    image_config=types.ImageConfig(
                        aspect_ratio='1:1',  # 정사각형
                    )
                )
            )
            
            # 생성된 이미지 추출
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    # 이미지 데이터 찾기
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        result_image = Image.open(io.BytesIO(image_data))
                        
                        logger.info(f"✅ Gemini generation succeeded")
                        logger.info(f"   Result size: {result_image.size}")
                        
                        return result_image
            
            raise Exception("No image generated in response")
            
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {e}")
            raise Exception(f"Gemini 이미지 생성 실패: {str(e)}")
    
    async def health_check(self) -> bool:
        """Gemini API 상태 확인"""
        try:
            # 간단한 텍스트 생성으로 테스트
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',  # 텍스트 전용 모델로 테스트
                contents='Hello'
            )
            return bool(response.text)
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False