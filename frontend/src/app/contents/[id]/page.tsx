'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { contentAPI } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { Content } from '@/types';
import Navbar from '@/components/Navbar';

export default function ContentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { user } = useAuthStore();
  const contentId = params.id as string;

  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  useEffect(() => {
    const fetchContent = async () => {
      if (!user || !contentId) return;

      try {
        const response = await contentAPI.getOne(contentId);
        setContent(response.data);
      } catch (err) {
        setError('콘텐츠를 불러오는데 실패했습니다.');
        console.error('Fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [user, contentId]);

  if (!user) {
    return null;
  }

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <p className="text-center text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div>
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
            {error || '콘텐츠를 찾을 수 없습니다.'}
          </div>
          <button
            onClick={() => router.push('/gallery')}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            갤러리로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navbar />

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* 뒤로가기 버튼 */}
        <button
          onClick={() => router.push('/gallery')}
          className="mb-6 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          ← 갤러리로 돌아가기
        </button>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* 이미지 영역 */}
          <div className="relative w-full bg-gray-200">
            <img
              src={`http://localhost:8000${content.original_image_url}`}
              alt={content.product_name || '이미지'}
              className="w-full h-auto"
            />
          </div>

          {/* 정보 영역 */}
          <div className="p-6">
            <h1 className="text-3xl font-bold mb-4">
              {content.product_name || '제목 없음'}
            </h1>

            {/* 가격 */}
            {content.price && (
              <p className="text-2xl font-bold text-blue-600 mb-6">
                {content.price.toLocaleString()}원
              </p>
            )}

            {/* 메타데이터 */}
            <div className="space-y-4">
              {content.category && (
                <div className="flex gap-2">
                  <span className="font-semibold text-gray-700 w-24">카테고리:</span>
                  <span className="text-gray-600">{content.category}</span>
                </div>
              )}

              {content.color && (
                <div className="flex gap-2">
                  <span className="font-semibold text-gray-700 w-24">색상:</span>
                  <span className="text-gray-600">{content.color}</span>
                </div>
              )}

              {content.caption && (
                <div>
                  <span className="font-semibold text-gray-700 block mb-2">설명:</span>
                  <p className="text-gray-600 whitespace-pre-wrap">{content.caption}</p>
                </div>
              )}

              <div className="flex gap-2">
                <span className="font-semibold text-gray-700 w-24">업로드:</span>
                <span className="text-gray-600">
                  {new Date(content.created_at).toLocaleDateString('ko-KR')}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}