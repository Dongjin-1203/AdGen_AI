'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { contentAPI, API_URL } from '@/lib/api';
import { Content } from '@/types';
import Navbar from '@/components/Navbar';
import { Sparkles, Upload, Download, RefreshCw, Image as ImageIcon } from 'lucide-react';

type Style = 'vintage' | 'modern' | 'minimal' | 'natural' | 'luxury';

interface StyleOption {
  id: Style;
  name: string;
  description: string;
  emoji: string;
  color: string;
}

const STYLE_OPTIONS: StyleOption[] = [
  {
    id: 'vintage',
    name: '빈티지',
    description: '따뜻한 레트로 감성',
    emoji: '🎞️',
    color: 'bg-amber-100 hover:bg-amber-200 border-amber-300'
  },
  {
    id: 'modern',
    name: '모던',
    description: '세련된 현대적 스타일',
    emoji: '🏙️',
    color: 'bg-blue-100 hover:bg-blue-200 border-blue-300'
  },
  {
    id: 'minimal',
    name: '미니멀',
    description: '깔끔한 화이트 배경',
    emoji: '⬜',
    color: 'bg-gray-100 hover:bg-gray-200 border-gray-300'
  },
  {
    id: 'natural',
    name: '내추럴',
    description: '자연스러운 아웃도어',
    emoji: '🌿',
    color: 'bg-green-100 hover:bg-green-200 border-green-300'
  },
  {
    id: 'luxury',
    name: '럭셔리',
    description: '고급스러운 프리미엄',
    emoji: '💎',
    color: 'bg-purple-100 hover:bg-purple-200 border-purple-300'
  }
];

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuthStore();

  // 콘텐츠 관련 상태
  const [contents, setContents] = useState<Content[]>([]);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [fetchingContents, setFetchingContents] = useState(true);

  // AI 생성 관련 상태
  const [selectedStyle, setSelectedStyle] = useState<Style | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  // 업로드 관련 상태
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadPreview, setUploadPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showUploadSection, setShowUploadSection] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    fetchContents();
  }, [user, router]);

  const fetchContents = async () => {
    try {
      const response = await contentAPI.getAll();
      setContents(response.data);
    } catch (err: any) {
      console.error('콘텐츠 로딩 실패:', err);
    } finally {
      setFetchingContents(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setUploadPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      await contentAPI.upload(formData);
      
      // 업로드 성공 후 목록 새로고침
      await fetchContents();
      
      // 업로드 폼 초기화
      setUploadFile(null);
      setUploadPreview(null);
      setShowUploadSection(false);
      
      alert('이미지가 업로드되었습니다!');
    } catch (err: any) {
      setError(err.response?.data?.detail || '업로드에 실패했습니다.');
    } finally {
      setUploading(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedContent || !selectedStyle) {
      setError('이미지와 스타일을 선택해주세요.');
      return;
    }

    setLoading(true);
    setError(null);
    setResultUrl(null);
    setProcessingTime(null);

    try {
      const formData = new FormData();
      formData.append('content_id', selectedContent.content_id);
      formData.append('style', selectedStyle);

      const response = await fetch(`${API_URL}/api/v1/generate-ad`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('AI 생성에 실패했습니다.');
      }

      const data = await response.json();
      setResultUrl(data.result_url);
      setProcessingTime(data.processing_time);
    } catch (err: any) {
      setError(err.message || 'AI 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!resultUrl) return;
    
    const link = document.createElement('a');
    link.href = resultUrl;
    link.download = `adgen_${selectedStyle}_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = () => {
    setResultUrl(null);
    setProcessingTime(null);
    setError(null);
  };

  if (!user) {
    return null;
  }

  if (fetchingContents) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mb-4"></div>
            <p className="text-xl">로딩 중...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-md p-6 text-white">
            <h1 className="text-3xl font-bold mb-2">
              {user.name}님, 환영합니다! 👋
            </h1>
            <p className="text-blue-100">
              AI로 프로페셔널한 광고 이미지를 만들어보세요
            </p>
          </div>
        </div>

        {/* 통계 (간단하게) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">내 이미지</p>
            <p className="text-2xl font-bold text-blue-600">{contents.length}개</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">선택된 이미지</p>
            <p className="text-2xl font-bold text-green-600">
              {selectedContent ? '1개' : '0개'}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-500 text-sm">선택된 스타일</p>
            <p className="text-2xl font-bold text-purple-600">
              {selectedStyle ? STYLE_OPTIONS.find(s => s.id === selectedStyle)?.name : '-'}
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-900 font-bold">✕</button>
          </div>
        )}

        {/* 메인 AI 생성 인터페이스 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 1. 이미지 선택/업로드 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <ImageIcon className="w-5 h-5" />
                1️⃣ 내 이미지
              </h2>
              <button
                onClick={() => setShowUploadSection(!showUploadSection)}
                className="text-sm px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-1"
              >
                <Upload className="w-4 h-4" />
                {showUploadSection ? '취소' : '업로드'}
              </button>
            </div>

            {/* 업로드 섹션 */}
            {showUploadSection && (
              <div className="mb-4 p-4 bg-blue-50 rounded-lg border-2 border-dashed border-blue-300">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="fileInput"
                />
                
                {uploadPreview ? (
                  <div className="space-y-3">
                    <img
                      src={uploadPreview}
                      alt="Preview"
                      className="w-full h-32 object-cover rounded"
                    />
                    <button
                      onClick={handleUpload}
                      disabled={uploading}
                      className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      {uploading ? '업로드 중...' : '업로드 완료'}
                    </button>
                  </div>
                ) : (
                  <label
                    htmlFor="fileInput"
                    className="block text-center py-8 cursor-pointer"
                  >
                    <Upload className="w-12 h-12 mx-auto text-blue-400 mb-2" />
                    <p className="text-sm text-gray-600">
                      클릭하여 이미지 선택
                    </p>
                  </label>
                )}
              </div>
            )}

            {/* 이미지 목록 */}
            {contents.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <ImageIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>아직 업로드된 이미지가 없습니다</p>
                <p className="text-sm mt-2">위의 '업로드' 버튼을 눌러주세요</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {contents.map((content) => (
                  <div
                    key={content.content_id}
                    onClick={() => setSelectedContent(content)}
                    className={`
                      p-3 border-2 rounded-lg cursor-pointer transition
                      ${selectedContent?.content_id === content.content_id
                        ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    <div className="flex gap-3 items-center">
                      <img
                        src={
                          content.thumbnail_url?.startsWith('http')
                            ? content.thumbnail_url
                            : `${API_URL}${content.thumbnail_url}`
                        }
                        alt={content.product_name}
                        className="w-16 h-16 object-cover rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold truncate">
                          {content.product_name}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {content.category || '미분류'}
                        </p>
                      </div>
                      {selectedContent?.content_id === content.content_id && (
                        <span className="text-blue-500 font-bold">✓</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 2. 스타일 선택 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              2️⃣ AI 스타일
            </h2>
            
            <div className="space-y-3">
              {STYLE_OPTIONS.map((style) => (
                <div
                  key={style.id}
                  onClick={() => setSelectedStyle(style.id)}
                  className={`
                    p-4 border-2 rounded-lg cursor-pointer transition
                    ${style.color}
                    ${selectedStyle === style.id
                      ? 'ring-2 ring-offset-2 ring-blue-500 border-blue-500'
                      : 'border-transparent'
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-3xl">{style.emoji}</span>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-800">
                        {style.name}
                      </p>
                      <p className="text-sm text-gray-600">
                        {style.description}
                      </p>
                    </div>
                    {selectedStyle === style.id && (
                      <span className="text-blue-500 font-bold text-xl">✓</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 3. 생성 결과 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">
              3️⃣ 생성 결과
            </h2>

            {!resultUrl && !loading && (
              <div className="text-center py-8">
                <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 mb-6">
                  이미지와 스타일을 선택하고<br />
                  생성 버튼을 눌러주세요
                </p>
                <button
                  onClick={handleGenerate}
                  disabled={!selectedContent || !selectedStyle}
                  className="
                    w-full px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-600
                    text-white font-bold rounded-lg text-lg
                    hover:from-blue-600 hover:to-purple-700
                    disabled:from-gray-300 disabled:to-gray-400
                    disabled:cursor-not-allowed
                    transition flex items-center justify-center gap-2
                    shadow-lg hover:shadow-xl
                  "
                >
                  <Sparkles className="w-6 h-6" />
                  AI 광고 생성하기
                </button>
                
                {(!selectedContent || !selectedStyle) && (
                  <p className="text-xs text-gray-400 mt-3">
                    {!selectedContent && '이미지를 선택하세요 '}
                    {!selectedContent && !selectedStyle && '+ '}
                    {!selectedStyle && '스타일을 선택하세요'}
                  </p>
                )}
              </div>
            )}

            {loading && (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mb-4"></div>
                <p className="text-gray-700 font-semibold mb-2">
                  AI가 광고를 생성하고 있습니다...
                </p>
                <p className="text-sm text-gray-500">
                  약 10-15초 소요됩니다
                </p>
              </div>
            )}

            {resultUrl && (
              <div className="space-y-4">
                <div className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden border-2 border-green-500">
                  <img
                    src={resultUrl}
                    alt="Generated ad"
                    className="w-full h-full object-contain"
                  />
                </div>

                {processingTime && (
                  <div className="text-center">
                    <span className="inline-block px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                      ✨ {processingTime.toFixed(1)}초 만에 완성!
                    </span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={handleDownload}
                    className="
                      px-4 py-3 bg-green-600 text-white rounded-lg
                      hover:bg-green-700 transition font-semibold
                      flex items-center justify-center gap-2
                      shadow hover:shadow-lg
                    "
                  >
                    <Download className="w-5 h-5" />
                    다운로드
                  </button>
                  <button
                    onClick={handleReset}
                    className="
                      px-4 py-3 bg-gray-600 text-white rounded-lg
                      hover:bg-gray-700 transition font-semibold
                      flex items-center justify-center gap-2
                      shadow hover:shadow-lg
                    "
                  >
                    <RefreshCw className="w-5 h-5" />
                    다시 생성
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 하단 도움말 */}
        {!resultUrl && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-blue-800 mb-2">
              💡 사용 팁:
            </p>
            <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
              <li>단색 배경의 제품 사진이 가장 좋은 결과를 만듭니다</li>
              <li>의류는 빈티지/모던, 테크 제품은 모던/미니멀 스타일 추천</li>
              <li>생성된 이미지는 바로 다운로드하거나 다른 스타일로 재생성할 수 있습니다</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}