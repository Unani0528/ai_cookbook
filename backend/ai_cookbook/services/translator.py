from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class Translator(ABC):
    def __init__(self, model: ChatOpenAI):
        self.model = model

    @abstractmethod
    async def translate(self, text: str) -> str:
        pass


class EnglishTranslator(Translator):
    async def translate(self, text: str) -> str:
        try:
            response = await self.model.ainvoke([
                HumanMessage(content=f"Please translate to English only: {text}")
            ])
            return response.content.strip()
        except Exception as e:
            print(f"Translation failed: {e}")
            return text


class KoreanTranslator(Translator):
    async def translate(self, text: str) -> str:
        try:
            response = await self.model.ainvoke([
                SystemMessage(content="Korean recipe translator"),
                HumanMessage(content=f"Translate to Korean recipe style: {text}")
            ])
            return response.content.strip()
        except Exception as e:
            print(f"Translation failed: {e}")
            return text
