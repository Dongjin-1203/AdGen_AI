"""
이미지 처리 유틸리티
배경 생성 관련 이미지 처리 함수 모음
"""
from PIL import Image
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# Instagram 비율 상수
# ==============================================================================

INSTAGRAM_RATIOS = {
    "4:5": (1080, 1350),   # Portrait (권장)
    "1:1": (1080, 1080),   # Square
    "16:9": (1080, 566),   # Landscape
}


# ==============================================================================
# 이미지 리사이즈 함수
# ==============================================================================

def resize_to_instagram_ratio(
    image: Image.Image,
    ratio: str = "4:5",
    maintain_aspect: bool = True
) -> Image.Image:
    """
    인스타그램 비율로 이미지 리사이즈
    
    Args:
        image: 입력 이미지
        ratio: 인스타그램 비율 ("4:5", "1:1", "16:9")
        maintain_aspect: 비율 유지 여부
        
    Returns:
        리사이즈된 이미지
        
    Example:
        >>> img = Image.open("photo.jpg")
        >>> resized = resize_to_instagram_ratio(img, ratio="4:5")
    """
    if ratio not in INSTAGRAM_RATIOS:
        raise ValueError(
            f"Invalid ratio '{ratio}'. Choose from: {list(INSTAGRAM_RATIOS.keys())}"
        )
    
    target_size = INSTAGRAM_RATIOS[ratio]
    
    if maintain_aspect:
        # 비율 유지 리사이즈
        image_aspect = image.width / image.height
        target_aspect = target_size[0] / target_size[1]
        
        if image_aspect > target_aspect:
            # 이미지가 타겟보다 넓음
            new_width = target_size[0]
            new_height = int(new_width / image_aspect)
        else:
            # 이미지가 타겟보다 높음
            new_height = target_size[1]
            new_width = int(new_height * image_aspect)
        
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 캔버스 생성 및 중앙 배치
        canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
        offset_x = (target_size[0] - new_width) // 2
        offset_y = (target_size[1] - new_height) // 2
        canvas.paste(
            resized, 
            (offset_x, offset_y), 
            resized if resized.mode == 'RGBA' else None
        )
        
        logger.info(f"Resized {image.size} → {target_size} (ratio: {ratio})")
        return canvas
    else:
        # 직접 리사이즈 (왜곡 가능)
        resized = image.resize(target_size, Image.Resampling.LANCZOS)
        logger.info(f"Resized to {target_size} (ratio: {ratio})")
        return resized


# ==============================================================================
# 배경 처리 함수
# ==============================================================================

def add_background_color(
    image: Image.Image,
    background_color: Tuple[int, int, int] = (255, 255, 255)
) -> Image.Image:
    """
    투명 이미지에 단색 배경 추가
    
    Args:
        image: 알파 채널이 있는 이미지
        background_color: RGB 배경색
        
    Returns:
        배경이 추가된 이미지
        
    Example:
        >>> img = Image.open("transparent.png")
        >>> with_bg = add_background_color(img, (255, 255, 255))
    """
    if image.mode != 'RGBA':
        logger.warning("Image doesn't have alpha channel, returning as-is")
        return image
    
    # 배경 생성
    background = Image.new('RGB', image.size, background_color)
    
    # 이미지 합성
    background.paste(image, (0, 0), image)
    
    logger.info(f"Added background color: RGB{background_color}")
    return background


# ==============================================================================
# 이미지 저장 함수
# ==============================================================================

def save_with_format(
    image: Image.Image,
    output_path: str,
    format: str = "PNG",
    quality: int = 95
) -> None:
    """
    지정된 포맷으로 이미지 저장
    
    Args:
        image: 저장할 이미지
        output_path: 저장 경로
        format: 이미지 포맷 (PNG, JPEG 등)
        quality: JPEG 압축 품질 (1-100)
        
    Example:
        >>> img = Image.open("photo.png")
        >>> save_with_format(img, "output.jpg", format="JPEG", quality=90)
    """
    format = format.upper()
    
    if format == "JPEG" and image.mode == 'RGBA':
        # RGBA → RGB 변환 (JPEG는 투명도 미지원)
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, (0, 0), image)
        rgb_image.save(output_path, format=format, quality=quality, optimize=True)
        logger.info(f"Saved JPEG (converted from RGBA): {output_path}")
    else:
        save_kwargs = {"format": format}
        if format == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        
        image.save(output_path, **save_kwargs)
        logger.info(f"Saved {format} image: {output_path}")


# ==============================================================================
# 이미지 정보 함수
# ==============================================================================

def get_image_info(image: Image.Image) -> dict:
    """
    이미지 메타데이터 추출
    
    Args:
        image: 입력 이미지
        
    Returns:
        메타데이터 딕셔너리
        
    Example:
        >>> img = Image.open("photo.jpg")
        >>> info = get_image_info(img)
        >>> print(info['width'], info['height'])
    """
    return {
        "size": image.size,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format,
        "aspect_ratio": round(image.width / image.height, 2)
    }


# ==============================================================================
# 추가 유틸리티 (선택)
# ==============================================================================

def validate_image_size(
    image: Image.Image,
    min_size: Tuple[int, int] = (256, 256),
    max_size: Tuple[int, int] = (4096, 4096)
) -> bool:
    """
    이미지 크기 검증
    
    Args:
        image: 검증할 이미지
        min_size: 최소 크기 (width, height)
        max_size: 최대 크기 (width, height)
        
    Returns:
        유효 여부
    """
    width, height = image.size
    min_w, min_h = min_size
    max_w, max_h = max_size
    
    if width < min_w or height < min_h:
        logger.warning(f"Image too small: {image.size} < {min_size}")
        return False
    
    if width > max_w or height > max_h:
        logger.warning(f"Image too large: {image.size} > {max_size}")
        return False
    
    return True