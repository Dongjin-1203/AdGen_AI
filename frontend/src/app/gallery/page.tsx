'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { contentAPI } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { Content } from '@/types';
import Navbar from '@/components/Navbar';

export default function GalleryPage() {
  const router = useRouter();
  const { user } = useAuthStore();

  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  useEffect(() => {
    const fetchContents = async () => {
      if (!user) return;

      try {
        const response = await contentAPI.getAll();
        setContents(response.data);
      } catch (err) {
        setError('콘텐츠를 불러오는데 실패했습니다.');
        console.error('Fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchContents();
  }, [user]);

  if (!user) {
    return null;
  }

  return (
    <div>
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">내 갤러리</h1>

        {/* 로딩 상태 */}
        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-600">로딩 중...</p>
          </div>
        )}

        {/* 에러 상태 */}
        {error && (
          <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* 빈 상태 */}
        {!loading && contents.length === 0 && (
          <div className="text-center py-12">
            <p className="text-6xl mb-4">📷</p>
            <p className="text-gray-600 mb-4">
              아직 업로드한 이미지가 없습니다.
            </p>
            <button
              onClick={() => router.push('/upload')}
              className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              이미지 업로드하기
            </button>
          </div>
        )}

        {/* 그리드 레이아웃 */}
        {!loading && contents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {contents.map((content) => (
              <div
                key={content.content_id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition cursor-pointer"
                onClick={() => router.push(`/contents/${content.content_id}`)}
              >
                {/* 이미지 영역 */}
                <div className="relative h-48 bg-gray-200">
                  <img
                    src={`http://localhost:8000${content.thumbnail_url || content.original_image_url}`}
                    alt={content.product_name || '이미지'}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* 카드 정보 영역 */}
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-2 truncate">
                    {content.product_name || '제목 없음'}
                  </h3>

                  {/* 메타데이터 (카테고리, 색상) */}
                  <div className="flex gap-2 mb-2 text-sm text-gray-600">
                    {content.category && (
                      <span className="px-2 py-1 bg-gray-100 rounded">
                        {content.category}
                      </span>
                    )}
                    {content.color && (
                      <span className="px-2 py-1 bg-gray-100 rounded">
                        {content.color}
                      </span>
                    )}
                  </div>

                  {/* 가격 */}
                  {content.price && (
                    <p className="text-xl font-bold text-blue-600">
                      {content.price.toLocaleString()}원
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}