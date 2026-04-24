from abc import ABC, abstractmethod
from typing import List, Dict


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


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI 兼容 API 的基类（Kimi、OpenAI 等）"""

    def _build_messages(self, messages: List[Dict[str, str]], system: str = '') -> List[Dict[str, str]]:
        """组装 messages，插入 system prompt"""
        msgs = list(messages)
        if system:
            msgs.insert(0, {"role": "system", "content": system})
        return msgs

    def _do_chat_request(self, url: str, headers: Dict, payload: Dict) -> Dict:
        """发送 HTTP 请求并解析响应"""
        import requests
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
