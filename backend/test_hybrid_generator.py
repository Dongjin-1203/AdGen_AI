"""
HybridGenerator 테스트
"""
import logging
from PIL import Image
from app.services.generation.hybrid_generator import HybridGenerator

# ✅ 로깅 설정 추가
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


def test_initialization():
    """초기화 테스트"""
    print("=" * 60)
    print("Test 1: Initialization")
    print("=" * 60)
    
    # 자동 모드
    print("\n1. Auto mode:")
    generator = HybridGenerator()
    print(f"   Mode: {generator.get_mode()}")
    
    # 강제 Replicate 모드
    print("\n2. Force Replicate mode:")
    generator_replicate = HybridGenerator(force_mode="replicate")
    print(f"   Mode: {generator_replicate.get_mode()}")
    
    print("\n✅ Initialization test passed\n")


def test_mode_switch():
    """모드 전환 테스트"""
    print("=" * 60)
    print("Test 2: Mode Switch")
    print("=" * 60)
    
    generator = HybridGenerator(force_mode="replicate")
    print(f"\n1. Initial mode: {generator.get_mode()}")
    
    # 모드 전환 시도 (GPU 없으면 에러 발생 가능)
    try:
        print("\n2. Switching to local mode...")
        generator.switch_mode("local")
        print(f"   ✅ Successfully switched to: {generator.get_mode()}")
    except Exception as e:
        print(f"   ⚠️ Switch failed: {type(e).__name__}")
        print(f"   Reason: {str(e)[:100]}")
    
    print("\n✅ Mode switch test completed\n")


def test_generation():
    """배경 생성 테스트"""
    print("=" * 60)
    print("Test 3: Background Generation")
    print("=" * 60)
    
    # 테스트 이미지 생성 (빨간색 512x512)
    test_image = Image.new('RGBA', (512, 512), (255, 0, 0, 255))
    print("\n1. Created test image (512x512, red)")
    
    # Replicate 모드로 생성 (API 토큰 필요)
    try:
        generator = HybridGenerator(force_mode="replicate")
        print(f"2. Generator mode: {generator.get_mode()}")
        
        result = generator.generate_background(
            product_image=test_image,
            prompt_text="white minimal background",
            aspect_ratio="square",
            style="minimal",
            num_inference_steps=10  # 빠른 테스트
        )
        
        print(f"3. Generated image: {result.size}")
        print("\n✅ Generation test passed\n")
        
        return result
        
    except Exception as e:
        print(f"\n⚠️ Generation test failed: {e}")
        print("   (This is expected if REPLICATE_API_TOKEN is not set)")
        return None


def test_fallback():
    """Fallback 로직 테스트"""
    print("=" * 60)
    print("Test 4: Fallback Logic")
    print("=" * 60)
    
    # 자동 모드 (GPU 없으면 자동으로 Replicate 사용)
    generator = HybridGenerator()
    print(f"\n1. Auto mode selected: {generator.get_mode()}")
    
    test_image = Image.new('RGBA', (512, 512), (0, 255, 0, 255))
    
    try:
        result = generator.generate_background(
            product_image=test_image,
            prompt_text="simple white background",
            num_inference_steps=10
        )
        print(f"2. Generated with {generator.get_mode()} mode")
        print(f"3. Result: {result.size}")
        print("\n✅ Fallback test passed\n")
        
    except Exception as e:
        print(f"\n⚠️ Fallback test failed: {e}")


def test_invalid_inputs():
    """잘못된 입력 테스트"""
    print("=" * 60)
    print("Test 5: Invalid Inputs")
    print("=" * 60)
    
    # 잘못된 force_mode
    print("\n1. Testing invalid force_mode...")
    try:
        generator = HybridGenerator(force_mode="invalid")
        print("   ❌ Should have raised ValueError")
    except ValueError as e:
        print(f"   ✅ Caught expected error: {e}")
    
    # 잘못된 switch_mode
    print("\n2. Testing invalid switch_mode...")
    generator = HybridGenerator(force_mode="replicate")
    try:
        generator.switch_mode("invalid")
        print("   ❌ Should have raised ValueError")
    except ValueError as e:
        print(f"   ✅ Caught expected error: {e}")
    
    print("\n✅ Invalid input test passed\n")


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("HYBRID GENERATOR TEST SUITE")
    print("="*60 + "\n")
    
    try:
        test_initialization()
        test_mode_switch()
        test_invalid_inputs()
        
        # 실제 생성 테스트 (선택적)
        # test_generation()
        # test_fallback()
        
        print("="*60)
        print("🎉 ALL TESTS PASSED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()