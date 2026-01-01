import axios from 'axios';
import { LoginRequest, SignupRequest, Token, User, Content } from '@/types';
const API_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');

    if (token){
        config.headers.Authorization = `Bearer ${token}`;
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

export default api;