import json

from ollama import AsyncClient

from .base import LLMBackend


class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.client = AsyncClient(host=base_url)

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.message.content

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        response = await self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            format="json",
        )
        return json.loads(response.message.content)
