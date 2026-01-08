'use client';

import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { useEffect } from 'react';

export default function Home() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);

  useEffect(() => {
    // 이미 로그인된 경우 대시보드로
    if (user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-blue-600 mb-4">AdGen AI</h1>
        <p className="text-gray-600 mb-8">
          소규모 패션 쇼핑몰을 위한 AI 광고 자동 생성 서비스
        </p>
        <div className="space-x-4">
          <button
            onClick={() => router.push('/login')}
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            로그인
          </button>
          <button
            onClick={() => router.push('/signup')}
            className="inline-block bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700"
          >
            회원가입
          </button>
        </div>
      </div>
    </div>
  );
}