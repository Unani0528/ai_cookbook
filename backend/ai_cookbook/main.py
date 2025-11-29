# FastAPI 관련 모듈 import
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

import os
from dotenv import load_dotenv

# 내부 모듈 import
from config.settings import settings  # 환경설정 (API 키, 엔드포인트, CORS 설정 등)
from models.recipe import (
    InitSessionRequest,
    InitSessionResponse,
    ChatRequest,
    ChatResponse,
    FinalRecipeRequest,
    FinalRecipeResponse,
    ChatHistoryResponse,
)
from services.recipe_generator import RecipeGenerator  # 레시피 생성 서비스
from services.image_generator import ImageGenerator  # 이미지 생성 서비스
from services.translator import EnglishTranslator  # 번역 서비스
from langchain_openai import ChatOpenAI  # OpenAI LLM 모델 연동
from langchain_core.runnables.history import RunnableWithMessageHistory  # 히스토리 기반 실행을 위한 래퍼
from langchain_core.chat_history import InMemoryChatMessageHistory  # 세션별 대화 히스토리 저장 객체

load_dotenv()

chat_service: ChatService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작, 종료 시 리소스 관리
    global chat_service
    chat_service = ChatOpenAI()
    yield

# 로깅 설정
# FastAPI 애플리케이션 동작을 추적하고 디버깅하기 위해 로그 메시지를 체계적으로 기록하는 시스템
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="Recipe AI Generator",
    description="레시피 생성 챗봇",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS 미들웨어 설정
# 프론트엔드가 다른 도메인에서 API를 호출할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,      # 허용된 origin 목록
    allow_credentials=True,                   # 쿠키 및 인증 정보 허용 여부
    allow_methods=["*"],                      # 모든 HTTP 메서드 허용
    allow_headers=["*"],                      # 모든 헤더 허용
)

# ==== 확인 완료 UP

# LLM(ChatOpenAI) 모델 초기화
model = ChatOpenAI(
    model=settings.deployment_name,           # 모델 배포 이름 (예: gpt-4o-mini)
    api_key=settings.openai_api_key,          # OpenAI API 키
    base_url=settings.endpoint_url.rstrip("/") + "/openai/v1/",  # 엔드포인트 URL
    temperature=0.0,                          # 창의성 제어 (0이면 일관된 응답)
)

# 세션별 대화 히스토리를 저장할 딕셔너리
store = {}

# 특정 세션 ID에 대한 대화 히스토리 반환 (없으면 새로 생성)
def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 모델에 메시지 히스토리를 추가하기 위한 래퍼
with_message_history = RunnableWithMessageHistory(model, get_session_history)

# 개별 서비스 초기화
image_gen = ImageGenerator()                 # 이미지 생성기
english_translator = EnglishTranslator(model) # 번역기 (영문 변환)
recipe_gen = RecipeGenerator(with_message_history) # 레시피 생성 서비스

# 현재 레시피 생성 중인지 상태 관리 (동시 요청 방지)
app.state.generating = False



# ========== API 엔드 포인트 (윤환 2025.11.29) START ==========
@app.post("/recipeChat/session/create", response_model=SessionResponse)
async def create_session():
    """새 채팅 세션 생성"""
    session_id = chat_service.create_session()
    return SessionResponse(session_id=session_id, message="세션이 생성되었습니다.")


@app.post("/recipeChat/session/{session_id}/profile", response_model=dict)
async def set_user_profile(session_id: str, request: UserProfileRequest):
    """사용자 프로필(알러지, 특이사항, 요리레벨) 설정"""
    success = chat_service.set_user_profile(
        session_id=session_id,
        allergy=request.allergy,
        preferences=request.preferences,
        cooking_level=request.cooking_level,
    )
    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"message": "프로필이 저장되었습니다."}


@app.get("/recipeChat/session/{session_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(session_id: str):
    """현재 사용자 프로필 조회"""
    profile = chat_service.get_user_profile(session_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return UserProfileResponse(**profile)


@app.post("/recipeChat/chat/{session_id}", response_model=ChatResponse)
async def chat(session_id: str, request: ChatRequest):
    """채팅 메시지 전송 및 응답 받기"""
    result = chat_service.chat(session_id=session_id, message=request.message)
    if result is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return ChatResponse(
        session_id=session_id,
        response=result["response"],
        is_recipe=result["is_recipe"],
    )


@app.get("/recipeChat/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """채팅 히스토리 조회"""
    history = chat_service.get_chat_history(session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return ChatHistoryResponse(session_id=session_id, history=history)


@app.get("/recipeChat/chat/{session_id}/last-recipe", response_model=LastRecipeResponse)
async def get_last_recipe(session_id: str):
    """마지막 레시피 조회 (이미지 생성 프롬프트용)"""
    recipe = chat_service.get_last_recipe(session_id)
    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail="레시피를 찾을 수 없습니다. 먼저 레시피를 요청해주세요."
        )
    return LastRecipeResponse(
        session_id=session_id,
        recipe=recipe["content"],
        recipe_name=recipe.get("name", ""),
        image_prompt_suggestion=recipe.get("image_prompt", ""),
    )


@app.delete("/recipeChat/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    success = chat_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"message": "세션이 삭제되었습니다."}


@app.get("/recipeChat/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy"}

# ========== 엔드포인트 (윤환 2025.11.29) END ==========






# 레시피 생성 API 엔드포인트
@app.post("/api/generate-recipe")
async def generate_recipe(request: RecipeRequest):
    """사용자 입력을 기반으로 맞춤 레시피를 생성"""
    if app.state.generating:
        return {"error": "이미 생성 중입니다."}

    app.state.generating = True  # 생성 중 상태로 변경

    try:
        # 비동기로 레시피 생성 (이미지 및 번역 포함)
        result = await recipe_gen.generate(request, image_gen, english_translator)
        logger.info("Recipe generated successfully")
        return result
    except Exception as e:
        logger.error(f"Recipe generation failed: {e}")
        raise
    finally:
        # 항상 상태 초기화
        app.state.generating = False


# 기본 루트 엔드포인트 (서버 상태 확인용)
@app.get("/")
async def index():
    return {"message": "Recipe AI Generator API"}
