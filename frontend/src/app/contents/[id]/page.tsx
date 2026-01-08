'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { contentAPI, API_URL } from '@/lib/api';
import { Content } from '@/types';
import Navbar from '@/components/Navbar';

export default function ContentDetail() {
  const params = useParams();
  const router = useRouter();
  const contentId = params.id as string;

  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await contentAPI.getOne(contentId);
        setContent(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || '콘텐츠를 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    if (contentId) {
      fetchContent();
    }
  }, [contentId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-screen">
          <p className="text-xl">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-screen">
          <p className="text-xl text-red-600">{error || '콘텐츠를 찾을 수 없습니다.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <button
          onClick={() => router.push('/gallery')}
          className="mb-6 text-blue-600 hover:text-blue-800 flex items-center"
        >
          ← 갤러리로 돌아가기
        </button>

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="aspect-square relative bg-gray-100">
            <img
              src={
                content.image_url?.startsWith('http')
                  ? content.image_url
                  : `${API_URL}${content.image_url}`
              }
              alt={content.product_name}
              className="w-full h-full object-contain"
            />
          </div>

          <div className="p-6">
            <h1 className="text-3xl font-bold mb-4">{content.product_name}</h1>
            
            <div className="space-y-3">
              <div className="flex">
                <span className="font-semibold w-24">카테고리:</span>
                <span>{content.category || '-'}</span>
              </div>
              <div className="flex">
                <span className="font-semibold w-24">색상:</span>
                <span>{content.color || '-'}</span>
              </div>
              <div className="flex">
                <span className="font-semibold w-24">가격:</span>
                <span className="text-blue-600 font-bold text-xl">
                  {content.price?.toLocaleString() || '0'}원
                </span>
              </div>
              <div className="flex">
                <span className="font-semibold w-24">업로드:</span>
                <span>
                  {content.created_at 
                    ? new Date(content.created_at).toLocaleString('ko-KR')
                    : '-'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}