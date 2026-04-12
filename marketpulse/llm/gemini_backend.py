import asyncio
import json

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from .base import LLMBackend

MAX_RETRIES = 6
# Gemini free tier: 5 RPM for 2.5-flash, 30 RPM for 2.0-flash
# Add delay between requests to stay under limits
REQUEST_DELAY = 13.0  # seconds between requests (safe for 5 RPM)


class GeminiBackend(LLMBackend):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self._last_request_time = 0.0

    async def _rate_limit_wait(self):
        """Enforce minimum delay between requests."""
        import time
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    async def _call_with_retry(self, config: types.GenerateContentConfig, user_prompt: str) -> str:
        for attempt in range(MAX_RETRIES):
            try:
                await self._rate_limit_wait()
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=config,
                )
                return response.text
            except ClientError as e:
                error_str = str(e)
                if "PerDay" in error_str or "per_day" in error_str.lower():
                    raise RuntimeError(
                        "Daily API quota exhausted. Either:\n"
                        "  1. Wait until tomorrow\n"
                        "  2. Upgrade to a paid Gemini API plan\n"
                        "  3. Install Ollama and set BACKEND=ollama in .env\n"
                        f"  Original error: {e}"
                    )
                if "429" in error_str and attempt < MAX_RETRIES - 1:
                    wait = 30 * (attempt + 1)
                    print(f"  [Rate limited] Waiting {wait}s before retry ({attempt + 1}/{MAX_RETRIES})...")
                    await asyncio.sleep(wait)
                else:
                    raise

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
        return await self._call_with_retry(config, user_prompt)

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        )
        text = await self._call_with_retry(config, user_prompt)
        return json.loads(text)
