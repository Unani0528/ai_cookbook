import json
from typing import Dict, Any
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage

from models.recipe import RecipeRequest


class RecipeGenerator:
    def __init__(self, llm_with_history: RunnableWithMessageHistory):
        self.llm_with_history = llm_with_history

    async def generate(self, request: RecipeRequest, image_gen, translator) -> Dict[str, Any]:
        """레시피 생성 + 이미지 생성"""
        prompt = self._build_prompt(request)

        # 1. 레시피 JSON 생성
        config = {"configurable": {"session_id": "recipe_session"}}

        messages = [
            SystemMessage(content="너는 취향에 따른 다양한 레시피를 선사할 수 있는 요리사야."),
            HumanMessage(content=prompt)
        ]

        response = await self.llm_with_history.ainvoke(messages, config=config)
        recipe_data = json.loads(response.content)

        # 2. 메인 이미지 생성
        eng_prompt = await translator.translate(request.dishName)
        recipe_data['image'] = image_gen.generate_image(eng_prompt)

        # 3. 단계별 이미지 생성
        for step in recipe_data['steps']:
            eng_desc = await translator.translate(step['description'])
            step['image'] = image_gen.generate_image(eng_desc)

        return recipe_data

    def _build_prompt(self, request: RecipeRequest) -> str:
        return f"""{request.dishName}을 만들고 싶은데 다음 조건이 있어. 요리 난이도는 {request.cookingLevel}이고,
알레르기 정보는 {request.allergies}야.
그리고 나의 취향은 {request.preferences} 이야.
이 정보를 바탕으로 나에게 맞는 레시피를 추천해줘.

이 때, 다음 형식에 맞춰서 대답해줘. 최종 결과는 json 형식이 되었으면 좋겠어.
{{
    "title": "<레시피 제목>",
    "servings": <인분(숫자만)>,
    "cookTime": <조리 예상 시간(분 단위, 숫자만)>,
    "ingredients": [
        {{
            "category": "주재료",
            "items": [<주재료 목록>]
        }},
        {{
            "category": "향신료",
            "items": [<향신료(주로 양념 등) 목록>]
        }}
    ],
    "steps": [
        {{
            "step": <조리 순서 번호(숫자만)>,
            "description": "<조리 순서 설명>",
            "image": "<조리 순서 이미지 URL>"
        }}
    ],
    "tips": [
        "알레르기 정보: <입력받은 알레르기 정보를 고려하여 레시피에 적용된 사항>",
        "초보자를 위한 팁: <초보자를 위한 팁>",
        "보관 방법: <권장하는 보관 방법>"
    ]
}}
"""
