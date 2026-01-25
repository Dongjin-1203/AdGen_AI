'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuthStore } from '@/lib/store';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ===== 타입 정의 =====
interface AdCopyData {
  headline: string;
  discount?: string;
  period?: string;
  brand?: string;
}

interface AdCopyHistoryItem {
  ad_copy_id: string;
  template_used: string;
  ad_copy_data: AdCopyData;
  final_image_url: string | null;
  created_at: string;
  product_name: string | null;
  category: string | null;
  model_image_url: string | null;
}

interface Statistics {
  total_count: number;
  template_counts: {
    minimal?: number;
    bold?: number;
    vintage?: number;
  };
  recent_7days_count: number;
  average_per_day: number;
}

// ===== 메인 컴포넌트 =====
export default function AdCopyHistoryPage() {
  const router = useRouter();
  const { token, user } = useAuthStore();

  const [adCopies, setAdCopies] = useState<AdCopyHistoryItem[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [loading, setLoading] = useState(false);

  // 초기화
  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }

    fetchStatistics();
    fetchAdCopyHistory();
  }, [token, page, selectedTemplate]);

  // 통계 조회
  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/ad-copy-statistics`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('통계 조회 실패:', error);
    }
  };

  // 히스토리 조회
  const fetchAdCopyHistory = async () => {
    setLoading(true);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '12'
      });

      if (selectedTemplate) {
        params.append('template', selectedTemplate);
      }

      const response = await fetch(
        `${API_URL}/api/v1/ad-copy-history?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAdCopies(data.results);
        setTotalPages(data.total_pages);
      }
    } catch (error) {
      console.error('히스토리 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 이미지 다운로드
  const downloadImage = async (adCopyId: string, headline: string) => {
    try {
      const response = await fetch(
        `${API_URL}/api/v1/ad-copy-history/${adCopyId}/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('다운로드 실패');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ad_${headline.substring(0, 20)}_${adCopyId.substring(0, 8)}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      console.log('✅ 다운로드 완료');
    } catch (error) {
      console.error('❌ 다운로드 실패:', error);
      alert('이미지 다운로드에 실패했습니다.');
    }
  };

  // 상세보기
  const viewDetail = (adCopyId: string) => {
    router.push(`/ad-detail/${adCopyId}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📋 광고 카피 히스토리</h1>
              <p className="text-sm text-gray-500 mt-1">
                생성된 광고를 확인하고 다운로드하세요
              </p>
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              + 새 광고 만들기
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* 통계 카드 */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">총 생성 개수</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {statistics.total_count}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">최근 7일</div>
              <div className="text-2xl font-bold text-blue-600 mt-1">
                {statistics.recent_7days_count}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">일평균 생성</div>
              <div className="text-2xl font-bold text-green-600 mt-1">
                {statistics.average_per_day}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">Minimal 템플릿</div>
              <div className="text-2xl font-bold text-purple-600 mt-1">
                {statistics.template_counts.minimal || 0}
              </div>
            </div>
          </div>
        )}

        {/* 필터 */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setSelectedTemplate('')}
            className={`px-4 py-2 rounded-lg ${
              selectedTemplate === ''
                ? 'bg-purple-600 text-white'
                : 'bg-white text-gray-700 border hover:bg-gray-50'
            }`}
          >
            전체
          </button>
          <button
            onClick={() => setSelectedTemplate('minimal')}
            className={`px-4 py-2 rounded-lg ${
              selectedTemplate === 'minimal'
                ? 'bg-purple-600 text-white'
                : 'bg-white text-gray-700 border hover:bg-gray-50'
            }`}
          >
            Minimal
          </button>
        </div>

        {/* 로딩 */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </div>
        )}

        {/* 광고 카피 그리드 */}
        {!loading && (
          <>
            {adCopies.length === 0 ? (
              <div className="text-center py-20">
                <div className="text-6xl mb-4">📭</div>
                <p className="text-gray-500">생성된 광고가 없습니다.</p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  첫 광고 만들기
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {adCopies.map((ad) => (
                  <div
                    key={ad.ad_copy_id}
                    className="bg-white border rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    {/* 최종 이미지 */}
                    {ad.final_image_url ? (
                      <div className="aspect-square bg-gray-100 relative">
                        <Image
                          src={ad.final_image_url}
                          alt={ad.ad_copy_data.headline}
                          fill
                          className="object-cover"
                        />
                      </div>
                    ) : (
                      <div className="aspect-square bg-gray-100 flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-4xl mb-2">⏳</div>
                          <p className="text-sm text-gray-500">이미지 생성 중...</p>
                        </div>
                      </div>
                    )}

                    {/* 정보 */}
                    <div className="p-4">
                      {/* 헤드라인 */}
                      <h3 className="font-bold text-lg mb-2 line-clamp-1">
                        {ad.ad_copy_data.headline}
                      </h3>

                      {/* 광고 데이터 */}
                      <div className="flex gap-2 mb-3">
                        {ad.ad_copy_data.discount && (
                          <span className="text-sm bg-red-100 text-red-600 px-2 py-1 rounded">
                            {ad.ad_copy_data.discount}
                          </span>
                        )}
                        {ad.ad_copy_data.period && (
                          <span className="text-sm bg-blue-100 text-blue-600 px-2 py-1 rounded">
                            {ad.ad_copy_data.period}
                          </span>
                        )}
                      </div>

                      {/* 메타 정보 */}
                      <div className="flex justify-between items-center text-xs text-gray-500 mb-4">
                        <span>{ad.category}</span>
                        <span>
                          {new Date(ad.created_at).toLocaleDateString('ko-KR')}
                        </span>
                      </div>

                      {/* 버튼 */}
                      <div className="flex gap-2">
                        {ad.final_image_url && (
                          <button
                            onClick={() => downloadImage(ad.ad_copy_id, ad.ad_copy_data.headline)}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            다운로드
                          </button>
                        )}
                        <button
                          onClick={() => viewDetail(ad.ad_copy_id)}
                          className="flex-1 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm"
                        >
                          상세보기
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 페이지네이션 */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  이전
                </button>
                <span className="px-4 py-2 text-gray-700">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  다음
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}