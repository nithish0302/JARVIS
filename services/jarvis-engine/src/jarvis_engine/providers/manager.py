from typing import List
from .base import BaseProvider
from .ollama import OllamaProvider
from .groq_provider import GroqProvider
from .openrouter import OpenRouterProvider
from .gemini_provider import GeminiProvider
from ..core.models import Message, ProviderStatus

class ProviderManager:
    def __init__(self):
        self.providers: List[BaseProvider] = [
            GeminiProvider(),
            OpenRouterProvider(),
            GroqProvider(),
            OllamaProvider(),
        ]

    def set_active_provider(self, provider_name: str, model_name: str):
        # Reorder providers so the selected one is first
        selected = next((p for p in self.providers if p.name == provider_name), None)
        if selected:
            # We don't dynamically change the model inside the provider for now,
            # as they read from config. If we need to support dynamic model switching,
            # we'd update the provider class or config here.
            self.providers.remove(selected)
            self.providers.insert(0, selected)

    async def chat(self, messages: List[Message]) -> tuple[str, str, str]:
        for provider in self.providers:
            try:
                if await provider.is_available():
                    response = await provider.chat(messages)
                    return response, provider.name, provider.model
            except Exception as e:
                print(f"Provider {provider.name} failed: {e}")
                continue
        
        fallback = self.providers[0]
        return (
            "I apologize, sir. All AI systems are "
            "currently unreachable. Please ensure "
            "Ollama is running locally or configure "
            "an OpenRouter API key in the settings.",
            "none",
            "none"
        )

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
