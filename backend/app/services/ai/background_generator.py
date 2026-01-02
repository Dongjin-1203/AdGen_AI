<<<<<<< HEAD
import torch
import logging
from PIL import Image
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, AutoencoderKL
from diffusers.utils import load_image
from .style_prompts import StylePrompts

from .image_processor import ImageProcessor

class SDXLGenerator:
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.logger = logging.getLogger(__name__)
        self.pipe = None
        self.controlnet = None
        
        # Models configuration - hardcoded for now, should move to config
        self.base_model_id = "stabilityai/stable-diffusion-xl-base-1.0"
        self.controlnet_model_id = "diffusers/controlnet-canny-sdxl-1.0"
        self.vae_model_id = "madebyollin/sdxl-vae-fp16-fix"

    def load_model(self):
        """
        Loads the SDXL ControlNet pipeline.
        """
        try:
            self.logger.info("Loading ControlNet model...")
            self.controlnet = ControlNetModel.from_pretrained(
                self.controlnet_model_id,
                torch_dtype=torch.float16,
                use_safetensors=True
            )

            self.logger.info("Loading VAE model...")
            vae = AutoencoderKL.from_pretrained(
                self.vae_model_id, 
                torch_dtype=torch.float16
            )

            self.logger.info("Loading SDXL Pipeline...")
            self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
                self.base_model_id,
                controlnet=self.controlnet,
                vae=vae,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            )
            
            self.pipe.to(self.device)
            # optimizations
            if self.device == "cuda":
                 self.pipe.enable_model_cpu_offload() 
                 # self.pipe.enable_xformers_memory_efficient_attention() # Enable if xformers is installed

            self.logger.info("SDXL Pipeline loaded successfully.")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
            raise e

    # internal preprocess_canny removed in favor of ImageProcessor.preprocess_canny

    def generate_background(
        self, 
        product_image: Image.Image, 
        prompt_text: str, 
        style: str = "minimal",
        negative_prompt: str = "",
        num_inference_steps: int = 30,
        controlnet_conditioning_scale: float = 0.5
    ) -> Image.Image:
        
        if self.pipe is None:
            self.load_model()
            
        style_config = StylePrompts.get_prompt(style)
        full_positive_prompt = f"{prompt_text}, {style_config['positive']}"
        full_negative_prompt = f"{negative_prompt}, {style_config['negative']}"
        
        # Prepare Control Image (Canny)
        # Prepare Control Image (Canny)
        control_image = ImageProcessor.preprocess_canny(product_image)
        
        self.logger.info(f"Generating image with style: {style}")
        
        images = self.pipe(
            prompt=full_positive_prompt,
            negative_prompt=full_negative_prompt,
            image=control_image,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            num_inference_steps=num_inference_steps,
        ).images
        
        return images[0]
=======
# 배경 생성
>>>>>>> origin/main
