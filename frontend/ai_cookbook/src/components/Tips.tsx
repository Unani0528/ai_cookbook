import React from 'react';
import { Sparkles } from 'lucide-react';

interface TipsProps {
  tips: string[];
}

const Tips: React.FC<TipsProps> = ({ tips }) => (
  <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-2xl border border-cyan-200 p-8">
    <h3 className="text-2xl font-bold text-gray-900 mb-4">맞춤형 팁 & 참고사항</h3>
    <div className="space-y-3">
      {tips.map((tip, idx) => (
        <div key={idx} className="flex gap-3">
          <Sparkles className="w-5 h-5 text-cyan-600 flex-shrink-0 mt-0.5" />
          <p className="text-gray-700">{tip}</p>
        </div>
      ))}
    </div>
  </div>
);

export default Tips;
