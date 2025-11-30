"""
레시피 구조 변환 서비스
- 채팅에서 생성된 레시피 텍스트를 구조화된 JSON으로 변환
- Upstage Solar2 모델 사용 (구조 변환 전용)
"""
import json
import logging
import os
from typing import Dict, Any
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class RecipeStructureConverter:
    """채팅 레시피를 구조화된 JSON으로 변환"""

    def __init__(self):
        # Upstage Solar2 모델 사용 (구조 변환 전용)
        self.llm = ChatUpstage(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=os.getenv("LLM_MODEL"),
            temperature=0.0,  # 정확한 구조 변환을 위해 temperature 0
        )

    async def convert_to_structure(
        self,
        recipe_text: str,
        dish_name: str,
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        채팅에서 생성된 레시피 텍스트를 구조화된 JSON으로 변환

        Args:
            recipe_text: 채팅에서 생성된 레시피 텍스트
            dish_name: 요리 이름
            user_info: 사용자 정보 (알레르기, 취향, 레벨)

        Returns:
            구조화된 레시피 JSON
        """
        prompt = self._build_conversion_prompt(recipe_text, dish_name, user_info)

        messages = [
            SystemMessage(content="""너는 레시피 텍스트를 정확하게 구조화된 JSON으로 변환하는 전문가야.
주어진 레시피 텍스트의 내용을 절대 변경하거나 추가하지 말고, 있는 그대로 구조화만 해줘.
텍스트에 없는 정보는 추측하지 말고, 있는 정보만 사용해."""),
            HumanMessage(content=prompt)
        ]

        try:
            response = await self.llm.ainvoke(messages)

            # JSON 파싱
            content = response.content.strip()

            # JSON 코드블록 제거
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            recipe_data = json.loads(content)

            logger.info(f"Successfully converted recipe to structured format")
            return recipe_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response content: {response.content}")
            raise ValueError(f"레시피 구조 변환 실패: JSON 파싱 오류 - {str(e)}")
        except Exception as e:
            logger.error(f"Failed to convert recipe structure: {e}")
            raise

    def _build_conversion_prompt(
        self,
        recipe_text: str,
        dish_name: str,
        user_info: Dict[str, Any]
    ) -> str:
        """구조 변환용 프롬프트 생성"""

        allergy_info = ", ".join(user_info.get('allergy', [])) if user_info.get('allergy') else "없음"

        return f"""다음은 채팅에서 생성된 "{dish_name}" 레시피야.
이 레시피를 아래 JSON 형식으로 정확하게 변환해줘.

**중요**:
- 레시피 내용을 절대 변경하거나 추가하지 마
- 텍스트에 있는 정보만 사용해
- 정보가 없으면 합리적인 기본값 사용 (예: 인분=2, 조리시간=30)
- steps의 description은 원본 텍스트를 그대로 사용

[사용자 정보]
- 알레르기: {allergy_info}
- 취향: {user_info.get('preferences', '없음')}
- 요리 레벨: {user_info.get('cooking_level', '초보')}

[레시피 텍스트]
{recipe_text}

[변환할 JSON 형식]
{{
    "title": "<레시피 제목 (텍스트에서 추출, 없으면 '{dish_name}' 사용)>",
    "servings": <인분 (텍스트에서 추출, 없으면 2)>,
    "cookTime": <조리 시간(분) (텍스트에서 추출, 없으면 30)>,
    "difficulty": "<beginner/intermediate/advanced 중 하나>",
    "ingredients": [
        {{
            "category": "주재료",
            "items": ["재료1 용량", "재료2 용량", ...]
        }},
        {{
            "category": "양념/향신료",
            "items": ["양념1 용량", "양념2 용량", ...]
        }}
    ],
    "steps": [
        {{
            "step": 1,
            "description": "<조리 순서 1 - 원본 텍스트 그대로>"
        }},
        {{
            "step": 2,
            "description": "<조리 순서 2 - 원본 텍스트 그대로>"
        }}
    ],
    "tips": [
        "알레르기 정보: {allergy_info}를 고려하여 레시피 작성됨",
        "<텍스트에서 추출한 팁 1>",
        "<텍스트에서 추출한 팁 2>"
    ]
}}

JSON만 출력해줘:"""
