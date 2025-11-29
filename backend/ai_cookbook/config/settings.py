import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    openai_api_key: str
    deployment_name: str
    endpoint_url: str
    cors_origins: list = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
