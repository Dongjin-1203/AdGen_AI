"""
Replicate API 배경 생성기
GPU 인프라 관리 불필요, 종량제 과금
"""
import replicate
import logging
import base64
import io
import requests
from PIL import Image
from typing import Optional

from ....GPU_server.generation.prompts import PromptEngine, StylePrompts


class ReplicateBackgroundGenerator:
    """Replicate API 기반 SDXL 배경 생성기"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Args:
            api_token: Replicate API 토큰 (없으면 환경 변수 REPLICATE_API_TOKEN 사용)
        """
        self.logger = logging.getLogger(__name__)
        self.prompt_engine = PromptEngine()  # ✅

        if api_token:
            self.client = replicate.Client(api_token=api_token)
        else:
            # 환경 변수에서 자동 로드
            self.client = replicate.Client()
        
        self.logger.info("✅ Replicate client initialized")
        
        
    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        """PIL Image를 base64 Data URI로 변환"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def _resize_and_center(
        image: Image.Image, 
        target_width: int, 
        target_height: int, 
        padding_percent: float = 0.7,
        vertical_alignment: str = "center"
    ) -> Image.Image:
        """이미지 리사이즈 및 배치"""
        # 투명 캔버스 생성
        canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        
        # 최대 크기 계산
        max_w = int(target_width * padding_percent)
        max_h = int(target_height * padding_percent)
        
        # 비율 유지 리사이즈
        img_w, img_h = image.size
        ratio = min(max_w / img_w, max_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 위치 계산
        x_offset = (target_width - new_w) // 2
        
        if vertical_alignment == "bottom":
            y_offset = target_height - new_h - int(target_height * 0.05)
        elif vertical_alignment == "top":
            y_offset = int(target_height * 0.05)
        else:
            y_offset = (target_height - new_h) // 2
        
        canvas.paste(resized_img, (x_offset, y_offset))
        return canvas
    
    def generate_background(
        self,
        product_image: Image.Image,
        prompt_text: str,
        aspect_ratio: str = "square",
        style: str = "minimal",
        negative_prompt: str = "",
        num_inference_steps: int = 30,
        controlnet_conditioning_scale: float = 0.5,
        padding_percent: float = 0.7,
        vertical_alignment: str = "center",
        use_ip_adapter: bool = False
    ) -> Image.Image:
        """Replicate API를 사용한 배경 생성"""
        
        # ===== 1. 타겟 크기 결정 =====
        dimensions = {
            "square": (1080, 1080),    # 1:1
            "portrait": (1080, 1352),  # 4:5
            "landscape": (1080, 608),  # 16:9
            "test": (512, 512)         # 테스트용
        }
        
        target_width, target_height = dimensions.get(aspect_ratio, dimensions["square"])
        
        # ===== 2. 안전한 프롬프트 생성 (PromptEngine 사용) =====
        safe_prompts = self.prompt_engine.generate_simple_prompt(
            user_prompt=prompt_text,
            style=style
        )
        
        full_positive_prompt = safe_prompts["positive"]
        full_negative_prompt = safe_prompts["negative"]
        
        # 사용자 네거티브 프롬프트 추가 (선택)
        if negative_prompt:
            full_negative_prompt = f"{negative_prompt}, {full_negative_prompt}"
        
        self.logger.info(
            f"🎨 Generating with Replicate: style={style}, "
            f"ratio={aspect_ratio} ({target_width}x{target_height})"
        )
        self.logger.debug(f"Prompt: {full_positive_prompt[:100]}...")
        
        # ===== 3. 이미지 전처리 =====
        processed_image = self._resize_and_center(
            product_image,
            target_width,
            target_height,
            padding_percent=padding_percent,
            vertical_alignment=vertical_alignment
        )
        
        # Base64 인코딩
        image_data_uri = self._image_to_base64(processed_image)
        
        # ===== 4. IP-Adapter 경고 =====
        if use_ip_adapter:
            self.logger.warning("⚠️ IP-Adapter not supported by Replicate API (ignored)")
        
        # ===== 5. Replicate API 호출 =====
        try:
            output = self.client.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "image": image_data_uri,
                    "prompt": full_positive_prompt,
                    "negative_prompt": full_negative_prompt,
                    "num_inference_steps": num_inference_steps,
                    "controlnet_conditioning_scale": controlnet_conditioning_scale,
                    "width": target_width,
                    "height": target_height,
                }
            )
            
            # ===== 6. 결과 이미지 다운로드 =====
            if isinstance(output, list) and len(output) > 0:
                response = requests.get(output[0])
                response.raise_for_status()
                result_image = Image.open(io.BytesIO(response.content))
                
                self.logger.info("✅ Background generation completed successfully")
                return result_image
            else:
                raise RuntimeError("No output from Replicate API")
                
        except Exception as e:
            self.logger.error(f"❌ Replicate generation failed: {e}")
            raise RuntimeError(f"Failed to generate background: {str(e)}")