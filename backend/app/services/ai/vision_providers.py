"""
여러 Vision AI 서비스를 동일한 인터페이스로 사용
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from google import genai
from google.genai import types
import mimetypes


# 1. 추상 클래스
class VisionProvider(ABC):
    
    @abstractmethod
    async def analyze_image(
        self, 
        image_path: str, 
        prompt: str,) -> Dict[str, Any]:
        """이미지 분석 (하위 클래스에서 구현)"""
        pass

# 2. 구현 클래스
class GeminiVisionProvider(VisionProvider):
    def __init__(self, api_key: str):
        # 1. Client 생성
        self.client = genai.Client(api_key=api_key)
 
    async def analyze_image(
            self, 
            image_path: str, 
            prompt: str) -> Dict[str, Any]:
        """Gemini API로 이미지 분석"""
        
        try:
            # 1. 이미지 로드
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # 2. MIME 타입 자동 감지
            
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = "image/jpeg"  # 기본값

            # 3. Part 객체 생성
            image_part = types.Part.from_bytes(
                data=image_bytes,  # 파일 바이트
                mime_type=mime_type
            )

            # 4. API 호출
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',  # 최신 모델!
                contents=[prompt, image_part]
            )
            
            # 5. 응답 받기
            return {
                "content": response.text,
                "success": True
            }
        
        except FileNotFoundError:
            return {
                "content": None,
                "success": False,
                "error": f"이미지 파일을 찾을 수 없습니다: {image_path}"
            }

        except Exception as e:
            return {
                "content": None,
                "success": False,
                "error": str(e)
            }