"""
인스타그램 광고 템플릿 라이브러리
1080×1080px 정사각형 포맷
"""

AD_TEMPLATES = {
    "minimal": {
        "name": "Minimal Clean",
        "description": "화이트 배경, 상품 중앙 배치, 하단 텍스트",
        "colors": ["#FFFFFF", "#000000", "#F5F5F5"],
        "best_for": ["미니멀", "모던", "심플", "깔끔", "현대적"],
        "html": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            width: 1080px;
            height: 1080px;
            background: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', 'Noto Sans KR', sans-serif;
        }
        .wrapper {
            width: 100%;
            height: 100%;
            padding: 80px;
            display: flex;
            flex-direction: column;
        }
        .image-container {
            flex: 7;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #F8F9FA;
            border-radius: 30px;
            padding: 40px;
        }
        .image-container img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        .text-container {
            flex: 3;
            padding-top: 50px;
        }
        .brand {
            font-size: 20px;
            color: #999;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 15px;
        }
        .headline {
            font-size: 56px;
            font-weight: 300;
            color: #111;
            line-height: 1.2;
            letter-spacing: -1px;
        }
        .discount {
            font-size: 72px;
            font-weight: 700;
            color: #000;
            margin: 30px 0 20px 0;
        }
        .period {
            font-size: 18px;
            color: #666;
            letter-spacing: 1px;
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="image-container">
            <img src="{{IMAGE_URL}}" alt="Product">
        </div>
        <div class="text-container">
            <div class="brand">{{BRAND}}</div>
            <h1 class="headline">{{HEADLINE}}</h1>
            <div class="discount">{{DISCOUNT}}</div>
            <div class="period">{{PERIOD}}</div>
        </div>
    </div>
</body>
</html>"""
    },
    
    "bold": {
        "name": "Bold Impact",
        "description": "빨간 배경, 강렬한 대비, 임팩트 있는 텍스트",
        "colors": ["#E74C3C", "#FFFFFF", "#2C3E50"],
        "best_for": ["대담한", "강렬한", "임팩트", "세일", "할인"],
        "html": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            width: 1080px;
            height: 1080px;
            background: #E74C3C;
            padding: 60px;
            font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', sans-serif;
        }
        .headline {
            font-size: 64px;
            font-weight: 900;
            color: white;
            margin-bottom: 30px;
            line-height: 1.1;
            text-transform: uppercase;
            letter-spacing: -2px;
            text-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        .image-box {
            background: white;
            border-radius: 30px;
            padding: 50px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            height: 650px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .image-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        .bottom {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-top: 30px;
            color: white;
        }
        .event-text {
            font-size: 28px;
            font-weight: 600;
        }
        .discount-badge {
            background: white;
            color: #E74C3C;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 32px;
            font-weight: 900;
        }
    </style>
</head>
<body>
    <div class="headline">{{HEADLINE}}</div>
    <div class="image-box">
        <img src="{{IMAGE_URL}}" alt="Product">
    </div>
    <div class="bottom">
        <div class="event-text">{{EVENT_NAME}}</div>
        <div class="discount-badge">{{DISCOUNT}}</div>
    </div>
</body>
</html>"""
    },
    
    "vintage": {
        "name": "Vintage Sepia",
        "description": "세피아 톤, 레트로 감성, 데코 테두리",
        "colors": ["#D4A574", "#8B7355", "#F5E6D3"],
        "best_for": ["빈티지", "레트로", "클래식", "앤티크", "옛날"],
        "html": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            width: 1080px;
            height: 1080px;
            background: linear-gradient(135deg, #f5e6d3 0%, #d4a574 100%);
            font-family: Georgia, 'Playfair Display', serif;
            padding: 60px;
        }
        .frame {
            border: 15px solid #8B7355;
            padding: 60px;
            background: rgba(255, 255, 255, 0.9);
            height: 100%;
            display: flex;
            flex-direction: column;
            box-shadow: inset 0 0 30px rgba(0,0,0,0.1);
        }
        .image-area {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 40px;
        }
        .image-area img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            filter: sepia(30%) contrast(90%);
            border-radius: 10px;
        }
        .text-area {
            text-align: center;
        }
        .headline {
            font-size: 52px;
            font-weight: 700;
            color: #5D4E37;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .discount {
            font-size: 56px;
            color: #8B7355;
            font-weight: 700;
        }
        .period {
            font-size: 20px;
            color: #8B7355;
            margin-top: 20px;
            letter-spacing: 2px;
        }
    </style>
</head>
<body>
    <div class="frame">
        <div class="image-area">
            <img src="{{IMAGE_URL}}" alt="Product">
        </div>
        <div class="text-area">
            <h1 class="headline">{{HEADLINE}}</h1>
            <div class="discount">{{DISCOUNT}}</div>
            <div class="period">{{PERIOD}}</div>
        </div>
    </div>
</body>
</html>"""
    }
}


def get_template(template_name: str) -> dict:
    """
    템플릿 가져오기
    
    Args:
        template_name: 'minimal', 'bold', 'vintage'
    
    Returns:
        템플릿 정보 dict
    """
    return AD_TEMPLATES.get(template_name, AD_TEMPLATES["minimal"])


def list_templates() -> list:
    """
    사용 가능한 모든 템플릿 목록
    
    Returns:
        템플릿 이름 리스트
    """
    return list(AD_TEMPLATES.keys())