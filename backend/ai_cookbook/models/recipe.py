from pydantic import BaseModel, Field
from typing import Optional, List, Literal
"""
API 요청/응답 모델 정의
- 3페이지 흐름: 초기화 → 채팅 → 최종 레시피
"""
# ============ 1페이지: 세션 초기화 ============

class InitSessionRequest(BaseModel):
    """1페이지 - 세션 초기화 요청"""
    allergy: str = Field(
        default="",
        description="알러지 목록",
        example="땅콩, 갑각류",
    )
    preferences: str = Field(
        default="",
        description="사용자 취향/선호사항",
        example="매운 음식 선호, 채식 위주",
    )
    cooking_level: Literal["beginner", "intermediate", "advanced"] = Field(
        default="beginner",
        description="요리 숙련도",
    )
    food_type: str = Field(
        ...,
        description="만들고자 하는 음식 종류",
        example="토마토 스파게티",
    )


class InitSessionResponse(BaseModel):
    """1페이지 - 세션 초기화 응답"""
    session_id: str
    initial_message: str = Field(
        description="첫 번째 레시피 추천 메시지",
    )
    message: str


# ============ 2페이지: 채팅 ============

class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str = Field(
        ...,
        description="사용자 메시지",
        example="양파는 빼고 만들어줘",
    )


class ChatResponse(BaseModel):
    """채팅 응답"""
    session_id: str
    response: str = Field(description="챗봇 응답")
    is_recipe: bool = Field(default=False, description="레시피 응답 여부")


class ChatHistoryItem(BaseModel):
    """채팅 히스토리 항목"""
    role: Literal["user", "assistant"]
    content: str


class ChatHistoryResponse(BaseModel):
    """채팅 히스토리 응답"""
    session_id: str
    history: List[ChatHistoryItem]


# ============ 2→3페이지: 레시피 확정 ============

class FinalRecipeRequest(BaseModel):
    """레시피 확정 요청"""
    user_confirmation: str = Field(
        default="이 레시피로 확정할게요",
        description="사용자 확정 메시지 (선택)",
    )


class FinalRecipeResponse(BaseModel):
    """최종 레시피 응답 (3페이지용)"""
    session_id: str
    recipe_name: str = Field(description="레시피 이름")
    recipe_content: str = Field(description="레시피 전체 내용")
    image_prompt: str = Field(description="이미지 생성용 프롬프트")
    is_finalized: bool = Field(default=False, description="확정 여부")


# ============ 레시피 생성 API (원본) ============

class RecipeRequest(BaseModel):
    """프론트엔드와 호환되는 RecipeRequest (camelCase)"""
    dishName: str
    allergies: str = "특이사항 없음"
    cookingLevel: str = "beginner"  # 'beginner' | 'intermediate' | 'advanced'
    preferences: str = "특이사항 없음"