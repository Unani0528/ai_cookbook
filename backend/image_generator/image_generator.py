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
    os.makedirs("image_results", exist_ok=True)

    temp_webp_file = f"image_results/{result_file_name}.webp"
    print(prefix, "Downloading image from URL...")
    # WebP 이미지 다운로드
    with open(temp_webp_file, "wb") as file:   # open in binary mode
        response = get(img_url)               # get request
        file.write(response.content)      # write to file

    # WebP 이미지를 PNG 형식으로 저장
    img = Image.open(temp_webp_file)
    print(prefix, "Converting WebP to PNG...")
    img.save("image_results/" + result_file_name, 'PNG')

    # 임시 WebP 파일 삭제 및 드라이버 종료
    if os.path.exists(temp_webp_file):
        os.remove(temp_webp_file)
    driver.quit()
    print(prefix, f"Image saved as {result_file_name}")
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
        t = Process(target=generateImage, args=(task[0], task[1]))
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

# 테스트용 메인 함수
if __name__ == "__main__":
    tasks = [
        ("A bucket full of stars in space, digital art", "1.png"),
        ("A serene mountain landscape at sunrise, digital art", "2.png")
        # ("A futuristic city skyline at night, digital art", "3.png"),
        # ("A majestic dragon flying over a castle, digital art", "4.png"),
        # ("A beautiful underwater coral reef, digital art", "5.png"),
        # ("A vibrant forest with magical creatures, digital art", "6.png"),
        # ("A snowy village during winter, digital art", "7.png"),
        # ("A desert with ancient ruins, digital art", "8.png"),
        # ("A bustling marketplace in a fantasy world, digital art", "9.png"),
        # ("A peaceful beach at sunset, digital art", "10.png"),
    ]
    result = generateImages(tasks)
    print("Result:", result)