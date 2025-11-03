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
    prefix = f"[{result_file_name}]"
    print(prefix, f"Generating image for prompt: {prompt}, output file: {result_file_name}")
    # prompt = 'A harsh cold look like stone staircase, digital art'
    # result_file_name = 'test.png'

    # Setup Chrome options (optional)
    chrome_options = Options()

    # chromedriver path input
    print(prefix, "waiting for page to load...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    # time.sleep(3)
    # driver.implicitly_wait(3)

    while True:
        try:
            time.sleep(1)
            html = driver.page_source
            soup = BeautifulSoup(html, features='html.parser')
            textarea_1 = driver.find_element(By.CSS_SELECTOR, 'textarea')
            button_1 = driver.find_element(By.CSS_SELECTOR, 'button.submit-button')
            print(prefix, 'Sending prompt to the web page...')
            textarea_1.send_keys(prompt)
            button_1.click()
            print(prefix, 'Prompt sent, waiting for image generation...')
            break
        except NoSuchElementException:
            print(prefix, 'Elements not found, retrying...')
            pass
        except Exception as e:
            print(prefix, 'error:', e)
            return False

    while True:
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, features='html.parser')
        img_tags = soup.find_all('img')
        img_url = None
        for img in img_tags:
            if 'https://sana.hanlab.ai/gradio_api' in img.get('src', ''):
                print(prefix, 'Image generated, downloading...')
                img_url = img['src']
                break
        if img_url is not None:
            break
    # 이미지 저장 폴더 생성
    print(prefix, "Creating image_results directory if not exists...")
    os.makedirs("image_results", exist_ok=True)

    temp_webp_file = f"image_results/{result_file_name}.webp"

    with open(temp_webp_file, "wb") as file:   # open in binary mode
        response = get(img_url)               # get request
        file.write(response.content)      # write to file
    # WebP 이미지 열기

    img = Image.open(temp_webp_file)
    print(prefix, "Converting WebP to PNG...")
    # PNG 형식으로 저장
    img.save("image_results/" + result_file_name, 'PNG')
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