from abc import ABC, abstractmethod
from typing import List
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
    async def chat(self, messages: List[Message], stream: bool = False) -> str:
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        pass
