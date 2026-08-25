import sys


def safe_print(*args, **kwargs) -> None:
    """print() that can't crash on characters the console encoding can't
    represent (e.g. Windows cp1252 vs. a narrow no-break space U+202F that
    Groq and other providers can legitimately return in normal text).
    Falls back to replacing unencodable characters instead of raising."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        target = kwargs.get("file") or sys.stdout
        encoding = getattr(target, "encoding", None) or "utf-8"
        safe_args = [
            str(a).encode(encoding, errors="replace").decode(encoding, errors="replace")
            for a in args
        ]
        print(*safe_args, **kwargs)
