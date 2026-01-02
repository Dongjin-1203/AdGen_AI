import axios from 'axios';
import { User, SignupRequest, Token, Content } from '@/types';

// 백엔드 URL 직접 지정
export const API_URL = 'https://adgen-backend-613605394208.asia-northeast3.run.app';

console.log('🔍 API_URL:', API_URL);

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  // 브라우저 환경에서만 localStorage 접근
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const authAPI = {
  signup: (data: SignupRequest) => api.post<User>('/api/auth/signup', data),
  login: (data: FormData) => api.post<Token>('/api/auth/login', data),
  getMe: () => api.get<User>('/api/auth/me'),
};

export const contentAPI = {
  upload: (formData: FormData) => api.post<Content>('/api/contents/upload', formData),
  getAll: () => api.get<Content[]>('/api/contents'),
  getOne: (id: string) => api.get<Content>(`/api/contents/${id}`),
};