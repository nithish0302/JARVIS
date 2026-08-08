import httpx
from typing import List
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
                r = await c.get("http://localhost:11434/api/tags")
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
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_HOST}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
        except httpx.TimeoutException:
            return (
                "Request timed out. "
                "Ollama may be processing a large response."
            )
        except Exception as e:
            return f"Ollama error: {str(e)}"
