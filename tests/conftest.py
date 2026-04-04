import pytest
import sys
import os

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_router.providers.base import LLMProvider
from model_router.router import ModelRouter


class MockProvider(LLMProvider):
    """一个永远返回固定内容的 mock provider，用于测试"""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_log = []

    @property
    def name(self) -> str:
        return "mock/test"

    def chat_completion(self, messages, system="", max_tokens=500, temperature=0.5, **kwargs):
        self.call_log.append({
            "messages": messages,
            "system": system,
            "max_tokens": max_tokens,
        })
        # 如果有针对 system 的固定回复，返回它
        for key, val in self.responses.items():
            if key in system:
                return val
        # 默认返回一个带相关性评分的 mock 回复
        return "关于'测试议题'，我的观点是：这是默认测试回复。\n\n以上观点与核心议题的相关性：9/10"


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def router(mock_provider):
    return ModelRouter(default_provider=mock_provider)
