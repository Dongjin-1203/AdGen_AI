'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { historyAPI, authAPI, API_URL } from '@/lib/api';
import { History } from '@/types';

export default function HistoryPage() {
  const [histories, setHistories] = useState<History[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userId, setUserId] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchHistories = async () => {
      try {
        // 1. 현재 사용자 정보 가져오기
        const userResponse = await authAPI.getMe();
        const currentUserId = userResponse.data.user_id;
        setUserId(currentUserId);

        // 2. 히스토리 조회
        const response = await historyAPI.getByUserId(currentUserId);
        setHistories(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || '히스토리를 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistories();
  }, []);

  const handleDelete = async (historyId: string) => {
    if (!confirm('정말 삭제하시겠습니까?')) {
      return;
    }

    try {
      await historyAPI.delete(historyId);
      
      // 삭제 성공 시 목록에서 제거
      setHistories(histories.filter(h => h.history_id !== historyId));
      
      alert('삭제되었습니다.');
    } catch (err: any) {
      alert(err.response?.data?.detail || '삭제에 실패했습니다.');
    }
  };

  const getStyleName = (style: string): string => {
    const styleMap: { [key: string]: string } = {
      'minimal': '미니멀',
      'emotional': '감성적',
      'street': '스트릿',
      'instagram': '인스타그램',
      'vintage': '빈티지',
      'modern': '모던',
      'natural': '내추럴',
      'luxury': '럭셔리',
    };
    return styleMap[style] || style;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="flex items-center justify-center h-screen">
          <p className="text-xl">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="flex items-center justify-center h-screen">
          <p className="text-xl text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">AI 생성 히스토리</h1>
          <p className="text-gray-600">총 {histories.length}개</p>
        </div>
        
        {histories.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">아직 생성된 이미지가 없습니다.</p>
            <button
              onClick={() => router.push('/gallery')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              갤러리에서 시작하기
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {histories.map((history) => (
              <div
                key={history.history_id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow relative"
              >
                {/* 삭제 버튼 */}
                <button
                  onClick={() => handleDelete(history.history_id)}
                  className="absolute top-2 right-2 z-10 bg-red-500 text-white rounded-full p-2 hover:bg-red-600 transition shadow-lg"
                  title="삭제"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>

                {/* 이미지 */}
                <div className="aspect-square relative bg-gray-100">
                  <img
                    src={
                      history.result_url?.startsWith('http')
                        ? history.result_url
                        : `${API_URL}${history.result_url}`
                    }
                    alt={`${getStyleName(history.style)} 스타일`}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* 정보 */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-lg">AI 생성 결과</h3>
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium">
                      {getStyleName(history.style)}
                    </span>
                  </div>

                  {/* 사용자 프롬프트 */}
                  {history.prompt && (
                    <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                      "{history.prompt}"
                    </p>
                  )}

                  {/* 처리 시간 */}
                  <p className="text-gray-500 text-sm mb-1">
                    ⚡ 처리 시간: {history.processing_time.toFixed(1)}초
                  </p>

                  {/* 생성 일시 */}
                  <p className="text-gray-400 text-xs">
                    {new Date(history.created_at).toLocaleString('ko-KR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
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
