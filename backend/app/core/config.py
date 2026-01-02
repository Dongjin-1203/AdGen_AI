
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AdGen AI"
    API_V1_STR: str = "/api/v1"
    
    # Model Configuration
    MODEL_DEVICE: str = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    
    # HuggingFace Models
    SDXL_BASE_MODEL: str = "stabilityai/stable-diffusion-xl-base-1.0"
    CONTROLNET_CANNY_MODEL: str = "diffusers/controlnet-canny-sdxl-1.0"
    SDXL_VAE_MODEL: str = "madebyollin/sdxl-vae-fp16-fix"
    
    # Storage
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    GENERATED_DIR: str = os.path.join(os.getcwd(), "generated")

    class Config:
        case_sensitive = True

settings = Settings()
