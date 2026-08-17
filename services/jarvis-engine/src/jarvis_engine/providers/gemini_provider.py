import httpx
import json
from typing import List, AsyncGenerator
from .base import BaseProvider
from ..core.models import Message

class GeminiProvider(BaseProvider):

  @property
  def name(self) -> str:
    return "gemini"

  @property
  def model(self) -> str:
    from ..core.config import settings
    return settings.GEMINI_MODEL

  async def is_available(self) -> bool:
    from ..core.config import settings
    if not settings.GEMINI_API_KEY:
      return False
    return True

  def _format_messages(self, messages: list[Message]) -> list[dict]:
    if len(messages) > 20:
      system_msgs = [m for m in messages if m.role == "system"]
      other_msgs = [m for m in messages if m.role != "system"]
      messages = system_msgs + other_msgs[-10:]
      
    formatted = []
    
    system_msg = next((m for m in messages if m.role == "system"), None)
    
    for m in messages:
        if m.role == "system":
            continue
        role = "model" if m.role == "assistant" else "user"
        formatted.append({
            "role": role,
            "parts": [{"text": m.content}]
        })
    return formatted, system_msg

  def _build_payload(self, formatted: list[dict], system_msg: Message = None) -> dict:
    payload = {
        "contents": formatted,
    }
    if system_msg:
        payload["system_instruction"] = {
            "parts": [{"text": system_msg.content}]
        }
    return payload

  async def chat(
    self,
    messages: list[Message],
    stream: bool = False
  ) -> str:
    from ..core.config import settings
    formatted, system_msg = self._format_messages(messages)
    payload = self._build_payload(formatted, system_msg)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    
    try:
      async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
          url,
          headers={"Content-Type": "application/json"},
          json=payload
        )
        response.raise_for_status()
        data = response.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return ""
    except httpx.TimeoutException:
      return "Gemini request timed out. Please try again."
    except Exception as e:
      return f"Gemini error: {str(e)}"

  async def stream(
    self,
    messages: list[Message]
  ) -> AsyncGenerator[str, None]:
    from ..core.config import settings
    formatted, system_msg = self._format_messages(messages)
    payload = self._build_payload(formatted, system_msg)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:streamGenerateContent?alt=sse&key={settings.GEMINI_API_KEY}"
    
    try:
      async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
          "POST",
          url,
          headers={"Content-Type": "application/json"},
          json=payload
        ) as response:
          response.raise_for_status()
          async for line in response.aiter_lines():
            if line.startswith("data: "):
              data_str = line[6:]
              if data_str.strip() == "[DONE]":
                break
              try:
                data = json.loads(data_str)
                if "candidates" in data and len(data["candidates"]) > 0:
                  parts = data["candidates"][0].get("content", {}).get("parts", [])
                  if parts and "text" in parts[0]:
                    yield parts[0]["text"]
              except Exception:
                pass
    except Exception as e:
      raise e
