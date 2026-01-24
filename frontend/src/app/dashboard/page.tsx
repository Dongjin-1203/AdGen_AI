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

interface AdCopyData {
  headline: string;
  discount?: string;
  period?: string;
  brand?: string;
  caption?: string;
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
  const [generationId, setGenerationId] = useState<string>('');
  
  // ⭐ 캡션 관련 (NEW)
  const [captionId, setCaptionId] = useState<string>('');
  const [aiCaption, setAiCaption] = useState<string>('');
  const [finalCaption, setFinalCaption] = useState<string>('');
  
  // 광고 카피 관련
  const [adCopyData, setAdCopyData] = useState<AdCopyData | null>(null);
  const [htmlPreview, setHtmlPreview] = useState<string>('');
  const [templateUsed, setTemplateUsed] = useState<string>('');

  // 이미지 렌더링 관련
  const [finalImageUrl, setFinalImageUrl] = useState<string>('');
  const [isRendering, setIsRendering] = useState(false);

  // ===== 초기화 =====
  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    
    addStep({
      id: 'select-image',
      title: '1️⃣ 이미지 선택',
      status: 'processing',
      content: null,
      timestamp: new Date(),
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
    setProgress(20);

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

    setTimeout(() => {
      addStep({
        id: 'select-style',
        title: '2️⃣ AI 스타일 선택',
        status: 'processing',
        content: null,
        timestamp: new Date(),
      });
    }, 300);
  };

  // ===== Step 2: 스타일 선택 =====
  const handleSelectStyle = (style: string) => {
    setSelectedStyle(style);
    setProgress(40);

    const selectedStyleData = AVAILABLE_STYLES.find(s => s.value === style);

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

    setTimeout(() => {
      addStep({
        id: 'generate',
        title: '3️⃣ AI 광고 모델 생성',
        status: 'processing',
        content: null,
        timestamp: new Date(),
      });
    }, 300);
  };

  // ===== Step 3: AI 광고 모델 생성 =====
  const handleGenerate = async () => {
    if (!selectedContent || !selectedStyle) return;

    setProgress(50);

    updateStep('generate', {
      status: 'processing',
      content: (
        <div className="flex flex-col items-center py-8">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-gray-600">AI가 패션 모델 이미지를 생성하고 있습니다...</p>
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
        setGenerationId(data.history_id);
        setProgress(60);

        updateStep('generate', {
          status: 'completed',
          content: (
            <div className="space-y-4">
              <div className="relative w-full aspect-square max-w-2xl mx-auto">
                <Image
                  src={data.result_url}
                  alt="Generated Model Image"
                  fill
                  className="object-contain rounded-lg shadow-xl"
                />
              </div>
              <div className="text-center text-sm text-gray-600">
                ⏱️ 생성 시간: {data.processing_time?.toFixed(2)}초
              </div>
            </div>
          ),
        });

        // ⭐ Step 4 자동 시작: 캡션 생성
        setTimeout(() => {
          addStep({
            id: 'caption-generate',
            title: '4️⃣ 광고 캡션 생성',
            status: 'processing',
            content: null,
            timestamp: new Date(),
          });
          
          handleGenerateCaption(data.history_id);
        }, 500);
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

  // ===== 캡션 생성 =====
  const handleGenerateCaption = async (historyId: string) => {
    if (!selectedContent) return;

    setProgress(70);

    updateStep('caption-generate', {
      status: 'processing',
      content: (
        <div className="flex flex-col items-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-green-600 mb-4"></div>
          <p className="text-gray-600">GPT가 광고 캡션을 작성하고 있습니다...</p>
          <p className="text-sm text-gray-500 mt-2">평균 2-3초 소요됩니다</p>
        </div>
      ),
    });

    try {
      const response = await fetch(`${API_URL}/api/v1/caption`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content_id: selectedContent.content_id,
          generation_id: historyId,
          user_request: userPrompt || undefined,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCaptionId(data.caption_id);
        setAiCaption(data.ai_caption);
        setFinalCaption(data.ai_caption); // 초기값
        setProgress(75);

        updateStep('caption-generate', {
          status: 'completed',
          content: (
            <div className="bg-green-50 p-6 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">✨</span>
                <h4 className="font-bold text-lg text-gray-900">AI가 생성한 캡션</h4>
              </div>
              <p className="text-gray-800 text-lg leading-relaxed">
                {data.ai_caption}
              </p>
            </div>
          ),
        });

        // ⭐ Step 5 추가: 캡션 확정
        setTimeout(() => {
          addStep({
            id: 'caption-confirm',
            title: '5️⃣ 캡션 확정',
            status: 'processing',
            content: null,
            timestamp: new Date(),
          });
        }, 500);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Caption generation failed');
      }
    } catch (error) {
      updateStep('caption-generate', {
        status: 'error',
        content: (
          <div className="text-center py-8">
            <p className="text-red-600 font-semibold mb-4">❌ 캡션 생성 실패</p>
            <p className="text-gray-600 mb-4">
              {error instanceof Error ? error.message : '알 수 없는 오류'}
            </p>
            <button
              onClick={() => handleGenerateCaption(historyId)}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              다시 시도
            </button>
          </div>
        ),
      });
    }
  };

  // ===== ⭐ Step 5: 캡션 확정 (NEW) =====
  const handleConfirmCaption = async (useOriginal: boolean) => {
    if (!captionId) return;

    setProgress(85);

    const captionToConfirm = useOriginal ? aiCaption : finalCaption;

    try {
      const response = await fetch(`${API_URL}/api/v1/caption/confirm`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          caption_id: captionId,
          final_caption: captionToConfirm,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        updateStep('caption-confirm', {
          status: 'completed',
          content: (
            <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">✅</span>
                <h4 className="font-bold text-lg text-gray-900">
                  {data.is_modified ? '캡션 수정 완료' : '캡션 확정 완료'}
                </h4>
              </div>
              <p className="text-gray-800 text-lg leading-relaxed mb-3">
                {captionToConfirm}
              </p>
              <p className="text-sm text-gray-600">
                {data.is_modified 
                  ? '💡 수정된 캡션이 보상 학습 데이터로 저장되었습니다.'
                  : '🎯 AI 캡션이 그대로 사용됩니다.'}
              </p>
            </div>
          ),
        });

        // ⭐ Step 6 자동 시작: 최종 광고 생성
        setTimeout(() => {
          addStep({
            id: 'ad-copy',
            title: '6️⃣ 최종 광고 페이지 생성',
            status: 'processing',
            content: null,
            timestamp: new Date(),
          });
          
          handleGenerateAdCopy();
        }, 500);
      } else {
        throw new Error('Caption confirmation failed');
      }
    } catch (error) {
      updateStep('caption-confirm', {
        status: 'error',
        content: (
          <div className="text-center py-8">
            <p className="text-red-600 font-semibold mb-4">❌ 캡션 확정 실패</p>
            <p className="text-gray-600 mb-4">
              {error instanceof Error ? error.message : '알 수 없는 오류'}
            </p>
          </div>
        ),
      });
    }
  };

  // ===== ⭐ Step 6: 최종 광고 생성 (수정됨: caption_id 사용) =====
  const handleGenerateAdCopy = async () => {
    if (!captionId) {
      alert('캡션을 먼저 확정해주세요.');
      return;
    }

    setProgress(80);

    // Step 6: Minimal 템플릿 생성 + 저장
    addStep({
      id: 'ad-copy',
      title: '6️⃣ 광고 템플릿 생성',
      status: 'processing',
      content: (
        <div className="flex flex-col items-center py-8">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mb-4"></div>
          <p className="text-gray-600">Minimal 템플릿을 생성하고 있습니다...</p>
          <p className="text-sm text-gray-500 mt-2">평균 2-3초 소요됩니다</p>
        </div>
      ),
      timestamp: new Date()
    });

    try {
      // ✨ Minimal 템플릿 생성 (바로 저장됨)
      const response = await fetch(`${API_URL}/api/v1/ad-copy`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          caption_id: captionId,
          user_request: userPrompt || undefined
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // ✨ 응답 구조 변경: ad_copy_id를 바로 받음
        const adCopyId = data.ad_copy_id;
        
        setProgress(90);
        console.log(`✅ Minimal 템플릿 생성 완료 (${data.processing_time.toFixed(2)}초)`);

        // Step 6 완료
        updateStep('ad-copy', {
          status: 'completed',
          content: (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-green-600 font-semibold mb-2">
                  ✅ Minimal 템플릿 생성 완료
                </p>
                <p className="text-sm text-gray-600">
                  ⏱️ 생성 시간: {data.processing_time.toFixed(2)}초
                </p>
              </div>
              
              {/* Minimal 템플릿 미리보기 */}
              <div className="border-2 border-purple-200 rounded-lg overflow-hidden">
                <div className="aspect-square bg-gray-50">
                  <iframe
                    srcDoc={data.html_content}
                    className="w-full h-full pointer-events-none"
                    title="Minimal Clean"
                    sandbox="allow-same-origin"
                  />
                </div>
              </div>
              
              {/* 광고 카피 정보 */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-lg border border-purple-100">
                <h5 className="font-semibold text-gray-900 mb-2">📝 광고 카피</h5>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">헤드라인:</span>
                    <p className="font-semibold text-gray-900">{data.ad_copy.headline}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">할인:</span>
                    <p className="font-semibold text-red-600">{data.ad_copy.discount}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">기간:</span>
                    <p className="text-gray-700">{data.ad_copy.period}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">브랜드:</span>
                    <p className="text-gray-800">{data.ad_copy.brand}</p>
                  </div>
                </div>
              </div>
            </div>
          ),
        });

        // ✨ /ad-copy/save 호출 제거 - 바로 PNG 생성으로 진행
        setTimeout(async () => {
          try {
            // Step 7: PNG 이미지 생성
            addStep({
              id: 'render-image',
              title: '7️⃣ PNG 이미지 생성',
              status: 'processing',
              content: (
                <div className="flex flex-col items-center py-8">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-green-600 mb-4"></div>
                  <p className="text-gray-600">고품질 PNG 이미지를 생성하고 있습니다...</p>
                  <p className="text-sm text-gray-500 mt-2">평균 2-3초 소요됩니다</p>
                </div>
              ),
              timestamp: new Date()
            });

            // PNG 이미지 생성
            const renderResponse = await fetch(`${API_URL}/api/v1/render-image`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                ad_copy_id: adCopyId
              })
            });

            if (renderResponse.ok) {
              const renderData = await renderResponse.json();
              setFinalImageUrl(renderData.image_url);
              setProgress(100);

              console.log(`✅ PNG 생성 완료: ${renderData.processing_time.toFixed(2)}초`);

              // Step 7 완료
              updateStep('render-image', {
                status: 'completed',
                content: (
                  <div className="text-center py-2">
                    <p className="text-green-600">✅ PNG 생성 완료 ({renderData.processing_time.toFixed(2)}초)</p>
                  </div>
                ),
              });

              // Step 8: 최종 완료
              setTimeout(() => {
                addStep({
                  id: 'final',
                  title: '✅ 완료',
                  status: 'completed',
                  content: (
                    <FinalImageResult
                      imageUrl={renderData.image_url}
                      adCopyId={adCopyId}
                      onReset={handleReset}
                    />
                  ),
                  timestamp: new Date()
                });
              }, 500);

            } else {
              throw new Error('PNG 생성 실패');
            }

          } catch (error) {
            console.error('PNG generation error:', error);
            updateStep('render-image', {
              status: 'error',
              content: (
                <div className="text-center py-8">
                  <p className="text-red-600 font-semibold mb-4">❌ PNG 생성 실패</p>
                  <button
                    onClick={handleGenerateAdCopy}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    다시 시도
                  </button>
                </div>
              ),
            });
          }
        }, 500);

      } else {
        throw new Error('템플릿 생성 실패');
      }

    } catch (error) {
      console.error('Ad Copy generation error:', error);
      updateStep('ad-copy', {
        status: 'error',
        content: (
          <div className="text-center py-8">
            <p className="text-red-600 font-semibold mb-4">❌ 템플릿 생성 실패</p>
            <button
              onClick={handleGenerateAdCopy}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
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
    setGenerationId('');
    setCaptionId('');
    setAiCaption('');
    setFinalCaption('');
    setAdCopyData(null);
    setHtmlPreview('');
    setTemplateUsed('');
    setFinalImageUrl('');      
    
    addStep({
      id: 'select-image',
      title: '1️⃣ 이미지 선택',
      status: 'processing',
      content: null,
      timestamp: new Date(),
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
              onCaptionConfirm={step.id === 'caption-confirm' && step.status === 'processing' ? (
                <CaptionEditor
                  aiCaption={aiCaption}
                  finalCaption={finalCaption}
                  onCaptionChange={setFinalCaption}
                  onConfirm={handleConfirmCaption}
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
  onCaptionConfirm,
}: {
  step: StepData;
  isLast: boolean;
  onSelectImage?: React.ReactNode;
  onSelectStyle?: React.ReactNode;
  onGenerate?: React.ReactNode;
  onCaptionConfirm?: React.ReactNode;
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
      {onCaptionConfirm}
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
        🎨 AI 패션 모델 생성하기
      </button>
    </div>
  );
}

// ===== 1. 모델 이미지 선택 컴포넌트 =====
function ModelImageSelector({
  images,
  selectedImage,
  onSelect,
}: {
  images: { history_id: string; result_url: string }[];
  selectedImage: string | null;
  onSelect: (historyId: string, url: string) => void;
}) {
  return (
    <div className="mt-4">
      <h4 className="font-semibold mb-3 text-gray-900">
        ✨ 생성된 모델 이미지 ({images.length}개)
      </h4>
      <p className="text-sm text-gray-600 mb-4">
        마음에 드는 이미지를 선택하세요
      </p>
      
      <div className="grid grid-cols-3 gap-4">
        {images.map((image, idx) => (
          <button
            key={image.history_id}
            onClick={() => onSelect(image.history_id, image.result_url)}
            className={`relative rounded-lg overflow-hidden border-4 transition-all hover:shadow-lg ${
              selectedImage === image.result_url
                ? 'border-blue-600 shadow-xl'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="aspect-square relative">
              <Image
                src={image.result_url}
                alt={`Model ${idx + 1}`}
                fill
                className="object-cover"
              />
            </div>
            {selectedImage === image.result_url && (
              <div className="absolute top-2 right-2 bg-blue-600 text-white rounded-full p-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
                </svg>
              </div>
            )}
            <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
              이미지 {idx + 1}
            </div>
          </button>
        ))}
      </div>
      
      {selectedImage && (
        <button
          onClick={() => {/* 다음 단계로 */}}
          className="w-full mt-6 py-4 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700"
        >
          선택 완료 ✓
        </button>
      )}
    </div>
  );
}

// ===== ⭐ 캡션 편집 컴포넌트 (NEW) =====
function CaptionEditor({
  aiCaption,
  finalCaption,
  onCaptionChange,
  onConfirm,
}: {
  aiCaption: string;
  finalCaption: string;
  onCaptionChange: (caption: string) => void;
  onConfirm: (useOriginal: boolean) => void;
}) {
  return (
    <div className="mt-4 space-y-4">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800 mb-2">
          💡 AI가 생성한 캡션을 확인하고, 필요시 수정하세요!
        </p>
        <p className="text-xs text-yellow-700">
          수정한 내용은 AI 학습에 활용되어 더 나은 캡션을 만드는 데 도움이 됩니다.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          ✏️ 캡션 수정
        </label>
        <textarea
          value={finalCaption}
          onChange={(e) => onCaptionChange(e.target.value)}
          rows={3}
          className="w-full p-4 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
          placeholder="캡션을 입력하세요..."
        />
        <p className="text-xs text-gray-500 mt-1">
          현재 길이: {finalCaption.length}자
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => onConfirm(true)}
          className="py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition flex items-center justify-center gap-2"
        >
          <span>✅</span>
          <span>그대로 사용</span>
        </button>
        
        <button
          onClick={() => onConfirm(false)}
          disabled={finalCaption === aiCaption}
          className="py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>✏️</span>
          <span>수정 완료</span>
        </button>
      </div>
    </div>
  );
}

// ===== 3. 최종 결과 컴포넌트 =====
function FinalResult({
  imageUrl,
  templateUsed,
  adCopyId,
  onReset,
}: {
  imageUrl: string;
  templateUsed: string;
  adCopyId: string;
  onReset: () => void;
}) {
  return (
    <div className="space-y-6">
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <h4 className="font-bold text-xl text-green-900">광고 생성 완료!</h4>
            <p className="text-green-700 text-sm">이미지가 저장되었습니다</p>
          </div>
        </div>
      </div>

      {/* 생성된 이미지 */}
      <div>
        <h4 className="font-semibold mb-3 text-gray-900">📸 최종 광고 이미지 (1080×1080px)</h4>
        <div className="border-4 border-gray-200 rounded-lg overflow-hidden shadow-xl">
          <Image
            src={imageUrl}
            alt="Final Ad"
            width={1080}
            height={1080}
            className="w-full"
          />
        </div>
      </div>

      {/* 액션 버튼 */}
      <div className="grid grid-cols-3 gap-3">
        <a
          href={imageUrl}
          download
          className="py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition flex items-center justify-center gap-2"
        >
          <span>💾</span>
          <span>다운로드</span>
        </a>
        
        <Link
          href="/history"
          className="py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition flex items-center justify-center gap-2"
        >
          <span>📜</span>
          <span>히스토리</span>
        </Link>
        
        <button
          onClick={onReset}
          className="py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition flex items-center justify-center gap-2"
        >
          <span>🎨</span>
          <span>새로 만들기</span>
        </button>
      </div>

      {/* 추가 정보 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <span>ℹ️</span> 광고 정보
        </h5>
        <div className="text-sm text-blue-800 space-y-1">
          <p>• 템플릿: {templateUsed}</p>
          <p>• ID: {adCopyId}</p>
          <p>• 이미지 URL: <a href={imageUrl} target="_blank" rel="noopener noreferrer" className="underline">링크</a></p>
        </div>
      </div>
    </div>
  );
}

// ===== 광고 카피 미리보기 컴포넌트 =====
function AdCopyPreview({
  adCopy,
  htmlPreview,
  templateUsed,
  generatedImageUrl,
  onReset,
}: {
  adCopy: AdCopyData;
  htmlPreview: string;
  templateUsed: string;
  generatedImageUrl: string;
  onReset: () => void;
}) {
  const templateDisplayNames: { [key: string]: string } = {
    minimal: 'Minimal Clean',
    bold: 'Bold Impact',
    vintage: 'Vintage Sepia',
  };

  return (
    <div className="space-y-6">
      {/* 광고 카피 정보 */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg border border-purple-100">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">✨</span>
          <h4 className="font-bold text-lg">생성된 광고 카피</h4>
          <span className="text-xs bg-white px-3 py-1 rounded-full text-gray-600 border border-gray-200">
            {templateDisplayNames[templateUsed] || templateUsed}
          </span>
        </div>
        
        <div className="space-y-3">
          <div>
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">헤드라인</span>
            <p className="text-xl font-bold text-gray-900 mt-1">{adCopy.headline}</p>
          </div>
          
          {adCopy.discount && (
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">할인</span>
              <p className="text-lg font-semibold text-red-600 mt-1">{adCopy.discount}</p>
            </div>
          )}
          
          {adCopy.period && (
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">기간</span>
              <p className="text-sm text-gray-700 mt-1">{adCopy.period}</p>
            </div>
          )}
          
          {adCopy.brand && (
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">브랜드</span>
              <p className="text-sm font-medium text-gray-800 mt-1">{adCopy.brand}</p>
            </div>
          )}
          
          {adCopy.caption && (
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">캡션</span>
              <p className="text-gray-700 mt-1 leading-relaxed">{adCopy.caption}</p>
            </div>
          )}
        </div>
      </div>

      {/* HTML 미리보기 */}
      <div>
        <h4 className="font-semibold mb-3 flex items-center gap-2 text-gray-900">
          <span>🎨</span> 광고 디자인 미리보기 (1080×1080px)
        </h4>
        <div className="border-4 border-gray-200 rounded-lg overflow-hidden shadow-lg bg-gray-50">
          <iframe
            srcDoc={htmlPreview}
            className="w-full aspect-square"
            title="Ad Preview"
            sandbox="allow-same-origin"
          />
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">
          💡 이 디자인은 인스타그램 정사각형 포맷(1:1)에 최적화되어 있습니다
        </p>
      </div>

      {/* 액션 버튼 */}
      <div className="grid grid-cols-3 gap-3">
        <button
          onClick={() => {
            const blob = new Blob([htmlPreview], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ad-${templateUsed}-${Date.now()}.html`;
            a.click();
            URL.revokeObjectURL(url);
          }}
          className="py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition flex items-center justify-center gap-2"
        >
          <span>💾</span>
          <span>HTML 다운로드</span>
        </button>
        
        <Link
          href="/history"
          className="py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition flex items-center justify-center gap-2"
        >
          <span>📜</span>
          <span>히스토리</span>
        </Link>
        
        <button
          onClick={onReset}
          className="py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition flex items-center justify-center gap-2"
        >
          <span>🎨</span>
          <span>새로 만들기</span>
        </button>
      </div>

      {/* 추가 정보 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <span>💡</span> 다음 단계
        </h5>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• HTML 파일을 다운로드하여 웹사이트에 바로 사용하세요</li>
          <li>• 이미지로 변환하여 소셜 미디어에 업로드하세요</li>
          <li>• 디자인 편집 툴로 추가 커스터마이징도 가능합니다</li>
        </ul>
      </div>
    </div>
  );
}

// ===== 4. 최종 결과 컴포넌트 =====
function FinalImageResult({
  imageUrl,
  adCopyId,
  onReset
}: {
  imageUrl: string;
  adCopyId: string;
  onReset: () => void;
}) {
  return (
    <div className="space-y-6">
      {/* 완료 메시지 */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <h4 className="font-bold text-xl text-green-900">광고 생성 완료!</h4>
            <p className="text-green-700 text-sm">이미지가 준비되었습니다</p>
          </div>
        </div>
      </div>

      {/* 생성된 이미지 */}
      <div>
        <h4 className="font-semibold mb-3 text-gray-900">
          📸 최종 광고 이미지 (1080×1080px)
        </h4>
        <div className="border-4 border-gray-200 rounded-lg overflow-hidden shadow-xl">
          <Image
            src={imageUrl}
            alt="Final Ad"
            width={1080}
            height={1080}
            className="w-full"
          />
        </div>
      </div>

      {/* 액션 버튼 */}
      <div className="grid grid-cols-3 gap-3">
        <a
          href={imageUrl}
          download
          target="_blank"
          rel="noopener noreferrer"
          className="py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition flex items-center justify-center gap-2"
        >
          <span>💾</span>
          <span>다운로드</span>
        </a>
        
        <Link
          href="/history"
          className="py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition flex items-center justify-center gap-2"
        >
          <span>📜</span>
          <span>히스토리</span>
        </Link>
        
        <button
          onClick={onReset}
          className="py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition flex items-center justify-center gap-2"
        >
          <span>🎨</span>
          <span>새로 만들기</span>
        </button>
      </div>

      {/* 추가 정보 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <span>ℹ️</span> 이미지 정보
        </h5>
        <div className="text-sm text-blue-800 space-y-1">
          <p>• 해상도: 1080×1080px (Instagram 최적화)</p>
          <p>• 형식: PNG (고품질)</p>
          <p>• ID: {adCopyId}</p>
        </div>
      </div>
    </div>
  );
}