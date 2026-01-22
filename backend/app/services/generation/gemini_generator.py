"""
Gemini API 기반 패션 광고 이미지 생성 서비스
GPU 서버 없이 Google Gemini API로 이미지 생성
"""
import google.generativeai as genai
from PIL import Image
import io
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


class GeminiImageGenerator:
    """Gemini API를 사용한 이미지 생성"""
    
    def __init__(self):
        """Gemini API 초기화"""
        if not settings.GOOGLE_MODEL_API_KEY:
            raise ValueError("GOOGLE_MODEL_API_KEY not found in settings")
        
        genai.configure(api_key=settings.GOOGLE_MODEL_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini Image Generator initialized")
    
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
                    "Create a professional resort-style fashion advertisement. "
                    "Show the clothing item in a bright, tropical beach setting with "
                    "natural sunlight, ocean background, and vacation vibes. "
                    "Professional photography quality, commercial shoot style."
                ),
                'retro': (
                    "Create a professional retro-style fashion advertisement. "
                    "Show the clothing item in a vintage 70s-80s aesthetic with "
                    "nostalgic atmosphere, analog film quality, and classic poses. "
                    "Professional photography quality, editorial style."
                ),
                'romantic': (
                    "Create a professional romantic-style fashion advertisement. "
                    "Show the clothing item in a soft, feminine setting with "
                    "dreamy atmosphere, pastel colors, and elegant mood. "
                    "Professional photography quality, luxury brand style."
                )
            }
            
            base_prompt = style_prompts.get(style.lower(), style_prompts['resort'])
            
            # 사용자 프롬프트 추가
            if user_prompt:
                final_prompt = f"{base_prompt}\n\nAdditional requirements: {user_prompt}"
            else:
                final_prompt = base_prompt
            
            logger.info(f"🎨 Generating fashion ad with Gemini")
            logger.info(f"   Style: {style}")
            logger.info(f"   Prompt length: {len(final_prompt)} chars")
            
            # 이미지를 bytes로 변환
            img_byte_arr = io.BytesIO()
            product_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Gemini API 호출
            response = self.model.generate_content([
                final_prompt,
                {
                    'mime_type': 'image/png',
                    'data': img_byte_arr.getvalue()
                }
            ])
            
            # 생성된 이미지 추출
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # 이미지 파트 찾기
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data'):
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
            test_model = genai.GenerativeModel('gemini-pro')
            response = test_model.generate_content("Hello")
            return bool(response.text)
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False