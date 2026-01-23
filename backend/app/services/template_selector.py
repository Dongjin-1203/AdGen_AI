"""
템플릿 선택 로직
style_tags 기반으로 최적의 광고 템플릿을 자동 선택
"""
from typing import List, Dict
from app.templates.ad_templates import AD_TEMPLATES


def select_template(style_tags: List[str]) -> str:
    """
    style_tags 기반 템플릿 자동 선택
    
    Args:
        style_tags: Vision AI가 분석한 스타일 태그 리스트
                   예: ["미니멀", "모던", "심플"]
    
    Returns:
        template_name: 'minimal', 'bold', 'vintage' 등
    
    Examples:
        >>> select_template(["미니멀", "모던"])
        'minimal'
        
        >>> select_template(["빈티지", "레트로"])
        'vintage'
        
        >>> select_template(["대담한", "강렬한"])
        'bold'
    """
    
    # style_tags가 None이거나 빈 리스트면 기본값
    if not style_tags:
        return "minimal"
    
    # 각 템플릿의 best_for 키워드와 매칭
    scores = {}
    
    for template_name, template_info in AD_TEMPLATES.items():
        score = 0
        best_for_keywords = template_info['best_for']
        
        # style_tags와 best_for 키워드 비교
        for tag in style_tags:
            for keyword in best_for_keywords:
                # 양방향 매칭: "미니멀" in "미니멀리즘" or "미니멀리즘" in "미니멀"
                if keyword in tag or tag in keyword:
                    score += 1
        
        scores[template_name] = score
    
    # 최고점 템플릿 선택
    if max(scores.values()) > 0:
        selected = max(scores.items(), key=lambda x: x[1])
        return selected[0]
    else:
        # 매칭되는게 없으면 기본값
        return "minimal"


def get_template_info(template_name: str) -> Dict:
    """
    템플릿 상세 정보 조회
    
    Args:
        template_name: 템플릿 이름
    
    Returns:
        템플릿 정보 dict (name, description, colors, best_for, html)
    """
    return AD_TEMPLATES.get(template_name, AD_TEMPLATES["minimal"])


def select_template_with_score(style_tags: List[str]) -> Dict[str, any]:
    """
    템플릿 선택 + 점수 반환 (디버깅용)
    
    Args:
        style_tags: 스타일 태그 리스트
    
    Returns:
        {
            'template': 'minimal',
            'score': 3,
            'all_scores': {'minimal': 3, 'bold': 0, 'vintage': 1}
        }
    """
    
    if not style_tags:
        return {
            'template': 'minimal',
            'score': 0,
            'all_scores': {}
        }
    
    scores = {}
    
    for template_name, template_info in AD_TEMPLATES.items():
        score = 0
        best_for_keywords = template_info['best_for']
        
        for tag in style_tags:
            for keyword in best_for_keywords:
                if keyword in tag or tag in keyword:
                    score += 1
        
        scores[template_name] = score
    
    selected_template = "minimal"
    max_score = 0
    
    if max(scores.values()) > 0:
        selected_template = max(scores.items(), key=lambda x: x[1])[0]
        max_score = scores[selected_template]
    
    return {
        'template': selected_template,
        'score': max_score,
        'all_scores': scores
    }


# 테스트용 함수
if __name__ == "__main__":
    # 테스트 케이스
    test_cases = [
        (["미니멀", "모던"], "minimal"),
        (["빈티지", "레트로"], "vintage"),
        (["대담한", "강렬한"], "bold"),
        (["심플", "깔끔"], "minimal"),
        (["클래식", "앤티크"], "vintage"),
        (["세일", "할인"], "bold"),
        ([], "minimal"),  # 빈 리스트
    ]
    
    print("=" * 50)
    print("템플릿 선택 테스트")
    print("=" * 50)
    
    for style_tags, expected in test_cases:
        result = select_template_with_score(style_tags)
        status = "✅" if result['template'] == expected else "❌"
        
        print(f"\n{status} style_tags: {style_tags}")
        print(f"   선택된 템플릿: {result['template']} (예상: {expected})")
        print(f"   점수: {result['score']}")
        print(f"   전체 점수: {result['all_scores']}")