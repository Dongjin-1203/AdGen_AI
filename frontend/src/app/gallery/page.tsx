'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { contentAPI, API_URL } from '@/lib/api';
import { Content } from '@/types';
import Navbar from '@/components/Navbar';

export default function Gallery() {
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const fetchContents = async () => {
      try {
        const response = await contentAPI.getAll();
        setContents(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || '콘텐츠를 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchContents();
  }, []);

  const handleCardClick = (contentId: string) => {
    router.push(`/contents/${contentId}`);
  };

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

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-screen">
          <p className="text-xl text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">갤러리</h1>
        
        {contents.length === 0 ? (
          <p className="text-center text-gray-500">아직 업로드된 콘텐츠가 없습니다.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {contents.map((content) => (
              <div
                key={content.content_id}
                onClick={() => handleCardClick(content.content_id)}
                className="bg-white rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
              >
                <div className="aspect-square relative bg-gray-100">
                  <img
                    src={`${API_URL}${content.thumbnail_url}`}
                    alt={content.product_name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-2">{content.product_name}</h3>
                  <p className="text-gray-600 text-sm mb-1">카테고리: {content.category || '-'}</p>
                  <p className="text-gray-600 text-sm mb-1">색상: {content.color || '-'}</p>
                  <p className="text-blue-600 font-bold">
                    {content.price?.toLocaleString() || '0'}원
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}