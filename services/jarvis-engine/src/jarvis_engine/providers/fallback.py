"""Shared provider-cascade/override/ask-mode logic used by the chat, chat
stream, and voice endpoints in api/routes.py, so the three don't drift out
of sync on how provider_override and fallback_mode are honored."""
from typing import List, Optional, TypedDict

from ..core.database import get_setting, set_setting
from .manager import provider_manager

VALID_PROVIDERS = {"gemini", "openrouter", "groq", "ollama"}


class CascadeResult(TypedDict, total=False):
    status: str  # "ok" | "asking" | "override_unavailable" | "all_failed"
    response_text: str
    provider_used: str
    model_used: str
    fallback_occurred: bool
    failed_provider: Optional[str]
    failed_providers: List[str]
    remaining: List[str]


async def get_provider_settings() -> tuple[Optional[str], str]:
    """Returns (provider_override or None, fallback_mode)."""
    override = (await get_setting("provider_override", "") or "").strip().lower()
    if override not in VALID_PROVIDERS:
        override = None
    fallback_mode = (await get_setting("fallback_mode", "auto") or "auto").strip().lower()
    if fallback_mode not in ("auto", "ask"):
        fallback_mode = "auto"
    return override, fallback_mode


def extract_provider_from_text(text: str) -> Optional[str]:
    """Best-effort scan of free text for a provider name, used to read the
    user's answer after we've asked which provider to fall back to."""
    lowered = (text or "").lower()
    if "open router" in lowered or "openrouter" in lowered:
        return "openrouter"
    for name in ("gemini", "groq", "ollama"):
        if name in lowered:
            return name
    return None


async def consume_awaiting_choice(user_text: str) -> Optional[str]:
    """If a prior turn asked the user to pick a fallback provider, this is
    their answer. Clears the pending flag either way (a non-matching reply
    falls through to a normal auto cascade rather than getting the user
    stuck) and returns the provider they named, if any."""
    awaiting = await get_setting("awaiting_provider_choice", "false") == "true"
    if not awaiting:
        return None
    await set_setting("awaiting_provider_choice", "false")
    return extract_provider_from_text(user_text)


def build_fallback_note(failed_provider: str, used_provider: str) -> str:
    return f"{failed_provider.title()} had an issue, so I used {used_provider.title()} instead. "


def build_ask_message(failed_provider: str, remaining: List[str]) -> str:
    options = ", ".join(p.title() for p in remaining) if remaining else "another provider"
    return (
        f"{failed_provider.title()} had an issue, sir, and I'm set to ask before "
        f"falling back rather than switch automatically. Would you like me to "
        f"try {options}?"
    )


def build_unconfigured_message() -> str:
    """Shown instead of a generic connection-failure message when NO
    provider has any credential/host configured at all (see
    ProviderManager.is_unconfigured()) - a fresh install with nothing set
    up yet, not a configured provider that's transiently down."""
    return (
        "I don't have any AI provider configured yet, sir. Please add an "
        "API key in Settings > Providers to get started."
    )


def build_override_unavailable_message(provider_name: str) -> str:
    return (
        f"{provider_name.title()} is locked in as the only provider I'm allowed to "
        f"use, sir, but it's unavailable right now. I haven't tried anything else - "
        f"clear the provider override in settings, or tell me to use a different "
        f"provider, if you'd like me to fall back."
    )


async def _provider_available(provider) -> bool:
    try:
        return await provider.is_available()
    except Exception:
        return False


async def run_cascade(messages, user_text: str = "", providers: Optional[list] = None) -> CascadeResult:
    """Runs the provider cascade honoring provider_override and
    fallback_mode. `providers` overrides the trial order (e.g. callers that
    reorder for automation/file commands) but provider_override still takes
    priority over it. Does not touch conversation persistence or TTS -
    callers handle that with the returned fields."""
    providers = providers if providers is not None else provider_manager.providers
    override, fallback_mode = await get_provider_settings()

    one_shot_provider = await consume_awaiting_choice(user_text)
    if one_shot_provider:
        override = one_shot_provider

    if override:
        provider = next(
            (p for p in providers if p.name == override), None
        )
        if provider is None or not await _provider_available(provider):
            return {"status": "override_unavailable", "failed_provider": override}
        try:
            response_text = await provider.chat(messages)
        except Exception:
            return {"status": "override_unavailable", "failed_provider": override}
        return {
            "status": "ok",
            "response_text": response_text,
            "provider_used": provider.name,
            "model_used": provider.model,
            "fallback_occurred": False,
            "failed_provider": None,
        }

    failed_providers: List[str] = []
    for provider in providers:
        available = await _provider_available(provider)
        if not available:
            failed_providers.append(provider.name)
            if fallback_mode == "ask":
                await set_setting("awaiting_provider_choice", "true")
                remaining = [
                    p.name for p in providers
                    if p.name != provider.name
                ]
                return {
                    "status": "asking",
                    "failed_provider": provider.name,
                    "failed_providers": failed_providers,
                    "remaining": remaining,
                }
            continue

        try:
            response_text = await provider.chat(messages)
        except Exception:
            failed_providers.append(provider.name)
            if fallback_mode == "ask":
                await set_setting("awaiting_provider_choice", "true")
                remaining = [
                    p.name for p in providers
                    if p.name != provider.name
                ]
                return {
                    "status": "asking",
                    "failed_provider": provider.name,
                    "failed_providers": failed_providers,
                    "remaining": remaining,
                }
            continue

        return {
            "status": "ok",
            "response_text": response_text,
            "provider_used": provider.name,
            "model_used": provider.model,
            "fallback_occurred": len(failed_providers) > 0,
            "failed_provider": failed_providers[0] if failed_providers else None,
            "failed_providers": failed_providers,
        }

    return {"status": "all_failed", "failed_providers": failed_providers}
