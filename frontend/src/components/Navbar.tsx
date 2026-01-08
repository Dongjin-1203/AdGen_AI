'use client';

import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

export default function Navbar() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
    logout();
    router.push('/login');
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <h1 
            className="text-2xl font-bold text-blue-600 cursor-pointer"
            onClick={() => router.push('/dashboard')}
          >
            AdGen_AI
          </h1>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-gray-700 hover:text-blue-600"
            >
              대시보드
            </button>
            <button
              onClick={() => router.push('/upload')}
              className="text-gray-700 hover:text-blue-600"
            >
              업로드
            </button>
            <button
              onClick={() => router.push('/gallery')}
              className="text-gray-700 hover:text-blue-600"
            >
              갤러리
            </button>
            {/* 테스트 버튼 제거 */}
            
            {user && (
              <div className="flex items-center space-x-4">
                <span className="text-gray-600">{user.name}님</span>
                <button
                  onClick={handleLogout}
                  className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                >
                  로그아웃
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}