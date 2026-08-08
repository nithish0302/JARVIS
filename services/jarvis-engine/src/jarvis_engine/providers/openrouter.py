from typing import List
from .base import BaseProvider
from ..core.models import Message
from ..core.config import settings

class OpenRouterProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def model(self) -> str:
        return settings.OPENROUTER_MODEL

    async def chat(self, messages: List[Message], stream: bool = False) -> str:
        return "JARVIS engine connected. AI coming in Milestone 3."

    async def is_available(self) -> bool:
        return False
