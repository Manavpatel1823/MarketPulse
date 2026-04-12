from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str = ""
    model: str = "gemini-2.5-flash"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"
    backend: Literal["ollama", "gemini"] = "gemini"

    rounds: int = 3
    agent_count: int = 10
    batch_size: int = 5
    max_interactions_per_round: int = 50
    persuasion_threshold: float = 0.7

    db_path: str = "marketpulse.db"
