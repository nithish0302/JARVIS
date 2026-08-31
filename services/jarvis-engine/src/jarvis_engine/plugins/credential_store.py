import ctypes
import ctypes.wintypes
import datetime
import sqlite3
import sys

from ..core.config import settings

if sys.platform == "win32":
    crypt32 = ctypes.windll.crypt32
else:
    crypt32 = None


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _check_windows():
    if not crypt32:
        raise NotImplementedError(
            "Credential store requires Windows DPAPI in this version."
        )


def _encrypt(data: bytes) -> bytes:
    _check_windows()
    blob_in = DATA_BLOB()
    blob_in.cbData = len(data)
    blob_in.pbData = ctypes.cast(
        ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)
    )

    blob_out = DATA_BLOB()

    if crypt32.CryptProtectData(
        ctypes.byref(blob_in), "JARVIS", None, None, None, 0, ctypes.byref(blob_out)
    ):
        result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result
    else:
        raise RuntimeError("CryptProtectData failed")


def _decrypt(data: bytes) -> bytes:
    _check_windows()
    blob_in = DATA_BLOB()
    blob_in.cbData = len(data)
    blob_in.pbData = ctypes.cast(
        ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)
    )

    blob_out = DATA_BLOB()

    if crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return result
    else:
        raise RuntimeError("CryptUnprotectData failed")


def _get_db():
    db = sqlite3.connect(settings.DB_PATH)
    # Ensure the table exists even if init_db wasn't fully run or we are testing
    db.execute("""
        CREATE TABLE IF NOT EXISTS plugin_credentials (
            plugin_id TEXT,
            key TEXT,
            encrypted_blob BLOB,
            created_at TEXT,
            updated_at TEXT,
            PRIMARY KEY (plugin_id, key)
        )
    """)
    return db


def store_credential(plugin_id: str, key: str, value: str) -> None:
    _check_windows()
    enc_value = _encrypt(value.encode("utf-8"))
    now = datetime.datetime.now(datetime.UTC).isoformat()

    with _get_db() as db:
        db.execute(
            """
            INSERT INTO plugin_credentials (plugin_id, key, encrypted_blob, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(plugin_id, key) DO UPDATE SET
                encrypted_blob=excluded.encrypted_blob,
                updated_at=excluded.updated_at
        """,
            (plugin_id, key, enc_value, now, now),
        )


def get_credential(plugin_id: str, key: str) -> str | None:
    _check_windows()
    with _get_db() as db:
        cursor = db.execute(
            """
            SELECT encrypted_blob FROM plugin_credentials WHERE plugin_id = ? AND key = ?
        """,
            (plugin_id, key),
        )
        row = cursor.fetchone()
        if not row:
            return None

        try:
            return _decrypt(row[0]).decode("utf-8")
        except Exception:
            return None


def delete_credential(plugin_id: str, key: str) -> None:
    with _get_db() as db:
        db.execute(
            """
            DELETE FROM plugin_credentials WHERE plugin_id = ? AND key = ?
        """,
            (plugin_id, key),
        )


def list_credential_keys(plugin_id: str) -> list[str]:
    with _get_db() as db:
        cursor = db.execute(
            """
            SELECT key FROM plugin_credentials WHERE plugin_id = ?
        """,
            (plugin_id,),
        )
        return [row[0] for row in cursor.fetchall()]
