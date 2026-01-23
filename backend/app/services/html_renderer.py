"""
HTML → PNG 이미지 렌더링 서비스
Playwright를 사용하여 광고 HTML을 고품질 이미지로 변환
"""
from playwright.async_api import async_playwright
import uuid
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HTMLRenderer:
    """
    HTML을 PNG 이미지로 렌더링
    Playwright 사용
    """
    
    def __init__(self):
        """초기화"""
        self.viewport_width = 1080
        self.viewport_height = 1080
        self.device_scale_factor = 2  # 고해상도 (2x)
    
    async def render_to_image(
        self,
        html: str,
        output_filename: Optional[str] = None,
        output_dir: str = "/tmp"
    ) -> str:
        """
        HTML → PNG 이미지 변환
        
        Args:
            html: HTML 문자열
            output_filename: 출력 파일명 (None이면 자동 생성)
            output_dir: 출력 디렉토리 (기본값: /tmp)
        
        Returns:
            output_path: 생성된 이미지 파일 경로
        """
        
        # 파일명 생성
        if not output_filename:
            output_filename = f"ad_{uuid.uuid4()}.png"
        
        # 확장자 확인
        if not output_filename.endswith('.png'):
            output_filename += '.png'
        
        output_path = os.path.join(output_dir, output_filename)
        
        logger.info(f"[HTMLRenderer] Starting render: {output_filename}")
        
        try:
            async with async_playwright() as p:
                # 브라우저 실행 (headless)
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                logger.info("[HTMLRenderer] Browser launched")
                
                # 페이지 생성
                page = await browser.new_page(
                    viewport={
                        'width': self.viewport_width,
                        'height': self.viewport_height
                    },
                    device_scale_factor=self.device_scale_factor
                )
                
                logger.info("[HTMLRenderer] Page created")
                
                # HTML 로드
                await page.set_content(html, wait_until='networkidle')
                
                logger.info("[HTMLRenderer] HTML loaded")
                
                # 폰트 로딩 대기 (중요!)
                # 웹폰트가 있을 경우 로딩 시간 필요
                await page.wait_for_timeout(2000)  # 2초 대기
                
                logger.info("[HTMLRenderer] Fonts loaded")
                
                # 스크린샷
                await page.screenshot(
                    path=output_path,
                    type='png',
                    full_page=False  # viewport 크기만큼만
                )
                
                logger.info(f"[HTMLRenderer] Screenshot saved: {output_path}")
                
                # 브라우저 종료
                await browser.close()
                
                logger.info("[HTMLRenderer] ✅ Render completed")
            
            return output_path
            
        except Exception as e:
            logger.error(f"[HTMLRenderer] ❌ Error: {e}", exc_info=True)
            
            # 임시 파일 정리
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            
            raise Exception(f"HTML 렌더링 실패: {str(e)}")
    
    async def render_to_bytes(
        self,
        html: str
    ) -> bytes:
        """
        HTML → PNG 바이트로 변환 (파일 저장 없이)
        
        Args:
            html: HTML 문자열
        
        Returns:
            image_bytes: PNG 이미지 바이트
        """
        
        logger.info("[HTMLRenderer] Starting render to bytes")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                page = await browser.new_page(
                    viewport={
                        'width': self.viewport_width,
                        'height': self.viewport_height
                    },
                    device_scale_factor=self.device_scale_factor
                )
                
                await page.set_content(html, wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # 바이트로 스크린샷
                image_bytes = await page.screenshot(
                    type='png',
                    full_page=False
                )
                
                await browser.close()
                
                logger.info("[HTMLRenderer] ✅ Render to bytes completed")
                
                return image_bytes
            
        except Exception as e:
            logger.error(f"[HTMLRenderer] ❌ Error: {e}", exc_info=True)
            raise Exception(f"HTML 렌더링 실패: {str(e)}")


# 테스트용
async def test_renderer():
    """렌더러 테스트"""
    
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                width: 1080px;
                height: 1080px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
            }
            .container {
                text-align: center;
                color: white;
            }
            h1 {
                font-size: 72px;
                margin: 0;
                font-weight: 900;
            }
            p {
                font-size: 32px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>테스트 광고</h1>
            <p>Playwright 렌더링 성공! ✨</p>
        </div>
    </body>
    </html>
    """
    
    renderer = HTMLRenderer()
    output_path = await renderer.render_to_image(
        html=test_html,
        output_filename="test_ad.png"
    )
    
    print(f"✅ 렌더링 완료: {output_path}")
    print(f"파일 크기: {os.path.getsize(output_path)} bytes")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_renderer())


# 싱글톤 패턴으로 렌더러 제공
_renderer_instance = None

def get_renderer() -> HTMLRenderer:
    """
    HTMLRenderer 인스턴스 가져오기 (싱글톤)
    """
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = HTMLRenderer()
    return _renderer_instance