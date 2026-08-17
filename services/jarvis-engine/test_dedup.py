import asyncio
from src.jarvis_engine.api.routes import generate_automation_command
from src.jarvis_engine.core.config import settings

async def main():
    if not settings.GROQ_API_KEY:
        print("Missing Groq API Key")
        return
        
    print("Testing: 'open firefox and search youtube'")
    await generate_automation_command("open firefox and search youtube", settings.GROQ_API_KEY)

if __name__ == "__main__":
    asyncio.run(main())
