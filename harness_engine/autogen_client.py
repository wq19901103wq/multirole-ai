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
    支持 Function Calling：在 client 层内部实现 ReAct 循环，对 AutoGen 透明。
    """

    def __init__(self, router: ModelRouter, model_name: str = "kimi/kimi-k2.5"):
        self.router = router
        self.model_name = model_name
        self._model_info = ModelInfo(
            vision=False,
            function_calling=True,
            json_output=False,
            family=ModelFamily.UNKNOWN,
        )
        self._capabilities = ModelCapabilities(
            vision=False,
            function_calling=True,
            json_output=False,
        )
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)

    def _convert_messages(self, messages: Sequence[SystemMessage | UserMessage | AssistantMessage]) -> tuple:
        """把 AutoGen 消息格式转换为我们内部格式"""
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

        return system, conversation

    def _format_tools_as_prompt(self, tools: Sequence[Any]) -> str:
        """把 AutoGen FunctionTool 格式转换为模型可理解的文本工具说明"""
        lines = ["\n\n【可用工具】"]
        for tool in tools:
            name = getattr(tool, "name", "unknown")
            desc = getattr(tool, "description", "")
            lines.append(f"\n工具: {name}")
            lines.append(f"描述: {desc}")
            # 尝试提取参数schema
            schema = getattr(tool, "schema", None)
            if schema:
                params = schema.get("parameters", {}).get("properties", {})
                required = schema.get("parameters", {}).get("required", [])
                if params:
                    lines.append("参数:")
                    for param_name, param_info in params.items():
                        ptype = param_info.get("type", "string")
                        pdesc = param_info.get("description", "")
                        req = "(必填)" if param_name in required else "(可选)"
                        lines.append(f"  - {param_name}: {ptype} {req} - {pdesc}")
            lines.append(f"\n调用格式:")
            lines.append(f"TOOL_CALL: {name}")
            for param_name in (schema.get("parameters", {}).get("properties", {}) if schema else {}):
                lines.append(f"{param_name}: <值>")
            lines.append("")
        lines.append("如果不需要工具，直接给出回答。")
        return "\n".join(lines)

    async def create(
        self,
        messages: Sequence[SystemMessage | UserMessage | AssistantMessage],
        *,
        tools: Sequence[Any] = [],
        json_output: bool | None = None,
        extra_create_args: dict = {},
        cancellation_token: CancellationToken | None = None,
    ) -> CreateResult:
        system, conversation = self._convert_messages(messages)

        # 如果有工具，在 client 层内部实现 ReAct 循环
        if tools:
            from tools.react_engine import ToolCallingEngine
            from tools.search_free import get_free_search_tool

            search_tool = get_free_search_tool()
            if search_tool and search_tool.providers:
                engine = ToolCallingEngine(self.router, search_tool)
                # ToolCallingEngine 会在内部添加工具说明并处理循环
                text = engine.run(
                    system_prompt=system,
                    conversation=conversation,
                    max_iterations=3,
                )
            else:
                # 搜索不可用，降级为直接调用
                text = self.router.chat(
                    messages=conversation,
                    system=system,
                    max_tokens=extra_create_args.get("max_tokens", 4000),
                    temperature=extra_create_args.get("temperature", 0.5),
                )
        else:
            # 无工具时直接调用
            text = self.router.chat(
                messages=conversation,
                system=system,
                max_tokens=extra_create_args.get("max_tokens", 4000),
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
