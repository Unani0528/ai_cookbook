import React from 'react';
import { Clock, Users } from 'lucide-react';
import type { Recipe } from './types';
import Tips from './Tips';

interface RecipeResultProps {
  recipe: Recipe;
  onReset: () => void;
  getDifficultyLabel: (difficulty: 'beginner' | 'intermediate' | 'advanced') => string;
}

const RecipeResult: React.FC<RecipeResultProps> = ({ recipe, onReset, getDifficultyLabel }) => (
  <div className="space-y-8">
    <div className="flex items-center justify-between">
      <button
        onClick={onReset}
        className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 transition"
      >
        <span>← 새 레시피 만들기</span>
      </button>
    </div>

    <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
      <div className="relative h-96">
        <img src={recipe.image} alt={recipe.title} className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent"></div>
        <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
          <h2 className="text-4xl font-bold mb-2">{recipe.title}</h2>
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>{recipe.cookTime}분</span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              <span>{recipe.servings}인분</span>
            </div>
            <div className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full">
              {getDifficultyLabel(recipe.difficulty)}
            </div>
          </div>
        </div>
      </div>

      <div className="p-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-6">재료</h3>
        <div className="grid md:grid-cols-2 gap-6">
          {recipe.ingredients.map((group, idx) => (
            <div key={idx} className="bg-gray-50 rounded-xl p-5">
              <h4 className="font-bold text-gray-900 mb-3">{group.category}</h4>
              <ul className="space-y-2">
                {group.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-center gap-2 text-gray-700">
                    <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full"></span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>

    <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
      <h3 className="text-2xl font-bold text-gray-900 mb-6">조리 과정</h3>
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {recipe.steps.map((step) => (
          <div key={step.step} className="bg-gray-50 rounded-xl overflow-hidden">
            <img src={step.image} alt={step.title} className="w-full h-48 object-cover" />
            <div className="p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  {step.step}
                </div>
                <h4 className="font-bold text-gray-900">{step.title}</h4>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>

    <Tips tips={recipe.tips} />

    <div className="flex gap-4 justify-center">
      <button
        onClick={onReset}
        className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition"
      >
        새 레시피 만들기
      </button>
    </div>
  </div>
);

export default RecipeResult;
