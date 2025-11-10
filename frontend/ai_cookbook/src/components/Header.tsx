import React from 'react';
import { ChefHat } from 'lucide-react';

const Header: React.FC = () => (
  <header className="bg-white shadow-sm border-b border-gray-200">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-xl flex items-center justify-center">
          <ChefHat className="w-7 h-7 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Recipe Generator</h1>
          <p className="text-sm text-gray-500">맞춤형 레시피를 자동으로 생성합니다</p>
        </div>
      </div>
    </div>
  </header>
);

export default Header;