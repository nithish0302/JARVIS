from typing import List
from .base import BaseProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider
from ..core.models import Message, ProviderStatus

class ProviderManager:
    def __init__(self):
        self.providers: List[BaseProvider] = [
            OllamaProvider(),
            OpenRouterProvider()
        ]

    async def chat(self, messages: List[Message]) -> tuple[str, str, str]:
        for provider in self.providers:
            if await provider.is_available():
                response = await provider.chat(messages)
                return response, provider.name, provider.model
        
        # If no providers are available, return mock for Milestone 2
        fallback = self.providers[0]
        return "JARVIS engine connected. AI coming in Milestone 3.", fallback.name, fallback.model

    async def get_status(self) -> List[ProviderStatus]:
        statuses = []
        for provider in self.providers:
            statuses.append(
                ProviderStatus(
                    name=provider.name,
                    available=await provider.is_available(),
                    model=provider.model
                )
            )
        return statuses

provider_manager = ProviderManager()
