'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { historyAPI, authAPI, api, API_URL } from '@/lib/api';
import { History } from '@/types';

export default function HistoryPage() {
  const router = useRouter();
  
  // 상태 관리
  const [histories, setHistories] = useState<History[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userId, setUserId] = useState<string | null>(null);
  
  // 일괄 다운로드 관련
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isSelectionMode, setIsSelectionMode] = useState(false);

  // ===== 초기 로드 =====
  useEffect(() => {
    const fetchHistories = async () => {
      try {
        const userResponse = await authAPI.getMe();
        const currentUserId = userResponse.data.user_id;
        setUserId(currentUserId);

        const response = await historyAPI.getByUserId(currentUserId);
        setHistories(response.data);
      } catch (err: any) {
        console.error('히스토리 로드 실패:', err);
        setError(err.response?.data?.detail || '히스토리를 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistories();
  }, []);

  // ===== 삭제 =====
  const handleDelete = async (historyId: string) => {
    if (!confirm('정말 삭제하시겠습니까?')) {
      return;
    }

    try {
      await historyAPI.delete(historyId);
      setHistories(histories.filter(h => h.history_id !== historyId));
      alert('삭제되었습니다.');
    } catch (err: any) {
      console.error('삭제 실패:', err);
      alert(err.response?.data?.detail || '삭제에 실패했습니다.');
    }
  };

  // ===== 단일 다운로드 (api 사용) =====
  const downloadVTONImage = async (historyId: string, style: string, createdAt: string) => {
    try {
      // ✅ export된 api 사용
      const response = await api.get(
        `/api/v1/history/${historyId}/download`,
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'image/png' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `vton_${style}_${createdAt}_${historyId.substring(0, 8)}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      console.log('✅ 다운로드 완료');
    } catch (error: any) {
      console.error('❌ 다운로드 실패:', error);
      if (error.response?.status === 401) {
        alert('인증이 만료되었습니다. 다시 로그인해주세요.');
        router.push('/login');
      } else {
        alert('이미지 다운로드에 실패했습니다.');
      }
    }
  };

  // ===== 일괄 다운로드 =====
  const downloadMultipleVTON = async (historyIds: string[]) => {
    if (historyIds.length === 0) {
      alert('다운로드할 이미지를 선택해주세요.');
      return;
    }

    if (historyIds.length > 50) {
      alert('한 번에 최대 50개까지만 다운로드할 수 있습니다.');
      return;
    }

    try {
      const response = await api.post(
        `/api/v1/history/download-batch`,
        historyIds,
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `vton_results_${historyIds.length}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      console.log(`✅ ${historyIds.length}개 일괄 다운로드 완료`);
    } catch (error: any) {
      console.error('❌ 일괄 다운로드 실패:', error);
      if (error.response?.status === 401) {
        alert('인증이 만료되었습니다. 다시 로그인해주세요.');
        router.push('/login');
      } else {
        alert('일괄 다운로드에 실패했습니다.');
      }
    }
  };

  // ===== 선택 관리 =====
  const toggleSelection = (historyId: string) => {
    setSelectedIds(prev => 
      prev.includes(historyId)
        ? prev.filter(id => id !== historyId)
        : [...prev, historyId]
    );
  };

  const handleSelectionModeChange = () => {
    setIsSelectionMode(!isSelectionMode);
    if (isSelectionMode) {
      setSelectedIds([]);
    }
  };

  const handleBatchDownload = () => {
    downloadMultipleVTON(selectedIds);
    setIsSelectionMode(false);
    setSelectedIds([]);
  };

  // ===== 스타일 이름 변환 =====
  const getStyleName = (style: string): string => {
    const styleMap: { [key: string]: string } = {
      'resort': '리조트',
      'retro': '레트로',
      'romantic': '로맨틱',
    };
    return styleMap[style] || style;
  };

  // ===== 로딩 =====
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

  // ===== 에러 =====
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl text-red-600 mb-4">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            대시보드로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  // ===== 메인 렌더링 =====
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🎨 VTON 히스토리</h1>
            <p className="text-gray-600 mt-1">총 {histories.length}개의 생성 결과</p>
          </div>
          <button
            onClick={() => router.push('/gallery')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            + 새로 만들기
          </button>
        </div>

        {/* 일괄 다운로드 섹션 */}
        {histories.length > 0 && (
          <div className="mb-6 flex justify-between items-center">
            <div className="flex gap-3">
              <button
                onClick={handleSelectionModeChange}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  isSelectionMode 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {isSelectionMode ? '선택 취소' : '일괄 다운로드'}
              </button>

              {isSelectionMode && selectedIds.length > 0 && (
                <button
                  onClick={handleBatchDownload}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  📦 {selectedIds.length}개 다운로드
                </button>
              )}
            </div>

            {isSelectionMode && (
              <span className="text-sm text-gray-500">
                {selectedIds.length}개 선택됨
              </span>
            )}
          </div>
        )}

        {/* 히스토리 그리드 */}
        {histories.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📭</div>
            <p className="text-gray-500 mb-4">아직 생성된 이미지가 없습니다.</p>
            <button
              onClick={() => router.push('/gallery')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              첫 이미지 만들기
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {histories.map((history) => {
              const createdDate = new Date(history.created_at).toLocaleDateString('ko-KR');
              const isSelected = selectedIds.includes(history.history_id);

              return (
                <div
                  key={history.history_id}
                  className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow relative"
                >
                  {/* 선택 체크박스 */}
                  {isSelectionMode && (
                    <div className="absolute top-2 left-2 z-10">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelection(history.history_id)}
                        className="w-6 h-6 rounded border-2 border-white cursor-pointer"
                      />
                    </div>
                  )}

                  {/* 삭제 버튼 */}
                  {!isSelectionMode && (
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
                  )}

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
                    {history.processing_time && (
                      <p className="text-gray-500 text-sm mb-2">
                        ⚡ 처리 시간: {history.processing_time.toFixed(1)}초
                      </p>
                    )}

                    {/* 생성 일시 */}
                    <p className="text-gray-400 text-xs mb-4">
                      {new Date(history.created_at).toLocaleString('ko-KR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>

                    {/* 다운로드 버튼 */}
                    {!isSelectionMode && (
                      <button
                        onClick={() => downloadVTONImage(
                          history.history_id, 
                          history.style, 
                          createdDate.replace(/\./g, '')
                        )}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        다운로드
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}