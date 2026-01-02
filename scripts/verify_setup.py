import sys
import os
from PIL import Image
try:
    # Adjust path to include backend
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
    from app.services.ai.background_generator import SDXLGenerator
    from app.services.ai.style_prompts import StylePrompts
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_imports():
    print("Testing imports...")
    try:
        generator = SDXLGenerator(device="cpu") # Force CPU for import test to avoid memory issues if GPU busy
        print("SDXLGenerator class instantiated successfully.")
    except Exception as e:
        print(f"Failed to instantiate SDXLGenerator: {e}")
        return

    print("Testing StylePrompts...")
    style = StylePrompts.get_prompt("minimal")
    assert "clean lines" in style["positive"]
    print("StylePrompts Verified.")

if __name__ == "__main__":
    test_imports()
    print("Verification Complete.")
