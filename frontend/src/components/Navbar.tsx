'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

export default function Navbar() {
    const router = useRouter();
    const { user, logout } = useAuthStore();

    const handleLogout = () => {
        logout();
        router.push('/login');
    };
    return (
        <nav className="bg-white shadow-md py-4">
            <div className="max-w-7xl mx-auto px-4 flex justify-between items-center">
                <Link href="/" className="text-2xl font-bold text-blue-500">
                    AdGen_AI
                </Link>

                {user ? (
                    <div className="flex items-center gap-6">
                        <Link href="/dashboard" className="text-gray-700 hover:text-blue-500">
                            대시보드
                        </Link>
                        <Link href="/upload" className="text-gray-700 hover:text-blue-500">
                            업로드
                        </Link>
                        <Link href="/gallery" className="text-gray-700 hover:text-blue-500">
                            갤러리
                        </Link>
                        <span className="text-gray-600">
                            {user.name}님
                        </span>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                        >
                            로그아웃
                        </button>
                    </div>
                ) : (
                    <div className="flex gap-4">
                        <Link href="/login" className="px-4 py-2 text-blue-500 border border-blue-500 rounded hover:bg-blue-50">
                            로그인
                        </Link>
                        <Link href="/signup" className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                            회원가입
                        </Link>
                    </div>
                )}
            </div>
        </nav>
    );
}