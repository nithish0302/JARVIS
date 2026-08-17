from jarvis_engine.api.routes import build_foreground_url

tests = [
  'search tamil songs on youtube',
  'play AR Rahman on youtube',
  'search gaming videos on youtube',
  'watch cricket highlights on youtube',
]
for t in tests:
  result = build_foreground_url(t)
  print(f'{t}')
  print(f'  -> {result["url"]}')
