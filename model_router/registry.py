from typing import Dict, Type
from .providers.base import LLMProvider


class ProviderRegistry:
    """模型 provider 注册表"""

    _registry: Dict[str, Type[LLMProvider]] = {}

    @classmethod
    def register(cls, alias: str, provider_cls: Type[LLMProvider]):
        cls._registry[alias] = provider_cls

    @classmethod
    def get(cls, alias: str) -> Type[LLMProvider]:
        if alias not in cls._registry:
            raise ValueError(f"Unknown provider alias: {alias}. Registered: {list(cls._registry.keys())}")
        return cls._registry[alias]

    @classmethod
    def create(cls, alias: str, **kwargs) -> LLMProvider:
        provider_cls = cls.get(alias)
        return provider_cls(**kwargs)
