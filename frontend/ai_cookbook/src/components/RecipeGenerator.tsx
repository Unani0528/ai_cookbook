import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Header';
import Form from './Form';
import Footer from './Footer';
import type { RecipeFormData } from './types';

const RecipeGenerator: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState<RecipeFormData>({
    allergies: '',
    cookingLevel: 'beginner',
    preferences: '',
    dishName: ''
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCookingLevelChange = (level: 'beginner' | 'intermediate' | 'advanced') => {
    setFormData(prev => ({ ...prev, cookingLevel: level }));
  };

  const generateRecipe = async () => {
    if (!formData.dishName.trim()) {
      alert('만들고 싶은 요리를 입력해주세요.');
      return;
    }

    setIsLoading(true);

    try {
      // 세션 초기화 API 호출
      const response = await fetch('http://localhost:8000/recipeChat/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          allergy: formData.allergies,
          preferences: formData.preferences,
          cooking_level: formData.cookingLevel,
          food_type: formData.dishName,
        }),
      });

      if (!response.ok) {
        throw new Error('세션 초기화 실패');
      }

      const data = await response.json();

      // 채팅 페이지로 이동 (세션 ID, 초기 메시지, formData 전달)
      navigate('/chat', {
        state: {
          sessionId: data.session_id,
          initialMessage: data.initial_message,
          formData: formData,
        },
      });
    } catch (error) {
      console.error('레시피 생성 오류:', error);
      setIsLoading(false);
      alert('레시피 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Form
          formData={formData}
          onInputChange={handleInputChange}
          onCookingLevelChange={handleCookingLevelChange}
          onSubmit={generateRecipe}
          isLoading={isLoading}
        />
      </main>
      <Footer />
    </div>
  );
};

export default RecipeGenerator;
