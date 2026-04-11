from typing import AsyncGenerator, Sequence, List, Any
from autogen_core.models import (
    ChatCompletionClient,
    CreateResult,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    RequestUsage,
    ModelInfo,
    ModelFamily,
    ModelCapabilities,
    LLMMessage,
)
from autogen_core import CancellationToken
from model_router.router import ModelRouter


class ModelRouterChatCompletionClient(ChatCompletionClient):
    """
    把 AutoGen 的 ChatCompletionClient 接口桥接到我们自己的 ModelRouter。
    这样 Harness Engine 底层可以继续走统一的模型路由层。
    """

    def __init__(self, router: ModelRouter, model_name: str = "kimi/kimi-k2.5"):
        self.router = router
        self.model_name = model_name
        self._model_info = ModelInfo(
            vision=False,
            function_calling=False,
            json_output=False,
            family=ModelFamily.UNKNOWN,
        )
        self._capabilities = ModelCapabilities(
            vision=False,
            function_calling=False,
            json_output=False,
        )
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)

    # ---- 必须实现的抽象方法 ----

    async def create(
        self,
        messages: Sequence[SystemMessage | UserMessage | AssistantMessage],
        *,
        tools: Sequence[Any] = [],
        json_output: bool | None = None,
        extra_create_args: dict = {},
        cancellation_token: CancellationToken | None = None,
    ) -> CreateResult:
        system = ""
        conversation: List[dict] = []

        for m in messages:
            if isinstance(m, SystemMessage):
                system = m.content or ""
            elif isinstance(m, UserMessage):
                content = m.content
                if isinstance(content, list):
                    content = " ".join(str(c) for c in content)
                conversation.append({"role": "user", "content": content})
            elif isinstance(m, AssistantMessage):
                content = m.content
                if isinstance(content, list):
                    content = " ".join(str(c) for c in content)
                if getattr(m, "thought", None):
                    content = f"{m.thought}\n{content}"
                conversation.append({"role": "assistant", "content": content})

        text = self.router.chat(
            messages=conversation,
            system=system,
            max_tokens=extra_create_args.get("max_tokens", 500),
            temperature=extra_create_args.get("temperature", 0.5),
        )

        return CreateResult(
            finish_reason="stop",
            content=text,
            usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
            cached=False,
        )

    async def create_stream(
        self,
        messages: Sequence[SystemMessage | UserMessage | AssistantMessage],
        *,
        tools: Sequence[Any] = [],
        json_output: bool | None = None,
        extra_create_args: dict = {},
        cancellation_token: CancellationToken | None = None,
    ) -> AsyncGenerator:
        result = await self.create(
            messages,
            tools=tools,
            json_output=json_output,
            extra_create_args=extra_create_args,
            cancellation_token=cancellation_token,
        )
        yield result

    async def close(self) -> None:
        pass

    @property
    def model_info(self) -> ModelInfo:
        return self._model_info

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._capabilities

    def count_tokens(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Any] = []
    ) -> int:
        # 简单估算：每条消息 100 tokens
        return len(messages) * 100

    def remaining_tokens(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Any] = []
    ) -> int:
        return 8000 - self.count_tokens(messages, tools=tools)

    @property
    def total_usage(self) -> RequestUsage:
        return self._total_usage

    @property
    def actual_usage(self) -> RequestUsage:
        return self._total_usage
