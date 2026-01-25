'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, API_URL } from '@/lib/api';

interface AdCopyData {
  headline: string;
  discount?: string;
  period?: string;
  brand?: string;
}

interface AdCopyDetail {
  ad_copy_id: string;
  template_used: string;
  ad_copy_data: AdCopyData;
  html_content: string;
  final_image_url: string;
  created_at: string;
  processing_time: number;
}

export default function AdCopyDetailPage({ params }: { params: { ad_copy_id: string } }) {
  const router = useRouter();
  const { ad_copy_id } = params;

  const [adCopy, setAdCopy] = useState<AdCopyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showHtmlCode, setShowHtmlCode] = useState(false);

  // 상세 정보 조회
  useEffect(() => {
    fetchAdCopyDetail();
  }, [ad_copy_id]);

  const fetchAdCopyDetail = async () => {
    try {
      const response = await api.get(`/api/v1/ad-copy-history/${ad_copy_id}`);
      setAdCopy(response.data);
    } catch (error: any) {
      console.error('상세 조회 실패:', error);
      if (error.response?.status === 401) {
        alert('인증이 만료되었습니다. 다시 로그인해주세요.');
        router.push('/login');
      } else if (error.response?.status === 404) {
        setError('광고를 찾을 수 없습니다.');
      } else {
        setError('상세 정보를 불러올 수 없습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  // 이미지 다운로드
  const downloadImage = async () => {
    if (!adCopy) return;

    try {
      const response = await api.get(
        `/api/v1/ad-copy-history/${ad_copy_id}/download`,
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'image/png' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ad_${adCopy.template_used}_${ad_copy_id.substring(0, 8)}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      console.log('✅ 이미지 다운로드 완료');
    } catch (error: any) {
      console.error('❌ 다운로드 실패:', error);
      alert('이미지 다운로드에 실패했습니다.');
    }
  };

  // HTML 다운로드
  const downloadHTML = () => {
    if (!adCopy) return;

    const blob = new Blob([adCopy.html_content], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ad_${adCopy.template_used}_${ad_copy_id.substring(0, 8)}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    console.log('✅ HTML 다운로드 완료');
  };

  // HTML 코드 복사
  const copyHtmlCode = () => {
    if (!adCopy) return;

    navigator.clipboard.writeText(adCopy.html_content);
    alert('HTML 코드가 복사되었습니다!');
  };

  // 삭제
  const handleDelete = async () => {
    if (!confirm('정말 삭제하시겠습니까?')) {
      return;
    }

    try {
      await api.delete(`/api/v1/ad-copy-history/${ad_copy_id}`);
      alert('삭제되었습니다.');
      router.push('/ad-history');
    } catch (error: any) {
      console.error('❌ 삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  // 템플릿 한글 이름
  const getTemplateName = (template: string) => {
    const names: { [key: string]: string } = {
      minimal: 'Minimal - 미니멀한 디자인',
      bold: 'Bold - 강렬한 디자인',
      vintage: 'Vintage - 빈티지 디자인',
    };
    return names[template] || template;
  };

  // 로딩
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  // 에러
  if (error || !adCopy) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl text-red-600 mb-4">{error || '데이터를 찾을 수 없습니다.'}</p>
          <button
            onClick={() => router.push('/ad-history')}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            광고 히스토리로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 헤더 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <button
              onClick={() => router.push('/ad-history')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              광고 히스토리로
            </button>

            <div className="flex gap-2">
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                삭제
              </button>
              <button
                onClick={downloadImage}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                다운로드
              </button>
            </div>
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mb-2">📋 광고 카피 상세</h1>
          <div className="flex gap-4 text-sm text-gray-600">
            <span>생성일: {new Date(adCopy.created_at).toLocaleDateString('ko-KR', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}</span>
            <span>•</span>
            <span>템플릿: {getTemplateName(adCopy.template_used)}</span>
          </div>
        </div>

        {/* 메인 콘텐츠 (2단 레이아웃) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* 좌측: 광고 이미지 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              📸 최종 광고 이미지
            </h2>
            
            <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-4">
              {adCopy.final_image_url ? (
                <img
                  src={adCopy.final_image_url}
                  alt="광고 이미지"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl mb-2">⏳</div>
                    <p className="text-gray-500">이미지 생성 중...</p>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={downloadImage}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              이미지 다운로드
            </button>
          </div>

          {/* 우측: 광고 카피 데이터 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              📝 광고 카피 데이터
            </h2>

            <div className="space-y-3">
              {/* 헤드라인 */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="text-sm text-purple-600 font-medium mb-1">💬 헤드라인</div>
                <div className="text-lg font-bold text-gray-900">{adCopy.ad_copy_data.headline}</div>
              </div>

              {/* 할인율 */}
              {adCopy.ad_copy_data.discount && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="text-sm text-red-600 font-medium mb-1">💰 할인</div>
                  <div className="text-lg font-bold text-gray-900">{adCopy.ad_copy_data.discount}</div>
                </div>
              )}

              {/* 기간 */}
              {adCopy.ad_copy_data.period && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-sm text-blue-600 font-medium mb-1">📅 기간</div>
                  <div className="text-lg font-bold text-gray-900">{adCopy.ad_copy_data.period}</div>
                </div>
              )}

              {/* 브랜드 */}
              {adCopy.ad_copy_data.brand && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="text-sm text-green-600 font-medium mb-1">🏷️ 브랜드</div>
                  <div className="text-lg font-bold text-gray-900">{adCopy.ad_copy_data.brand}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 생성 정보 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            📊 생성 정보
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="flex items-center gap-3">
              <div className="text-2xl">⏱️</div>
              <div>
                <div className="text-sm text-gray-500">처리 시간</div>
                <div className="text-lg font-semibold text-gray-900">{adCopy.processing_time.toFixed(1)}초</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-2xl">📅</div>
              <div>
                <div className="text-sm text-gray-500">생성 일시</div>
                <div className="text-lg font-semibold text-gray-900">
                  {new Date(adCopy.created_at).toLocaleString('ko-KR')}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-2xl">🎨</div>
              <div>
                <div className="text-sm text-gray-500">템플릿</div>
                <div className="text-lg font-semibold text-gray-900">{adCopy.template_used}</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-2xl">🤖</div>
              <div>
                <div className="text-sm text-gray-500">AI 모델</div>
                <div className="text-lg font-semibold text-gray-900">GPT-4 Turbo</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-2xl">📏</div>
              <div>
                <div className="text-sm text-gray-500">이미지 크기</div>
                <div className="text-lg font-semibold text-gray-900">800 x 800 (PNG)</div>
              </div>
            </div>
          </div>
        </div>

        {/* HTML 소스코드 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              💻 HTML 소스코드
            </h2>
            <button
              onClick={() => setShowHtmlCode(!showHtmlCode)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
            >
              {showHtmlCode ? '코드 숨기기 ▲' : '코드 보기 ▼'}
            </button>
          </div>

          {showHtmlCode && (
            <div>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm mb-4">
                <code>{adCopy.html_content}</code>
              </pre>
              <button
                onClick={copyHtmlCode}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                📋 코드 복사
              </button>
            </div>
          )}
        </div>

        {/* 하단 액션 버튼 */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            🔧 작업
          </h2>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={downloadImage}
              className="flex-1 min-w-[200px] px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              📥 이미지 다운로드
            </button>

            <button
              onClick={downloadHTML}
              className="flex-1 min-w-[200px] px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              📄 HTML 다운로드
            </button>

            <button
              onClick={handleDelete}
              className="flex-1 min-w-[200px] px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              🗑️ 삭제
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}