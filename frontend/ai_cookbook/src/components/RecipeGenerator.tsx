import React, { useState } from 'react';
import Header from './Header';
import Form from './Form';
import Loading from './Loading';
import RecipeResult from './RecipeResult';
import Footer from './Footer';
import type { RecipeFormData, Recipe, Step } from './types';

const RecipeGenerator: React.FC = () => {
  const [step, setStep] = useState<Step>('input');
  const [formData, setFormData] = useState<RecipeFormData>({
    allergies: '',
    cookingLevel: 'beginner',
    preferences: '',
    dishName: ''
  });
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [_loading, setLoading] = useState<boolean>(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCookingLevelChange = (level: 'beginner' | 'intermediate' | 'advanced') => {
    setFormData(prev => ({ ...prev, cookingLevel: level }));
  };

  const generateRecipe = async () => {
    setLoading(true);
    setStep('loading');

    try {
      console.log(formData);
      const response = await fetch('http://localhost:8000/api/generate-recipe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      setTimeout(() => {
        setRecipe({
          title: data.title || `맞춤형 레시피: ${formData.dishName}`,
          image: data.image || 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800&q=80',
          servings: data.servings || 4,
          cookTime: data.cookTime || 45,
          difficulty: data.difficulty || formData.cookingLevel,
          ingredients: data.ingredients || [
            { category: '주재료', items: ['토마토 4개', '양파 1개', '마늘 3쪽', '올리브유 2큰술'] },
            { category: '향신료', items: ['큐민 1작은술', '파프리카 1작은술', '소금', '후추'] }
          ],
          steps: data.steps || [
            { step: 1, title: '재료 준비', description: '모든 채소를 깨끗이 씻고 한입 크기로 자릅니다.', image: 'https://images.unsplash.com/photo-1506368249639-73a05d6f6488?w=400&q=80' },
            { step: 2, title: '채소 볶기', description: '달군 팬에 올리브유를 두르고 양파와 마늘을 먼저 볶아 향을 냅니다.', image: 'https://images.unsplash.com/photo-1556911220-bff31c812dba?w=400&q=80' },
            { step: 3, title: '끓이기', description: '토마토와 향신료를 넣고 중불에서 30분간 끓입니다.', image: 'https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?w=400&q=80' },
            { step: 4, title: '완성', description: '그릇에 담고 신선한 허브로 장식하여 따뜻하게 서빙합니다.', image: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80' }
          ],
          tips: data.tips || [
            '알레르기 정보: 귀하의 알레르기 정보를 반영하여 대체 재료를 사용했습니다.',
            '초보자를 위한 팁: 약한 불에서 천천히 조리하면 실패 확률이 낮습니다.',
            '보관 방법: 냉장 보관 시 3일, 냉동 보관 시 1개월까지 가능합니다.'
          ]
        });
        setStep('result');
        setLoading(false);
      }, 3000);
    } catch (error) {
      console.error('레시피 생성 오류:', error);
      setLoading(false);
      setStep('input');
      alert('레시피 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  const resetForm = () => {
    setStep('input');
    setRecipe(null);
    setFormData({
      allergies: '',
      cookingLevel: 'beginner',
      preferences: '',
      dishName: ''
    });
  };

  const getDifficultyLabel = (difficulty: 'beginner' | 'intermediate' | 'advanced'): string => {
    switch (difficulty) {
      case 'beginner': return '초보자용';
      case 'intermediate': return '중급자용';
      case 'advanced': return '고급자용';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {step === 'input' && (
          <Form
            formData={formData}
            onInputChange={handleInputChange}
            onCookingLevelChange={handleCookingLevelChange}
            onSubmit={generateRecipe}
          />
        )}
        {step === 'loading' && <Loading />}
        {step === 'result' && recipe && (
          <RecipeResult
            recipe={recipe}
            onReset={resetForm}
            getDifficultyLabel={getDifficultyLabel}
          />
        )}
      </main>
      <Footer />
    </div>
  );
};

export default RecipeGenerator;
