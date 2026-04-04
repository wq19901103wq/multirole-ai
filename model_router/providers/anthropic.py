import os
from typing import List, Dict, Any
import anthropic
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = None,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    @property
    def name(self) -> str:
        return f"anthropic/{self.model}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> str:
        # Anthropic 要求第一条消息必须是 user
        msgs = messages.copy()
        if msgs and msgs[0].get("role") == "system":
            msgs.pop(0)

        # 转换 role: assistant -> assistant, user -> user, 其他过滤
        clean_msgs = []
        for m in msgs:
            role = m.get("role")
            if role in ("user", "assistant"):
                clean_msgs.append({"role": role, "content": m.get("content", "")})

        if not clean_msgs:
            clean_msgs.append({"role": "user", "content": "Please respond."})

        try:
            resp = self.client.messages.create(
                model=self.model,
                messages=clean_msgs,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if resp.content and len(resp.content) > 0:
                return resp.content[0].text
            return "【无响应】"
        except Exception as e:
            return f"【错误: {str(e)}】"
