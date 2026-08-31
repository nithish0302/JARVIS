from starlette.testclient import TestClient

from jarvis_engine.main import app


def test_voice_websocket_ordering_and_seq():
    with TestClient(app) as client, client.websocket_connect("/ws/voice") as ws:
        commands = [
            ("what is the time", "The time is 09:30 PM, sir."),
            ("open notepad", "Opening Notepad, sir."),
            ("volume up", "Volume up, sir."),
            ("what time is it", "The time is 09:31 PM, sir."),
            ("lock screen", "Screen locked, sir."),
        ]

        last_seq = -1
        all_command_event_logs = []

        for idx, (text, direct_resp) in enumerate(commands, 1):
            # 1. Wake word detected -> listening
            res = client.post("/voice/status/update", json={"status": "listening"})
            assert res.status_code == 200

            # 2. Voice input processed -> processing, voice_input, voice_response
            res = client.post(
                "/voice/input", json={"text": text, "direct_response": direct_resp}
            )
            assert res.status_code == 200

            # 3. TTS begins speaking -> speaking
            res = client.post("/voice/status/update", json={"status": "speaking"})
            assert res.status_code == 200

            # 4. TTS finishes -> idle
            res = client.post("/voice/status/update", json={"status": "idle"})
            assert res.status_code == 200

            # Collect the 6 events for this command. "audio_level" is a
            # continuous background stream (the mic waveform feed) that
            # shares this same socket and can interleave at any point,
            # independent of command sequencing - skip it from the
            # ordering assertions below but still check its seq.
            events = []
            while len(events) < 6:
                msg = ws.receive_json()

                # Verify sequence number monotonically increases
                seq = msg.get("seq")
                assert seq is not None, f"Event missing seq: {msg}"
                assert seq > last_seq, (
                    f"Sequence not monotonically increasing: {seq} <= {last_seq}"
                )
                last_seq = seq

                if msg.get("type") == "audio_level":
                    continue
                events.append(msg)

            # Format event summary for logging
            seq_summary = []
            for e in events:
                if e["type"] == "voice_status":
                    seq_summary.append(e["status"])
                else:
                    seq_summary.append(e["type"])

            all_command_event_logs.append((idx, text, seq_summary, events))

            # Verify exact expected ordering:
            # [listening, processing, voice_input, voice_response, speaking, idle]
            expected_order = [
                "listening",
                "processing",
                "voice_input",
                "voice_response",
                "speaking",
                "idle",
            ]
            assert seq_summary == expected_order, (
                f"Order mismatch in command {idx}: {seq_summary} != {expected_order}"
            )
            assert seq_summary[-1] == "idle", (
                f"'idle' must be last in command {idx}"
            )
            assert "idle" not in seq_summary[:-1], (
                f"'idle' appeared prematurely in command {idx}: {seq_summary}"
            )

        print("\n=== 5 CONSECUTIVE VOICE COMMANDS WEBSOCKET EVENT ORDER LOG ===")
        for idx, text, seq_summary, events in all_command_event_logs:
            print(f"Command #{idx} ('{text}'):")
            for e in events:
                if e["type"] == "voice_status":
                    print(f"  [seq={e['seq']}] voice_status: {e['status']}")
                elif e["type"] == "voice_input":
                    print(f"  [seq={e['seq']}] voice_input: {e['text']}")
                elif e["type"] == "voice_response":
                    print(f"  [seq={e['seq']}] voice_response: {e['text']}")
            print(f"  Result order: {' -> '.join(seq_summary)}")
            print("---------------------------------------------------------------")
