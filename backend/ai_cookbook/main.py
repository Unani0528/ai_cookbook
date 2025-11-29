from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config.settings import settings
from models.recipe import RecipeRequest
from services.recipe_generator import RecipeGenerator
from services.image_generator import ImageGenerator
from services.translator import EnglishTranslator
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Recipe AI Generator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM 모델 초기화
model = ChatOpenAI(
    model=settings.deployment_name,
    api_key=settings.openai_api_key,
    base_url=settings.endpoint_url.rstrip("/") + "/openai/v1/",
    temperature=0.0,
)

# 세션 히스토리 관리
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 서비스 초기화 (순환 참조 해결)
with_message_history = RunnableWithMessageHistory(model, get_session_history)
image_gen = ImageGenerator()
english_translator = EnglishTranslator(model)
recipe_gen = RecipeGenerator(with_message_history)

# 상태 관리
app.state.generating = False


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
        raise
    finally:
        app.state.generating = False


@app.get("/")
async def index():
    return {"message": "Recipe AI Generator API"}
