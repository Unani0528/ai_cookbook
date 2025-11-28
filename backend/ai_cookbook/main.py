from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import RedirectResponse
import time
import json

from fastapi import FastAPI, Request
from typing import Optional
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from os import listdir
from os.path import isfile, join
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from fastapi.middleware.cors import CORSMiddleware

# 메시지 히스토리
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

app = FastAPI()

# 프론트엔드 출처(Vite dev server: 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

#.env 불러오기
load_dotenv()

# LangChain용 LLM 객체 만들기 (Azure OpenAI v1 방식)
model = ChatOpenAI(
    model=os.getenv("DEPLOYMENT_NAME"),               
    api_key=os.getenv("OPENAI_API_KEY"),            
    base_url=os.getenv("ENDPOINT_URL").rstrip("/") + "/openai/v1/",
    temperature=0.0,
)

class FormData(BaseModel):
    allergies: str = "특이사항 없음"
    cookingLevel: str = "beginner"
    dishName: str = ""
    preferences :str = "특이사항 없음"

# 프롬프트 템플릿
from langchain_core.prompts import ChatPromptTemplate

generating = False
result = {}

@app.post("/api/generate-recipe")
def generate_recipe(form_data: FormData):
    global generating
    global result
    if generating:
        return None
    generating = True

    prompt = f"""{form_data.dishName}을 만들고 싶은데 다음 조건이 있어. 요리 난이도는 {form_data.cookingLevel}이고, 
                 알레르기 정보는 {form_data.allergies}야. 
                 그리고 나의 취향은 {form_data.preferences} 이야. 
                 이 정보를 바탕으로 나에게 맞는 레시피를 추천해줘."""


    # 레시피 생성 시작
    response = with_message_history.invoke([
        SystemMessage(content="너는 취향에 따른 다양한 레시피를 선사할 수 있는 요리사야."),
        HumanMessage(content=prompt + """
        이 때, 다음 형식에 맞춰서 대답해줘. 최종 결과는 json 형식이 되었으면 좋겠어.
        {
            "title": "<레시피 제목>",
            "servings": <인분(숫자만)>,
            "cookTime": <조리 예상 시간(분 단위, 숫자만)>,
            "ingredients": [
                {
                    "category": "주재료",
                    "items": [<주재료 목록>]
                },
                {
                    "category": "향신료",
                    "items": [<향신료(주로 양념 등) 목록>]
                }
            ],
            "steps": [
                {
                    "step": <조리 순서 번호(숫자만)>,
                    "description": "<조리 순서 설명>",
                    "image": "<조리 순서 이미지 URL>"
                }
            ],
            "tips": [
                "알레르기 정보: <입력받은 알레르기 정보를 고려하여 레시피에 적용된 사항>",
                "초보자를 위한 팁: <초보자를 위한 팁>",
                "보관 방법: <권장하는 보관 방법>"
            ]
        }
    """)], config=config).content

    print(response)

    result['result'] = json.loads(response)

    # 이미지 생성
    english_prompt = translate_to_english(prompt)
    img_url = generateImage(english_prompt)
    print("Generated image URL:", img_url)
    result['result']['image'] = img_url

    for step in result['result']['steps']:
        english_description = translate_to_english(step['description'])
        img_url = generateImage(english_description)
        print(f"Generated image URL for step {step['step']}:", img_url)
        step['image'] = img_url

    # 레시피 생성 끝
    print("Process finished.")
    generating = False
    return result['result']

# 메시지 히스토리 사용 예제
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(model, get_session_history)
config = {"configurable": {"session_id": "user1234"}}

# 이미지 생성 및 리다이렉트 엔드포인트
@app.get("/image_generator/generate")
def submit_and_redirect(prompt: str = ""):
    """
    Submits data, starts a background task, and redirects the user.
    """
    return {"title": prompt}
    original_prompt = prompt
    # 이미 이미지를 생성중인 경우 혹은 입력이 공백일 경우 리다이렉트
    if not prompt or prompt.strip() == "":
        return RedirectResponse(url="/", status_code=303)
    # 이미 있는 이미지 제거
    for f in [f for f in listdir('static/image_results') if isfile(join('static/image_results', f))]:
        os.remove(join('static/image_results', f))

    # 입력된 문장을 영어로 번역
    print("Translating prompt to english...")
    prompt = translate_to_english(prompt)
    print("Translated prompt:", prompt)
    response = model.invoke([
        SystemMessage(content="You are a pro chef that can cook any food for various people who are in various circumstances. You should provide personal recipe for each person who wants their own recipe."),
        HumanMessage(f"Please tell the sequence of recipe the following prompt in details as you can, please specify the amount required on ingredients based on 1 person serving food. the reference is 'https://www.10000recipe.com/', if you think that question is not related to recipe, you must return an empty string. you don't need to list the ingredients. just description only. you must not use line break character. you must print only the result and must use separator with '###' when listing the each element of sequence.: {prompt}")
        ]).content
    print('summarized response:', response)
    words = response.split('###')
    # 순서 설명이 없거나 1개일 경우 리다이렉트
    if (len(words) <= 1):
        return RedirectResponse(url="/", status_code=303)
    tasks = []
    index = 1
    for word in words:
        tasks.append(('cooking recipe - ', word, f"{ ('%02d' if len(words) > 9 else '%d') % index}. {word}.png"))
        index += 1
    generateImages(original_prompt, tasks)
    # generateImages([("A beautiful landscape", f"{prompt}.png"), ("A futuristic city", "city.png")])
    # Redirect to a "success" page or another relevant page

    return {"title":"테스트"}

    result = {}

    result['title'] = prompt.split('###')[0]
    return result
    steps = []
    for i, word in enumerate(words):
        if word.strip() == "":
            continue  # 빈 문자열은 건너뜀
        step = {
            'step': i + 1,
            'title': word.strip(),
            'image': f"{ ('%02d' if len(words) > 9 else '%d') % (i + 1)}. {word.strip()}.png"
        }
        steps.append(step)
    result['steps'] = steps

    return result

    # return RedirectResponse(url="/success", status_code=303)

