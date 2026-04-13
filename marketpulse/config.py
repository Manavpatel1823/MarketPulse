from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Gemini (optional)
    gemini_api_key: str = ""
    model: str = "gemini-2.5-flash"

    # Ollama (local)
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"

    # OpenRouter (paid, multi-model)
    marketpulse_api: str = ""  # OpenRouter API key, matches .env var name
    openrouter_model: str = "deepseek/deepseek-chat-v3"

    backend: Literal["ollama", "gemini", "openrouter"] = "ollama"

    rounds: int = 3
    agent_count: int = 10
    batch_size: int = 5
    max_interactions_per_round: int = 50
    persuasion_threshold: float = 0.7

    use_hardcoded_personas: bool = True

    db_path: str = "marketpulse.db"
