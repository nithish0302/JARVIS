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

    async def chat(self, messages: List[Message], stream: bool = False) -> str:
        return "JARVIS engine connected. AI coming in Milestone 3."

    async def is_available(self) -> bool:
        return False
