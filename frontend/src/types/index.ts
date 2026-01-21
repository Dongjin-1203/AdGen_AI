export interface User {
  user_id: string;
  email: string;
  name: string;
  phone: string;
  created_at: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
  phone: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Content {
  content_id: string;
  user_id: string;
  product_name: string;
  category: string;
  color: string;
  price: number;
  thumbnail_url: string;
  image_url: string;
  created_at: string;
}

export interface History {
  history_id: string;
  content_id: string;
  user_id: string;
  style: string;
  prompt?: string;              // Optional - 사용자 추가 프롬프트
  result_url: string;           // 생성된 이미지 URL
  processing_time: number;      // 처리 시간 (초)
  created_at: string;           // 생성 일시
  
  // 백엔드에서 JOIN으로 가져오는 추가 정보
  original_image_url?: string;  // 원본 이미지 URL
  product_name?: string;        // 제품명
}