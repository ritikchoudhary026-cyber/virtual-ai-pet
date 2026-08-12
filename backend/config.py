"""Centralized configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """All runtime settings, read from .env or OS environment."""

    # Inference mode: "offline", "online", or "auto"
    DEFAULT_MODE: str = os.getenv("DEFAULT_MODE", "auto")

    # Offline engine (Phi-3 GGUF via llama-cpp-python)
    PHI_MODEL_PATH: str = os.getenv("PHI_MODEL_PATH", "models/Phi-3-mini-4k-instruct-q4.gguf")

    # Online engine (Nemotron 3.5 Lightning via OpenRouter)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL: str = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning")
    OPENROUTER_TIMEOUT: int = int(os.getenv("OPENROUTER_TIMEOUT", "15"))
    OPENROUTER_MAX_RETRIES: int = int(os.getenv("OPENROUTER_MAX_RETRIES", "2"))

    # Chroma vector DB path for RAG memory
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")


settings = Settings()
