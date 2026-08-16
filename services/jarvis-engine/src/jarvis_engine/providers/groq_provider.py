from groq import Groq
from .base import BaseProvider
from ..core.models import Message
from typing import AsyncGenerator

class GroqProvider(BaseProvider):

  @property
  def name(self) -> str:
    return "groq"

  @property
  def model(self) -> str:
    from ..core.config import settings
    return settings.GROQ_MODEL

  async def is_available(self) -> bool:
    from ..core.config import settings
    return bool(settings.GROQ_API_KEY)

  async def chat(
    self,
    messages: list[Message],
    stream: bool = False
  ) -> str:
    from ..core.config import settings
    try:
      client = Groq(api_key=settings.GROQ_API_KEY)
      groq_messages = [
        {
          "role": m.role 
            if m.role != "assistant" 
            else "assistant",
          "content": m.content
        }
        for m in messages
        if m.role in ["system","user","assistant"]
      ]
      response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=groq_messages,
        max_tokens=2048,
      )
      return response.choices[0].message.content
    except Exception as e:
      return f"Groq error: {str(e)}"

  async def stream(
    self,
    messages: list[Message]
  ) -> AsyncGenerator[str, None]:
    from ..core.config import settings
    try:
      client = Groq(api_key=settings.GROQ_API_KEY)
      groq_messages = [
        {"role": m.role, "content": m.content}
        for m in messages
        if m.role in ["system","user","assistant"]
      ]
      response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=groq_messages,
        max_tokens=2048,
        stream=True,
      )
      for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
          yield content
    except Exception as e:
      raise e
