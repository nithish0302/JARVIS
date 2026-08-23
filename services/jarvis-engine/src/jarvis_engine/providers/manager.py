from typing import List
from .base import BaseProvider
from .ollama import OllamaProvider
from .groq_provider import GroqProvider
from .openrouter import OpenRouterProvider
from .gemini_provider import GeminiProvider
from ..core.models import Message, ProviderStatus
# Cerebras is integrated but INACTIVE: the account returns HTTP 402
# (payment_required / param "quota") on every chat completion, for every model
# in its catalog. Auth is fine (/v1/models returns 200), so this is purely an
# account credit-balance issue, not a code issue. cerebras_provider.py is kept
# ready to go - re-add the import and the CerebrasProvider() entry below to
# re-enable once the billing side is sorted out.
# from .cerebras_provider import CerebrasProvider

class ProviderManager:
    """Manages the fallback list of AI LLM providers.

    NOTE: This manager is instantiated as a process-wide singleton (`provider_manager`).
    It maintains global, in-memory state rather than per-conversation or per-request state.
    Calling `set_active_provider()` reorders the provider priority list globally, which
    affects all subsequent and concurrent in-flight requests across the application.
    This is an intentional design tradeoff appropriate for a single-user desktop assistant.
    """
    def __init__(self):
        self.providers: List[BaseProvider] = [
            GeminiProvider(),
            OpenRouterProvider(),
            GroqProvider(),
            OllamaProvider(),
        ]

    def set_active_provider(self, provider_name: str, model_name: str):
        """Reorder the global providers list so the chosen provider is prioritized first."""
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

# Process-wide global singleton. Shared across all routes, streams, and background tasks.
provider_manager = ProviderManager()
