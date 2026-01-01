'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import Navbar from '@/components/Navbar';

export default function DashboardPage() {
    const router = useRouter();
    const { user } = useAuthStore();

    useEffect(() => {
        if (!user) {
            router.push('/login');
        }
    }, [user, router]);
        if (!user) {
            return null;
        }
    return (
        <div>
            <Navbar />
            <div className="max-w-7xl mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold mb-6">대시보드</h1>

                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 className="text-xl font-semibold mb-2">
                        {user.name}님, 환영합니다!
                    </h2>
                    <p className="text-gray-600">
                        AdGen_AI에 오신 것을 환영합니다.
                    </p>
                </div>
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-4">내 정보</h3>

                    <div className="space-y-3">
                        <div className="flex gap-2">
                            <span className="font-semibold text-gray-700">이메일:</span>
                            <span className="text-gray-600">{user.email}</span>
                        </div>
                        <div className="flex gap-2">
                            <span className="font-semibold text-gray-700">이름:</span>
                            <span className="text-gray-600">{user.name}</span>
                        </div>
                        {user.phone && (
                            <div className="flex gap-2">
                                <span className="font-semibold text-gray-700">전화번호:</span>
                                <span className="text-gray-600">{user.phone}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}