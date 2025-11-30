import { useLocation, useNavigate } from "react-router-dom";
import RecipeResult from "./RecipeResult";

export default function RecipeResultPage() {
  const navigate = useNavigate();
  const { state } = useLocation();

  // recipe가 없으면 안전 처리
  if (!state || !state.recipe) {
    return <div>레시피 데이터가 없습니다. 처음부터 다시 시작해주세요.</div>;
  }

  const recipe = state.recipe;

  const getDifficultyLabel = (level: string) => {
    switch (level) {
      case "beginner":
        return "초급";
      case "intermediate":
        return "중급";
      case "advanced":
        return "고급";
      default:
        return "";
    }
  };

  return (
    <RecipeResult
      recipe={recipe}
      onReset={() => navigate("/")}
      getDifficultyLabel={getDifficultyLabel}
    />
  );
}
