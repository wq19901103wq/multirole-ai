import os
import requests
from typing import List, Dict, Any
from .base import LLMProvider


class KimiProvider(LLMProvider):
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

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> str:
        import logging
        logger = logging.getLogger(__name__)
        
        # 构建 OpenAI 兼容格式的消息
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Kimi Code 代理使用特殊请求头模拟 Claude Code
        if self.use_proxy:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "claude-code/0.1.39 (Node.js 20.11.0; darwin 23.6.0; arm64)",
            }
        else:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

        try:
            logger.info(f"[KimiProvider] 发送请求到 {self.base_url}/v1/chat/completions")
            logger.info(f"[KimiProvider] 消息数量: {len(full_messages)}")
            
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            
            logger.info(f"[KimiProvider] 响应状态码: {resp.status_code}")
            
            if resp.status_code != 200:
                error_text = resp.text[:200]
                logger.error(f"[KimiProvider] 请求失败: {resp.status_code} - {error_text}")
                return f"【API错误: HTTP {resp.status_code} - {error_text}】"
            
            result = resp.json()
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
        except requests.exceptions.Timeout:
            logger.error("[KimiProvider] 请求超时")
            return "【错误: 请求超时】"
        except Exception as e:
            logger.error(f"[KimiProvider] 异常: {e}")
            return f"【错误: {str(e)}】"
