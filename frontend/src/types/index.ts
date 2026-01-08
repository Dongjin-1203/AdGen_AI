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
  image_url: string;        // ← 추가!
  created_at: string;
}