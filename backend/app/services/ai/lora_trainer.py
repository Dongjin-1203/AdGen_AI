import logging
import torch

class LoRATrainer:
    def __init__(self, model_id: str, device: str = "cuda"):
        self.model_id = model_id
        self.device = device
        self.logger = logging.getLogger(__name__)

    def load_lora_weights(self, pipeline, lora_path: str, adapter_name: str = "default"):
        """
        Loads LoRA weights into the provided pipeline.
        """
        try:
            self.logger.info(f"Loading LoRA weights from {lora_path}")
            pipeline.load_lora_weights(lora_path, adapter_name=adapter_name)
            self.logger.info("LoRA weights loaded successfully.")
            return pipeline
        except Exception as e:
            self.logger.error(f"Failed to load LoRA weights: {str(e)}")
            raise e

    def train_lora(
        self, 
        dataset_path: str, 
        output_path: str, 
        epochs: int = 1, # Default to 1 for quick testing
        batch_size: int = 1,
        rank: int = 4
    ):
        """
        Executes LoRA Fine-tuning on the provided dataset.
        """
        try:
            from peft import LoraConfig, get_peft_model
            from diffusers import DDPMScheduler, UNet2DConditionModel, AutoencoderKL
            from transformers import AutoTokenizer, CLIPTextModel, CLIPTextModelWithProjection
            from accelerate import Accelerator
            import os
            from torch.utils.data import Dataset, DataLoader
            from torchvision import transforms
            from torch.optim import AdamW
            from PIL import Image

            self.logger.info(f"Initializing LoRA training... ({self.device})")
            
            # Simple check for empty dataset
            if not os.path.exists(dataset_path) or not os.listdir(dataset_path):
                 self.logger.error(f"Dataset not found or empty at {dataset_path}")
                 return
            
            # 1. Setup Accelerator
            accelerator = Accelerator(
                gradient_accumulation_steps=1,
                mixed_precision="fp16" if self.device == "cuda" else "no"
            )

            # 2. Load Models
            self.logger.info("Loading SDXL components...")
            # For pure UNet LoRA training
            vae = AutoencoderKL.from_pretrained("stabilityai/sdxl-vae", torch_dtype=torch.float32)
            tokenizer_one = AutoTokenizer.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", subfolder="tokenizer")
            tokenizer_two = AutoTokenizer.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", subfolder="tokenizer_2")
            text_encoder_one = CLIPTextModel.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", subfolder="text_encoder")
            text_encoder_two = CLIPTextModelWithProjection.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", subfolder="text_encoder_2")
            unet = UNet2DConditionModel.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", subfolder="unet")
            noise_scheduler = DDPMScheduler.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", subfolder="scheduler")

            # Freeze frozen components
            vae.requires_grad_(False)
            text_encoder_one.requires_grad_(False)
            text_encoder_two.requires_grad_(False)
            unet.requires_grad_(False)

            # 3. Setup LoRA Config
            self.logger.info(f"Setting up LoRA (Rank: {rank})...")
            lora_config = LoraConfig(
                r=rank,
                lora_alpha=rank,
                init_lora_weights="gaussian",
                target_modules=["to_k", "to_q", "to_v", "to_out.0"],
            )
            unet = get_peft_model(unet, lora_config)
            unet.print_trainable_parameters()

            # 4. Dataset & Dataloader
            class FashionDataset(Dataset):
                def __init__(self, dataset_path, tokenizer_one, tokenizer_two, size=512):
                    self.root = dataset_path
                    self.image_paths = [os.path.join(dataset_path, f) for f in os.listdir(dataset_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                    self.tokenizer_one = tokenizer_one
                    self.tokenizer_two = tokenizer_two
                    self.size = size
                    self.transforms = transforms.Compose([
                        transforms.Resize(size, interpolation=transforms.InterpolationMode.BILINEAR),
                        transforms.CenterCrop(size),
                        transforms.ToTensor(),
                        transforms.Normalize([0.5], [0.5]),
                    ])

                def __len__(self):
                    return len(self.image_paths)

                def __getitem__(self, idx):
                    img_path = self.image_paths[idx]
                    txt_path = os.path.splitext(img_path)[0] + ".txt"
                    image = Image.open(img_path).convert("RGB")
                    pixel_values = self.transforms(image)
                    caption = ""
                    if os.path.exists(txt_path):
                        with open(txt_path, "r", encoding="utf-8") as f:
                            caption = f.read().strip()
                    input_ids_one = self.tokenizer_one(caption, padding="max_length", max_length=77, truncation=True, return_tensors="pt").input_ids
                    input_ids_two = self.tokenizer_two(caption, padding="max_length", max_length=77, truncation=True, return_tensors="pt").input_ids
                    return {"pixel_values": pixel_values, "input1": input_ids_one.squeeze(), "input2": input_ids_two.squeeze()}

            self.logger.info(f"Loading dataset from {dataset_path}...")
            dataset = FashionDataset(dataset_path, tokenizer_one, tokenizer_two)
            train_dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

            optimizer = AdamW(unet.parameters(), lr=1e-4)

            # Prepare with Accelerator
            unet, optimizer, train_dataloader = accelerator.prepare(unet, optimizer, train_dataloader)
            
            # Move static models to device
            vae.to(accelerator.device)
            text_encoder_one.to(accelerator.device)
            text_encoder_two.to(accelerator.device)

            # 5. Training Loop
            self.logger.info(f"Starting training loop ({len(dataset)} images, {epochs} epochs)...")
            
            for epoch in range(epochs):
                self.logger.info(f"Epoch {epoch+1}/{epochs} started.")
                unet.train()
                for step, batch in enumerate(train_dataloader):
                    with accelerator.accumulate(unet):
                        # Convert images to latents
                        latents = vae.encode(batch["pixel_values"].to(vae.dtype)).latent_dist.sample()
                        latents = latents * vae.config.scaling_factor
                        
                        # Sample noise
                        noise = torch.randn_like(latents)
                        timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps, (latents.shape[0],), device=latents.device)
                        timesteps = timesteps.long()
                        
                        noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)
                        
                        # Get text embeddings
                        prompt_embeds_list = []
                        for text_encoder, input_ids in zip([text_encoder_one, text_encoder_two], [batch["input1"], batch["input2"]]):
                            prompt_embeds = text_encoder(input_ids, output_hidden_states=True)
                            pooled_prompt_embeds = prompt_embeds[0]
                            prompt_embeds = prompt_embeds.hidden_states[-2]
                            prompt_embeds_list.append(prompt_embeds)
                            
                        prompt_embeds = torch.concat([prompt_embeds_list[0], prompt_embeds_list[1]], dim=-1)
                        add_text_embeds = pooled_prompt_embeds # Simplified
                        
                        # Predict noise
                        # Dummy time_ids (crop coords)
                        add_time_ids = torch.tensor([[1024., 1024., 0., 0., 1024., 1024.]]).to(latents.device)

                        model_pred = unet(
                            noisy_latents, 
                            timesteps, 
                            encoder_hidden_states=prompt_embeds, 
                            added_cond_kwargs={"text_embeds": add_text_embeds, "time_ids": add_time_ids}
                        ).sample
                        
                        loss = torch.nn.functional.mse_loss(model_pred.float(), noise.float(), reduction="mean")
                        
                        accelerator.backward(loss)
                        optimizer.step()
                        optimizer.zero_grad()
                    
                    if step % 5 == 0:
                        self.logger.info(f"Epoch {epoch} Step {step} Loss: {loss.item():.4f}")

            # 6. Save Weights
            self.logger.info(f"Saving LoRA weights to {output_path}...")
            os.makedirs(output_path, exist_ok=True)
            unet.save_pretrained(output_path) 
            self.logger.info("LoRA Fine-tuning complete.")
            
        except Exception as e:
            self.logger.error(f"Error during LoRA training: {str(e)}")
            raise e
