'use client';

import Link from 'next/link';

export default function Home() {
    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
            <div className="text-center space-y-8">
                <h1 className="text-5xl font-bold text-gray-900">AdGen AI</h1>
                <p className="text-xl text-gray-600">1분 만에 인스타그램 광고 완성</p>
                <div className="flex gap-4 justify-center">
                    <Link href="/login" className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                        로그인
                    </Link>
                    <Link href="/signup" className="px-6 py-3 border border-blue-500 text-blue-500 rounded-lg hover:bg-blue-50">
                        회원가입
                    </Link>
                </div>
            </div>
        </div>
    )
};
