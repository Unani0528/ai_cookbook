import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageGenerator:
    def __init__(self, base_url: str = "https://sana.hanlab.ai/"):
        self.base_url = base_url
        self.timeout = 60

    def generate_image(self, prompt: str) -> str:
        """단일 이미지 생성"""
        logger.info(f"Generating image for: {prompt[:50]}...")

        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(self.base_url)
            self._wait_and_submit(driver, prompt)
            return self._wait_for_image(driver)
        finally:
            driver.quit()

    def _wait_and_submit(self, driver, prompt: str):
        """프롬프트 입력 및 제출 대기"""
        for _ in range(10):
            try:
                textarea = driver.find_element(By.CSS_SELECTOR, 'textarea')
                button = driver.find_element(By.CSS_SELECTOR, 'button.submit-button')
                textarea.clear()
                textarea.send_keys(prompt)
                button.click()
                return
            except Exception:
                time.sleep(1)
        raise TimeoutError("UI elements not found")

    def _wait_for_image(self, driver) -> str:
        """이미지 생성 대기"""
        for _ in range(self.timeout):
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if 'gradio_api' in src:
                    logger.info(f"Image generated: {src}")
                    return src
            time.sleep(1)
        raise TimeoutError("Image generation timeout")
