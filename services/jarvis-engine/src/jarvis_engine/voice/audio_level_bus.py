"""Thread-safe hand-off point for real-time mic levels.

wake_word.py's audio callback and speech_recorder.py's record loop both run
on real-time-sensitive audio threads and already compute an RMS level per
frame/chunk for their own purposes (self-interrupt threshold, VAD). This
module lets them hand that value off to the asyncio side (a background task
in main.py) without doing any awaiting or broadcasting themselves.

push_level() is O(1) and never blocks: queue.Queue's put/get are internally
locked but only ever held for a pointer swap, never for I/O, so this is safe
to call directly from a PortAudio callback thread.
"""

import queue

_level_queue: "queue.Queue[float]" = queue.Queue()


def push_level(level: float) -> None:
  """Non-blocking. Call from any audio thread with the RMS level for the
  current frame/chunk."""
  try:
    _level_queue.put_nowait(float(level))
  except Exception:
    pass


def get_latest_level():
  """Drains the queue and returns the most recent level pushed since the
  last call, or None if nothing new arrived. Intended to be polled at a
  throttled rate by a single consumer (the broadcaster task in main.py)."""
  latest = None
  try:
    while True:
      latest = _level_queue.get_nowait()
  except queue.Empty:
    pass
  return latest
