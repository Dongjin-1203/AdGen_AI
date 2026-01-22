'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { useAuthStore } from '@/lib/store';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ===== 타입 정의 =====
interface Content {
  content_id: string;
  product_name?: string;
  category?: string;
  image_url: string;
  thumbnail_url?: string;
}

interface StepData {
  id: string;
  title: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  content?: React.ReactNode;
  timestamp: Date;
}

const AVAILABLE_STYLES = [
  { value: 'resort', label: '리조트', emoji: '🏖️', description: '밝고 경쾌한 휴양지 분위기' },
  { value: 'retro', label: '레트로', emoji: '📻', description: '빈티지하고 복고적인 감성' },
  { value: 'romantic', label: '로맨틱', emoji: '💕', description: '부드럽고 여성스러운 분위기' },
] as const;

// ===== 메인 컴포넌트 =====
export default function DashboardPage() {
  const router = useRouter();
  const { token, user } = useAuthStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  // 상태 관리
  const [steps, setSteps] = useState<StepData[]>([]);
  const [progress, setProgress] = useState(0);
  const [contents, setContents] = useState<Content[]>([]);
  
  // 선택된 값들
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<string>('');
  const [userPrompt, setUserPrompt] = useState('');
  const [generatedResult, setGeneratedResult] = useState<string>('');

  // ===== 초기화 =====
  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    
    // 초기 단계 추가
    addStep({
      id: 'select-image',
      title: '1️⃣ 이미지 선택',
      status: 'processing',
      content: null,
    });

    fetchContents();
  }, [token]);

  // ===== 자동 스크롤 =====
  useEffect(() => {
    if (scrollRef.current) {
      setTimeout(() => {
        scrollRef.current?.scrollTo({
          top: scrollRef.current.scrollHeight,
          behavior: 'smooth',
        });
      }, 100);
    }
  }, [steps]);

  // ===== Helper Functions =====
  const addStep = (step: StepData) => {
    setSteps(prev => [...prev, step]);
  };

  const updateStep = (id: string, updates: Partial<StepData>) => {
    setSteps(prev =>
      prev.map(step =>
        step.id === id ? { ...step, ...updates } : step
      )
    );
  };

  const fetchContents = async () => {
    try {
      const response = await fetch(`${API_URL}/api/contents`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setContents(data);
      }
    } catch (error) {
      console.error('Failed to fetch contents:', error);
    }
  };

  // ===== Step 1: 이미지 선택 =====
  const handleSelectContent = (content: Content) => {
    setSelectedContent(content);
    setProgress(33);

    // Step 1 완료 처리
    updateStep('select-image', {
      status: 'completed',
      content: (
        <div className="flex items-center gap-4">
          <div className="relative w-20 h-20 flex-shrink-0">
            <Image
              src={content.thumbnail_url || content.image_url}
              alt={content.product_name || ''}
              fill
              className="object-cover rounded-lg"
            />
          </div>
          <div>
            <p className="font-semibold text-gray-900">
              {content.product_name || '이름 없음'}
            </p>
            {content.category && (
              <p className="text-sm text-gray-500">{content.category}</p>
            )}
          </div>
        </div>
      ),
    });

    // Step 2 추가
    setTimeout(() => {
      addStep({
        id: 'select-style',
        title: '2️⃣ AI 스타일 선택',
        status: 'processing',
        content: null,
      });
    }, 300);
  };

  // ===== Step 2: 스타일 선택 =====
  const handleSelectStyle = (style: string) => {
    setSelectedStyle(style);
    setProgress(66);

    const selectedStyleData = AVAILABLE_STYLES.find(s => s.value === style);

    // Step 2 완료 처리
    updateStep('select-style', {
      status: 'completed',
      content: (
        <div className="flex items-center gap-3">
          <span className="text-3xl">{selectedStyleData?.emoji}</span>
          <div>
            <p className="font-semibold text-gray-900">{selectedStyleData?.label}</p>
            <p className="text-sm text-gray-500">{selectedStyleData?.description}</p>
          </div>
        </div>
      ),
    });

    // Step 3 추가
    setTimeout(() => {
      addStep({
        id: 'generate',
        title: '3️⃣ AI 광고 생성',
        status: 'processing',
        content: null,
      });
    }, 300);
  };

  // ===== Step 3: 생성 =====
  const handleGenerate = async () => {
    if (!selectedContent || !selectedStyle) return;

    setProgress(75);

    // 생성 중 표시
    updateStep('generate', {
      status: 'processing',
      content: (
        <div className="flex flex-col items-center py-8">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-gray-600">AI가 광고를 생성하고 있습니다...</p>
          <p className="text-sm text-gray-500 mt-2">평균 30-60초 소요됩니다</p>
        </div>
      ),
    });

    try {
      const formData = new FormData();
      formData.append('content_id', selectedContent.content_id);
      formData.append('style', selectedStyle);
      if (userPrompt) {
        formData.append('prompt', userPrompt);
      }

      const response = await fetch(`${API_URL}/api/v1/generate-ad-replicate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedResult(data.result_url);
        setProgress(100);

        // 생성 완료
        updateStep('generate', {
          status: 'completed',
          content: (
            <div className="space-y-4">
              <div className="relative w-full aspect-square max-w-2xl mx-auto">
                <Image
                  src={data.result_url}
                  alt="Generated Ad"
                  fill
                  className="object-contain rounded-lg shadow-xl"
                />
              </div>
              <div className="flex gap-3">
                
                  href={data.result_url}
                  download="generated-ad.jpg"
                  className="flex-1 text-center py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition"
                >
                  💾 다운로드
                </a>
                <Link
                  href="/history"
                  className="flex-1 text-center py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition"
                >
                  📜 히스토리
                </Link>
                <button
                  onClick={handleReset}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
                >
                  🎨 새로 만들기
                </button>
              </div>
              <div className="text-center text-sm text-gray-600">
                ⏱️ 생성 시간: {data.processing_time?.toFixed(2)}초
              </div>
            </div>
          ),
        });
      } else {
        throw new Error('Generation failed');
      }
    } catch (error) {
      updateStep('generate', {
        status: 'error',
        content: (
          <div className="text-center py-8">
            <p className="text-red-600 font-semibold mb-4">❌ 생성 실패</p>
            <p className="text-gray-600 mb-4">
              {error instanceof Error ? error.message : '알 수 없는 오류'}
            </p>
            <button
              onClick={handleGenerate}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              다시 시도
            </button>
          </div>
        ),
      });
    }
  };

  const handleReset = () => {
    setSteps([]);
    setProgress(0);
    setSelectedContent(null);
    setSelectedStyle('');
    setUserPrompt('');
    setGeneratedResult('');
    
    addStep({
      id: 'select-image',
      title: '1️⃣ 이미지 선택',
      status: 'processing',
      content: null,
    });
  };

  // ===== 렌더링 =====
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 상단 고정 진행바 */}
      <div className="sticky top-0 z-50 bg-white border-b shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4 mb-2">
            <h1 className="text-xl font-bold text-gray-900">AI 광고 생성</h1>
            <div className="flex-1"></div>
            <span className="text-sm font-medium text-gray-700">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* 스크롤 가능한 단계 영역 */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
          {steps.map((step, idx) => (
            <StepCard
              key={step.id}
              step={step}
              isLast={idx === steps.length - 1}
              // 각 단계별 입력 UI
              onSelectImage={step.id === 'select-image' && step.status === 'processing' ? (
                <GallerySelector
                  contents={contents}
                  selectedContent={selectedContent}
                  onSelect={handleSelectContent}
                />
              ) : null}
              onSelectStyle={step.id === 'select-style' && step.status === 'processing' ? (
                <StyleSelector
                  styles={AVAILABLE_STYLES}
                  selectedStyle={selectedStyle}
                  userPrompt={userPrompt}
                  onSelectStyle={handleSelectStyle}
                  onPromptChange={setUserPrompt}
                />
              ) : null}
              onGenerate={step.id === 'generate' && step.status === 'processing' ? (
                <GenerateButton
                  onGenerate={handleGenerate}
                  disabled={!selectedContent || !selectedStyle}
                />
              ) : null}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ===== 하위 컴포넌트들 =====

function StepCard({
  step,
  isLast,
  onSelectImage,
  onSelectStyle,
  onGenerate,
}: {
  step: StepData;
  isLast: boolean;
  onSelectImage?: React.ReactNode;
  onSelectStyle?: React.ReactNode;
  onGenerate?: React.ReactNode;
}) {
  return (
    <div
      className="bg-white rounded-xl shadow-md p-6 animate-slideUp"
      style={{
        animationDelay: '0.1s',
      }}
    >
      {/* 헤더 */}
      <div className="flex items-center gap-3 mb-4">
        {step.status === 'completed' && (
          <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
        {step.status === 'processing' && (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
        {step.status === 'error' && (
          <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        )}
        <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
      </div>

      {/* 내용 */}
      {step.content && (
        <div className="mt-4">
          {step.content}
        </div>
      )}

      {/* 입력 UI */}
      {onSelectImage}
      {onSelectStyle}
      {onGenerate}
    </div>
  );
}

function GallerySelector({
  contents,
  selectedContent,
  onSelect,
}: {
  contents: Content[];
  selectedContent: Content | null;
  onSelect: (content: Content) => void;
}) {
  return (
    <div className="mt-4">
      {contents.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="mb-4">아직 업로드된 이미지가 없습니다</p>
          <Link
            href="/upload"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            이미지 업로드하기
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {contents.map((content) => (
            <button
              key={content.content_id}
              onClick={() => onSelect(content)}
              className={`rounded-lg overflow-hidden border-2 transition-all hover:shadow-lg ${
                selectedContent?.content_id === content.content_id
                  ? 'border-blue-600 shadow-lg'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="aspect-square relative">
                <Image
                  src={content.thumbnail_url || content.image_url}
                  alt={content.product_name || ''}
                  fill
                  className="object-cover"
                />
              </div>
              <div className="p-3 bg-white">
                <p className="text-sm font-medium truncate">
                  {content.product_name || '이름 없음'}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function StyleSelector({
  styles,
  selectedStyle,
  userPrompt,
  onSelectStyle,
  onPromptChange,
}: {
  styles: typeof AVAILABLE_STYLES;
  selectedStyle: string;
  userPrompt: string;
  onSelectStyle: (style: string) => void;
  onPromptChange: (prompt: string) => void;
}) {
  return (
    <div className="mt-4 space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {styles.map((style) => (
          <button
            key={style.value}
            onClick={() => onSelectStyle(style.value)}
            className={`p-6 rounded-xl border-2 transition-all ${
              selectedStyle === style.value
                ? 'border-blue-600 bg-blue-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-4xl mb-2">{style.emoji}</div>
            <div className="font-semibold text-gray-900">{style.label}</div>
            <div className="text-xs text-gray-500 mt-1">{style.description}</div>
          </button>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          💬 추가 요청 (선택사항)
        </label>
        <textarea
          value={userPrompt}
          onChange={(e) => onPromptChange(e.target.value)}
          placeholder="예: 배경을 따뜻한 느낌으로"
          rows={3}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  );
}

function GenerateButton({
  onGenerate,
  disabled,
}: {
  onGenerate: () => void;
  disabled: boolean;
}) {
  return (
    <div className="mt-6">
      <button
        onClick={onGenerate}
        disabled={disabled}
        className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold text-lg hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        🎨 AI 광고 생성하기
      </button>
    </div>
  );
}