import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';

interface AuthStore {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,  
      user: null,
      
      // 로그인 시 token + user 함께 저장
      setAuth: (token, user) => set({ token, user }),
      
      // user만 업데이트 (필요시)
      setUser: (user) => set({ user }),
      
      // 로그아웃 시 token + user 모두 삭제
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
);