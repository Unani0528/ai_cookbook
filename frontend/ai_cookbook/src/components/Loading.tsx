import React from 'react';
import { UtensilsCrossed, Loader2 } from 'lucide-react';

const Loading: React.FC = () => (
  <div className="max-w-2xl mx-auto">
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-12 text-center">
      <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full mb-6 animate-pulse">
        <UtensilsCrossed className="w-10 h-10 text-white" />
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-3">레시피를 생성하고 있습니다</h3>
      <p className="text-gray-600 mb-8">AI가 당신만을 위한 맞춤형 레시피와 이미지를 만들고 있습니다</p>

      <div className="space-y-4 max-w-md mx-auto">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-cyan-500 animate-spin" />
          <span className="text-gray-700">레시피 분석 중...</span>
        </div>
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-cyan-500 animate-spin" />
          <span className="text-gray-700">재료 최적화 중...</span>
        </div>
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-cyan-500 animate-spin" />
          <span className="text-gray-700">단계별 이미지 생성 중...</span>
        </div>
      </div>
    </div>
  </div>
);

export default Loading;
