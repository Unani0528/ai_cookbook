export interface RecipeFormData {
  allergies: string;
  cookingLevel: 'beginner' | 'intermediate' | 'advanced';
  preferences: string;
  dishName: string;
}

export interface IngredientGroup {
  category: string;
  items: string[];
}

export interface RecipeStep {
  step: number;
  title: string;
  description: string;
  image: string;
}

export interface Recipe {
  title: string;
  image: string;
  servings: number;
  cookTime: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  ingredients: IngredientGroup[];
  steps: RecipeStep[];
  tips: string[];
}

export type Step = 'input' | 'loading' | 'result';