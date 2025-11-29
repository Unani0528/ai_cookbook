import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List

load_dotenv()


class Settings(BaseSettings):
    # Azure OpenAI 설정 (기존 레거시 지원용, 선택적)
    openai_api_key: str = ""
    deployment_name: str = ""
    endpoint_url: str = ""

    # Upstage LLM 설정 (새로운 RAG 시스템용)
    llm_api_key: str
    llm_base_url: str
    llm_model: str

    # Upstage Embedding 설정
    embedding_model: str
    embedding_api_key: str
    embedding_base_url: str

    # Qdrant Vector Store 설정
    rag_host: str = "localhost"
    rag_port: int = 6333
    rag_collection_name: str

    # CORS 설정
    cors_origins: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False  # 환경 변수 대소문자 구분 안 함
        extra = "ignore"  # 정의되지 않은 환경 변수 무시


settings = Settings()
