import { useLocation, useNavigate } from "react-router-dom";
import Header from "./Header";
import Footer from "./Footer";

export default function RecipeResultPage() {
  const navigate = useNavigate();
  const { state } = useLocation();

  // recipe가 없으면 안전 처리
  if (!state || !state.recipe) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">레시피 데이터가 없습니다.</h2>
          <button
            onClick={() => navigate("/")}
            className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-6 py-3 rounded-xl"
          >
            처음부터 다시 시작
          </button>
        </div>
      </div>
    );
  }

  const recipe = state.recipe;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">{recipe.title}</h1>

          {recipe.image && (
            <img
              src={recipe.image}
              alt={recipe.title}
              className="w-full h-auto rounded-lg mb-6"
            />
          )}

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">인분</p>
              <p className="text-xl font-semibold">{recipe.servings}인분</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">조리시간</p>
              <p className="text-xl font-semibold">{recipe.cookTime}분</p>
            </div>
          </div>

          {recipe.ingredients && (
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">재료</h2>
              {recipe.ingredients.map((group: any, idx: number) => (
                <div key={idx} className="mb-4">
                  <h3 className="font-semibold text-lg text-gray-700 mb-2">{group.category}</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {group.items.map((item: string, i: number) => (
                      <li key={i} className="text-gray-600">{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}

          {recipe.steps && (
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">조리 순서</h2>
              {recipe.steps.map((step: any, idx: number) => (
                <div key={idx} className="mb-6 border-l-4 border-cyan-500 pl-4">
                  <h3 className="font-semibold text-lg text-gray-700 mb-2">
                    {step.step}. {step.description}
                  </h3>
                  {step.image && (
                    <img
                      src={step.image}
                      alt={`Step ${step.step}`}
                      className="w-full h-auto rounded-lg mt-2"
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {recipe.tips && (
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">팁</h2>
              <ul className="space-y-2">
                {recipe.tips.map((tip: string, idx: number) => (
                  <li key={idx} className="bg-yellow-50 p-3 rounded-lg text-gray-700">
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={() => navigate("/")}
            className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold py-3 px-6 rounded-xl shadow-lg hover:shadow-xl transition"
          >
            새로운 레시피 만들기
          </button>
        </div>
      </main>
      <Footer />
    </div>
  );
}
