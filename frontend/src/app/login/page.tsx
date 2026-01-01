'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authAPI } from '@/lib/api';
import { useAuthStore } from '@/lib/store';

export default function LoginPage() {
    // Hooks
    const router = useRouter();
    const { setAuth } = useAuthStore();

    // State
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // handleSubmit 함수
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        // 로딩 시작
        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            // 로그인 API 호출
            const response = await authAPI.login(formData);
            const token = response.data.access_token;

            localStorage.setItem('token', token);
            const userResponse = await authAPI.getMe();
            
            // 전역 상태 저장
            setAuth(userResponse.data, token);
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || '로그인에 실패했습니다.');
            console.error('Login error:', err);
        } finally {
            setLoading(false);
        };
    }; return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
            <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md">
                <h1 className="text-2xl font-bold mb-6 text-center">
                    로그인
                    {error && (
                        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
                            {error}
                        </div>
                    )}
                </h1>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block mb-2 text-sm font-medium text-gray-700">
                            이메일
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="example@email.com"
                            />
                        </label>
                    </div>
                    <div>
                        <label className="block mb-2 text-sm font-medium text-gray-700">
                            비밀번호
                        </label>
                        <input
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="비밀번호 입력"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                    {loading ? '로그인 중...' : '로그인'}
                    </button>
                    <div className="text-center text-sm text-gray-600">
                        아직 계정이 없으신가요?{' '}
                        <Link href="/signup" className="text-blue-500 hover:underline">
                            회원가입
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    )
};