"""
Central configuration — all environment variables are loaded here.

Usage:
    from config import settings
    print(settings.data_dir)

Requires: pip install pydantic-settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""

    nvidia_openai_api_key: str = ""
    nvidia_openai_api_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nvidia_openai_model: str = "openai/gpt-oss-20b"

    database_url: str = ""  # Neon Postgres in production
    
    # App
    data_dir: str = "data"
    sqlite_db_path: str = "data/verimed.sqlite3"
    max_image_size_mb: int = 10
    ocr_min_confidence: float = 0.4
    
    allowed_origins: str = "http://localhost:3000,http://localhost:8000,https://verimed-web.netlify.app"


settings = Settings()
