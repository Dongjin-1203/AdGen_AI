"""
Import 경로 테스트
"""

def test_generation_imports():
    """배경 생성 모듈 import 테스트"""
    print("Testing generation imports...")
    
    from app.services.generation import SDXLGenerator, ReplicateBackgroundGenerator
    from backend.GPU_server.generation.prompts import PromptEngine, StylePrompts
    from backend.shared.utils import resize_to_instagram_ratio, INSTAGRAM_RATIOS
    
    print("✅ Generation imports successful")


def test_img_processing_imports():
    """이미지 전처리 모듈 import 테스트"""
    print("Testing img_processing imports...")
    
    from app.services.img_processing import (
        BackgroundRemovalService,
        ColorCorrection,
        StyleProcessor,
        WrinkleRemoval
    )
    
    print("✅ Image processing imports successful")


def test_vision_imports():
    """Vision AI 모듈 import 테스트"""
    print("Testing vision imports...")
    
    from app.services.vision import ProductAnalyzer, GeminiVisionProvider
    
    print("✅ Vision imports successful")


def test_all():
    """전체 import 테스트"""
    try:
        test_generation_imports()
        test_img_processing_imports()
        test_vision_imports()
        
        print("\n" + "=" * 50)
        print("🎉 All imports successful!")
        print("=" * 50)
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        raise


if __name__ == "__main__":
    test_all()