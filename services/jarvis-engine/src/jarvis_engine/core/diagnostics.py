"""File-based diagnostic logging for the packaged/frozen sidecar.

The installed app has no visible console for the sidecar process, so
print()/stdout is useless for post-mortem debugging once something fails
in a user's machine. This writes a plain-text log to debug.log, next to
jarvis.db (both live under the app data dir the Tauri shell sets as the
sidecar's cwd - see apps/desktop/src-tauri/src/lib.rs's
prepare_engine_data_dir/spawn_engine_sidecar), so it's discoverable at
the same predictable, writable, per-install location regardless of
platform or how the binary was launched.
"""
import logging
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import settings

LOG_PATH = Path(settings.DB_PATH).resolve().parent / "debug.log"


def setup_file_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("jarvis.diagnostics")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = RotatingFileHandler(
            LOG_PATH, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)
        # Also mirror to stdout when one exists (dev mode / `uv run start.py`)
        # so this doesn't become a file-only, less-visible duplicate there.
        logger.propagate = False
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(handler.formatter)
        logger.addHandler(stream_handler)

    return logger


diagnostics_logger = setup_file_logging()


class RequestLoggingMiddleware:
    """Pure-ASGI middleware (not BaseHTTPMiddleware, to avoid buffering
    responses) that logs the raw Origin header, path, and whether the
    CORS middleware ended up granting the request, for every HTTP
    request. Must be added to the app AFTER CORSMiddleware (add_middleware
    stacks outermost-last, so this needs to run outside it) so it can
    observe the Access-Control-Allow-Origin header CORSMiddleware adds to
    the actual response, not just to preflight.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        origin = headers.get(b"origin", b"(none)").decode("latin-1")
        path = scope.get("path", "")
        method = scope.get("method", "")

        status_holder = {}
        response_headers_holder = {}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                response_headers_holder.update(
                    {k.decode("latin-1").lower(): v.decode("latin-1")
                     for k, v in message.get("headers", [])}
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            diagnostics_logger.error(
                "UNHANDLED EXCEPTION for %s %s | Origin: %s\n%s",
                method, path, origin, traceback.format_exc(),
            )
            raise

        allow_origin = response_headers_holder.get("access-control-allow-origin")
        if origin == "(none)":
            cors_outcome = "N/A (no Origin header)"
        elif allow_origin:
            cors_outcome = f"ALLOWED (Access-Control-Allow-Origin: {allow_origin})"
        else:
            cors_outcome = "REJECTED (no Access-Control-Allow-Origin in response)"

        diagnostics_logger.info(
            "%s %s | Origin: %s | CORS: %s | Status: %s",
            method, path, origin, cors_outcome, status_holder.get("status", "?"),
        )
