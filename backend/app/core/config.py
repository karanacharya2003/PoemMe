from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Info
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Shakespearean Poem Generator"
    VERSION: str = "1.0.0"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173"
    ]

    # Model paths
    MODEL_PATH: str = os.path.join(os.path.dirname(__file__), "../models/poem_model.keras")
    TOKENIZER_PATH: str = os.path.join(os.path.dirname(__file__), "../models/tokenizer.pkl")

    # Streaming
    STREAM_DELAY: float = 0.05
    MAX_TOKENS: int = 500

    class Config:
        case_sensitive = True

settings = Settings()
