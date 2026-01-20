'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { useAuthStore } from '@/lib/store';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type ImageSource = 'gallery' | 'upload';

interface Content {
  content_id: string;
  product_name?: string;
  category?: string;
  image_url: string;
  thumbnail_url?: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { token, user } = useAuthStore();

  const [imageSource, setImageSource] = useState<ImageSource>('gallery');
  const [userPrompt, setUserPrompt] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [contents, setContents] = useState<Content[]>([]);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [generatedResult, setGeneratedResult] = useState<string>('');

  useEffect(() => {
    if (!token) {
      router.push('/login');
    }
  }, [token, router]);

  useEffect(() => {
    if (token) {
      fetchContents();
    }
  }, [token]);

  const fetchContents = async () => {
    try {
      const response = await fetch(`${API_URL}/api/contents`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setContents(data);
      }
    } catch (error) {
      console.error('Failed to fetch contents:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleUploadAndUse = async () => {
    if (!uploadFile) return;

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await fetch(`${API_URL}/api/contents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const newContent = await response.json();
        setSelectedContent(newContent);
        await fetchContents();
        setImageSource('gallery');
        setStep(2);
        alert('✅ 업로드 완료! Vision AI 분석이 완료되었습니다.');
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('❌ 업로드 실패');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectContent = (content: Content) => {
    setSelectedContent(content);
    setStep(2);
  };

  const handleSelectStyle = (style: string) => {
    setSelectedStyle(style);
    setStep(3);
  };

  const handleGenerate = async () => {
    if (!selectedContent || !selectedStyle) return;

    setIsLoading(true);

    try {
      // ✅ JSON 형식으로 요청 데이터 준비
      const requestBody = {
        prompt: userPrompt || `${selectedStyle} style background`, // 프롬프트가 없으면 기본값
        style: selectedStyle,
        aspect_ratio: 'square', // 또는 'portrait', 'landscape'
        num_inference_steps: 30,
      };

      console.log('🎨 AI 생성 시작:', requestBody);
      console.log('🔗 엔드포인트:', `${API_URL}/api/contents/${selectedContent.content_id}/generate-background`);

      // ✅ 올바른 엔드포인트 호출
      const response = await fetch(
        `${API_URL}/api/contents/${selectedContent.content_id}/generate-background`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json', // ✅ JSON 헤더 추가
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(requestBody), // ✅ JSON으로 변환
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('✅ 생성 완료:', data);
        console.log('✅ 사용된 모드:', data.mode); // local or replicate
        
        setGeneratedResult(data.result_url);
        alert(`✅ 생성 완료! (${data.processing_time.toFixed(2)}초)\n모드: ${data.mode}`);
      } else {
        const errorData = await response.json();
        console.error('❌ 에러 응답:', errorData);
        throw new Error(errorData.detail || 'Generation failed');
      }
    } catch (error) {
      console.error('❌ Generate error:', error);
      alert('❌ 생성 실패: ' + (error instanceof Error ? error.message : '알 수 없는 오류'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI 광고 생성
          </h1>
          <p className="text-gray-600">
            이미지를 선택하고 스타일을 적용하여 AI 광고를 생성하세요
          </p>
        </div>

        <div className="flex items-center justify-center mb-8">
          <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className="w-10 h-10 rounded-full bg-current text-white flex items-center justify-center font-bold">
              1
            </div>
            <span className="ml-2 font-medium">이미지</span>
          </div>
          <div className={`w-20 h-1 mx-4 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-300'}`} />
          <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className="w-10 h-10 rounded-full bg-current text-white flex items-center justify-center font-bold">
              2
            </div>
            <span className="ml-2 font-medium">스타일</span>
          </div>
          <div className={`w-20 h-1 mx-4 ${step >= 3 ? 'bg-blue-600' : 'bg-gray-300'}`} />
          <div className={`flex items-center ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className="w-10 h-10 rounded-full bg-current text-white flex items-center justify-center font-bold">
              3
            </div>
            <span className="ml-2 font-medium">생성</span>
          </div>
        </div>

        {step === 1 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">1️⃣ 이미지 선택</h2>

            <div className="flex gap-3 mb-6">
              <button
                type="button"
                onClick={() => setImageSource('gallery')}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
                  imageSource === 'gallery'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📂 갤러리에서 선택
              </button>
              <button
                type="button"
                onClick={() => setImageSource('upload')}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
                  imageSource === 'upload'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                ⬆️ 새로 업로드
              </button>
            </div>

            {imageSource === 'gallery' && (
              <>
                {contents.length === 0 ? (
                  <div className="text-center py-16 text-gray-500">
                    <p className="text-lg mb-2">아직 업로드된 이미지가 없습니다</p>
                    <p className="text-sm">새로 업로드 탭에서 이미지를 추가하세요</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {contents.map((content) => (
                      <button
                        key={content.content_id}
                        type="button"
                        onClick={() => handleSelectContent(content)}
                        className={`text-left rounded-lg overflow-hidden border-2 transition-all hover:shadow-lg ${
                          selectedContent?.content_id === content.content_id
                            ? 'border-blue-600 shadow-lg'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="aspect-square relative">
                          <Image
                            src={content.thumbnail_url || content.image_url}
                            alt={content.product_name || '상품'}
                            fill
                            className="object-cover"
                          />
                        </div>
                        <div className="p-3 bg-white">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {content.product_name || '이름 없음'}
                          </p>
                          {content.category && (
                            <p className="text-xs text-gray-500 mt-1">
                              {content.category}
                            </p>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}

            {imageSource === 'upload' && (
              <div className="text-center py-12">
                <p className="text-lg mb-4">업로드 페이지로 이동합니다</p>
                <Link
                  href="/upload"
                  className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg"
                >
                  업로드 페이지로 이동
                </Link>
              </div>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">2️⃣ AI 스타일 선택</h2>

            {selectedContent && (
              <div className="mb-6 p-4 bg-gray-50 rounded-lg flex items-center gap-4">
                <div className="relative w-16 h-16">
                  <Image
                    src={selectedContent.thumbnail_url || selectedContent.image_url}
                    alt="선택된 이미지"
                    fill
                    className="object-cover rounded"
                  />
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {selectedContent.product_name || '선택된 이미지'}
                  </p>
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    이미지 변경
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-5 gap-4 mb-6">
              {[
                { value: 'minimal', label: '미니멀', emoji: '⚪' },
                { value: 'modern', label: '모던', emoji: '🏙️' },
                { value: 'vintage', label: '빈티지', emoji: '📻' },
                { value: 'natural', label: '내추럴', emoji: '🌿' },
                { value: 'luxury', label: '럭셔리', emoji: '💎' },
              ].map((style) => (
                <button
                  key={style.value}
                  type="button"
                  onClick={() => handleSelectStyle(style.value)}
                  className={`p-6 rounded-xl border-2 transition-all ${
                    selectedStyle === style.value
                      ? 'border-blue-600 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow'
                  }`}
                >
                  <div className="text-4xl mb-2">{style.emoji}</div>
                  <div className="font-medium text-gray-900">{style.label}</div>
                </button>
              ))}
            </div>

            <div className="mt-6">
              <label htmlFor="user-prompt" className="block text-sm font-medium text-gray-700 mb-2">
                💬 추가 요청 (선택사항)
              </label>
              <textarea
                id="user-prompt"
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                placeholder="예: 배경을 따뜻한 느낌으로, 텍스트를 크게 강조, 제품을 중앙에 배치"
                rows={3}
                className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
              <p className="text-xs text-gray-500 mt-2">
                💡 선택한 스타일에 추가로 원하는 요청을 자유롭게 입력하세요
              </p>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition"
              >
                이전
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                disabled={!selectedStyle}
                className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                다음
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">3️⃣ AI 광고 생성</h2>

            <div className="mb-8 p-6 bg-gray-50 rounded-lg space-y-3">
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-700">이미지:</span>
                <span className="text-gray-900">
                  {selectedContent?.product_name || '선택됨'}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-700">스타일:</span>
                <span className="text-gray-900 capitalize">{selectedStyle}</span>
              </div>
              {userPrompt && (
                <div className="flex items-start gap-3">
                  <span className="font-medium text-gray-700">요청:</span>
                  <span className="text-gray-900">{userPrompt}</span>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleGenerate}
              disabled={isLoading}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold text-lg hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '생성 중... ⏳' : '🎨 AI 광고 생성하기'}
            </button>

            {generatedResult && (
              <div className="mt-8">
                <h3 className="text-xl font-bold mb-4">생성 결과</h3>
                <div className="relative w-full aspect-square max-w-2xl mx-auto">
                  <Image
                    src={generatedResult}
                    alt="Generated"
                    fill
                    className="object-contain rounded-lg shadow-xl"
                  />
                </div>
                <div className="flex gap-3 mt-6">
                  
                  <a
                    href={generatedResult}
                    download="generated-ad.jpg"
                    className="flex-1 text-center py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition"
                  >
                    다운로드
                  </a>
                  <Link
                    href="/history"
                    className="flex-1 text-center py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition"
                  >
                    히스토리 보기
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      setStep(1);
                      setSelectedContent(null);
                      setSelectedStyle('');
                      setUserPrompt('');
                      setGeneratedResult('');
                    }}
                    className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
                  >
                    새로 만들기
                  </button>
                </div>
              </div>
            )}

            {!generatedResult && (
              <button
                type="button"
                onClick={() => setStep(2)}
                className="w-full py-3 mt-4 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition"
              >
                이전
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}