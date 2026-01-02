export interface User{
    user_id: string;
    email: string;
    name: string;
    phone?: string;
    created_at: string;
}

export interface Content {
  content_id: string;
  user_id: string;
  original_image_url: string;
  thumbnail_url?: string;
  product_name?: string;
  category?: string;
  color?: string;
  price?: number;
  caption?: string;
  created_at: string;
}

export interface LoginRequest{
    username: string;
    password: string;
}

export interface SignupRequest{
    email: string;
    name: string;
    password: string;
    phone?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}