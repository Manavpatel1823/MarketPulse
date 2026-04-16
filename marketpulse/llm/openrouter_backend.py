import asyncio
import json
import random

from openai import AsyncOpenAI, RateLimitError, APIError

from .base import LLMBackend

MAX_RETRIES = 10
BASE_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 60.0  # cap exponential growth; a 60s window covers most upstream rate-limit periods


class OpenRouterBackend(LLMBackend):
    """OpenRouter via the OpenAI-compatible async SDK.

    One key unlocks access to Claude, GPT, DeepSeek, Gemini, Llama, etc.
    Swap models by changing the `model` string — no other code change needed.

    Retries on 429 (rate limit) with exponential backoff + jitter. This is
    important for popular upstream providers (e.g. DeepSeek via DeepInfra)
    that throttle shared pools during traffic spikes.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek/deepseek-chat-v3",
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def _call_with_retry(self, **kwargs):
        """Call the chat completion API with exponential backoff on 429s."""
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                return await self.client.chat.completions.create(**kwargs)
            except RateLimitError as e:
                last_exc = e
                # Prefer server-provided Retry-After when available; fall back
                # to capped exponential so a burst doesn't fail after ~60s.
                retry_after = None
                try:
                    ra = getattr(e, "response", None)
                    if ra is not None:
                        retry_after = float(ra.headers.get("retry-after") or 0)
                except Exception:
                    retry_after = None
                exp = BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 1)
                delay = min(MAX_BACKOFF_SECONDS, max(retry_after or 0, exp))
                print(f"  [rate-limited] retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s")
                await asyncio.sleep(delay)
            except APIError as e:
                # 5xx server errors — retry once
                last_exc = e
                if attempt < 2:
                    await asyncio.sleep(BASE_BACKOFF_SECONDS * (attempt + 1))
                else:
                    raise
        raise last_exc

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self._call_with_retry(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        response = await self._call_with_retry(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
