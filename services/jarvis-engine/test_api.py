import asyncio
import httpx
import json

BASE_URL = "http://localhost:8765"

async def test_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/health")
        data = r.json()
        ollama = next(
            (p for p in data["providers"] 
             if p["name"] == "ollama"), None
        )
        available = ollama and ollama["available"]
        print(f"Health check: {'PASS' if available else 'FAIL'}")
        print(f"Ollama available: {available}")
        return data

async def test_chat(conv_id=None):
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "message": "Hello, who are you?",
            "conversation_id": conv_id,
            "provider": "ollama",
            "model": "llama3.2:3b"
        }
        r = await client.post(
            f"{BASE_URL}/chat", 
            json=payload
        )
        data = r.json()
        print(f"\nTest Chat 1: {'PASS' if r.status_code == 200 else 'FAIL'}")
        print(f"Response: {data.get('response', 'ERROR')}")
        print(f"Conversation ID: {data.get('conversation_id')}")
        return data

async def test_followup(conv_id):
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "message": "What can you help me with?",
            "conversation_id": conv_id,
            "provider": "ollama",
            "model": "llama3.2:3b"
        }
        r = await client.post(
            f"{BASE_URL}/chat",
            json=payload
        )
        data = r.json()
        print(f"\nTest Chat 2 (follow-up): {'PASS' if r.status_code == 200 else 'FAIL'}")
        print(f"Response: {data.get('response', 'ERROR')}")
        return data

async def test_history(conv_id):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/conversation/{conv_id}"
        )
        data = r.json()
        msg_count = len(data)
        passed = msg_count >= 4
        print(f"\nTest History: {'PASS' if passed else 'FAIL'}")
        print(f"Message count: {msg_count} (expected 4+)")
        for m in data:
            print(f"  [{m['role']}]: {m['content'][:80]}...")
        return data

async def main():
    print("=" * 50)
    print("JARVIS Engine Integration Tests")
    print("=" * 50)
    
    print("\n--- Test 1: Health Check ---")
    await test_health()
    
    print("\n--- Test 2: First Chat ---")
    chat1 = await test_chat()
    conv_id = chat1.get("conversation_id")
    
    print("\n--- Test 3: Follow-up Chat ---")
    await test_followup(conv_id)
    
    print("\n--- Test 4: Conversation History ---")
    await test_history(conv_id)
    
    print("\n" + "=" * 50)
    print("Tests complete")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
