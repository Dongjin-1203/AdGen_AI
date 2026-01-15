'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

// ⭐ API_URL 정의
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface VisionResult {
  category: string;
  sub_category: string;
  color: string;
  material: string;
  fit: string;
  style_tags: string[];
  confidence: number;
}

export default function UploadPage() {
  const router = useRouter();
  const { user, token } = useAuthStore();

  // 1단계: 파일 업로드
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // 2단계: Vision AI 분석 결과
  const [visionResult, setVisionResult] = useState<VisionResult | null>(null);
  const [uploadedContentId, setUploadedContentId] = useState<string>('');
  
  // 3단계: 사용자 수정
  const [productName, setProductName] = useState('');
  const [category, setCategory] = useState('');
  const [subCategory, setSubCategory] = useState('');
  const [color, setColor] = useState('');
  const [material, setMaterial] = useState('');
  const [fit, setFit] = useState('');
  const [styleTags, setStyleTags] = useState<string[]>([]);
  const [price, setPrice] = useState('');
  
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const handleSaveOptional = async () => {
    if (!uploadedContentId) return;

    try {
      const formData = new FormData();
      if (productName) formData.append('product_name', productName);
      if (price) formData.append('price', price);

      const response = await fetch(`${API_URL}/api/contents/${uploadedContentId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        alert('저장되었습니다!');
      }
    } catch (err) {
      console.error('저장 실패:', err);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setFile(droppedFile);
      setPreviewUrl(URL.createObjectURL(droppedFile));
    }
  };

  // ⭐ 1단계: 업로드 + Vision AI 분석
  const handleUpload = async () => {
    if (!file) {
      setError('이미지를 선택해주세요.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('📤 업로드 시작...');
      
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/api/contents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      console.log('📡 응답 상태:', response.status);

      if (!response.ok) {
        throw new Error('업로드 실패');
      }

      const data = await response.json();
      
      console.log('=== Backend 응답 ===');
      console.log(data);
      console.log('==================');
      
      // Vision AI 결과 저장
      setUploadedContentId(data.content_id);
      
      // ⭐ style_tags 안전한 파싱
      let tags: string[] = [];
      if (data.style_tags) {
        try {
          tags = typeof data.style_tags === 'string' 
            ? JSON.parse(data.style_tags) 
            : data.style_tags;
        } catch (e) {
          console.error('style_tags 파싱 실패:', e);
          tags = [];
        }
      }
      
      setVisionResult({
        category: data.category || '',
        sub_category: data.sub_category || '',
        color: data.color || '',
        material: data.material || '',
        fit: data.fit || '',
        style_tags: tags,
        confidence: data.ai_confidence || 0,
      });
      
      // 폼 초기값 설정
      setCategory(data.category || '');
      setSubCategory(data.sub_category || '');
      setColor(data.color || '');
      setMaterial(data.material || '');
      setFit(data.fit || '');
      setStyleTags(tags);
      
      console.log('✅ Vision AI 결과 저장 완료');
      
      // 2단계로 이동
      setStep(2);
      
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.message || '업로드에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8">이미지 업로드</h1>

        {error && (
          <div className="p-3 mb-4 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* 1단계: 이미지 업로드 */}
        {step === 1 && (
          <div className="space-y-6">
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
                isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
              }`}
              onClick={() => document.getElementById('fileInput')?.click()}
            >
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="max-h-96 mx-auto rounded-lg"
                />
              ) : (
                <div>
                  <p className="text-6xl mb-4">📷</p>
                  <p className="text-xl text-gray-600 mb-2">
                    클릭하거나 이미지를 드래그하세요
                  </p>
                  <p className="text-sm text-gray-400">
                    JPG, PNG, GIF, WEBP (최대 10MB)
                  </p>
                </div>
              )}
            </div>

            <input
              id="fileInput"
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />

            {file && (
              <button
                type="button"
                onClick={handleUpload}
                disabled={loading}
                className="w-full py-4 bg-blue-600 text-white rounded-lg text-lg font-bold hover:bg-blue-700 disabled:bg-gray-400 transition"
              >
                {loading ? '분석 중... 🔍' : '업로드 후 AI 분석 시작'}
              </button>
            )}
          </div>
        )}

        {/* 2단계: Vision AI 결과 확인 */}
        {step === 2 && visionResult && (
          <div className="space-y-6">
            {/* AI 분석 결과 요약 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-2xl">🤖</span>
                <h2 className="text-xl font-bold text-blue-900">AI 분석 완료!</h2>
              </div>
              <p className="text-blue-800 mb-2">
                신뢰도: <strong>{(visionResult.confidence * 100).toFixed(1)}%</strong>
              </p>
              <p className="text-sm text-blue-600">
                분석 결과가 자동으로 저장되었습니다. 갤러리에서 확인하세요!
              </p>
            </div>

            {/* 미리보기 */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <img
                src={previewUrl!}
                alt="Uploaded"
                className="max-h-64 mx-auto rounded-lg"
              />
            </div>

            {/* AI 분석 결과 표시 (읽기 전용) */}
            <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
              <h3 className="text-lg font-bold mb-4">AI 분석 결과</h3>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    카테고리
                  </label>
                  <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                    {category || '-'}
                  </div>
                </div>

                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    세부 카테고리
                  </label>
                  <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                    {subCategory || '-'}
                  </div>
                </div>

                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    색상
                  </label>
                  <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                    {color || '-'}
                  </div>
                </div>

                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    소재
                  </label>
                  <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                    {material || '-'}
                  </div>
                </div>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  핏/스타일
                </label>
                <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                  {fit || '-'}
                </div>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  스타일 태그
                </label>
                <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                  {styleTags.length > 0 ? styleTags.join(', ') : '-'}
                </div>
              </div>

              <p className="text-xs text-gray-500 mt-4">
                💡 갤러리에서 상세 정보를 수정할 수 있습니다
              </p>
            </div>

            {/* 추가 정보 입력 필드 */}
            <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
              <h3 className="text-lg font-bold mb-4">추가 정보 (선택)</h3>

              <div>
                <label htmlFor="product-name" className="block mb-2 text-sm font-medium text-gray-700">
                  상품명 (선택)
                </label>
                <input
                  id="product-name"
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="예: 베이지 니트"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label htmlFor="price" className="block mb-2 text-sm font-medium text-gray-700">
                  가격 (선택)
                </label>
                <input
                  id="price"
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="190000"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* 버튼 */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setStep(1);
                  setFile(null);
                  setPreviewUrl(null);
                  setVisionResult(null);
                }}
                className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition"
              >
                다시 업로드
              </button>
              
              {/* 저장 버튼 (선택사항 있을 때만) */}
              {(productName || price) && (
                <button
                  type="button"
                  onClick={handleSaveOptional}
                  className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition"
                >
                  저장하기
                </button>
              )}
              
              <button
                type="button"
                onClick={() => {
                  console.log('✅ 갤러리로 이동');
                  router.push('/gallery');
                }}
                className="flex-1 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition"
              >
                ✅ 갤러리 확인하기
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}