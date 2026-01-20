'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { contentAPI, API_URL } from '@/lib/api';
import { Content } from '@/types';

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
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">로딩 중...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <p className="text-xl text-red-600 mb-4">
              {error || '콘텐츠를 찾을 수 없습니다.'}
            </p>
            <button
              onClick={() => router.push('/gallery')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              갤러리로 돌아가기
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.push('/gallery')}
              className="text-gray-600 hover:text-gray-900 transition flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              갤러리로
            </button>
            <h1 className="text-xl font-bold text-gray-900">콘텐츠 상세</h1>
            <div className="w-20"></div> {/* 공간 확보 */}
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 왼쪽: 이미지 */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
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
            </div>

            {/* 썸네일 (있는 경우) */}
            {content.thumbnail_url && content.thumbnail_url !== content.image_url && (
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">썸네일</h3>
                <img
                  src={
                    content.thumbnail_url?.startsWith('http')
                      ? content.thumbnail_url
                      : `${API_URL}${content.thumbnail_url}`
                  }
                  alt="Thumbnail"
                  className="w-32 h-32 object-cover rounded"
                />
              </div>
            )}
          </div>

          {/* 오른쪽: 정보 */}
          <div className="space-y-6">
            {/* 기본 정보 */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                {content.product_name}
              </h2>

              <div className="space-y-4">
                {/* 카테고리 */}
                <div className="flex items-start">
                  <span className="font-semibold text-gray-700 w-32">카테고리:</span>
                  <span className="text-gray-900">{content.category || '-'}</span>
                </div>

                {/* 색상 */}
                <div className="flex items-start">
                  <span className="font-semibold text-gray-700 w-32">색상:</span>
                  <span className="text-gray-900">{content.color || '-'}</span>
                </div>

                {/* 가격 */}
                {content.price && (
                  <div className="flex items-start">
                    <span className="font-semibold text-gray-700 w-32">가격:</span>
                    <span className="text-blue-600 font-bold text-2xl">
                      {content.price.toLocaleString()}원
                    </span>
                  </div>
                )}

                {/* 업로드 일시 */}
                <div className="flex items-start">
                  <span className="font-semibold text-gray-700 w-32">업로드:</span>
                  <span className="text-gray-600 text-sm">
                    {content.created_at
                      ? new Date(content.created_at).toLocaleString('ko-KR')
                      : '-'}
                  </span>
                </div>

                {/* 콘텐츠 ID */}
                <div className="flex items-start">
                  <span className="font-semibold text-gray-700 w-32">ID:</span>
                  <span className="text-gray-500 text-xs font-mono">
                    {content.content_id}
                  </span>
                </div>
              </div>
            </div>

            {/* 액션 버튼들 */}
            <div className="space-y-3">
              {/* 배경 생성 버튼 - 메인 CTA */}
              <button
                onClick={() => router.push(`/generate/${contentId}`)}
                className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition shadow-lg flex items-center justify-center gap-2"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                🎨 AI 배경 생성하기
              </button>

              {/* 수정 버튼 */}
              <button
                onClick={() => alert('수정 기능은 준비 중입니다!')}
                className="w-full py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                정보 수정
              </button>

              {/* 삭제 버튼 */}
              <button
                onClick={() => {
                  if (confirm('정말 삭제하시겠습니까?')) {
                    alert('삭제 기능은 준비 중입니다!');
                  }
                }}
                className="w-full py-3 bg-red-100 text-red-700 rounded-lg font-medium hover:bg-red-200 transition flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                삭제
              </button>
            </div>

            {/* 안내 메시지 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">💡 다음 단계</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• [AI 배경 생성하기]를 클릭하여 새로운 배경을 만들어보세요</li>
                <li>• 다양한 스타일과 비율로 여러 버전을 생성할 수 있습니다</li>
                <li>• 생성된 이미지는 바로 다운로드 가능합니다</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}