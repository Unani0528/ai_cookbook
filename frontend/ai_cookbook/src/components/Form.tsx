import React from 'react';
import { Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import type { RecipeFormData } from './types';

interface FormProps {
  formData: RecipeFormData;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onCookingLevelChange: (level: 'beginner' | 'intermediate' | 'advanced') => void;
  onSubmit: () => void;
  isLoading?: boolean;
}

const Form: React.FC<FormProps> = ({ formData, onInputChange, onCookingLevelChange, onSubmit, isLoading }) => {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-6 py-3 rounded-full mb-6">
          <Sparkles className="w-5 h-5" />
          <span className="font-semibold">AI 기반 맞춤형 레시피</span>
        </div>
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          당신만을 위한 레시피를<br />생성해드립니다
        </h2>
        <p className="text-lg text-gray-600">
          알레르기, 요리 실력, 취향을 입력하면 AI가 최적의 레시피를 만들어드립니다
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 space-y-8">
        {/* Step 1 */}
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-cyan-100 rounded-full flex items-center justify-center">
              <span className="text-cyan-600 font-bold">1</span>
            </div>
            <h3 className="text-xl font-bold text-gray-900">개인 정보 입력</h3>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">알레르기 정보</label>
            <input
              type="text"
              name="allergies"
              value={formData.allergies}
              onChange={onInputChange}
              placeholder="예: 땅콩, 갑각류, 유제품"
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition"
            />
            <p className="mt-2 text-sm text-gray-500">알레르기가 있는 재료를 쉼표로 구분하여 입력해주세요</p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">요리 실력</label>
            <div className="grid grid-cols-3 gap-3">
              {(['beginner', 'intermediate', 'advanced'] as const).map(level => (
                <button
                  key={level}
                  type="button"
                  onClick={() => onCookingLevelChange(level)}
                  className={`px-4 py-3 rounded-xl font-medium transition ${
                    formData.cookingLevel === level
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {level === 'beginner' && '초보'}
                  {level === 'intermediate' && '중수'}
                  {level === 'advanced' && '고수'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">요리 취향 및 선호사항</label>
            <textarea
              name="preferences"
              value={formData.preferences}
              onChange={onInputChange}
              placeholder="예: 매운 음식을 좋아함, 채식 선호, 저염식, 간단한 조리법 선호"
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none resize-none transition"
            />
          </div>
        </div>

        <div className="border-t border-gray-200"></div>

        {/* Step 2 */}
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-purple-600 font-bold">2</span>
            </div>
            <h3 className="text-xl font-bold text-gray-900">만들고 싶은 요리</h3>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">요리 이름</label>
            <input
              type="text"
              name="dishName"
              value={formData.dishName}
              onChange={onInputChange}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && formData.dishName.trim() && !isLoading) {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              placeholder="예: 비건 칠리, 김치찌개, 파스타"
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition text-lg"
            />
          </div>
        </div>

        <div className="bg-cyan-50 border border-cyan-200 rounded-xl p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-cyan-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-cyan-900">
            <strong className="font-semibold">참고:</strong> AI가 입력하신 정보를 분석하여 최적의 레시피와 단계별 이미지를 생성합니다. 생성에는 약 30초에서 1분 정도 소요됩니다.
          </div>
        </div>

        <button
          onClick={onSubmit}
          disabled={!formData.dishName.trim() || isLoading}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition duration-200 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>레시피 생성 중...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>AI 레시피 생성하기</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Form;
