import os
from typing import List, Dict
from .base import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return f"openai/{self.model}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> str:
        msgs = self._build_messages(messages, system)

        payload = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            result = self._do_chat_request(
                f"{self.base_url}/chat/completions",
                headers=headers,
                payload=payload,
            )
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"] or "【无内容】"
            return "【无响应】"
        except Exception as e:
            return f"【错误: {str(e)}】"
