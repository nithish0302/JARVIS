import asyncio

from fastapi.testclient import TestClient

from jarvis_engine.core.database import init_db
from jarvis_engine.main import app


def run_tests():
    # Initialize DB (needs event loop)
    asyncio.run(init_db())

    with TestClient(app) as client:
        # POST /settings
        print("--- POST /settings (research, planner) ---")
        post_resp = client.post(
            "/settings", json={"personality_mode": "research", "modifier": "planner"}
        )
        print(f"POST Response: {post_resp.status_code}")


if __name__ == "__main__":
    run_tests()
