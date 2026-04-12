from abc import ABC, abstractmethod


class LLMBackend(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a free-form text response."""
        ...

    @abstractmethod
    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Generate a JSON response. The backend ensures valid JSON output."""
        ...
