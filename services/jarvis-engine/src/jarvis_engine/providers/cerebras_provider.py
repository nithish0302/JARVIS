import json
from collections.abc import AsyncGenerator

import httpx

from ..core.models import Message
from .base import BaseProvider


class CerebrasProvider(BaseProvider):
    def __init__(self):
        self._selected_model = None

    @property
    def name(self) -> str:
        return "cerebras"

    # Cerebras's current public catalog. Ordered by preference: gpt-oss-120b is
    # the larger/stronger of the two, gemma-4-31b is the smaller multimodal one.
    # The old llama3.1-8b / llama-3.3-70b entries were stale - neither is in the
    # catalog anymore, so selection always silently fell through to models[0].
    PREFERRED_MODELS = ["gpt-oss-120b", "gemma-4-31b"]

    @property
    def model(self) -> str:
        return (
            self._selected_model if self._selected_model else self.PREFERRED_MODELS[0]
        )

    async def is_available(self) -> bool:
        from ..core.config import settings

        if not settings.CEREBRAS_API_KEY:
            return False

        if self._selected_model is None:
            try:
                async with httpx.AsyncClient(timeout=10.0) as c:
                    r = await c.get(
                        "https://api.cerebras.ai/v1/models",
                        headers={
                            "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}"
                        },
                    )
                    if r.status_code == 200:
                        data = r.json()
                        models = [m["id"] for m in data.get("data", [])]
                        self._selected_model = next(
                            (m for m in self.PREFERRED_MODELS if m in models),
                            models[0] if models else None,
                        )
                        if not self._selected_model:
                            return False
                        print(
                            f"[CEREBRAS] Auto-selected model: {self._selected_model} from available models"
                        )
                        return True
                    return False
            except Exception:
                return False
        return True

    async def chat(self, messages: list[Message], stream: bool = False) -> str:
        from ..core.config import settings

        # Ensure model is selected
        if not self._selected_model:
            await self.is_available()

        try:
            payload = {
                "model": self._selected_model,
                "messages": [
                    {
                        "role": m.role if m.role != "assistant" else "assistant",
                        "content": m.content,
                    }
                    for m in messages
                    if m.role in ["system", "user", "assistant"]
                ],
                "max_tokens": 2048,
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            return "Cerebras request timed out. Please try again."
        except Exception as e:
            return f"Cerebras error: {e!s}"

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        from ..core.config import settings

        if not self._selected_model:
            await self.is_available()

        payload = {
            "model": self._selected_model,
            "messages": [
                {
                    "role": m.role if m.role != "assistant" else "assistant",
                    "content": m.content,
                }
                for m in messages
                if m.role in ["system", "user", "assistant"]
            ],
            "max_tokens": 2048,
            "stream": True,
        }
        try:
            async with (
                httpx.AsyncClient(timeout=30.0) as client,
                client.stream(
                    "POST",
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}",
                        "Content-Type": "application/json",
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
            raise e
