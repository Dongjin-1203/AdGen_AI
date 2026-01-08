import torch
import logging
import cv2
import numpy as np
from PIL import Image
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, AutoencoderKL
from diffusers.utils import load_image
from .style_prompts import StylePrompts



class SDXLGenerator:
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.logger = logging.getLogger(__name__)
        self.pipe = None
        self.controlnet = None
        
        # Models configuration - hardcoded for now, should move to config
        # Switched to RealVisXL V4.0 for better photorealism (Benchmarking)
        self.base_model_id = "SG161222/RealVisXL_V4.0"
        self.controlnet_model_id = "diffusers/controlnet-canny-sdxl-1.0"

    def load_model(self):
        try:
            # CPU does not support float16 for many ops, use float32 if cpu
            dtype = torch.float32 if self.device == "cpu" else torch.float16
            
            self.logger.info("Loading ControlNet model...")
            self.controlnet = ControlNetModel.from_pretrained(
                self.controlnet_model_id,
                torch_dtype=dtype,
                use_safetensors=True
            )

            self.logger.info("Loading VAE model (default)...")
            vae = AutoencoderKL.from_pretrained(
                "stabilityai/sdxl-vae", # Use standalone VAE to ensure clean load
                torch_dtype=torch.float32 # Always force float32 for VAE to avoid artifacts
            )

            self.logger.info("Loading SDXL Pipeline...")
            self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
                self.base_model_id,
                controlnet=self.controlnet,
                vae=vae,
                torch_dtype=dtype,
                use_safetensors=True,
                variant="fp16" if dtype == torch.float16 else None
            )
            
            self.pipe.to(self.device)
            # optimizations
            if self.device == "cuda":
                 self.pipe.enable_model_cpu_offload() 
            
            # Load IP-Adapter for Identity Preservation (Benchmarking)
            self.logger.info("Loading IP-Adapter...")
            try:
                self.pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl.bin")
                # Set default IP-Adapter scale (0.5 is usually good for mixing with ControlNet)
                self.pipe.set_ip_adapter_scale(0.5) 
            except Exception as e:
                self.logger.warning(f"Failed to load IP-Adapter: {e}. Proceeding without it.")

            self.logger.info("SDXL Pipeline loaded successfully.")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
            raise e
    
    @staticmethod
    def _preprocess_canny(image: Image.Image, low_threshold: int = 50, high_threshold: int = 150) -> Image.Image:
        """
        Internal helper: Preprocesses an image for ControlNet Canny edge detection.
        """
        try:
            image_array = np.array(image)
            
            # Ensure image is in a format cv2 can handle
            if image.mode == 'RGBA':
                # Create a BLACK background to contrast with potential white items/transparency
                bg_color = (0, 0, 0) 
                background = Image.new('RGB', image.size, bg_color)
                # Paste the image on the background using alpha as mask
                background.paste(image, mask=image.split()[3])
                image_array = np.array(background)
                gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                 image_array = np.array(image)
                 gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

            # Detect edges
            edges = cv2.Canny(gray_image, low_threshold, high_threshold)
            
            # Convert back to 3-channel image for ControlNet input compatibility
            edges_rgb = np.concatenate([edges[:, :, None]], axis=2)
            edges_rgb = np.concatenate([edges_rgb, edges_rgb, edges_rgb], axis=2)
            
            return Image.fromarray(edges_rgb)
        except Exception as e:
            raise e

    @staticmethod
    def _resize_and_center(
        image: Image.Image, 
        target_width: int, 
        target_height: int, 
        padding_percent: float = 0.8,
        vertical_alignment: str = "center"
    ) -> Image.Image:
        """
        Internal helper: Resizes and positions image.
        """
        # Create a blank canvas (transparent)
        canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        
        # Calculate maximum allowed size for the image based on padding
        max_w = int(target_width * padding_percent)
        max_h = int(target_height * padding_percent)
        
        # Calculate new size maintaining aspect ratio
        img_w, img_h = image.size
        ratio = min(max_w / img_w, max_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        # Resize the image
        resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Calculate position
        x_offset = (target_width - new_w) // 2
        
        if vertical_alignment == "bottom":
             # Place at bottom with slight margin (5%)
             y_offset = target_height - new_h - int(target_height * 0.05)
        elif vertical_alignment == "top":
             # Place at top with slight margin
             y_offset = int(target_height * 0.05)
        else:
             # Center
             y_offset = (target_height - new_h) // 2
        
        # Paste centered
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
        
        if self.pipe is None:
            self.load_model()
            
        if self.pipe is None:
            self.load_model()
            
        # Instagram aspect ratio definitions (SDXL compatible values)
        # Using dimensions divisible by 8 near the target
        dimensions = {
            "square": (1080, 1080),   # 1:1
            "portrait": (1080, 1352), # 4:5 (approx 1350, mod 8)
            "landscape": (1080, 608), # 16:9 (approx 607.5, mod 8)
            "test": (512, 512)        # Low res for fast CPU testing
        }
        
        target_width, target_height = dimensions.get(aspect_ratio, dimensions["square"])
            
        style_config = StylePrompts.get_prompt(style)
        full_positive_prompt = f"{prompt_text}, {style_config['positive']}"
        full_negative_prompt = f"{negative_prompt}, {style_config['negative']}"
        
        # Resize and center product image on correct canvas size BEFORE Canny
        processed_image = self._resize_and_center(
            product_image, 
            target_width, 
            target_height,
            padding_percent=padding_percent,
            vertical_alignment=vertical_alignment
        )
        
        # Prepare Control Image (Canny) from the positioned image
        control_image = self._preprocess_canny(processed_image)
        
        # Prepare arguments
        kwargs = {
            "prompt": full_positive_prompt,
            "negative_prompt": full_negative_prompt,
            "image": control_image,
            "controlnet_conditioning_scale": controlnet_conditioning_scale,
            "num_inference_steps": num_inference_steps,
            "width": target_width,
            "height": target_height,
        }
        
        # Add IP-Adapter image if enabled
        # Note: IP-Adapter expects the ORIGINAL cropped product image, not the canvas. 
        # But usually passing the processed_image (canvas) is safer for positioning, 
        # however IP-Adapter works best with the object content. 
        # Let's pass the processed_image to ensure the 'content' matches the 'structure'.
        if use_ip_adapter:
            kwargs["ip_adapter_image"] = processed_image
        
        self.logger.info(f"Generating image with style: {style}, ratio: {aspect_ratio}")
        print(f"Starting SDXL generation steps ({num_inference_steps} steps)...")
        
        images = self.pipe(**kwargs).images
        
        return images[0]
