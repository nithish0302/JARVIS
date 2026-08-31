from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from ..core.models import Message


class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass

    @abstractmethod
    async def chat(self, messages: list[Message], stream: bool = False) -> str:
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        pass

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        yield ""
