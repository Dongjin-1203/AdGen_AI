import json
import shutil
from pathlib import Path
from PIL import Image
import sys

def is_real_model(labeling_data: dict) -> bool:
    """실제 모델 판별 (마네킹 제외)"""
    top = labeling_data.get("상의", [{}])[0]
    bottom = labeling_data.get("하의", [{}])[0]
    outer = labeling_data.get("아우터", [{}])[0]
    dress = labeling_data.get("원피스", [{}])[0]
    
    has_full_outfit = (
        (top and bottom) or
        (outer and bottom) or
        dress
    )
    
    return has_full_outfit


def filter_kfashion_real_models(
    dataset_path: str,
    output_path: str = "./female_models",
    samples_per_category: int = 10
):
    """K-Fashion에서 실제 모델만 추출 (마네킹 제외)"""
    dataset = Path(dataset_path)
    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)
    
    # 한글 카테고리 → 영문 매핑
    categories = {
        "리조트": "resort",
        "로맨틱": "romantic",
        "레트로": "retro"
    }
    
    results = {eng: [] for eng in categories.values()}
    
    print("🔍 K-Fashion 실제 모델 추출 시작...\n")
    print(f"📂 입력 경로: {dataset_path}")
    print(f"📂 출력 경로: {output_path}\n")
    
    for kor_name, eng_name in categories.items():
        # JSON 파일 경로
        json_dir = dataset / "라벨링데이터" / kor_name
        # 이미지 파일 경로
        img_dir = dataset / "원천데이터" / "원천데이터_1" / kor_name
        
        if not json_dir.exists():
            print(f"⚠️  JSON 폴더가 없습니다: {json_dir}")
            continue
        
        if not img_dir.exists():
            print(f"⚠️  이미지 폴더가 없습니다: {img_dir}")
            continue
        
        # JSON 파일 찾기
        json_files = list(json_dir.glob("*.json"))
        print(f"📁 {kor_name} ({eng_name}): {len(json_files)}개 JSON 파일 발견")
        
        if len(json_files) == 0:
            print(f"   ⚠️  JSON 파일이 없습니다.\n")
            continue
        
        checked = 0
        mannequins = 0
        errors = 0
        
        for json_file in json_files:
            if len(results[eng_name]) >= samples_per_category:
                break
            
            checked += 1
            
            try:
                # JSON 읽기
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                labeling = data["데이터셋 정보"]["데이터셋 상세설명"]["라벨링"]
                
                # 실제 모델 판별
                if not is_real_model(labeling):
                    mannequins += 1
                    continue
                
                # ✅ 핵심 수정: JSON 파일명 기반으로 이미지 찾기
                json_stem = json_file.stem  # 확장자 제외 (예: "100873")
                
                # 가능한 확장자 시도
                img_file = None
                for ext in ['.jpg', '.jpeg', '.JPG', '.JPEG']:
                    potential_file = img_dir / f"{json_stem}{ext}"
                    if potential_file.exists():
                        img_file = potential_file
                        break
                
                if img_file is None:
                    errors += 1
                    continue
                
                # 이미지 확인
                try:
                    img = Image.open(img_file)
                    img.verify()
                    # verify 후 다시 열기
                    img = Image.open(img_file)
                except Exception:
                    errors += 1
                    continue
                
                # 스타일 정보
                style = labeling.get("스타일", [{}])[0]
                style_name = style.get("스타일", "")
                
                results[eng_name].append({
                    "json": json_file,
                    "image": img_file,
                    "labeling": labeling,
                    "style": style_name
                })
                
                print(f"   ✓ {len(results[eng_name])}/{samples_per_category}: {img_file.name} (스타일: {style_name})")
                
            except Exception as e:
                errors += 1
                continue
        
        print(f"   📊 통계 - 검사: {checked}개 | 마네킹: {mannequins}개 | 오류: {errors}개 | 실제 모델: {len(results[eng_name])}개")
        print(f"✅ {kor_name} ({eng_name}): {len(results[eng_name])}개 추출 완료\n")
    
    # 파일 복사
    print("📦 파일 복사 중...")
    total = 0
    
    for eng_name, items in results.items():
        if not items:
            continue
        
        cat_output = output / eng_name
        cat_output.mkdir(exist_ok=True)
        
        for i, item in enumerate(items):
            dst_img = cat_output / f"{eng_name}_{i:02d}.jpg"
            dst_json = cat_output / f"{eng_name}_{i:02d}.json"
            
            try:
                shutil.copy(item["image"], dst_img)
                shutil.copy(item["json"], dst_json)
                total += 1
                print(f"   ✓ 복사 완료: {dst_img.name}")
            except Exception as e:
                print(f"   ✗ 복사 실패: {item['image'].name} - {e}")
    
    print(f"\n🎉 총 {total}개 실제 모델 이미지 준비 완료!")
    print(f"📂 저장 위치: {output_path}")
    
    # 최종 통계
    print("\n📊 최종 통계:")
    for eng_name, items in results.items():
        if items:
            styles = [item["style"] for item in items if item["style"]]
            unique_styles = set(styles)
            print(f"   {eng_name}: {len(items)}개 - 스타일: {', '.join(unique_styles) if unique_styles else 'N/A'}")
        else:
            print(f"   {eng_name}: 0개")
    
    return results


if __name__ == "__main__":
    # Backend 기준 경로
    DATASET_PATH = r"./New_sample"
    OUTPUT_PATH = r"./female_models"
    
    print("=" * 60)
    print("K-Fashion 실제 모델 추출 스크립트 (Backend)")
    print("=" * 60)
    
    try:
        results = filter_kfashion_real_models(
            dataset_path=DATASET_PATH,
            output_path=OUTPUT_PATH,
            samples_per_category=10
        )
        
        print("\n✅ 완료!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)