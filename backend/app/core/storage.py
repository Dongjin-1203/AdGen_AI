"""
GCS Storage Helper Functions
업데이트: download_from_gcs, upload_to_gcs 추가
"""

from google.cloud import storage
from google.oauth2 import service_account
from config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_storage_client = None

def get_storage_client():
    """GCS 클라이언트 가져오기 (싱글톤)"""
    global _storage_client
    
    if _storage_client is None:
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            _storage_client = storage.Client(credentials=credentials)
        else:
            _storage_client = storage.Client()
        
        logger.info("GCS Storage 클라이언트 초기화 완료")
    
    return _storage_client


def download_from_gcs(gcs_path: str, bucket_name: Optional[str] = None) -> bytes:
    """
    GCS에서 파일 다운로드
    
    Args:
        gcs_path: GCS 경로 (예: uploads/xxx.jpg)
        bucket_name: 버킷명 (기본값: settings.GCS_BUCKET_NAME)
    
    Returns:
        파일 바이트 데이터
    """
    try:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        
        logger.info(f"Downloading from GCS: gs://{bucket_name}/{gcs_path}")
        
        data = blob.download_as_bytes()
        
        logger.info(f"Downloaded {len(data)} bytes")
        return data
        
    except Exception as e:
        logger.error(f"Error downloading from GCS: {e}", exc_info=True)
        raise


def upload_to_gcs(
    file_data: bytes,
    destination_path: str,
    content_type: str = "image/jpeg",
    bucket_name: Optional[str] = None
) -> str:
    """
    GCS에 파일 업로드
    
    Args:
        file_data: 업로드할 파일 데이터
        destination_path: GCS 경로 (예: ai_generated/xxx.jpg)
        content_type: 파일 타입
        bucket_name: 버킷명 (기본값: settings.GCS_BUCKET_NAME)
    
    Returns:
        공개 URL (https://storage.googleapis.com/...)
    """
    try:
        bucket_name = bucket_name or settings.GCS_BUCKET_NAME
        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_path)
        
        logger.info(f"Uploading to GCS: gs://{bucket_name}/{destination_path}")
        
        blob.upload_from_string(file_data, content_type=content_type)
        
        # 공개 URL 생성
        public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_path}"
        
        logger.info(f"Upload complete: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Error uploading to GCS: {e}", exc_info=True)
        raise