from collections.abc import AsyncGenerator

import httpx

from ..core.models import Message
from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def model(self) -> str:
        from ..core.config import settings

        return settings.OPENROUTER_MODEL

    async def is_available(self) -> bool:
        from ..core.config import settings

        if not settings.OPENROUTER_API_KEY:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
                )
                return r.status_code == 200
        except Exception:
            return False

    async def chat(self, messages: list[Message], stream: bool = False) -> str:
        from ..core.config import settings

        try:
            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {"role": m.role, "content": m.content}
                    for m in messages
                    if m.role != "system" or m.content.strip() != ""
                ],
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:1420",
                        "X-Title": "JARVIS Desktop Assistant",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException as e:
            raise Exception("OpenRouter request timed out. Please try again.") from e
        except Exception as e:
            raise Exception(f"OpenRouter error: {e!s}") from e

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        import json

        from ..core.config import settings

        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in messages
                if m.role != "system" or m.content.strip() != ""
            ],
            "stream": True,
        }
        try:
            async with (
                httpx.AsyncClient(timeout=60.0) as client,
                client.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:1420",
                        "X-Title": "JARVIS",
                    },
                    json=payload,
                ) as response,
            ):
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            content = data["choices"][0].get("delta", {}).get("content")
                            if content:
                                yield content
                        except Exception:
                            pass
        except Exception as e:
            # If streaming fails, raise exception so routes.py can catch it and fallback
            raise e
