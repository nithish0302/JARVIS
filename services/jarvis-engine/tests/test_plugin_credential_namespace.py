"""Regression tests for credential-namespace resolution.

The bug: delete_plugin_credentials() passed the raw plugin_id to the
credential store instead of resolving credential_namespace first. Gmail
and Google Calendar both store their OAuth tokens under "google", so
deleting "gmail" looked for keys that were never there, deleted nothing,
and still returned {"status": "ok"} - Disconnect appeared to work while
the tokens stayed on disk and the plugin stayed connected.

is_configured() had the resolution logic inline and correct, which is why
the plugin list kept reporting is_configured=True after a "successful"
disconnect. The resolution now lives in one place
(PluginRegistry.resolve_namespace) that both call sites use.

These tests point the credential store at a temporary database via
settings.DB_PATH - they must never touch the real one, which holds live
OAuth tokens.
"""

import sqlite3

import pytest

from jarvis_engine.core.config import settings
from jarvis_engine.plugins import credential_store
from jarvis_engine.plugins.placeholders import register_placeholders
from jarvis_engine.plugins.registry import registry


@pytest.fixture(autouse=True)
def _plugins_registered():
    """The registry is populated by the app lifespan, so tests that don't
    spin up the client would otherwise see it empty. register() is keyed
    by plugin id, so re-registering is idempotent."""
    register_placeholders()


@pytest.fixture
def temp_cred_db(tmp_path, monkeypatch):
    """Point the credential store at a throwaway DB for the duration."""
    db_path = tmp_path / "creds.db"
    monkeypatch.setattr(settings, "DB_PATH", str(db_path))
    yield db_path


def _rows(db_path):
    db = sqlite3.connect(str(db_path))
    try:
        return sorted(
            db.execute("SELECT plugin_id, key FROM plugin_credentials").fetchall()
        )
    finally:
        db.close()


# --------------------------------------------------------------------------
# Namespace resolution
# --------------------------------------------------------------------------


def test_gmail_and_calendar_share_the_google_namespace():
    """The root cause: these two do NOT store under their own ids."""
    assert registry.resolve_namespace("gmail") == "google"
    assert registry.resolve_namespace("google_calendar") == "google"


def test_plugin_without_explicit_namespace_uses_its_own_id():
    assert registry.resolve_namespace("github") == "github"
    assert registry.resolve_namespace("weather") == "weather"


def test_unknown_plugin_resolves_to_none():
    assert registry.resolve_namespace("does_not_exist") is None


def test_plugins_sharing_namespace_reports_both_google_plugins():
    shared = registry.plugins_sharing_namespace("google")
    assert set(shared) == {"gmail", "google_calendar"}
    assert registry.plugins_sharing_namespace("github") == ["github"]


def test_is_configured_and_delete_agree_on_the_namespace():
    """The two call sites must never disagree again - that disagreement
    was the entire bug."""
    for plugin_id in ("gmail", "google_calendar", "github", "weather"):
        plugin = registry.get_plugin(plugin_id)
        expected = plugin.credential_namespace or plugin_id
        assert registry.resolve_namespace(plugin_id) == expected


# --------------------------------------------------------------------------
# Disconnect actually deletes
# --------------------------------------------------------------------------


def test_disconnecting_gmail_clears_the_shared_google_tokens(api_client, temp_cred_db):
    """THE REGRESSION TEST.

    Before the fix this deleted nothing and returned status ok.
    """
    credential_store.store_credential("google", "access_token", "at-value")
    credential_store.store_credential("google", "refresh_token", "rt-value")
    credential_store.store_credential("github", "token", "gh-value")

    assert registry.is_configured("gmail") is True
    assert registry.is_configured("google_calendar") is True

    res = api_client.delete("/plugins/gmail/credentials")

    assert res.status_code == 200
    body = res.json()
    assert body["namespace"] == "google"
    assert body["deleted_keys"] == 2, (
        "Disconnect deleted nothing - it resolved the wrong namespace and "
        "reported success anyway."
    )
    assert body["also_disconnected"] == ["google_calendar"]

    # Physically gone, not just reported gone.
    assert _rows(temp_cred_db) == [("github", "token")]

    # Both Google plugins now read as disconnected.
    assert registry.is_configured("gmail") is False
    assert registry.is_configured("google_calendar") is False
    # And nothing else was touched.
    assert registry.is_configured("github") is True


def test_disconnecting_calendar_also_clears_gmail(api_client, temp_cred_db):
    """Symmetry check: the shared grant means either side disconnects both."""
    credential_store.store_credential("google", "access_token", "at")
    credential_store.store_credential("google", "refresh_token", "rt")

    res = api_client.delete("/plugins/google_calendar/credentials")

    assert res.status_code == 200
    assert res.json()["also_disconnected"] == ["gmail"]
    assert registry.is_configured("gmail") is False
    assert registry.is_configured("google_calendar") is False
    assert _rows(temp_cred_db) == []


def test_disconnecting_github_leaves_google_alone(api_client, temp_cred_db):
    """A plugin with its own namespace must not take others down with it."""
    credential_store.store_credential("google", "access_token", "at")
    credential_store.store_credential("google", "refresh_token", "rt")
    credential_store.store_credential("github", "token", "gh")

    res = api_client.delete("/plugins/github/credentials")

    assert res.status_code == 200
    assert res.json()["also_disconnected"] == []
    assert registry.is_configured("github") is False
    assert registry.is_configured("gmail") is True
    assert _rows(temp_cred_db) == [
        ("google", "access_token"),
        ("google", "refresh_token"),
    ]


def test_deleted_key_count_makes_a_no_op_visible(api_client, temp_cred_db):
    """Disconnecting something already disconnected must not look
    identical to a real disconnect - deleted_keys is what distinguishes
    them, and its absence is what let the original bug hide."""
    res = api_client.delete("/plugins/gmail/credentials")

    assert res.status_code == 200
    assert res.json()["deleted_keys"] == 0


def test_unknown_plugin_is_rejected_not_silently_ok(api_client, temp_cred_db):
    res = api_client.delete("/plugins/not_a_plugin/credentials")

    assert res.status_code == 404
    assert "not_a_plugin" in res.json()["detail"]
