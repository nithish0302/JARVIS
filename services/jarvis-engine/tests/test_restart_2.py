import asyncio
import json

from fastapi.testclient import TestClient

from jarvis_engine.core.database import init_db
from jarvis_engine.main import app


def run_tests():
    # Initialize DB (needs event loop)
    asyncio.run(init_db())

    with TestClient(app) as client:
        # GET /settings
        print("\n--- GET /settings after restart ---")
        get_resp = client.get("/settings")
        print(f"JSON Output:\n{json.dumps(get_resp.json(), indent=2)}")


if __name__ == "__main__":
    run_tests()
