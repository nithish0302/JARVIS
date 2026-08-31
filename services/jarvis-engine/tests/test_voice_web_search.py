"""Voice's /voice/input previously never called needs_web_search() at all,
so a query like "search for the latest news" got a flat "I can't browse
the internet" instead of an actual search. These tests exercise the LLM
path (direct_response is None) and mock the provider + search pipeline to
confirm: a search-triggering query actually calls search_web() and folds
real results into the prompt sent to the provider, an ordinary query does
not call search_web() at all (regression check), and foreground search
(needs_foreground_search/build_foreground_url) is never invoked from the
voice path - see the report for why that's a deliberate choice, not an
oversight."""

from unittest.mock import AsyncMock, MagicMock, patch

from starlette.testclient import TestClient

from jarvis_engine.main import app


def _fake_provider(response_text: str):
    provider = MagicMock()
    provider.name = "ollama"
    provider.model = "phi4-mini"
    provider.is_available = AsyncMock(return_value=True)
    provider.chat = AsyncMock(return_value=response_text)
    return provider


def test_voice_input_triggers_web_search_for_search_query():
    fake_results = [
        {
            "title": "Big Tech News Today",
            "snippet": "Something genuinely important happened in tech today.",
            "source": "TechCrunch",
            "url": "http://example.com/1",
        },
    ]
    provider = _fake_provider(
        "Something important happened today, according to TechCrunch, sir."
    )

    with (
        patch("jarvis_engine.api.routes.provider_manager") as mock_pm,
        patch(
            "jarvis_engine.api.routes.search_web",
            new=AsyncMock(return_value=fake_results),
        ) as mock_search,
        patch("jarvis_engine.api.routes.needs_web_search", return_value=True),
        patch(
            "jarvis_engine.api.routes.extract_search_query",
            return_value="latest tech news",
        ) as mock_extract,
        patch("jarvis_engine.api.routes.needs_foreground_search") as mock_fg,
        patch("jarvis_engine.api.routes.build_foreground_url") as mock_build_fg,
    ):
        mock_pm.providers = [provider]

        with TestClient(app) as client:
            res = client.post(
                "/voice/input", json={"text": "search for the latest tech news"}
            )

    assert res.status_code == 200
    body = res.json()
    assert "TechCrunch" in body["response"] or "important" in body["response"]

    # The actual fetch happened with the right query and chat's max_results.
    mock_extract.assert_called_once_with("search for the latest tech news")
    mock_search.assert_awaited_once()
    call_args, call_kwargs = mock_search.call_args
    assert call_args[0] == "latest tech news"
    assert call_kwargs.get("max_results") == 5

    # Results actually reached the model: the message list passed to
    # provider.chat() must contain a system message with the search
    # content, inserted before the user's own message.
    sent_messages = provider.chat.call_args[0][0]
    assert sent_messages[-1].role == "user"
    search_messages = [
        m for m in sent_messages if m.role == "system" and "TechCrunch" in m.content
    ]
    assert len(search_messages) == 1
    assert (
        "spoken aloud" in search_messages[0].content
    )  # voice-specific brevity instruction

    # Voice must never trigger foreground (visible browser tab) search.
    mock_fg.assert_not_called()
    mock_build_fg.assert_not_called()


def test_voice_input_ordinary_command_does_not_search():
    """Regression check: a query with no search need must not call
    search_web at all, and the LLM path proceeds normally."""
    provider = _fake_provider("It's currently quite pleasant outside, sir.")

    with (
        patch("jarvis_engine.api.routes.provider_manager") as mock_pm,
        patch("jarvis_engine.api.routes.search_web", new=AsyncMock()) as mock_search,
    ):
        mock_pm.providers = [provider]

        with TestClient(app) as client:
            res = client.post("/voice/input", json={"text": "tell me a joke"})

    assert res.status_code == 200
    mock_search.assert_not_awaited()
    provider.chat.assert_awaited_once()


def test_voice_input_direct_response_bypasses_search_and_llm_entirely():
    """Regression check for the DO-NOT-TOUCH branch: direct_response short
    circuits before any of the new search logic or the LLM."""
    with patch("jarvis_engine.api.routes.search_web", new=AsyncMock()) as mock_search:
        with TestClient(app) as client:
            res = client.post(
                "/voice/input",
                json={
                    "text": "open notepad",
                    "direct_response": "Opening Notepad, sir.",
                },
            )

    assert res.status_code == 200
    body = res.json()
    assert body["response"].endswith("Opening Notepad, sir.")
    assert body["provider_used"] == "direct"
    mock_search.assert_not_awaited()
