import httpx
from typing import List, AsyncGenerator
from .base import BaseProvider
from ..core.models import Message
from ..core.config import settings

class OllamaProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return settings.OLLAMA_MODEL

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get(f"{settings.OLLAMA_HOST}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def chat(self, messages: List[Message], stream: bool = False) -> str:
        try:
            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": m.role, "content": m.content}
                    for m in messages
                ],
                "stream": False
            }
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_HOST}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
        except httpx.TimeoutException as e:
            raise Exception(
                "Request timed out. Ollama may be processing a large response."
            ) from e
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}") from e

    async def stream(
      self,
      messages: list[Message]
    ) -> AsyncGenerator[str, None]:
      from ..core.config import settings
      payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
          {"role": m.role, "content": m.content}
          for m in messages
        ],
        "stream": True
      }
      async with httpx.AsyncClient(
        timeout=90.0
      ) as client:
        async with client.stream(
          "POST",
          f"{settings.OLLAMA_HOST}/api/chat",
          json=payload
        ) as response:
          async for line in response.aiter_lines():
            if line.strip():
              try:
                import json
                data = json.loads(line)
                token = data.get(
                  "message", {}
                ).get("content", "")
                if token:
                  yield token
                if data.get("done"):
                  break
              except json.JSONDecodeError:
                continue
