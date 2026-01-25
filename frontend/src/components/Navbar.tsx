'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/store';

export default function NavbarWithDropdown() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Link href="/dashboard" className="text-2xl font-bold text-blue-600 hover:text-blue-700 transition">
            AdGen AI
          </Link>
          
          <div className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className="text-gray-700 hover:text-blue-600 font-medium transition"
            >
              대시보드
            </Link>
            <Link
              href="/upload"
              className="text-gray-700 hover:text-blue-600 font-medium transition"
            >
              업로드
            </Link>
            <Link
              href="/gallery"
              className="text-gray-700 hover:text-blue-600 font-medium transition"
            >
              갤러리
            </Link>
            
            {/* 히스토리 드롭다운 */}
            <div 
              className="relative"
              onMouseEnter={() => setIsHistoryOpen(true)}
              onMouseLeave={() => setIsHistoryOpen(false)}
            >
              <button className="text-gray-700 hover:text-blue-600 font-medium transition flex items-center gap-1">
                히스토리
                <svg 
                  className={`w-4 h-4 transition-transform ${isHistoryOpen ? 'rotate-180' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* 드롭다운 메뉴 */}
              {isHistoryOpen && (
                <div className="absolute top-full left-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                  <Link
                    href="/history"
                    className="block px-4 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition"
                  >
                    🎨 VTON 히스토리
                  </Link>
                  <Link
                    href="/ad-history"
                    className="block px-4 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition border-t border-gray-100"
                  >
                    📋 광고 히스토리
                  </Link>
                </div>
              )}
            </div>
            
            {user && (
              <div className="flex items-center gap-4 pl-4 border-l border-gray-300">
                <span className="text-gray-600">{user.name}님</span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition"
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