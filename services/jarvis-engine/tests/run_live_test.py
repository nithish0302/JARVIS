import asyncio

from fastapi.testclient import TestClient

from jarvis_engine.core.database import init_db
from jarvis_engine.main import app


def run_tests():
    from jarvis_engine.providers.manager import provider_manager

    # Move ollama to front
    ollama_p = next((p for p in provider_manager.providers if p.name == "ollama"), None)
    if ollama_p:
        provider_manager.providers.remove(ollama_p)
        provider_manager.providers.insert(0, ollama_p)

    # Initialize DB (needs event loop)
    asyncio.run(init_db())

    test_configs = [
        {
            "mode": "assistant",
            "modifier": "none",
            "query": "how should I approach fixing a flaky test?",
        },
        {
            "mode": "developer",
            "modifier": "none",
            "query": "how should I approach fixing a flaky test?",
        },
        {
            "mode": "research",
            "modifier": "none",
            "query": "how should I approach fixing a flaky test?",
        },
        {"mode": "developer", "modifier": "quiet", "query": "what is 2 + 2?"},
    ]

    with TestClient(app) as client:
        for config in test_configs:
            print(
                f"\n--- Testing Mode: {config['mode']}, Modifier: {config['modifier']} ---"
            )

            # Set settings
            set_resp = client.post(
                "/settings",
                json={
                    "personality_mode": config["mode"],
                    "modifier": config["modifier"],
                },
            )
            print(f"Set Settings Response: {set_resp.status_code}")

            # Run chat
            chat_resp = client.post("/chat", json={"message": config["query"]})

            if chat_resp.status_code == 200:
                content = chat_resp.json()
                if "response" in content:
                    print(f"Response:\n{content['response']}\n")
                else:
                    print(f"Unexpected format: {content}")
            else:
                print(f"Chat failed: {chat_resp.status_code} - {chat_resp.text}")


if __name__ == "__main__":
    run_tests()
