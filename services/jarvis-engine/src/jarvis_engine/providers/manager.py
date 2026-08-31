from ..core.models import Message, ProviderStatus
from .base import BaseProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider

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
        self._all_providers: list[BaseProvider] = [
            GeminiProvider(),
            OpenRouterProvider(),
            GroqProvider(),
            OllamaProvider(),
        ]

    @property
    def providers(self) -> list[BaseProvider]:
        """The active provider cascade, computed fresh on every access.

        Ollama is silently excluded whenever OLLAMA_HOST is unset (neither
        .env nor a live settings-table override) - it's a genuinely
        optional, self-hosted provider, not a fourth cloud fallback that
        merely happens to be "unavailable" right now. Excluding it here
        (rather than in is_available()/get_status() alone) keeps it out of
        every consumer - the chat cascade, /providers, /health, the
        <SYSTEM_STATE> "Available Brains" list - without each of them
        needing to know why.
        """
        from ..core.config import settings

        if not settings.OLLAMA_HOST:
            return [p for p in self._all_providers if p.name != "ollama"]
        return list(self._all_providers)

    @providers.setter
    def providers(self, value: list[BaseProvider]):
        """Tests patch provider_manager.providers directly with fake
        provider lists (see tests/test_provider_fallback.py's
        _patch_providers / conftest.py's _reset_provider_state) - keep
        that working by writing straight through to the underlying list.
        The OLLAMA_HOST filter above still applies on read."""
        self._all_providers = list(value)

    @providers.deleter
    def providers(self):
        """No-op: unittest.mock.patch.object(provider_manager, "providers",
        ...) calls delattr() to undo the patch when it can't tell the
        attribute was already set (true for anything backed by a
        property). conftest.py's _reset_provider_state fixture explicitly
        restores the real provider list before AND after every test
        regardless, so there's nothing further to do here."""
        pass

    def set_active_provider(self, provider_name: str, model_name: str):
        """Reorder the underlying providers list so the chosen provider is prioritized first."""
        selected = next(
            (p for p in self._all_providers if p.name == provider_name), None
        )
        if selected:
            # We don't dynamically change the model inside the provider for now,
            # as they read from config. If we need to support dynamic model switching,
            # we'd update the provider class or config here.
            self._all_providers.remove(selected)
            self._all_providers.insert(0, selected)

    def is_unconfigured(self) -> bool:
        """True when NO provider has any credential/host set at all - .env
        default or live settings-table override, either counts. This is
        the "first run, nothing set up yet" state: distinct from a
        configured provider being transiently down, which gets the normal
        fallback/error handling instead. Callers use this to choose a
        "go configure a provider in Settings" message over a generic
        connection-failure one.
        """
        from ..core.config import settings

        return not any(
            [
                settings.GEMINI_API_KEY,
                settings.GROQ_API_KEY,
                settings.OPENROUTER_API_KEY,
                settings.OLLAMA_HOST,
            ]
        )

    async def chat(self, messages: list[Message]) -> tuple[str, str, str]:
        for provider in self.providers:
            try:
                if await provider.is_available():
                    response = await provider.chat(messages)
                    return response, provider.name, provider.model
            except Exception as e:
                print(f"Provider {provider.name} failed: {e}")
                continue

        if self.is_unconfigured():
            message = (
                "I don't have any AI provider configured yet, sir. "
                "Please add an API key in Settings > Providers to get "
                "started."
            )
        else:
            message = (
                "I apologize, sir. All AI systems are "
                "currently unreachable. Please check your "
                "provider configuration in Settings."
            )
        return (message, "none", "none")

    async def get_status(self) -> list[ProviderStatus]:
        statuses = []
        for provider in self.providers:
            statuses.append(
                ProviderStatus(
                    name=provider.name,
                    available=await provider.is_available(),
                    model=provider.model,
                )
            )
        return statuses


# Process-wide global singleton. Shared across all routes, streams, and background tasks.
provider_manager = ProviderManager()


async def restore_preferred_provider() -> str | None:
    """Reads back the PREFERRED provider/model persisted by a manual
    /provider/switch (see api/routes.py) and reorders provider_manager the
    same way set_active_provider() does for a live switch - the restart
    resumes with the same first-choice provider instead of the hardcoded
    Gemini -> OpenRouter -> Groq -> Ollama default.

    This is deliberately the SAME reordering mechanism as a live
    /provider/switch call, not provider_override's hard lock (see
    core/config.py's PREFERRED_PROVIDER / PROVIDER_OVERRIDE docs) - a
    provider restored this way still falls back to the next one in the
    cascade if it's unavailable.

    Returns the restored provider name, or None if there was no
    preference to restore (fresh install, or never manually switched) -
    in which case provider_manager's default order is left untouched.
    Called once, early in main.py's lifespan startup, before the app
    serves any requests.
    """
    from ..core.config import settings
    from ..core.database import get_setting

    preferred_provider = await get_setting(
        "preferred_provider", settings.PREFERRED_PROVIDER
    )
    if not preferred_provider:
        return None
    preferred_model = await get_setting("preferred_model", settings.PREFERRED_MODEL)
    provider_manager.set_active_provider(preferred_provider, preferred_model)
    return preferred_provider
