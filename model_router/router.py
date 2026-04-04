from typing import List, Dict, Any, Optional
from .providers.base import LLMProvider


class ModelRouter:
    """
    模型路由层：根据策略选择底层 Provider。
    当前支持显式指定 provider，未来可扩展为负载均衡/Fallback/成本感知路由。
    """

    def __init__(self, default_provider: Optional[LLMProvider] = None):
        self.default_provider = default_provider

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        max_tokens: int = 500,
        temperature: float = 0.5,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        p = provider or self.default_provider
        if p is None:
            raise RuntimeError("No LLM provider configured")
        return p.chat_completion(
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
