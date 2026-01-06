"""
Replicate API를 사용한 배경 생성
GPU 인프라 관리 불필요, 종량제 과금
"""
import replicate
import logging
import base64
import io
from PIL import Image
from typing import Optional
from .style_prompts import StylePrompts


class ReplicateBackgroundGenerator:
    """Replicate API를 사용한 SDXL 배경 생성"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Args:
            api_token: Replicate API 토큰 (없으면 환경 변수에서 자동 로드)
        """
        self.logger = logging.getLogger(__name__)
        self.client = replicate.Client(api_token=api_token)
        
    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        """PIL Image를 base64 문자열로 변환"""
        buffered = io.BytesIO()
        # PNG로 저장 (투명도 유지)
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def _resize_and_center(
        image: Image.Image, 
        target_width: int, 
        target_height: int, 
        padding_percent: float = 0.8
    ) -> Image.Image:
        """이미지 리사이즈 및 중앙 정렬"""
        # 투명 캔버스 생성
        canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        
        # 패딩을 고려한 최대 크기 계산
        max_w = int(target_width * padding_percent)
        max_h = int(target_height * padding_percent)
        
        # 비율 유지하며 리사이즈
        img_w, img_h = image.size
        ratio = min(max_w / img_w, max_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 중앙 배치
        x_offset = (target_width - new_w) // 2
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
        controlnet_conditioning_scale: float = 0.5
    ) -> Image.Image:
        """
        Replicate API를 사용하여 배경 생성
        
        Args:
            product_image: 제품 이미지 (배경 제거된 상태)
            prompt_text: 생성할 배경 설명
            aspect_ratio: "square", "portrait", "landscape"
            style: "minimal", "emotional", "street"
            negative_prompt: 제외할 요소
            num_inference_steps: 생성 스텝 수
            controlnet_conditioning_scale: ControlNet 강도
            
        Returns:
            배경이 생성된 최종 이미지
        """
        # 인스타그램 비율 설정
        dimensions = {
            "square": (1080, 1080),    # 1:1
            "portrait": (1080, 1352),  # 4:5
            "landscape": (1080, 608)   # 16:9
        }
        
        target_width, target_height = dimensions.get(aspect_ratio, dimensions["square"])
        
        # 스타일 프롬프트 가져오기
        style_config = StylePrompts.get_prompt(style)
        full_positive_prompt = f"{prompt_text}, {style_config['positive']}"
        full_negative_prompt = f"{negative_prompt}, {style_config['negative']}"
        
        # 이미지 리사이즈 및 중앙 정렬
        processed_image = self._resize_and_center(
            product_image,
            target_width,
            target_height,
            padding_percent=0.7
        )
        
        # base64 인코딩
        image_data_uri = self._image_to_base64(processed_image)
        
        self.logger.info(
            f"Generating with Replicate: style={style}, "
            f"ratio={aspect_ratio} ({target_width}x{target_height})"
        )
        
        try:
            # Replicate SDXL ControlNet 실행
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
            
            # 결과 이미지 로드
            if isinstance(output, list) and len(output) > 0:
                # Replicate는 URL을 반환
                import requests
                response = requests.get(output[0])
                result_image = Image.open(io.BytesIO(response.content))
                
                self.logger.info("Background generation completed successfully")
                return result_image
            else:
                raise Exception("No output from Replicate")
                
        except Exception as e:
            self.logger.error(f"Replicate generation failed: {e}")
            raise Exception(f"Failed to generate background: {str(e)}")