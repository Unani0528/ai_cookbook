from pydantic import BaseModel, Field
from typing import List, Optional

class RecipeRequest(BaseModel):
    """프론트엔드와 호환되는 RecipeRequest (camelCase)"""
    dishName: str
    allergies: str = "특이사항 없음"
    cookingLevel: str = "beginner"  # 'beginner' | 'intermediate' | 'advanced'
    preferences: str = "특이사항 없음"
