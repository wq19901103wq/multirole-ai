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
    
    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 500,
        temperature: float = 0.5,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        支持 function calling 的对话
        
        Returns:
            包含 content 和 tool_calls 的字典
            {
                "content": str | None,
                "tool_calls": [{"id": ..., "function": {"name": ..., "arguments": ...}}]
            }
        """
        p = provider or self.default_provider
        if p is None:
            raise RuntimeError("No LLM provider configured")
        
        # 检查 provider 是否支持 tools
        if hasattr(p, 'chat_completion_with_tools'):
            return p.chat_completion_with_tools(
                messages=messages,
                system=system,
                tools=tools or [],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
        else:
            # 降级为普通 chat，返回格式兼容的字典
            content = p.chat_completion(
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return {"content": content, "tool_calls": []}
