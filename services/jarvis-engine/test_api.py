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

async def test_providers():
  async with httpx.AsyncClient() as client:
    r = await client.get(f"{BASE_URL}/providers")
    data = r.json()
    print(f"\nTest Providers: PASS")
    for p in data:
      status = "available" if p["available"] else "unavailable"
      print(f"  {p['name']}: {status} ({p['model']})")
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

async def test_memories():
  async with httpx.AsyncClient() as client:
    
    # Test saving a memory via chat
    r = await client.post(
      f"{BASE_URL}/chat",
      json={
        "message": 
          "I prefer concise responses " +
          "without unnecessary explanations",
        "conversation_id": None,
        "provider": "ollama",
        "model": "llama3.2:3b"
      }
    )
    
    # Check memories were extracted
    r2 = await client.get(f"{BASE_URL}/memories")
    memories = r2.json()
    print(f"\nTest Memories: {'PASS' if len(memories) > 0 else 'FAIL'}")
    print(f"Memories saved: {len(memories)}")
    for m in memories[:3]:
      print(f"  [{m['category']}] {m['content'][:60]}...")
    
    # Test manual memory creation
    r3 = await client.post(
      f"{BASE_URL}/memories",
      json={
        "content": 
          "Nithish is building JARVIS " +
          "with Tauri v2 and React",
        "category": "project",
        "importance": 8
      }
    )
    print(f"Manual memory: {'PASS' if r3.status_code == 200 else 'FAIL'}")
    
    # Test memory search
    r4 = await client.get(
      f"{BASE_URL}/memories/search?q=JARVIS"
    )
    results = r4.json()
    print(f"Memory search: {'PASS' if len(results) > 0 else 'FAIL'}")

async def test_conversations():
  async with httpx.AsyncClient() as client:
    r = await client.get(
      f"{BASE_URL}/conversations"
    )
    data = r.json()
    print(f"\nTest Conversations: {'PASS' if r.status_code == 200 else 'FAIL'}")
    print(f"Conversations found: {len(data)}")
    for c in data[:3]:
      print(f"  {c['id'][:8]}... — {c.get('message_count', 0)} messages")

async def main():
    print("=" * 50)
    print("JARVIS Engine Integration Tests")
    print("=" * 50)
    
    print("\n--- Test 1: Health Check ---")
    await test_health()
    
    print("\n--- Test 1.5: Providers Check ---")
    await test_providers()
    
    print("\n--- Test 2: First Chat ---")
    chat1 = await test_chat()
    conv_id = chat1.get("conversation_id")
    
    print("\n--- Test 3: Follow-up Chat ---")
    await test_followup(conv_id)
    
    print("\n--- Test 4: Conversation History ---")
    await test_history(conv_id)
    
    print("\n--- Test 5: Long Term Memory ---")
    await test_memories()
    
    print("\n--- Test 6: Conversations List ---")
    await test_conversations()
    
    print("\n" + "=" * 50)
    print("Tests complete")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
