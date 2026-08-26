import sqlite3
db = sqlite3.connect(r'd:\JARVIS\services\jarvis-engine\src\data\jarvis.db')
db.execute("INSERT INTO gap_log (gap_id, user_request, detected_intent, gap_reason, timestamp, resolved) VALUES ('123', 'book me a flight to Mumbai', NULL, 'I cannot book flights.', '2026-08-26T12:00:00Z', 0)")
db.commit()
