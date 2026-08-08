import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8765/chat",
            json={"message": "Hello JARVIS", "provider": "ollama", "model": "llama3.2:3b"}
        )
        print("Chat Response:", response.json())
        
        # Also test getting conversation history
        conv_id = response.json()["conversation_id"]
        response_hist = await client.get(f"http://localhost:8765/conversation/{conv_id}")
        print("History:", response_hist.json())

if __name__ == "__main__":
    asyncio.run(main())
