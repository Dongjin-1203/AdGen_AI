"""
GPU 서버 클라이언트
메인 백엔드 → GPU 서버 통신
"""
import httpx
import logging
from PIL import Image
from typing import Optional
import io

from config import settings

logger = logging.getLogger(__name__)


class GPUServerClient:
    """GPU 서버 API 클라이언트"""
    
    def __init__(self):
        self.base_url = settings.GPU_SERVER_URL.rstrip('/')
        self.timeout = settings.GPU_SERVER_TIMEOUT  # config에서 가져오기
    
    async def health_check(self) -> dict:
        """GPU 서버 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"GPU 서버 연결 실패: {e}")
            return {"status": "unavailable", "error": str(e)}
    
    async def generate_background(
        self,
        product_image: Image.Image,
        prompt_text: str,
        style: str = "minimal",
        aspect_ratio: str = "1:1",
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        controlnet_scale: float = 0.5,
        ip_adapter_scale: float = 0.8
    ) -> Image.Image:
        """
        GPU 서버로 배경 생성 요청
        
        Args:
            product_image: 제품 이미지 (PIL Image)
            prompt_text: 배경 생성 프롬프트
            style: 스타일 (minimal, modern, luxury, natural, vibrant)
            aspect_ratio: 이미지 비율 (1:1, 4:3, 16:9)
            num_inference_steps: 생성 스텝 수 (20-50)
            guidance_scale: 가이던스 스케일 (7-15)
            controlnet_scale: ControlNet 강도 (0.3-0.8)
            ip_adapter_scale: IP-Adapter 강도 (0.5-1.0)
        
        Returns:
            생성된 이미지 (PIL Image)
        
        Raises:
            RuntimeError: GPU 서버 요청 실패 시
        """
        try:
            # 이미지를 BytesIO로 변환
            img_buffer = io.BytesIO()
            product_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            
            # API 요청 데이터
            files = {
                "image": ("product.png", img_buffer, "image/png")
            }
            data = {
                "prompt": prompt_text,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "controlnet_conditioning_scale": controlnet_scale,
                "ip_adapter_scale": ip_adapter_scale
            }
            
            logger.info(f"🎨 GPU 서버 요청 시작: style={style}, aspect_ratio={aspect_ratio}")
            
            # GPU 서버에 POST 요청
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    files=files,
                    data=data
                )
                
                response.raise_for_status()
                
                # 응답 이미지 파싱
                result_image = Image.open(io.BytesIO(response.content))
                logger.info(f"✅ GPU 서버 생성 완료: {result_image.size}")
                
                return result_image
                
        except httpx.TimeoutException:
            logger.error("⏰ GPU 서버 타임아웃")
            raise RuntimeError("이미지 생성 시간이 초과되었습니다. 다시 시도해주세요.")
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ GPU 서버 HTTP 에러: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"GPU 서버 오류: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ GPU 서버 요청 실패: {e}")
            raise RuntimeError(f"이미지 생성 중 오류 발생: {str(e)}")


# 싱글톤 인스턴스
gpu_client = GPUServerClient()