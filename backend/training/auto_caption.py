import os
from pathlib import Path

def generate_captions(dataset_dir: str, trigger_word: str = "ohwx"):
    """
    Generates .txt caption files for each image in the dataset directory.
    trigger_word: A unique token to represent the style (e.g., 'ohwx', 'sks').
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    dataset_path = Path(dataset_dir)
    
    if not dataset_path.exists():
        print(f"Error: Directory {dataset_dir} not found.")
        return

    count = 0
    print(f"Scanning {dataset_dir} for images...")
    
    for file_path in dataset_path.iterdir():
        if file_path.suffix.lower() in image_extensions:
            # Create corresponding text file path
            txt_path = file_path.with_suffix(".txt")
            
            # Skip if caption already exists (to avoid overwriting manual work)
            if txt_path.exists():
                print(f"Skipping existing caption: {txt_path.name}")
                continue
                
            # Generate simple caption based on filename or default template
            # Extract simple keyword from filename (e.g., 'jacket' from 'jacket_01.jpg')
            filename_key = file_path.stem.split('_')[0]
            
            caption = f"a photo of {trigger_word} {filename_key}, {filename_key} style, high quality, 8k"
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(caption)
            
            print(f"Created caption for {file_path.name}: '{caption}'")
            count += 1

    print(f"\nCompleted! Generated {count} caption files.")
    print(f"Trigger word used: '{trigger_word}'")

if __name__ == "__main__":
    # Default path based on previous flattening step
    DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../backend/dataset/images"))
    generate_captions(DATASET_DIR)
