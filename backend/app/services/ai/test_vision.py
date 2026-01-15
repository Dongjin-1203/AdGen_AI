"""
Vision AI 테스트
backend/test_images/ 폴더의 이미지들을 분석하여 정확도 검증
"""
import asyncio
import os
from pathlib import Path
from .product_analyzer import ProductAnalyzer
from config import settings

# 테스트 이미지 디렉토리
TEST_IMAGE_DIR = Path(__file__).parent.parent.parent.parent / "test_images"

# 테스트 이미지 목록
TEST_IMAGES = [
    "test_beige_woman_sweater.jpg",
    "test_black_pants.jpg",
    "test_blue_oxford_shirt.jpg",
    "test_denim_jeans.jpg",
    "test_gray_knit_sweater.jpg",
    "test_jacket.jpg",
    "test_white_T-shirt.jpg"
]


async def test_single_image(analyzer: ProductAnalyzer, image_name: str):
    """단일 이미지 테스트"""
    image_path = TEST_IMAGE_DIR / image_name
    
    print("\n" + "=" * 60)
    print(f"📷 테스트: {image_name}")
    print("=" * 60)
    
    # 이미지 존재 확인
    if not image_path.exists():
        print(f"❌ 이미지 파일이 없습니다: {image_path}")
        return None
    
    # 분석 실행
    result = await analyzer.analyze(str(image_path))
    
    # 결과 출력
    if result.get('success'):
        print(f"✅ 분석 성공!")
        print(f"   카테고리: {result.get('category', 'N/A')}")
        print(f"   세부 카테고리: {result.get('sub_category', 'N/A')}")
        print(f"   색상: {result.get('color', 'N/A')}")
        print(f"   소재 추정: {result.get('material_guess', 'N/A')}")
        print(f"   핏: {result.get('fit', 'N/A')}")
        print(f"   스타일 태그: {', '.join(result.get('style_tags', []))}")
        print(f"   신뢰도: {result.get('confidence', 0):.2%}")
    else:
        print(f"❌ 분석 실패: {result.get('error', 'Unknown error')}")
        if 'raw_content' in result:
            print(f"📄 원본 응답:\n{result['raw_content'][:200]}...")
    
    return result


async def test_all_images():
    """모든 테스트 이미지 분석"""
    print("\n🚀 Vision AI 테스트 시작")
    print(f"📂 테스트 디렉토리: {TEST_IMAGE_DIR}")
    print(f"📊 테스트 이미지 수: {len(TEST_IMAGES)}")
    
    # API 키 확인
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        print("\n❌ GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다!")
        print("   .env 파일에 API 키를 추가하세요.")
        return
    
    # ProductAnalyzer 초기화
    try:
        analyzer = ProductAnalyzer(provider="gemini")
    except Exception as e:
        print(f"\n❌ ProductAnalyzer 초기화 실패: {e}")
        return
    
    # 결과 저장
    results = []
    success_count = 0
    
    # 각 이미지 분석
    for image_name in TEST_IMAGES:
        result = await test_single_image(analyzer, image_name)
        
        if result:
            results.append({
                "image": image_name,
                "result": result
            })
            if result.get('success'):
                success_count += 1
    
    # 전체 요약
    print("\n" + "=" * 60)
    print("📊 테스트 요약")
    print("=" * 60)
    print(f"전체 이미지: {len(TEST_IMAGES)}개")
    print(f"성공: {success_count}개")
    print(f"실패: {len(TEST_IMAGES) - success_count}개")
    print(f"성공률: {success_count / len(TEST_IMAGES) * 100:.1f}%")
    
    # 평균 신뢰도
    if success_count > 0:
        avg_confidence = sum(
            r['result']['confidence'] 
            for r in results 
            if r['result'].get('success')
        ) / success_count
        print(f"평균 신뢰도: {avg_confidence:.2%}")
    
    # 상세 결과 테이블
    print("\n📋 상세 결과:")
    print(f"{'이미지':<30} {'카테고리':<15} {'색상':<10} {'신뢰도':<10}")
    print("-" * 65)
    
    for item in results:
        image = item['image']
        result = item['result']
        
        if result.get('success'):
            category = result.get('category', 'N/A')
            color = result.get('color', 'N/A')
            confidence = f"{result.get('confidence', 0):.2%}"
        else:
            category = "FAILED"
            color = "-"
            confidence = "-"
        
        print(f"{image:<30} {category:<15} {color:<10} {confidence:<10}")


async def test_specific_image(image_name: str):
    """특정 이미지만 테스트 (디버깅용)"""
    print(f"\n🔍 단일 이미지 테스트: {image_name}")
    
    # API 키 확인
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        print("\n❌ GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다!")
        return
    
    # ProductAnalyzer 초기화
    analyzer = ProductAnalyzer(provider="gemini")
    
    # 분석
    await test_single_image(analyzer, image_name)


if __name__ == "__main__":
    # .env 파일 로드 (python-dotenv 사용)
    from dotenv import load_dotenv
    import os
    
    # 환경별 .env 파일 자동 선택
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        env_file = ".env.production"
    else:
        env_file = ".env"
    
    print(f"📄 환경 변수 로드: {env_file}")
    load_dotenv(env_file)
    
    # 전체 테스트 실행
    asyncio.run(test_all_images())
    
    # 특정 이미지만 테스트하려면:
    # asyncio.run(test_specific_image("test_beige_woman_sweater.jpg"))