from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import RedirectResponse
import time

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from os import listdir
from os.path import isfile, join
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

app = FastAPI()

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

# 이미지 생성 및 리다이렉트 엔드포인트
@app.get("/image_generator/generate")
def submit_and_redirect(prompt: str = ""):
    """
    Submits data, starts a background task, and redirects the user.
    """
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
        HumanMessage(f"Please tell the sequence of recipe the following prompt in details as you can, please specify the amount required on ingredients based on 1 person serving food. if you think that question is not related to recipe, you must return an empty string. you don't need to list the ingredients. just description only. you must not use line break character. you must print only the result and must use separator with '###' when listing the each element of sequence.: {prompt}")
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
    generateImages(tasks)
    # generateImages([("A beautiful landscape", f"{prompt}.png"), ("A futuristic city", "city.png")])
    # Redirect to a "success" page or another relevant page
    return RedirectResponse(url="/success", status_code=303)

# 메인 화면
@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

# 이미지 생성 후 결과 화면
@app.get("/success", response_class=HTMLResponse)
def success(request: Request):
    image_file_names = [f for f in listdir('static/image_results') if isfile(join('static/image_results', f))]
    return templates.TemplateResponse("success.html", context={"request": request, "image_file_names": image_file_names})

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

def generateImage(prompt: str, result_file_name: str="test.png"):
    """
    주어진 프롬프트로 이미지 파일을 생성합니다.<p>
    :param prompt: 이미지 생성에 사용할 프롬프트<p>
    :param result_file_name: 생성된 이미지를 저장할 파일 이름<p>
    :return: 성공 여부 (True/False)
    """
    # 파일 이름에 사용할 수 없는 글자가 있을 경우 replace
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        result_file_name = result_file_name.replace(char, '-')
    # 로그 출력용 접두사
    prefix = f"[{result_file_name}]"
    print(prefix, f"Generating image for prompt: {prompt}, output file: {result_file_name}")

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
    # 이미지 저장 폴더 생성
    print(prefix, "Creating image_results directory if not exists...")
    os.makedirs("static/image_results", exist_ok=True)

    file_name = translate_to_korean(result_file_name.replace('.png', '')) + ';;;' + result_file_name.replace('.png', '')

    temp_webp_file = f"static/image_results/{file_name}"
    print(prefix, "Downloading image from URL...")
    # WebP 이미지 다운로드
    try:
        with open(temp_webp_file, "wb") as file:   # open in binary mode
            response = get(img_url)               # get request
            file.write(response.content)      # write to file
    except Exception as e:
        print(prefix, "Error downloading image:", e)

    # # WebP 이미지를 PNG 형식으로 저장
    # img = Image.open(temp_webp_file)
    # print(prefix, "Converting WebP to PNG...")
    # translated_file_name = translate_to_korean(result_file_name.replace('.png', ''))
    # print(prefix, "Translated file name:", translated_file_name)
    # img.save("static/image_results/" + translated_file_name + ';;;' + result_file_name.replace('.png', ''), 'PNG')

    # # 임시 WebP 파일 삭제 및 드라이버 종료
    # if os.path.exists(temp_webp_file):
    #     os.remove(temp_webp_file)
    driver.quit()
    print(prefix, f"Image saved as {file_name}")
    return True

def generateImages(tasks: list):
    """
    여러 프롬프트와 파일 이름을 받아 병렬적으로 이미지를 생성합니다.<p>
    :param tasks: 이미지 생성에 사용할 프롬프트와 파일 이름이 있는 튜플의 리스트. 예시: [("A monkey holding a banana", "monkey.png"), ("An old sign", "sign.png")]<p>
    :return: 성공 여부 (True/False)
    """
    # result = Queue()

    # 이미지 생성 작업을 병렬로 실행
    threads = []
    for task in tasks:
        t = Process(target=generateImage, args=(task[0] + task[1], task[2]))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    
    # result.put('STOP')
    # while True:
    #     tmp = result.get()
    #     if tmp == 'STOP':
    #         break

    print("All tasks completed.")
    return True