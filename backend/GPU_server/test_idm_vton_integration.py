import os
import sys
import torch
import numpy as np
from PIL import Image

# Add current dir to path to find generation module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generation.idm_vton_generator import IDMVTONGenerator

def get_segmentation_mask(image_path):
    print("Generating mask with SegFormer...")
    from transformers import SegformerImageProcessor, AutoModelForSemanticSegmentation
    import torch.nn as nn
    
    processor = SegformerImageProcessor.from_pretrained("mattmdjaga/segformer_b2_clothes")
    model = AutoModelForSemanticSegmentation.from_pretrained("mattmdjaga/segformer_b2_clothes")
    
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits.cpu()
    
    upsampled_logits = nn.functional.interpolate(
        logits, size=image.size[::-1], mode="bilinear", align_corners=False
    )
    pred_seg = upsampled_logits.argmax(dim=1)[0]
    
    # Labels: 5 (Upper), 6 (Dress), 7 (Coat), 14 (L-Arm), 15 (R-Arm)
    labels_to_include = [5, 6, 7, 14, 15] 
    
    mask = np.zeros_like(pred_seg, dtype=np.uint8)
    for label in labels_to_include:
        mask[pred_seg == label] = 255
        
    mask_img = Image.fromarray(mask).convert("L")
    return mask_img

def get_densepose(image_path):
    print("Generating DensePose...")
    try:
        from controlnet_aux import DenseposeDetector
        densepose_detector = DenseposeDetector.from_pretrained("lllyasviel/ControlNet")
        image = Image.open(image_path).convert("RGB")
        pose_img = densepose_detector(image)
        return pose_img
    except ImportError:
        print("ControlNet Aux not installed. Returning blank pose (Will likely fail quality check).")
        return Image.new("RGB", (768, 1024), (0,0,0))
    except Exception as e:
        print(f"DensePose failed: {e}")
        return Image.new("RGB", (768, 1024), (0,0,0))

def main():
    # Paths (Assuming run from backend/GPU_server or root provided)
    # We need to find the assets.
    # Original assets were in IDM-VTON folder.
    # IDM-VTON folder might still be there in root, or we use the copied ones if I moved assets?
    # I only moved src.
    # So I should look in the original IDM-VTON folder or use absolute paths.
    
    base_path = r"C:\Users\mjuik\codeit_AdGen\AdGen_AI\IDM-VTON"
    human_img_path = os.path.join(base_path, "human_input.jpg")
    garm_img_path = os.path.join(base_path, "brown_coat_black_pants.jpg")
    
    if not os.path.exists(human_img_path):
        print(f"Error: {human_img_path} not found.")
        return

    print("Initializing Generator...")
    generator = IDMVTONGenerator(device="cuda" if torch.cuda.is_available() else "cpu")
    
    print("Loading Images...")
    human_img = Image.open(human_img_path).convert("RGB")
    garm_img = Image.open(garm_img_path).convert("RGB")
    
    # Pre-process
    print("Preprocessing Inputs...")
    mask_img = get_segmentation_mask(human_img_path)
    pose_img = get_densepose(human_img_path)
    
    # Resize to target (IDM-VTON Standard)
    target_size = (768, 1024)
    human_img = human_img.resize(target_size, Image.Resampling.LANCZOS)
    garm_img = garm_img.resize(target_size, Image.Resampling.LANCZOS)
    mask_img = mask_img.resize(target_size, Image.Resampling.NEAREST)
    pose_img = pose_img.resize(target_size, Image.Resampling.LANCZOS)
    
    print("Generating...")
    result = generator.generate(
        human_image=human_img,
        garm_image=garm_img,
        garment_description="model is wearing a brown coat and black pants",
        pose_image=pose_img,
        mask_image=mask_img,
        num_inference_steps=1  # Reduced to 1 for quick integration test
    )
    
    output_path = "integrated_idm_vton_result.png"
    result.save(output_path)
    print(f"Success! Saved to {output_path}")

if __name__ == "__main__":
    main()
