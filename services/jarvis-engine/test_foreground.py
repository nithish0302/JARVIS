from jarvis_engine.api.routes import build_foreground_url, needs_foreground_search

tests = [
    ("show me latest iPhone price", True),
    ("search tamil songs on youtube", True),
    ("play AR Rahman on youtube", True),
    ("open gmail", True),
    ("open youtube and search gaming", True),
    ("what is the latest AI news", False),
    ("search for news", False),
    ("open skills hub", False),
    ("show my files", False),
    ("lock my screen", False),
]

print("Foreground Search Detection:")
for msg, expected in tests:
    result = needs_foreground_search(msg)
    status = "PASS" if result == expected else "FAIL"
    tag = "FORE" if result else "BACK"
    print(f"  {status} [{tag}] {msg}")
    if result:
        url_info = build_foreground_url(msg)
        print(f"         URL: {url_info['url'][:60]}")
