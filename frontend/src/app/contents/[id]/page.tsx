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
  const [isEditing, setIsEditing] = useState(false);  // 🆕 수정 모드
  const [editData, setEditData] = useState({  // 🆕 수정 데이터
    product_name: '',
    category: '',
    color: '',
    price: 0
  });

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await contentAPI.getOne(contentId);
        setContent(response.data);
        // 수정 폼 초기값 설정
        setEditData({
          product_name: response.data.product_name || '',
          category: response.data.category || '',
          color: response.data.color || '',
          price: response.data.price || 0
        });
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

  // 🆕 삭제 핸들러
  const handleDelete = async () => {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    try {
      await contentAPI.delete(contentId);
      alert('삭제되었습니다!');
      router.push('/gallery');
    } catch (err: any) {
      alert('삭제 실패: ' + (err.response?.data?.detail || '알 수 없는 오류'));
    }
  };

  // 🆕 수정 핸들러
  const handleUpdate = async () => {
    try {
      const formData = new FormData();
      formData.append('product_name', editData.product_name);
      formData.append('category', editData.category);
      formData.append('color', editData.color);
      formData.append('price', editData.price.toString());
      formData.append('confirmed', 'true');
      
      await contentAPI.update(contentId, formData);
      
      // 성공하면 다시 조회
      const response = await contentAPI.getOne(contentId);
      setContent(response.data);
      setIsEditing(false);
      alert('수정되었습니다!');
    } catch (err: any) {
      alert('수정 실패: ' + (err.response?.data?.detail || '알 수 없는 오류'));
    }
  };

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
            <div className="w-20"></div>
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
              {isEditing ? (
                // 🆕 수정 모드
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">정보 수정</h2>
                  
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">상품명</label>
                    <input
                      type="text"
                      value={editData.product_name}
                      onChange={(e) => setEditData({...editData, product_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">카테고리</label>
                    <input
                      type="text"
                      value={editData.category}
                      onChange={(e) => setEditData({...editData, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">색상</label>
                    <input
                      type="text"
                      value={editData.color}
                      onChange={(e) => setEditData({...editData, color: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">가격</label>
                    <input
                      type="number"
                      value={editData.price}
                      onChange={(e) => setEditData({...editData, price: Number(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="flex gap-2 mt-6">
                    <button
                      onClick={handleUpdate}
                      className="flex-1 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
                    >
                      저장
                    </button>
                    <button
                      onClick={() => setIsEditing(false)}
                      className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition"
                    >
                      취소
                    </button>
                  </div>
                </div>
              ) : (
                // 보기 모드
                <>
                  <h2 className="text-3xl font-bold text-gray-900 mb-6">
                    {content.product_name}
                  </h2>

                  <div className="space-y-4">
                    <div className="flex items-start">
                      <span className="font-semibold text-gray-700 w-32">카테고리:</span>
                      <span className="text-gray-900">{content.category || '-'}</span>
                    </div>

                    <div className="flex items-start">
                      <span className="font-semibold text-gray-700 w-32">색상:</span>
                      <span className="text-gray-900">{content.color || '-'}</span>
                    </div>

                    {content.price && (
                      <div className="flex items-start">
                        <span className="font-semibold text-gray-700 w-32">가격:</span>
                        <span className="text-blue-600 font-bold text-2xl">
                          {content.price.toLocaleString()}원
                        </span>
                      </div>
                    )}

                    <div className="flex items-start">
                      <span className="font-semibold text-gray-700 w-32">업로드:</span>
                      <span className="text-gray-600 text-sm">
                        {content.created_at
                          ? new Date(content.created_at).toLocaleString('ko-KR')
                          : '-'}
                      </span>
                    </div>

                    <div className="flex items-start">
                      <span className="font-semibold text-gray-700 w-32">ID:</span>
                      <span className="text-gray-500 text-xs font-mono">
                        {content.content_id}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* 액션 버튼들 */}
            {!isEditing && (
              <div className="space-y-3">
                {/* 수정 버튼 */}
                <button
                  onClick={() => setIsEditing(true)}
                  className="w-full py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  정보 수정
                </button>

                {/* 삭제 버튼 */}
                <button
                  onClick={handleDelete}
                  className="w-full py-3 bg-red-100 text-red-700 rounded-lg font-medium hover:bg-red-200 transition flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  삭제
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}