# AI
def translate_to_english(text: str) -> str:
    """
    주어진 텍스트를 영어로 번역합니다.<p>
    :param text: 번역할 텍스트<p>
    :return: 번역된 영어 텍스트<p>
    """
    try:
        return model.invoke([HumanMessage(f"Please translate the following text into english. you must print only the result: {text}")]).content
    except Exception as e:
        print("Translation to english failed:", e)
        return text  # 번역 실패 시 원본 텍스트 반환

def translate_to_korean(text: str) -> str:
    """
    주어진 텍스트를 한국어로 번역합니다.<p>
    :param text: 번역할 텍스트<p>
    :return: 번역된 한국어 텍스트<p>
    """
    try:
        translated = model.invoke([SystemMessage("You're an pro chef. when i tell you some english sentence, please translate it into korean as recipe."), HumanMessage(f"Please translate the following text into korean, as it looks like to tell someone to know its recipe. you must print only the result and you must put the numbering order at the start point of the sentence: {text}")]).content
        if translated.strip() == "":
            return text # 빈 문자열일 경우 원본 텍스트 반환
        return translated
    except Exception as e:
        print("Translation to korean failed:", e)
        return text  # 번역 실패 시 원본 텍스트 반환

# image generation code
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import os
from requests import get
from PIL import Image
from multiprocessing import Process, Queue

url = 'https://sana.hanlab.ai/'
steps = []

def generateImage(prompt: str):
    """
    주어진 프롬프트로 이미지 파일을 생성합니다.<p>
    :param prompt: 이미지 생성에 사용할 프롬프트<p>
    :param result_file_name: 생성된 이미지를 저장할 파일 이름<p>
    :return: 성공 여부 (True/False)
    """
    # 로그 출력용 접두사
    prefix = f"[{prompt}]"
    print(prefix, f"Generating image for prompt: {prompt}")

    # Selenium 웹드라이버 설정 및 페이지 접속
    chrome_options = Options()
    print(prefix, "waiting for page to load...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # 페이지 로딩 대기 및 요소 찾기
    while True:
        try:
            # 페이지 로딩 대기
            time.sleep(1)
            # 페이지 소스 가져오기
            html = driver.page_source
            soup = BeautifulSoup(html, features='html.parser')
            textarea_1 = driver.find_element(By.CSS_SELECTOR, 'textarea')
            button_1 = driver.find_element(By.CSS_SELECTOR, 'button.submit-button')
            # 프롬프트 전송
            print(prefix, 'Sending prompt to the web page...')
            textarea_1.send_keys(prompt)
            button_1.click()
            print(prefix, 'Prompt sent, waiting for image generation...')
            break
        except NoSuchElementException:
            # 요소를 찾지 못한 경우 재시도 (페이지 로딩중일 수 있음)
            print(prefix, 'Elements not found, retrying...')
            pass
        except Exception as e:
            print(prefix, 'error:', e)
            return False

    # 이미지 생성 대기 및 다운로드
    time_out = 0
    while True:
        time_out += 1
        # 1분 이상 이미지 생성이 지연되면 타임아웃 처리
        if time_out > 60:
            print(prefix, "Timeout waiting for image generation.")
            driver.quit()
            return False
        # 1초 대기 후 페이지 소스 파싱
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, features='html.parser')
        img_tags = soup.find_all('img')
        img_url = None
        # 생성된 이미지 URL 찾기
        for img in img_tags:
            if 'https://sana.hanlab.ai/gradio_api' in img.get('src', ''):
                print(prefix, 'Image URL found:', img['src'])
                img_url = img['src']
                break
        # 이미지 URL을 찾았으면 루프 종료
        if img_url is not None:
            break
    driver.quit()
    return img_url

# def generateImages(prompt:str, tasks: list):
#     """
#     여러 프롬프트와 파일 이름을 받아 병렬적으로 이미지를 생성합니다.<p>
#     :param tasks: 이미지 생성에 사용할 프롬프트와 파일 이름이 있는 튜플의 리스트. 예시: [("A monkey holding a banana", "monkey.png"), ("An old sign", "sign.png")]<p>
#     :return: 성공 여부 (True/False)
#     """
#     # result = Queue()

#     # 이미지 생성 작업을 병렬로 실행
#     threads = []
#     for task in tasks:
#         t = Process(target=generateImage, args=(task[0] + task[1], task[2]))
#         t.start()
#         threads.append(t)
#     for t in threads:
#         t.join()

#     print("All tasks completed.")