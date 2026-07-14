from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    OLLAMA_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="qwen3:8b")
    SEARXNG_URL: str = Field(default="http://localhost:8080")
    DB_PATH: str = Field(default="lsa.db")

    class Config:
        env_file = ".env"

settings = Settings()
