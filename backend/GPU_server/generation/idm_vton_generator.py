import sys
import os
import torch
import logging
from PIL import Image
from diffusers import UNet2DConditionModel, AutoencoderKL
from transformers import CLIPImageProcessor, AutoTokenizer
from transformers import CLIPTextModel, CLIPTextModelWithProjection, CLIPVisionModelWithProjection
from typing import Optional, Tuple

# Add the current directory to sys.path to allow imports from local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
# idm_vton is located in the parent directory of generation/
# backend/GPU_server/idm_vton
idm_vton_path = os.path.abspath(os.path.join(current_dir, "..", "idm_vton"))
sys.path.insert(0, idm_vton_path)

from src.tryon_pipeline import StableDiffusionXLInpaintPipeline as TryonPipeline
from src.unet_hacked_garmnet import UNet2DConditionModel as UNet2DConditionModel_ref
from src.unet_hacked_tryon import UNet2DConditionModel as UNet2DConditionModel_tryon

class IDMVTONGenerator:
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.logger = logging.getLogger(__name__)
        self.pipe = None
        self.unet = None
        
        # Model Path configuration
        # Assuming we will download weights or use a fixed path. 
        # For now, using the Hugging Face Hub ID.
        self.base_model_path = "yisol/IDM-VTON"

    def load_model(self):
        try:
            self.logger.info("Loading IDM-VTON models...")
            
            # Monkey patch for _remove_lora issue (Apply BEFORE loading pipeline)
            from diffusers.models.attention_processor import Attention
            if not hasattr(Attention, "_original_set_processor"):
                Attention._original_set_processor = Attention.set_processor
                def patched_set_processor(self, processor, **kwargs):
                    safe_kwargs = {k: v for k, v in kwargs.items() if k != "_remove_lora"}
                    return Attention._original_set_processor(self, processor, **safe_kwargs)
                Attention.set_processor = patched_set_processor
                self.logger.info("Applied monkey patch for Attention.set_processor")

            # 1. Load UNet (Tryon)
            unet = UNet2DConditionModel_tryon.from_pretrained(
                self.base_model_path,
                subfolder="unet",
                torch_dtype=torch.float16,
            )

            # 2. Load tokenizer & text encoder
            tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_path,
                subfolder="tokenizer",
                use_fast=False,
            )
            text_encoder = CLIPTextModel.from_pretrained(
                self.base_model_path,
                subfolder="text_encoder",
                torch_dtype=torch.float16,
            )
            
            # 3. Load VAE
            vae = AutoencoderKL.from_pretrained(
                self.base_model_path,
                subfolder="vae",
                torch_dtype=torch.float16,
            )

            # 4. Load UNet (Garment)
            unet_encoder = UNet2DConditionModel_ref.from_pretrained(
                self.base_model_path,
                subfolder="unet_encoder",
                torch_dtype=torch.float16,
            )

            # 5. Load Scheduler - handled by pipeline defaults usually, but can be explicit
            # For simplicity, letting the pipeline handle it or using the one from the repo config

            # 6. Initialize Pipeline
            # Note: TryonPipeline handles the complex assembly of these components
            self.pipe = TryonPipeline.from_pretrained(
                self.base_model_path,
                unet=unet,
                vae=vae,
                feature_extractor_clip=CLIPImageProcessor(),
                text_encoder=text_encoder,
                tokenizer=tokenizer,
                unet_encoder=unet_encoder,
                torch_dtype=torch.float16,
            )
            
            self.pipe.to(self.device)
            self.logger.info("IDM-VTON Pipeline loaded successfully.")

        except Exception as e:
            self.logger.error(f"Error loading IDM-VTON models: {str(e)}")
            raise e

    def generate(
        self,
        human_image: Image.Image,
        garm_image: Image.Image,
        garment_description: str,
        pose_image: Image.Image,
        mask_image: Image.Image,
        num_inference_steps: int = 30,
        seed: int = 42
    ) -> Image.Image:
        """
        Generates a virtual try-on image.
        
        Args:
            human_image (PIL.Image): Image of the person (model).
            garm_image (PIL.Image): Image of the garment (flat lay).
            garment_description (str): Description of the garment.
            pose_image (PIL.Image): DensePose image (RGB).
            mask_image (PIL.Image): Segmentation mask (L) covering the area to replace.
            num_inference_steps (int): Number of denoising steps.
            seed (int): Random seed.
        """
        if self.pipe is None:
            self.load_model()
            
        try:
            # Preprocessing
            # IDM-VTON works best with 768x1024 resolution
            target_size = (768, 1024)
            
            # Resize human image
            if human_image.size != target_size:
                human_image = human_image.resize(target_size, Image.Resampling.LANCZOS)
                
            # Resize garment image
            if garm_image.size != target_size:
                garm_image = garm_image.resize(target_size, Image.Resampling.LANCZOS)

            # Prepare Inputs
            # In a real scenario, we might need OpenPose/DensePose data here.
            # IDM-VTON pipeline internally can handle some of this if configured, 
            # BUT the inference_custom.py used pre-computed mask/pose.
            # For this MVP, we are effectively porting the "inference_custom.py" logic.
            # It passed 'pose_img', 'mask_img' etc.
            
            # CRITICAL: IDM-VTON requires DensePose and Mask.
            # If we don't have them, the quality drops or it fails.
            # inference_custom.py assumed these inputs existed.
            # For this integration to work 'as is', we might need to assume the caller provides them
            # OR logic to auto-generate them.
            
            # Since the user asked to "use the IDM-VTON we used before", 
            # and that script ran successfully with specific inputs, 
            # we will simplify the input for now to just image+garment 
            # and rely on the pipeline's internal capabilities OR placeholders if the pipeline enforces it.
            
            # Re-reading inference_custom.py logic:
            # It explicitly loaded 'image_path', 'garm_img_path', 'pose_image', 'mask_image'.
            # We need to bridge this gap. 
            # Ideally, we should add DensePose generation here, but that is a heavy dependency.
            
            # Strategy:
            # Pass the mandatory inputs (human, garm, prompt).
            # The 'TryonPipeline' defined in src/tryon_pipeline.py likely expects specific tensor inputs.
            # Let's check how 'pipe()' is called in inference_custom.py
            
            # pipe(
            #    prompt=prompt,
            #    image=human_img,
            #    mask_image=mask,
            #    pose_image=pose_img,
            #    ip_adapter_image=garm_img,
            #    ...
            # )
            
            # We strictly need 'mask_image' (human mask) and 'pose_image' (DensePose).
            # If we don't implement auto-masking/pose here, this class is incomplete.
            # HOWEVER, for the "Presentation/Demo" phase, maybe we can use dummy/cached 
            # pose/masks if the human model is fixed (like 'human_input.jpg').
            
            # But the requirement is "Integration".
            # I will generate the class assuming these inputs are handled or passed.
            # For now, to keep it simple and runnable, I will define the method signature generally
            # and internally handle the inputs as best as possible, 
            # perhaps raising a warning if mask/pose are missing.
            
            # Wait, `inference_custom.py` line 180+ loads `pose_img` and `mask`.
            # If we are making a general generator, we either need a Preprocessor class or 
            # we need to integrate OpenPose/DensePose.
            
            # Given the constraints (time/complexity), I will assume for this step
            # that we might use a fixed human model (as tested) OR 
            # simply structure the class to accept these as optional inputs.
            
            # Let's mirror the `pipe` call exactly.
            
            # Prepare text prompts
            (prompt_embeds, neg_embeds, pooled_embeds, neg_pooled_embeds) = self.pipe.encode_prompt(
                garment_description, 
                num_images_per_prompt=1, 
                do_classifier_free_guidance=True, 
                negative_prompt="monochrome, lowres, bad anatomy, worst quality, low quality"
            )
            
            (prompt_embeds_c, _, _, _) = self.pipe.encode_prompt(
                "a photo of a clothes", 
                num_images_per_prompt=1, 
                do_classifier_free_guidance=False, 
                negative_prompt="monochrome, lowres, bad anatomy, worst quality, low quality"
            )

            # Prepare Tensors
            # Normalize images to [-1, 1] and CHW format
            import numpy as np
            
            def to_tensor(img):
                return torch.from_numpy(np.array(img)/127.5 - 1.0).permute(2,0,1).unsqueeze(0)

            human_tensor = to_tensor(human_image).to(self.device, dtype=torch.float16)
            garm_tensor = to_tensor(garm_image).to(self.device, dtype=torch.float16)
            
            # Helper: If pose/mask not provided, we need them.
            # For this Class logic, we ideally accept them as args. 
            # If strictly integrating 'as is', we assume the caller handles it.
            # But the user logic had 'DenseposeDetector' inside main().
            # I will assume for now we use 'pose_image' and 'mask_image' that ARE PASSED IN.
            # I will add them to the method signature in a separate edit or assume they are passed in kwargs/args if I change signature.
            # Wait, I cannot change signature easily here without breaking the previous step's intent if I defined it strictly.
            # Let's check my previous write. I did NOT include pose/mask in generate().
            # I should update the signature first.
            pose_tensor = to_tensor(pose_image).to(self.device, dtype=torch.float16)
            
            # Call Pipeline
            images = self.pipe(
                prompt_embeds=prompt_embeds,
                negative_prompt_embeds=neg_embeds,
                pooled_prompt_embeds=pooled_embeds,
                negative_pooled_prompt_embeds=neg_pooled_embeds,
                num_inference_steps=num_inference_steps,
                strength=1.0,
                pose_img=pose_tensor,
                text_embeds_cloth=prompt_embeds_c,
                cloth=garm_tensor,
                mask_image=mask_image,
                image=human_tensor,
                height=1024,
                width=768,
                guidance_scale=2.0,
                ip_adapter_image=garm_image,
            ).images

            return images[0]

        except Exception as e:
            self.logger.error(f"Error during IDM-VTON generation: {str(e)}")
            raise e

    def _get_prompts(self, garment_desc: str) -> Tuple[str, str]:
        positive = f"model is wearing {garment_description}"
        negative = "monochrome, lowres, bad anatomy, worst quality, low quality"
        return positive, negative

