# FastAPI 관련 모듈 import
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
import json

from dotenv import load_dotenv

# 내부 모듈 import
from config.settings import settings
from models.recipe import (
    InitSessionRequest,
    InitSessionResponse,
    ChatRequest,
    ChatResponse,
    FinalRecipeRequest,
    FinalRecipeResponse,
    ChatHistoryResponse,
    RecipeRequest,
)
from services.chat_service import ChatService
from services.recipe_generator import RecipeGenerator
from services.image_generator import ImageGenerator
from services.translator import EnglishTranslator
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

load_dotenv()

chat_service: ChatService = None
recipe_gen: RecipeGenerator = None
image_gen: ImageGenerator = None
english_translator: EnglishTranslator = None

# 세션 히스토리 관리
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 리소스 관리"""
    global chat_service, recipe_gen, image_gen, english_translator
    try:
        logger.info("Initializing ChatService...")
        chat_service = ChatService()
        logger.info("ChatService initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ChatService: {e}")
        logger.warning("Server will start without ChatService. Please ensure Qdrant is running at localhost:6333")
        chat_service = None

    try:
        # 레시피 생성 서비스 초기화
        logger.info("Initializing RecipeGenerator services...")
        model = AzureChatOpenAI(
            azure_deployment=settings.deployment_name,
            api_key=settings.openai_api_key,
            azure_endpoint=settings.endpoint_url,
            api_version="2024-02-15-preview",
            temperature=0.0,
        )
        with_message_history = RunnableWithMessageHistory(model, get_session_history)
        image_gen = ImageGenerator()
        english_translator = EnglishTranslator(model)
        recipe_gen = RecipeGenerator(with_message_history, model)
        logger.info("RecipeGenerator services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RecipeGenerator: {e}")

    try:
        yield
    finally:
        logger.info("Shutting down...")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="Recipe AI Generator",
    description="RAG 기반 레시피 생성 챗봇 API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 상태 관리
app.state.generating = False



# ========== API 엔드 포인트 (윤환 2025.11.29) START ==========
# ============ 1페이지: 세션 초기화 (사용자 정보 + 음식 종류) ============
@app.post("/recipeChat/init", response_model=InitSessionResponse)
async def init_session(request: InitSessionRequest):
    """
    1페이지에서 호출
    - 사용자 정보(알러지, 취향, 레벨)와 음식 종류를 받아 세션 생성
    - 첫 번째 레시피 추천을 자동 생성
    """
    if chat_service is None:
        raise HTTPException(
            status_code=503,
            detail="ChatService is not available. Please ensure Qdrant is running at localhost:6333"
        )

    result = chat_service.init_session(
        allergy=request.allergy,
        preferences=request.preferences,
        cooking_level=request.cooking_level,
        food_type=request.food_type,
    )
    return InitSessionResponse(
        session_id=result["session_id"],
        initial_message=result["initial_message"],
        message="세션이 생성되었습니다. 채팅 페이지로 이동하세요.",
    )


# ============ 2페이지: 채팅 ============

@app.post("/recipeChat/chat/{session_id}", response_model=ChatResponse)
async def chat(session_id: str, request: ChatRequest):
    """
    2페이지에서 호출
    - 사용자와 대화하며 레시피 수정/추천
    """
    result = chat_service.chat(session_id=session_id, message=request.message)
    if result is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return ChatResponse(
        session_id=session_id,
        response=result["response"],
        is_recipe=result["is_recipe"],
    )


@app.post("/recipeChat/chat/{session_id}/stream")
async def chat_stream(session_id: str, request: ChatRequest):
    """
    2페이지에서 호출 (스트리밍 버전)
    - 사용자와 대화하며 레시피 수정/추천 (실시간 스트리밍)
    """
    if chat_service is None:
        raise HTTPException(
            status_code=503,
            detail="ChatService is not available. Please ensure Qdrant is running at localhost:6333"
        )

    async def generate():
        try:
            async for chunk in chat_service.chat_stream(session_id=session_id, message=request.message):
                # Server-Sent Events (SSE) 형식으로 전송
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            # 스트리밍 종료 신호
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    if session_id not in chat_service.sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/recipeChat/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """채팅 히스토리 조회 (페이지 새로고침 시 복원용)"""
    history = chat_service.get_chat_history(session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return ChatHistoryResponse(session_id=session_id, history=history)


@app.get("/recipeChat/session/{session_id}/info")
async def get_session_info(session_id: str):
    """세션 정보 조회 (사용자 프로필 + 음식 종류)"""
    info = chat_service.get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return info


# ============ 3페이지: 최종 레시피 확정 ============

@app.post("/recipeChat/finalize/{session_id}", response_model=FinalRecipeResponse)
async def finalize_recipe(session_id: str, request: FinalRecipeRequest):
    """
    2페이지에서 '레시피 확정' 버튼 클릭 시 호출
    - 현재까지의 대화에서 최종 레시피 확정
    """
    result = chat_service.finalize_recipe(
        session_id=session_id,
        user_confirmation=request.user_confirmation,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    content = result['recipe_content']
    
    # content = {
    #         "title": "레시피 제목",
    #         "servings": 3,
    #         "cookTime": 30,
    #         "ingredients": [
    #             {
    #                 "category": "주재료",
    #                 "items": ["주재료1", "주재료2"]
    #             },
    #             {
    #                 "category": "향신료",
    #                 "items": ["향신료1", "향신료2"]
    #             }],
    #             "steps": [
    #                 {
    #                     "step": 3,
    #                     "description": "<조리 순서 설명>",
    #                     "image": "<조리 순서 이미지 URL>"
    #                 }
    #             ],
    #         "tips": [
    #             "알레르기 정보: <입력받은 알레르기 정보를 고려하여 레시피에 적용된 사항>",
    #             "초보자를 위한 팁: <초보자를 위한 팁>",
    #             "보관 방법: <권장하는 보관 방법>"
    #             ]
    #         }

    return FinalRecipeResponse(
        session_id=session_id,
        recipe_name=result["recipe_name"],
        recipe_content=content,
        image_prompt=result["image_prompt"],
        is_finalized=True,
    )


@app.get("/recipeChat/recipe/{session_id}", response_model=FinalRecipeResponse)
async def get_final_recipe(session_id: str):
    """
    3페이지에서 호출
    - 확정된 최종 레시피 조회
    """
    result = chat_service.get_final_recipe(session_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="확정된 레시피가 없습니다. 먼저 레시피를 확정해주세요.",
        )
    return FinalRecipeResponse(
        session_id=session_id,
        recipe_name=result["recipe_name"],
        recipe_content=result["recipe_content"],
        image_prompt=result["image_prompt"],
        is_finalized=True,
    )


# ============ 공통 ============

@app.delete("/recipeChat/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    success = chat_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"message": "세션이 삭제되었습니다."}


@app.get("/recipeChat/health")
async def health_check():
    return {"status": "healthy"}
# ========== 엔드포인트 (윤환 2025.11.29) END ==========


# ========== 레시피 생성 API (원본) ==========

@app.post("/api/generate-recipe")
async def generate_recipe(request: RecipeRequest):
    """맞춤 레시피 생성 (프론트엔드 호환)"""
    if app.state.generating:
        return {"error": "이미 생성 중입니다."}

    app.state.generating = True

    try:
        # 동기적으로 레시피 생성 (프론트엔드가 응답을 기다림)
        result = await recipe_gen.generate(request, image_gen, english_translator)
        logger.info("Recipe generated successfully")
        return result
    except Exception as e:
        logger.error(f"Recipe generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"레시피 생성 실패: {str(e)}")
    finally:
        app.state.generating = False


# 기본 루트 엔드포인트 (서버 상태 확인용)
@app.get("/")
async def root():
    return {
        "message": "Recipe AI Generator API v2.0",
        "docs": "/docs",
        "health": "/recipeChat/health",
    }
