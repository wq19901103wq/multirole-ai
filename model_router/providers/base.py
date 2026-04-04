from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMProvider(ABC):
    """底层模型 provider 统一接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> str:
        """
        返回模型的纯文本回复
        """
        raise NotImplementedError
