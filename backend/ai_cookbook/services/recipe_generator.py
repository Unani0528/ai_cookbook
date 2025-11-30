import json
import logging
from typing import Dict, Any
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage

from models.recipe import RecipeRequest

logger = logging.getLogger(__name__)

class RecipeGenerator:
    def __init__(self, llm_with_history: RunnableWithMessageHistory, llm):
        self.llm_with_history = llm_with_history
        # LLM 모델 (이미지 프롬프트 생성용)
        self.llm = llm

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

        # 2. 메인 이미지 생성 (레시피 전체 컨텍스트 반영)
        logger.info("Generating main image prompt with recipe context...")
        main_image_prompt = await self._generate_main_image_prompt(request, recipe_data)
        logger.info(f"Main image prompt (KR): {main_image_prompt}")
        eng_main_prompt = await translator.translate(main_image_prompt)
        logger.info(f"Main image prompt (EN): {eng_main_prompt}")
        recipe_data['image'] = image_gen.generate_image(eng_main_prompt)

        # 3. 단계별 이미지 생성 (각 단계의 컨텍스트 반영)
        for idx, step in enumerate(recipe_data['steps']):
            logger.info(f"Generating step {idx + 1} image prompt...")
            step_image_prompt = await self._generate_step_image_prompt(
                request, recipe_data, step, idx
            )
            logger.info(f"Step {idx + 1} image prompt (KR): {step_image_prompt}")
            eng_step_prompt = await translator.translate(step_image_prompt)
            logger.info(f"Step {idx + 1} image prompt (EN): {eng_step_prompt}")
            step['image'] = image_gen.generate_image(eng_step_prompt)

        return recipe_data

    async def _generate_main_image_prompt(self, request: RecipeRequest, recipe_data: Dict[str, Any]) -> str:
        """레시피 전체 컨텍스트를 반영한 메인 이미지 프롬프트 생성"""
        # 주재료 추출
        main_ingredients = []
        for ing_group in recipe_data.get('ingredients', []):
            if ing_group.get('category') == '주재료':
                main_ingredients = ing_group.get('items', [])[:3]  # 상위 3개만
                break

        ingredients_text = ', '.join(main_ingredients) if main_ingredients else ''

        prompt = f"""다음 레시피의 완성된 요리 사진을 위한 이미지 생성 프롬프트를 작성해줘.
레시피 제목: {recipe_data.get('title', request.dishName)}
주요 재료: {ingredients_text}
사용자 선호사항: {request.preferences}
알레르기 정보: {request.allergies}

이미지는 다음과 같은 특징을 가져야 해:
- 완성된 요리가 맛있게 보이도록 플레이팅된 모습
- 주요 재료가 잘 보이도록 구성
- 사용자의 선호사항이 시각적으로 반영된 모습

위 정보를 바탕으로 이미지 생성 AI가 이해할 수 있는 상세한 프롬프트를 한 문장으로 작성해줘.
예시: "맛있게 플레이팅된 매운 불고기, 고추와 야채가 많이 들어가 있고, 하얀 접시에 담겨있는 모습"

프롬프트만 출력해줘:"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _generate_step_image_prompt(
        self, request: RecipeRequest, recipe_data: Dict[str, Any], step: Dict[str, Any], step_idx: int
    ) -> str:
        """각 조리 단계의 컨텍스트를 반영한 이미지 프롬프트 생성"""
        # 이전 단계들의 설명 수집 (컨텍스트)
        previous_steps = []
        for i in range(step_idx):
            if i < len(recipe_data['steps']):
                previous_steps.append(recipe_data['steps'][i]['description'])

        previous_context = ' -> '.join(previous_steps[-2:]) if previous_steps else '조리 시작'

        prompt = f"""다음 조리 단계의 과정 사진을 위한 이미지 생성 프롬프트를 작성해줘.
레시피: {recipe_data.get('title', request.dishName)}
현재 단계: {step['description']}
이전 단계들: {previous_context}

이미지는 다음과 같은 특징을 가져야 해:
- 현재 조리 단계의 과정이 명확하게 보이는 모습
- 재료와 조리 도구가 잘 보이도록 구성
- 주방 환경에서 실제로 조리하는 자연스러운 장면

위 정보를 바탕으로 이미지 생성 AI가 이해할 수 있는 상세한 프롬프트를 한 문장으로 작성해줘.
예시: "팬에서 고기를 볶고 있는 모습, 고추와 양파가 함께 볶여지고 있고, 주걱으로 저어주는 장면"

프롬프트만 출력해줘:"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

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
