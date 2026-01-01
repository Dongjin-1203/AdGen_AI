"""
Google Cloud Storage 이미지 업로드 유틸리티
개발: 로컬 파일 시스템 사용
배포: GCS 사용
"""
import os
from pathlib import Path
from google.cloud import storage
from config import UPLOAD_DIR

def upload_to_gcs(file_path: str, destination_blob_name: str) -> str:
    """
    GCS에 파일 업로드
    
    Args:
        file_path: 로컬 파일 경로
        destination_blob_name: GCS 내 경로 (예: user_id/filename.jpg)
    
    Returns:
        공개 URL
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    
    if not bucket_name:
        # GCS 미설정 시 로컬 URL 반환
        return f"/uploads/{destination_blob_name}"
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        blob.upload_from_filename(file_path)
        
        # 공개 URL 반환
        return f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
    except Exception as e:
        print(f"GCS upload error: {e}")
        # 에러 시 로컬 URL 반환
        return f"/uploads/{destination_blob_name}"

def get_storage_url(relative_path: str) -> str:
    """
    저장소 URL 생성
    
    Args:
        relative_path: 상대 경로 (예: user_id/filename.jpg)
    
    Returns:
        전체 URL
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    
    if bucket_name:
        return f"https://storage.googleapis.com/{bucket_name}/{relative_path}"
    else:
        return f"/uploads/{relative_path}"