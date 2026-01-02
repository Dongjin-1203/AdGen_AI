import sys
import os
import argparse
from PIL import Image

# Add backend directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.app.services.ai.background_generator import SDXLGenerator
from backend.app.services.ai.background_remover import BackgroundRemover
from backend.app.services.ai.image_processor import ImageProcessor

def test_pipeline(image_path: str, prompt: str, output_dir: str = "test_outputs"):
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading image from {image_path}...")
    try:
        original_image = Image.open(image_path).convert("RGB")
        original_image.save(os.path.join(output_dir, "original.jpg"))
    except Exception as e:
        print(f"Failed to load image: {e}")
        return

    # 1. Background Removal
    print("\n[1] Testing Background Removal...")
    try:
        no_bg_image = BackgroundRemover.remove_background(original_image)
        no_bg_path = os.path.join(output_dir, "no_bg.png")
        no_bg_image.save(no_bg_path)
        print(f"Background removed saved to {no_bg_path}")
    except Exception as e:
        print(f"Background removal failed: {e}")
        no_bg_image = original_image # Fallback for next steps

    # 2. Image Processing (Canny)
    print("\n[2] Testing Canny Preprocessing...")
    try:
        canny_image = ImageProcessor.preprocess_canny(no_bg_image)
        canny_path = os.path.join(output_dir, "canny.png")
        canny_image.save(canny_path)
        print(f"Canny edge map saved to {canny_path}")
    except Exception as e:
        print(f"Canny processing failed: {e}")

    # 3. Background Generation
    print("\n[3] Testing Background Generation (SDXL)...")
    try:
        generator = SDXLGenerator(device="cuda" if sys.platform != "darwin" else "mps") # crude check, better to use torch.device
        # Note: If no GPU, this will fail or be very slow if we didn't handle CPU fallback in class, 
        # but class defaults to cuda.
        
        generated_image = generator.generate_background(
            product_image=no_bg_image,
            prompt_text=prompt,
            style="minimal"
        )
        gen_path = os.path.join(output_dir, "generated.png")
        generated_image.save(gen_path)
        print(f"Generated image saved to {gen_path}")
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test AI Pipeline")
    parser.add_argument("--image", type=str, required=True, help="Path to input product image")
    parser.add_argument("--prompt", type=str, default="on a wooden table, soft lighting", help="Prompt for background")
    args = parser.parse_args()
    
    test_pipeline(args.image, args.prompt)
