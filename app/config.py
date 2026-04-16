from pydantic_settings import BaseSettings
from functools import lru_cache

from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/freshroute"
    database_pool_size: int = 10

    # Firebase
    firebase_project_id: str = "freshroute-hackathon"
    firebase_credentials_path: str = "./firebase-credentials.json"

    # Pipeline config
    p1_top_n: int = 20
    p2_top_k: int = 20
    p6_top_k: int = 10
    bundle_cache_ttl_seconds: int = 3600
    min_impressions_for_learning: int = 200

    # Store connector
    default_connector: str = "mock"

    # LLM (Gemini)
    OPENAI_API_KEY: str 
    OPENAI_MODEL: str =  "gpt-oss-120b"
    TEMPERATURE: float = 0.1

    model_config = {
        "env_file": ".env", 
        "env_file_encoding": "utf-8",
        "extra" : "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
