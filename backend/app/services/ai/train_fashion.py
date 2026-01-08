import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.app.services.ai.lora_trainer import LoRATrainer

# Configure logging
logging.basicConfig(level=logging.INFO)

def run_training():
    dataset_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../backend/dataset/images"))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../backend/models/fashion_lora"))
    
    trainer = LoRATrainer(model_id="stabilityai/stable-diffusion-xl-base-1.0", device="cuda") # Will auto-fallback/accelerate handles device usually, but init arg is mostly for logging now.
    
    print(f"Starting training with dataset: {dataset_dir}")
    print(f"Output directory: {output_dir}")
    
    trainer.train_lora(
        dataset_path=dataset_dir, 
        output_path=output_dir, 
        epochs=1, # 1 epoch for testing/demo
        batch_size=1, 
        rank=4
    )

if __name__ == "__main__":
    run_training()
