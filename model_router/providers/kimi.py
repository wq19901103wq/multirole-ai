import os
import requests
from typing import List, Dict, Any
from .base import LLMProvider


class KimiProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.kimi.com/coding",
        model: str = "kimi-k2.5",
    ):
        self.api_key = api_key or os.getenv("KIMI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return f"kimi/{self.model}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> str:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system

        try:
            resp = requests.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=60,
            )
            result = resp.json()
            if "content" in result and len(result["content"]) > 0:
                return result["content"][0]["text"]
            elif "error" in result:
                return f"【API错误: {result['error'].get('message', '未知错误')}】"
            return "【无响应】"
        except Exception as e:
            return f"【错误: {str(e)}】"
