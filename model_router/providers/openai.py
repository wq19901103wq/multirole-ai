import os
from typing import List, Dict, Any
from openai import OpenAI
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

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
        msgs = messages.copy()
        if system:
            msgs.insert(0, {"role": "system", "content": system})
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=msgs,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content or "【无内容】"
        except Exception as e:
            return f"【错误: {str(e)}】"
