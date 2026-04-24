import os
import logging
from typing import List, Dict, Any
from .base import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class KimiProvider(OpenAICompatibleProvider):
    """
    Kimi API Provider

    支持两种模式：
    1. Moonshot API (api.moonshot.cn) - 需要设置 KIMI_API_KEY
    2. Kimi Code 本地代理 (127.0.0.1:18790) - 无需额外配置

    通过环境变量 MULTIROLE_KIMI_MODE 切换：
    - moonshot (默认): 使用 Moonshot API
    - proxy: 使用本地 Kimi Code 代理
    """
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
    ):
        mode = os.getenv("MULTIROLE_KIMI_MODE", "moonshot").lower()

        if mode == "proxy":
            # 使用本地 Kimi Code 代理
            self.api_key = api_key or os.getenv("KIMICODE_API_KEY", "dummy-key")
            self.base_url = (base_url or "http://127.0.0.1:18790").rstrip("/")
            self.model = model or "kimi-for-coding"
            self.use_proxy = True
        else:
            # 使用 Moonshot API
            self.api_key = api_key or os.getenv("KIMI_API_KEY", "")
            self.base_url = (base_url or "https://api.moonshot.cn").rstrip("/")
            self.model = model or "moonshot-v1-8k"
            self.use_proxy = False

    @property
    def name(self) -> str:
        return f"kimi/{self.model}"

    def _get_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.use_proxy:
            headers["User-Agent"] = "claude-code/0.1.39 (Node.js 20.11.0; darwin 23.6.0; arm64)"
        return headers

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> str:
        full_messages = self._build_messages(messages, system)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        headers = self._get_headers()

        try:
            logger.info(f"[KimiProvider] 发送请求到 {self.base_url}/v1/chat/completions")
            logger.info(f"[KimiProvider] 消息数量: {len(full_messages)}")

            result = self._do_chat_request(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                payload=payload,
            )

            logger.info(f"[KimiProvider] 响应状态码: 200")

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                logger.info(f"[KimiProvider] 成功获取响应，长度: {len(content)}")
                return content
            elif "error" in result:
                error_msg = result['error'].get('message', '未知错误')
                logger.error(f"[KimiProvider] API 错误: {error_msg}")
                return f"【API错误: {error_msg}】"
            logger.warning(f"[KimiProvider] 无响应内容，完整响应: {result}")
            return "【无响应】"
        except Exception as e:
            logger.error(f"[KimiProvider] 异常: {e}")
            return f"【错误: {str(e)}】"

    def chat_completion_with_tools(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        支持 function calling 的对话

        文档：https://platform.moonshot.cn/docs/api/chat#function-calling
        """
        full_messages = self._build_messages(messages, system)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools

        headers = self._get_headers()

        try:
            logger.info(f"[KimiProvider] Function Calling 请求，工具数量: {len(tools) if tools else 0}")

            result = self._do_chat_request(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                payload=payload,
            )

            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])

                logger.info(f"[KimiProvider] 响应: content长度={len(content)}, tool_calls={len(tool_calls)}")

                formatted_tool_calls = []
                for tc in tool_calls:
                    formatted_tool_calls.append({
                        "id": tc.get("id"),
                        "function": {
                            "name": tc.get("function", {}).get("name"),
                            "arguments": tc.get("function", {}).get("arguments", "{}"),
                        }
                    })

                return {
                    "content": content,
                    "tool_calls": formatted_tool_calls
                }
            else:
                logger.warning(f"[KimiProvider] 无响应内容")
                return {"content": "【无响应】", "tool_calls": []}

        except Exception as e:
            logger.error(f"[KimiProvider] 异常: {e}")
            return {"content": f"【错误: {str(e)}】", "tool_calls": []}
