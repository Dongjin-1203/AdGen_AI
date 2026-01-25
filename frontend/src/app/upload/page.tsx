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
  const [selectedCategory, setSelectedCategory] = useState<string>(''); // ⭐ 카테고리 선택
  
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
  
  // ⭐ 편집 모드 상태
  const [isEditing, setIsEditing] = useState(false);
  
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  // ⭐ AI 분석 결과 저장 (수정사항 포함)
  const handleSaveAnalysis = async () => {
    if (!uploadedContentId) return;

    try {
      setLoading(true);
      
      const formData = new FormData();
      formData.append('category', category);
      formData.append('sub_category', subCategory);
      formData.append('color', color);
      formData.append('material', material);
      formData.append('fit', fit);
      formData.append('style_tags', JSON.stringify(styleTags));
      
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
        alert('✅ 저장되었습니다!');
        setIsEditing(false);
      } else {
        throw new Error('저장 실패');
      }
    } catch (err) {
      console.error('저장 실패:', err);
      alert('❌ 저장에 실패했습니다.');
    } finally {
      setLoading(false);
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

  // ⭐ 1단계: 업로드 + Vision AI 분석 (카테고리 포함)
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
      
      // ⭐ 카테고리 전달 (Few-shot Learning 활성화)
      if (selectedCategory) {
        formData.append('category', selectedCategory);
        console.log('🎯 카테고리 전달:', selectedCategory);
      }

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

            {/* ⭐ 카테고리 선택 (Few-shot Learning 활성화) */}
            {file && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  제품 카테고리 (선택) <span className="text-blue-600">✨ AI 정확도 향상</span>
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-lg"
                >
                  <option value="">선택 안함</option>
                  <option value="상의">상의</option>
                  <option value="하의">하의</option>
                  <option value="아우터">아우터</option>
                  <option value="원피스">원피스</option>
                  <option value="신발">신발</option>
                  <option value="가방">가방</option>
                  <option value="액세서리">액세서리</option>
                </select>
                <p className="mt-2 text-xs text-gray-500">
                  💡 카테고리를 선택하면 AI가 더 정확하게 분석합니다 (Few-shot Learning)
                </p>
              </div>
            )}

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
            {/* 미리보기 */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <img
                src={previewUrl!}
                alt="Uploaded"
                className="max-h-64 mx-auto rounded-lg"
              />
            </div>

            {/* ⭐ AI 분석 결과 (편집 가능) */}
            <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold">AI 분석 결과</h3>
                {!isEditing ? (
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
                  >
                    ✏️ 수정
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setIsEditing(false)}
                      className="px-4 py-2 bg-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-400 transition"
                    >
                      취소
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveAnalysis}
                      disabled={loading}
                      className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition"
                    >
                      {loading ? '저장 중...' : '💾 저장'}
                    </button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* 카테고리 */}
                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    카테고리
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                      {category || '-'}
                    </div>
                  )}
                </div>

                {/* 세부 카테고리 */}
                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    세부 카테고리
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={subCategory}
                      onChange={(e) => setSubCategory(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                      {subCategory || '-'}
                    </div>
                  )}
                </div>

                {/* 색상 */}
                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    색상
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={color}
                      onChange={(e) => setColor(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                      {color || '-'}
                    </div>
                  )}
                </div>

                {/* 소재 */}
                <div>
                  <label className="block mb-2 text-sm font-medium text-gray-700">
                    소재
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={material}
                      onChange={(e) => setMaterial(e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                      {material || '-'}
                    </div>
                  )}
                </div>
              </div>

              {/* 핏/스타일 */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  핏/스타일
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={fit}
                    onChange={(e) => setFit(e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                    {fit || '-'}
                  </div>
                )}
              </div>

              {/* 스타일 태그 */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  스타일 태그
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={styleTags.join(', ')}
                    onChange={(e) => setStyleTags(e.target.value.split(',').map(t => t.trim()))}
                    placeholder="쉼표로 구분: 캐주얼, 데일리"
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <div className="px-4 py-2 border rounded-lg bg-yellow-50 font-medium">
                    {styleTags.length > 0 ? styleTags.join(', ') : '-'}
                  </div>
                )}
              </div>

              {!isEditing && (
                <p className="text-xs text-gray-500 mt-4">
                  💡 결과가 정확하지 않다면 수정 버튼을 눌러 수정하세요
                </p>
              )}
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
                  setIsEditing(false);
                  setSelectedCategory('');
                }}
                className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition"
              >
                다시 업로드
              </button>
              
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