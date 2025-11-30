"""
채팅 서비스 - RAG 체인 및 세션 관리
- 3페이지 흐름: 초기화 → 채팅 → 최종 레시피
"""

import os
import re
import uuid
from typing import Dict, Optional, Any, List

from dotenv import load_dotenv
from qdrant_client import QdrantClient

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_qdrant import QdrantVectorStore
from langchain_upstage import ChatUpstage, UpstageEmbeddings

load_dotenv()


class ChatService:
    """RAG 기반 레시피 챗봇 서비스"""

    def __init__(self):
        self._init_llm()
        self._init_embeddings()
        self._init_vector_store()
        self._init_rag_chain()

        # 세션별 데이터 저장소
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.chat_histories: Dict[str, ChatMessageHistory] = {}
        self.final_recipes: Dict[str, Dict[str, str]] = {}

    def _init_llm(self):
        self.llm = ChatUpstage(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=os.getenv("LLM_MODEL"),
        )

    def _init_embeddings(self):
        self.embeddings = UpstageEmbeddings(
            model=os.getenv("EMBEDDING_MODEL"),
            api_key=os.getenv("EMBEDDING_API_KEY"),
            base_url=os.getenv("EMBEDDING_BASE_URL"),
        )

    def _init_vector_store(self):
        self.qdrant_client = QdrantClient(
            host=os.getenv("RAG_HOST"),
            port=int(os.getenv("RAG_PORT", 6333)),
        )
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=os.getenv("RAG_COLLECTION_NAME"),
            embedding=self.embeddings,
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 10})

    def _init_rag_chain(self):
        prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                "당신은 요리 전문가 입니다. human이 당신에게 레시피를 물어보면, "
                "초보자에게 요리를 쉽고 정확하게 알려주는 역할을 합니다. "
                "답변에는 정확한 용량(g, ml, 숟가락 등)을 명시하고 "
                "재료 손질시 손질한 재료의 크기(cm 등) 또는 손질 방법을 명시하고 "
                "조리 하는 과정에서는 상세한 시간도 안내해서 human이 따라할 수 있도록 하세요. "
                "알러지가 있는 식재료가 있다면 어떠한 사용자의 요청에도 절대 포함시키지 마세요. "
                "사용자의 특이사항(선호, 비선호 사항 등)과 요리 레벨(숙련도)을 반영해서 레시피를 생성하세요. "
                "요리와 관련 없는 질문은 답변하지 마세요. "
                "레시피를 제공할 때는 반드시 요리 이름을 첫 줄에 명시해주세요."
                "전체 요리과정에 걸리는 시간, 몇 인분인지도 요리 이름 바로 아래에 출력해주세요"
                "이전 답변에서 변경된 사항이 있어도 전체의 레시피를 출력하세요"
                ,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "human",
                "다음 컨텍스트를 참고해서 질문에 답변해줘.\n\n"
                "[알러지]\n{allergy}\n\n"
                "[특이사항]\n{user_profile}\n\n"
                "[요리 레벨]\n{user_level}\n\n"
                "[컨텍스트]\n{context}\n\n"
                "[질문]\n{question}"
            ),
        ])

        def docs_to_text(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self.base_rag_chain = (
            {
                "context": (
                    RunnablePassthrough()
                    .pick("question")
                    | self.retriever
                    | RunnableLambda(docs_to_text)
                ),
                "question": RunnablePassthrough().pick("question"),
                "chat_history": RunnablePassthrough().pick("chat_history"),
                "allergy": RunnablePassthrough().pick("allergy"),
                "user_profile": RunnablePassthrough().pick("user_profile"),
                "user_level": RunnablePassthrough().pick("user_level"),
            }
            | prompt_template
            | self.llm
            | StrOutputParser()
        )

    def _get_session_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = ChatMessageHistory()
        return self.chat_histories[session_id]

    # ============ 1페이지: 세션 초기화 ============

    def init_session(
        self,
        allergy: str,
        preferences: str,
        cooking_level: str,
        food_type: str,
    ) -> Dict[str, Any]:
        """
        세션 생성 + 첫 번째 레시피 자동 추천
        """
        session_id = str(uuid.uuid4())

        # 세션 정보 저장
        self.sessions[session_id] = {
            "allergy": allergy or [],
            "preferences": preferences or "",
            "cooking_level": cooking_level or "초보",
            "food_type": food_type,
            "is_finalized": False,
        }

        # 첫 번째 레시피 자동 생성
        initial_question = f"{food_type} 레시피를 알려줘"
        result = self._run_chain(session_id, initial_question)

        return {
            "session_id": session_id,
            "initial_message": result["response"],
        }

    # ============ 2페이지: 채팅 ============

    def chat(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """사용자 메시지 처리"""
        if session_id not in self.sessions:
            return None
        return self._run_chain(session_id, message)

    async def chat_stream(self, session_id: str, message: str):
        """사용자 메시지 처리 (스트리밍)"""
        if session_id not in self.sessions:
            return  # async generator에서는 return None 대신 return만 사용

        async for chunk in self._run_chain_stream(session_id, message):
            yield chunk

    def _run_chain(self, session_id: str, message: str) -> Dict[str, Any]:
        """RAG 체인 실행"""
        profile = self.sessions[session_id]
        allergy_str = ", ".join(profile["allergy"]) if profile["allergy"] else "없음"

        chain_with_history = RunnableWithMessageHistory(
            self.base_rag_chain,
            get_session_history=self._get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        config = {"configurable": {"session_id": session_id}}

        response = chain_with_history.invoke(
            {
                "question": message,
                "allergy": allergy_str,
                "user_profile": profile["preferences"],
                "user_level": profile["cooking_level"],
            },
            config=config,
        )

        is_recipe = self._is_recipe_response(response)

        # 레시피 응답이면 임시 저장 (최종 확정 전)
        if is_recipe:
            self.sessions[session_id]["last_recipe"] = {
                "content": response,
                "name": self._extract_recipe_name(response),
            }

        return {"response": response, "is_recipe": is_recipe}

    async def _run_chain_stream(self, session_id: str, message: str):
        """RAG 체인 실행 (스트리밍)"""
        profile = self.sessions[session_id]
        allergy_str = ", ".join(profile["allergy"]) if profile["allergy"] else "없음"

        chain_with_history = RunnableWithMessageHistory(
            self.base_rag_chain,
            get_session_history=self._get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        config = {"configurable": {"session_id": session_id}}

        # 전체 응답을 모아서 나중에 히스토리에 저장
        full_response = ""

        async for chunk in chain_with_history.astream(
            {
                "question": message,
                "allergy": allergy_str,
                "user_profile": profile["preferences"],
                "user_level": profile["cooking_level"],
            },
            config=config,
        ):
            full_response += chunk
            yield chunk

        # 스트리밍 완료 후 레시피 확인 및 저장
        is_recipe = self._is_recipe_response(full_response)
        if is_recipe:
            self.sessions[session_id]["last_recipe"] = {
                "content": full_response,
                "name": self._extract_recipe_name(full_response),
            }

    def get_chat_history(self, session_id: str) -> Optional[List[Dict[str, str]]]:
        if session_id not in self.chat_histories:
            return None
        history = self.chat_histories[session_id]
        return [
            {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
            for msg in history.messages
        ]

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        if session_id not in self.sessions:
            return None
        session = self.sessions[session_id]
        return {
            "allergy": session["allergy"],
            "preferences": session["preferences"],
            "cooking_level": session["cooking_level"],
            "food_type": session["food_type"],
            "is_finalized": session.get("is_finalized", False),
        }

    # ============ 2→3페이지: 레시피 확정 ============

    def finalize_recipe(
        self,
        session_id: str,
        user_confirmation: str = "",
    ) -> Optional[Dict[str, str]]:
        """현재 레시피를 최종 확정"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        last_recipe = session.get("last_recipe")

        if not last_recipe:
            # 마지막 레시피가 없으면 히스토리에서 찾기
            history = self.get_chat_history(session_id)
            if history:
                for msg in reversed(history):
                    if msg["role"] == "assistant" and self._is_recipe_response(msg["content"]):
                        last_recipe = {
                            "content": msg["content"],
                            "name": self._extract_recipe_name(msg["content"]),
                        }
                        break

        if not last_recipe:
            return None

        # 최종 레시피 저장
        recipe_name = last_recipe["name"]
        recipe_content = last_recipe["content"]

        self.final_recipes[session_id] = {
            "recipe_name": recipe_name,
            "recipe_content": recipe_content,
            "image_prompt": self._generate_image_prompt(recipe_name, recipe_content),
        }

        session["is_finalized"] = True

        return self.final_recipes[session_id]

    # ============ 3페이지: 최종 레시피 조회 ============

    def get_final_recipe(self, session_id: str) -> Optional[Dict[str, str]]:
        """확정된 최종 레시피 조회"""
        return self.final_recipes.get(session_id)

    # ============ 유틸리티 ============

    def _is_recipe_response(self, response: str) -> bool:
        keywords = ["재료", "만드는 방법", "조리", "손질", "끓이", "볶", "굽", "찌"]
        return any(kw in response for kw in keywords)

    def _extract_recipe_name(self, response: str) -> str:
        lines = response.strip().split("\n")
        for line in lines[:3]:
            line = line.strip()
            if line and not line.startswith("-") and not line.startswith("*"):
                name = re.sub(r"[#*\[\]()]", "", line).strip()
                if name and len(name) < 50:
                    return name
        return "레시피"

    def _generate_image_prompt(self, recipe_name: str, recipe_content: str) -> str:
        return (
            f"A beautifully plated {recipe_name}, professional food photography, "
            f"warm lighting, appetizing presentation, high resolution, "
            f"top-down view, garnished elegantly"
        )

    def delete_session(self, session_id: str) -> bool:
        if session_id not in self.sessions:
            return False
        del self.sessions[session_id]
        self.chat_histories.pop(session_id, None)
        self.final_recipes.pop(session_id, None)
        return True