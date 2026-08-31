import json
from collections.abc import AsyncGenerator

import httpx

from ..core.models import Message
from .base import BaseProvider


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

    def _format_messages(
        self, messages: list[Message]
    ) -> tuple[list[dict], Message | None]:
        system_msgs = [m for m in messages if m.role == "system"]
        system_instruction_text = "\n\n---\n\n".join(m.content for m in system_msgs)
        system_msg = (
            Message(role="system", content=system_instruction_text, timestamp="")
            if system_instruction_text
            else None
        )

        other_msgs = [m for m in messages if m.role != "system"]

        while other_msgs:
            total_len = sum(len(m.content) for m in other_msgs) + (
                len(system_instruction_text) if system_instruction_text else 0
            )
            estimated_tokens = total_len // 4
            if estimated_tokens > 6000:
                print(
                    f"[WARNING] Gemini token budget exceeded ({estimated_tokens} > 6000). Trimming oldest message."
                )
                other_msgs.pop(0)
            else:
                break

        # Gemini requires the conversation to start with a 'user' message
        if other_msgs and other_msgs[0].role == "assistant":
            other_msgs.pop(0)

        formatted = []
        for m in other_msgs:
            role = "model" if m.role == "assistant" else "user"
            if formatted and formatted[-1]["role"] == role:
                formatted[-1]["parts"][0]["text"] += "\n\n" + m.content
            else:
                formatted.append({"role": role, "parts": [{"text": m.content}]})
        return formatted, system_msg

    def _build_payload(self, formatted: list[dict], system_msg: Message = None) -> dict:
        payload = {
            "contents": formatted,
        }
        if system_msg:
            payload["systemInstruction"] = {"parts": [{"text": system_msg.content}]}
        return payload

    async def chat(self, messages: list[Message], stream: bool = False) -> str:
        from ..core.config import settings

        formatted, system_msg = self._format_messages(messages)
        payload = self._build_payload(formatted, system_msg)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"

        import json

        print("[DEBUG GEMINI PAYLOAD]", json.dumps(payload, indent=2))

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url, headers={"Content-Type": "application/json"}, json=payload
                )
                response.raise_for_status()
                data = response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                return ""
        except httpx.TimeoutException as e:
            raise Exception("Gemini request timed out. Please try again.") from e
        except Exception as e:
            raise Exception(f"Gemini error: {e!s}") from e

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        from ..core.config import settings

        formatted, system_msg = self._format_messages(messages)
        payload = self._build_payload(formatted, system_msg)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:streamGenerateContent?alt=sse&key={settings.GEMINI_API_KEY}"

        try:
            async with (
                httpx.AsyncClient(timeout=60.0) as client,
                client.stream(
                    "POST",
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                ) as response,
            ):
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "candidates" in data and len(data["candidates"]) > 0:
                                parts = (
                                    data["candidates"][0]
                                    .get("content", {})
                                    .get("parts", [])
                                )
                                if parts and "text" in parts[0]:
                                    yield parts[0]["text"]
                        except Exception:
                            pass
        except Exception as e:
            raise e
