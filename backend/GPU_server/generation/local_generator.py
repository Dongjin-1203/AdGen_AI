"""
로컬 SDXL 배경 생성기
RealVisXL V4.0 + ControlNet + IP-Adapter
"""
import torch
import logging
import cv2
import numpy as np
from PIL import Image
from typing import Optional
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, AutoencoderKL

from .prompts.style_prompts import StylePrompts


class SDXLGenerator:
    """로컬 GPU 기반 SDXL 배경 생성기"""
    
    def __init__(self, device: str = "cuda"):
        # CUDA 사용 가능 여부 확인
        if not torch.cuda.is_available():
            raise RuntimeError(
                "❌ GPU 서버 초기화 실패: CUDA를 사용할 수 없습니다.\n"
                "이 서버는 GPU 전용입니다. GPU가 설치되어 있는지 확인하세요."
            )
        self.device = device
        self.logger = logging.getLogger(__name__)
        self.pipe = None
        self.controlnet = None
        self.ip_adapter_loaded = False  # IP-Adapter 로드 상태 추적
        
        # Models configuration
        self.base_model_id = "SG161222/RealVisXL_V4.0"
        self.controlnet_model_id = "diffusers/controlnet-canny-sdxl-1.0"

    def load_model(self):
        """SDXL 파이프라인 로드"""
        try:
            # float16으로 메모리 절약
            dtype = torch.float16
            
            self.logger.info("Loading ControlNet model...")
            self.controlnet = ControlNetModel.from_pretrained(
                self.controlnet_model_id,
                torch_dtype=dtype,
                use_safetensors=True
            )

            self.logger.info("Loading VAE model...")
            # VAE만 float32로 로드
            vae = AutoencoderKL.from_pretrained(
                "stabilityai/sdxl-vae",
                torch_dtype=torch.float32
            )

            self.logger.info("Loading SDXL Pipeline...")
            self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
                self.base_model_id,
                controlnet=self.controlnet,
                vae=vae,
                torch_dtype=dtype,
                use_safetensors=True
            )
            
            self.pipe = self.pipe.to(self.device)
            
            # VAE는 float32 유지
            self.pipe.vae = self.pipe.vae.to(self.device, dtype=torch.float32)
            
            
            # Load IP-Adapter
            self.logger.info("Loading IP-Adapter...")
            try:
                self.pipe.load_ip_adapter(
                    "h94/IP-Adapter", 
                    subfolder="sdxl_models", 
                    weight_name="ip-adapter_sdxl.bin"
                )
                if hasattr(self.pipe, 'image_encoder'):
                    self.pipe.image_encoder = self.pipe.image_encoder.to(self.device, dtype=dtype)
                
                self.pipe.set_ip_adapter_scale(0.5)
                self.ip_adapter_loaded = True  # IP-Adapter 로드 성공
                self.logger.info("IP-Adapter loaded successfully")
            except Exception as e:
                self.logger.warning(f"Failed to load IP-Adapter: {e}. Proceeding without it.")

            # 메모리 최적화
            # IP-Adapter와 attention slicing은 호환되지 않으므로 분기 처리
            if not self.ip_adapter_loaded:
                self.pipe.enable_attention_slicing()
                self.logger.info("✅ Attention slicing enabled")
            else:
                self.logger.info("⚠️ Attention slicing skipped (incompatible with IP-Adapter)")
            
            # VAE slicing은 항상 사용 가능
            self.pipe.enable_vae_slicing()

            self.logger.info("✅ SDXL Pipeline loaded successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error loading models: {str(e)}")
            raise e
    
    @staticmethod
    def _preprocess_canny(
        image: Image.Image, 
        low_threshold: int = 50, 
        high_threshold: int = 150
    ) -> Image.Image:
        """Canny Edge Detection 전처리"""
        try:
            image_array = np.array(image)
            
            if image.mode == 'RGBA':
                bg_color = (0, 0, 0) 
                background = Image.new('RGB', image.size, bg_color)
                background.paste(image, mask=image.split()[3])
                image_array = np.array(background)
                gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                image_array = np.array(image)
                gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

            edges = cv2.Canny(gray_image, low_threshold, high_threshold)
            edges_rgb = np.stack([edges, edges, edges], axis=2)
            
            return Image.fromarray(edges_rgb)
            
        except Exception as e:
            raise RuntimeError(f"Canny preprocessing failed: {e}")

    @staticmethod
    def _resize_and_center(
        image: Image.Image, 
        target_width: int, 
        target_height: int, 
        padding_percent: float = 0.8,
        vertical_alignment: str = "center"
    ) -> Image.Image:
        """이미지 리사이즈 및 중앙 정렬"""
        canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        
        max_w = int(target_width * padding_percent)
        max_h = int(target_height * padding_percent)
        
        img_w, img_h = image.size
        ratio = min(max_w / img_w, max_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
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
        controlnet_conditioning_scale: float = 1.0,
        padding_percent: float = 0.7,
        vertical_alignment: str = "center",
        use_ip_adapter: bool = True
    ) -> Image.Image:
        """배경 생성"""
        if self.pipe is None:
            self.load_model()
            
        dimensions = {
            "square": (1080, 1080),
            "portrait": (1080, 1352),
            "landscape": (1080, 608),
            "test": (512, 512)
        }
        
        target_width, target_height = dimensions.get(aspect_ratio, dimensions["square"])
            
        style_config = StylePrompts.get_prompt(style)
        full_positive_prompt = f"{prompt_text}, {style_config['positive']}"
        full_negative_prompt = f"{negative_prompt}, {style_config['negative']}"
        
        processed_image = self._resize_and_center(
            product_image, 
            target_width, 
            target_height,
            padding_percent=padding_percent,
            vertical_alignment=vertical_alignment
        )
        
        control_image = self._preprocess_canny(processed_image)
        
        kwargs = {
            "prompt": full_positive_prompt,
            "negative_prompt": full_negative_prompt,
            "image": control_image,
            "controlnet_conditioning_scale": controlnet_conditioning_scale,
            "num_inference_steps": num_inference_steps,
            "width": target_width,
            "height": target_height,
        }
        
        if use_ip_adapter:
            kwargs["ip_adapter_image"] = processed_image
        
        self.logger.info(f"🎨 Generating: style={style}, ratio={aspect_ratio}")
        
        # latent를 float32로 변환하는 콜백 (VAE decode 전)
        def callback_on_step_end(pipe, step, timestep, callback_kwargs):
            # 마지막 스텝에서 latent를 float32로 변환
            if step == num_inference_steps - 1:
                latents = callback_kwargs.get("latents")
                if latents is not None:
                    callback_kwargs["latents"] = latents.to(dtype=torch.float32)
            return callback_kwargs
        
        kwargs["callback_on_step_end"] = callback_on_step_end
        
        images = self.pipe(**kwargs).images
        
        return images[0]