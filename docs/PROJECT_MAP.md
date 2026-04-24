# 项目地图 (PROJECT MAP)

> 本文档为 **multirole-ai** 项目的完整结构索引与模块依赖关系图。
> 自动生成于：2026-04-11

## 项目概览

- **总文件数**: 61 个 Python 文件
- **总类数**: 46 个
- **总函数/方法数**: 195 个

## 目录结构

```
multirole-ai/
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── feishu.py
│   ├── web.py
│   └── wechat.py
├── api/
│   └── server.py
├── benchmarks/
│   └── benchmark_engine.py
├── core/
│   ├── __init__.py
│   ├── event.py
│   ├── message.py
│   └── topic.py
├── drift_guard/
│   ├── __init__.py
│   ├── anchor.py
│   ├── checkpoint.py
│   ├── scorer.py
│   └── truncator.py
├── examples/
│   ├── run_consensus_demo.py
│   ├── run_debate.py
│   └── run_real_debate.py
├── harness_engine/
│   ├── __init__.py
│   ├── agents
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── debater.py
│   │   └── moderator.py
│   ├── autogen_agents.py
│   ├── autogen_client.py
│   ├── consensus_detector.py
│   ├── engine.py
│   ├── group_chat.py
│   └── persona_generator.py
├── model_router/
│   ├── __init__.py
│   ├── providers
│   │   ├── __init__.py
│   │   ├── anthropic.py
│   │   ├── base.py
│   │   ├── kimi.py
│   │   └── openai.py
│   ├── registry.py
│   └── router.py
├── session/
│   ├── __init__.py
│   ├── manager.py
│   ├── models.py
│   ├── store.py
│   └── store_redis.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_adapters.py
│   ├── test_api.py
│   ├── test_drift_guard.py
│   ├── test_feishu_api.py
│   ├── test_harness_engine.py
│   ├── test_model_router.py
│   ├── test_persona_generator.py
│   ├── test_redis_integration.py
│   ├── test_session.py
│   └── test_websocket.py
└── tools/
    ├── __init__.py
    ├── kimi_function_search.py
    ├── react_engine.py
    ├── search.py
    ├── search_free.py
    └── vision.py
```

## 模块依赖关系图

```
multirole-ai/
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── feishu.py  [被 server.py 依赖]
│   ├── web.py  [被 server.py 依赖]
│   └── wechat.py
├── api/
│   └── server.py  [被 test_api.py, test_feishu_api.py, test_redis_integration.py, test_websocket.py 依赖]
├── benchmarks/
│   └── benchmark_engine.py
├── core/
│   ├── __init__.py
│   ├── event.py  [被 base.py, feishu.py, web.py, wechat.py, engine.py, manager.py, models.py, test_adapters.py 依赖]
│   ├── message.py  [被 checkpoint.py, truncator.py, consensus_detector.py, engine.py, group_chat.py, manager.py, test_adapters.py, test_drift_guard.py 依赖]
│   └── topic.py  [被 server.py, benchmark_engine.py, anchor.py, checkpoint.py, run_consensus_demo.py, run_debate.py, run_real_debate.py, engine.py, manager.py, test_drift_guard.py, test_harness_engine.py, test_persona_generator.py, test_redis_integration.py, test_session.py 依赖]
├── drift_guard/
│   ├── __init__.py
│   ├── anchor.py  [被 feishu.py, web.py, wechat.py, engine.py, group_chat.py, test_harness_engine.py 依赖]
│   ├── checkpoint.py  [被 engine.py, group_chat.py, test_harness_engine.py 依赖]
│   ├── scorer.py
│   └── truncator.py  [被 engine.py 依赖]
├── examples/
│   ├── run_consensus_demo.py  [被 server.py 依赖]
│   ├── run_debate.py
│   └── run_real_debate.py
├── harness_engine/
│   ├── __init__.py
│   ├── agents
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── debater.py  [被 test_harness_engine.py, test_persona_generator.py 依赖]
│   │   └── moderator.py  [被 test_harness_engine.py 依赖]
│   ├── autogen_agents.py  [被 group_chat.py 依赖]
│   ├── autogen_client.py  [被 group_chat.py 依赖]
│   ├── consensus_detector.py
│   ├── engine.py  [被 server.py, run_consensus_demo.py, run_debate.py, run_real_debate.py, manager.py, test_persona_generator.py, test_redis_integration.py 依赖]
│   ├── group_chat.py  [被 test_harness_engine.py 依赖]
│   └── persona_generator.py  [被 run_real_debate.py, test_persona_generator.py 依赖]
├── model_router/
│   ├── __init__.py
│   ├── providers
│   │   ├── __init__.py
│   │   ├── anthropic.py
│   │   ├── base.py  [被 benchmark_engine.py, run_consensus_demo.py, conftest.py 依赖]
│   │   ├── kimi.py  [被 server.py, run_debate.py, run_real_debate.py, vision.py 依赖]
│   │   └── openai.py
│   ├── registry.py  [被 server.py 依赖]
│   └── router.py  [被 server.py, checkpoint.py, scorer.py, run_consensus_demo.py, run_debate.py, run_real_debate.py, autogen_client.py, engine.py, group_chat.py, conftest.py, test_redis_integration.py, vision.py 依赖]
├── session/
│   ├── __init__.py
│   ├── manager.py  [被 server.py, test_redis_integration.py 依赖]
│   ├── models.py  [被 test_redis_integration.py 依赖]
│   ├── store.py  [被 server.py, test_redis_integration.py 依赖]
│   └── store_redis.py  [被 server.py, test_redis_integration.py 依赖]
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_adapters.py
│   ├── test_api.py
│   ├── test_drift_guard.py
│   ├── test_feishu_api.py
│   ├── test_harness_engine.py
│   ├── test_model_router.py
│   ├── test_persona_generator.py
│   ├── test_redis_integration.py
│   ├── test_session.py
│   └── test_websocket.py
└── tools/
    ├── __init__.py
    ├── kimi_function_search.py
    ├── react_engine.py  [被 autogen_client.py, group_chat.py 依赖]
    ├── search.py  [被 autogen_agents.py, autogen_client.py, group_chat.py, kimi_function_search.py, react_engine.py, search.py 依赖]
    ├── search_free.py  [被 autogen_agents.py, autogen_client.py, group_chat.py, search.py 依赖]
    └── vision.py
```

## 文件索引

### adapters

#### adapters/__init__.py
- **职责**: 适配器模块入口，导出所有适配器类

#### adapters/base.py
- **职责**: 前端适配器抽象基类定义
- **类**: BaseAdapter
- **关键函数/方法**: render_events, extract_user_message, extract_session_id
- **依赖模块**:
  - `from core.event import DiscussionEvent`

#### adapters/feishu.py
- **职责**: 飞书机器人消息适配器
- **类**: FeishuAdapter
- **关键函数/方法**: render_events, extract_user_message, extract_session_id
- **依赖模块**:
  - `from core.event import DiscussionEvent`
  - `from drift_guard.anchor import TopicAnchor`

#### adapters/web.py
- **职责**: Web/JSON 前端适配器
- **类**: WebAdapter
- **关键函数/方法**: render_events, extract_user_message, extract_session_id
- **依赖模块**:
  - `from core.event import DiscussionEvent`
  - `from drift_guard.anchor import TopicAnchor`

#### adapters/wechat.py
- **职责**: 企业微信/微信公众号适配器
- **类**: WechatAdapter
- **关键函数/方法**: render_events, extract_user_message, extract_session_id
- **依赖模块**:
  - `from core.event import DiscussionEvent`
  - `from drift_guard.anchor import TopicAnchor`

### api

#### api/server.py
- **职责**: 统一 API 入口（Flask），提供 /v1/discuss 及 WebSocket 流式接口
- **关键函数/方法**: _msg_to_event, discuss, feishu_discuss, discuss_consensus, discuss_stream, on_message, discuss_consensus_stream, on_message, on_consensus, health, swagger_ui, index
- **依赖模块**:
  - `from model_router.providers.kimi import KimiProvider`
  - `from model_router.router import ModelRouter`
  - `from model_router.registry import ProviderRegistry`
  - `from harness_engine.engine import HarnessEngine`
  - `from session.manager import SessionManager`
  - `from session.store_redis import RedisSessionStore`
  - `from adapters.web import WebAdapter`
  - `from adapters.feishu import FeishuAdapter`
  - `from examples.run_consensus_demo import DemoProvider`
  - `from core.topic import Topic`

### benchmarks

#### benchmarks/benchmark_engine.py
- **职责**: HarnessEngine 性能基准测试脚本
- **类**: _FakeAnthropic, _FakeOpenAI, MockProvider
- **关键函数/方法**: __init__, __init__, __init__, name, chat_completion, run_benchmark, main
- **依赖模块**:
  - `from core.topic import Topic`
  - `from model_router.providers.base import LLMProvider`

### core

#### core/__init__.py
- **职责**: 核心模块入口，导出 Message/Topic/Event 等

#### core/event.py
- **职责**: 事件模型定义（TurnResult, DiscussionEvent）
- **类**: TurnResult, DiscussionEvent

#### core/message.py
- **职责**: 消息模型定义（Role, Message）
- **类**: Role, Message
- **关键函数/方法**: relevance_score, is_moderation

#### core/topic.py
- **职责**: 议题模型定义（Topic）
- **类**: Topic
- **关键函数/方法**: anchor_prompt

### drift_guard

#### drift_guard/__init__.py
- **职责**: DriftGuard 模块入口

#### drift_guard/anchor.py
- **职责**: 议题锚定器，防止话题漂移
- **类**: TopicAnchor
- **关键函数/方法**: __init__, inject_prompt, extract_relevance, clean_response
- **依赖模块**:
  - `from core.topic import Topic`

#### drift_guard/checkpoint.py
- **职责**: 主持人对齐检查点
- **类**: ModeratorCheckpoint
- **关键函数/方法**: __init__, check
- **依赖模块**:
  - `from core.message import Message`
  - `from model_router.router import ModelRouter`
  - `from core.topic import Topic`

#### drift_guard/scorer.py
- **职责**: 相关性评分器
- **类**: RelevanceScorer
- **关键函数/方法**: __init__, score
- **依赖模块**:
  - `from model_router.router import ModelRouter`

#### drift_guard/truncator.py
- **职责**: 上下文截断器
- **类**: ContextTruncator
- **关键函数/方法**: __init__, truncate
- **依赖模块**:
  - `from core.message import Message`

### examples

#### examples/run_consensus_demo.py
- **职责**: 共识驱动多轮讨论演示脚本（Mock 模式）
- **类**: DemoProvider
- **关键函数/方法**: __init__, name, _extract_topic, _get_round_idx, chat_completion, _agent_responses, main
- **依赖模块**:
  - `from model_router.providers.base import LLMProvider`
  - `from model_router.router import ModelRouter`
  - `from harness_engine.engine import HarnessEngine`
  - `from core.topic import Topic`

#### examples/run_debate.py
- **职责**: 本地调试脚本，直接运行 Harness Engine
- **关键函数/方法**: main
- **依赖模块**:
  - `from model_router.providers.kimi import KimiProvider`
  - `from model_router.router import ModelRouter`
  - `from harness_engine.engine import HarnessEngine`
  - `from core.topic import Topic`

#### examples/run_real_debate.py
- **职责**: 真实端到端多代理辩论示例
- **关键函数/方法**: main
- **依赖模块**:
  - `from model_router.providers.kimi import KimiProvider`
  - `from model_router.router import ModelRouter`
  - `from harness_engine.engine import HarnessEngine`
  - `from core.topic import Topic`
  - `from harness_engine.persona_generator import PersonaGenerator`

### harness_engine

#### harness_engine/__init__.py
- **职责**: Harness 引擎模块入口

#### harness_engine/autogen_agents.py
- **职责**: AutoGen Agent 配置，ReAct 模式
- **关键函数/方法**: create_react_agent, create_moderator_agent, create_debater_agent_basic
- **依赖模块**:
  - `from tools.search_free import get_free_search_tool`

#### harness_engine/autogen_client.py
- **职责**: AutoGen ChatCompletionClient 桥接
- **类**: ModelRouterChatCompletionClient
- **关键函数/方法**: __init__, model_info, capabilities, count_tokens, remaining_tokens, total_usage, actual_usage
- **依赖模块**:
  - `from autogen_core.models import (`
  - `from model_router.router import ModelRouter`
  - `from tools.react_engine import ToolCallingEngine`
  - `from tools.search_free import get_free_search_tool`
  - `from tools.search import get_search_tool`

#### harness_engine/consensus_detector.py
- **职责**: 共识检测器
- **类**: ConsensusDetector
- **关键函数/方法**: __init__, check, _parse, _fallback_check
- **依赖模块**:
  - `from core.message import Message`

#### harness_engine/engine.py
- **职责**: Harness 引擎核心入口
- **类**: HarnessEngine
- **关键函数/方法**: __init__, run, run_stream, run_until_consensus, run_until_consensus_stream
- **依赖模块**:
  - `from core.topic import Topic`
  - `from core.event import TurnResult`
  - `from core.message import Message, Role`
  - `from model_router.router import ModelRouter`
  - `from drift_guard.anchor import TopicAnchor`
  - `from drift_guard.checkpoint import ModeratorCheckpoint`
  - `from drift_guard.truncator import ContextTruncator`

#### harness_engine/group_chat.py
- **职责**: 受控轮次群组讨论实现
- **类**: HarnessGroupChat
- **关键函数/方法**: __init__, _try_import_autogen, run_round, _build_context, _run_manual, _run_with_autogen, candidate_func, selector_func
- **依赖模块**:
  - `from core.message import Message, Role`
  - `from model_router.router import ModelRouter`
  - `from drift_guard.anchor import TopicAnchor`
  - `from drift_guard.checkpoint import ModeratorCheckpoint`
  - `from tools.react_engine import ToolCallingEngine`
  - `from tools.search import get_search_tool`
  - `from harness_engine.autogen_client import ModelRouterChatCompletionClient`
  - `from tools.search_free import get_free_search_tool`
  - `from harness_engine.autogen_agents import create_debater_agent_with_tools`
  - `from harness_engine.autogen_agents import create_react_agent`
  - `from harness_engine.autogen_agents import create_moderator_agent`

#### harness_engine/persona_generator.py
- **职责**: 动态 Persona 生成器
- **类**: PersonaGenerator
- **关键函数/方法**: generate, _generate_default, _generate_with_llm

### harness_engine/agents

#### harness_engine/agents/__init__.py
- **职责**: Agent 子模块入口

#### harness_engine/agents/base.py
- **职责**: Agent 规格基类
- **类**: HarnessAgentSpec

#### harness_engine/agents/debater.py
- **职责**: 辩论者 Agent
- **类**: DebaterAgent
- **关键函数/方法**: __init__

#### harness_engine/agents/moderator.py
- **职责**: 主持人 Agent
- **类**: ModeratorAgent
- **关键函数/方法**: __init__

### model_router

#### model_router/__init__.py
- **职责**: 模型路由模块入口

#### model_router/registry.py
- **职责**: Provider 注册表
- **类**: ProviderRegistry
- **关键函数/方法**: register, get, create

#### model_router/router.py
- **职责**: 模型路由器
- **类**: ModelRouter
- **关键函数/方法**: __init__, chat, chat_with_tools

### model_router/providers

#### model_router/providers/__init__.py
- **职责**: Provider 子模块入口

#### model_router/providers/anthropic.py
- **职责**: Anthropic Claude Provider
- **类**: AnthropicProvider
- **关键函数/方法**: __init__, name, chat_completion

#### model_router/providers/base.py
- **职责**: Provider 抽象基类
- **类**: LLMProvider
- **关键函数/方法**: name, chat_completion

#### model_router/providers/kimi.py
- **职责**: Kimi/Moonshot Provider
- **类**: KimiProvider
- **关键函数/方法**: __init__, name, chat_completion, chat_completion_with_tools

#### model_router/providers/openai.py
- **职责**: OpenAI Provider
- **类**: OpenAIProvider
- **关键函数/方法**: __init__, name, chat_completion

### session

#### session/__init__.py
- **职责**: 会话模块入口

#### session/manager.py
- **职责**: 会话管理器
- **类**: SessionManager
- **关键函数/方法**: __init__, create_session, run_discussion, run_discussion_consensus, _turns_to_events
- **依赖模块**:
  - `from core.topic import Topic`
  - `from core.event import TurnResult, DiscussionEvent`
  - `from core.message import Message, Role`
  - `from harness_engine.engine import HarnessEngine`

#### session/models.py
- **职责**: 会话数据模型
- **类**: DiscussionSession
- **关键函数/方法**: latest_summary
- **依赖模块**:
  - `from core.event import TurnResult`

#### session/store.py
- **职责**: 内存存储实现
- **类**: MemorySessionStore
- **关键函数/方法**: __init__, get, save, delete

#### session/store_redis.py
- **职责**: Redis 存储实现
- **类**: RedisSessionStore
- **关键函数/方法**: __init__, _key, get, save, delete

### tests

#### tests/__init__.py
- **职责**: 测试包

#### tests/conftest.py
- **职责**: Pytest 共享 fixtures（MockProvider）
- **类**: MockProvider
- **关键函数/方法**: __init__, name, chat_completion, mock_provider, router
- **依赖模块**:
  - `from model_router.providers.base import LLMProvider`
  - `from model_router.router import ModelRouter`

#### tests/test_adapters.py
- **职责**: 适配器单元测试
- **关键函数/方法**: make_events, test_web_adapter, test_feishu_adapter, test_wechat_adapter
- **依赖模块**:
  - `from core.message import Message, Role`
  - `from core.event import DiscussionEvent`

#### tests/test_api.py
- **职责**: API 端点测试
- **关键函数/方法**: client, test_health_endpoint, test_discuss_endpoint, test_discuss_missing_message
- **依赖模块**:
  - `from api.server import app`
  - `from api.server import session_manager, router`

#### tests/test_drift_guard.py
- **职责**: DriftGuard 组件测试
- **关键函数/方法**: test_topic_anchor_injects_forbidden_words, test_extract_relevance, test_clean_response, test_context_truncator, test_moderator_checkpoint
- **依赖模块**:
  - `from core.topic import Topic`
  - `from core.message import Message, Role`

#### tests/test_feishu_api.py
- **职责**: 飞书 API 端点测试
- **关键函数/方法**: client, test_feishu_discuss_endpoint, test_feishu_discuss_missing_message
- **依赖模块**:
  - `from api.server import app`
  - `from api.server import session_manager, router`

#### tests/test_harness_engine.py
- **职责**: Harness 引擎测试
- **关键函数/方法**: test_harness_engine_manual_fallback, test_harness_engine_custom_personas, test_harness_engine_with_autogen_installed
- **依赖模块**:
  - `from core.topic import Topic`
  - `from harness_engine.agents.debater import DebaterAgent`
  - `from harness_engine.group_chat import HarnessGroupChat`
  - `from harness_engine.agents.moderator import ModeratorAgent`
  - `from drift_guard.anchor import TopicAnchor`
  - `from drift_guard.checkpoint import ModeratorCheckpoint`

#### tests/test_model_router.py
- **职责**: 模型路由测试
- **关键函数/方法**: test_provider_registry, test_provider_registry_unknown

#### tests/test_persona_generator.py
- **职责**: Persona 生成器测试
- **关键函数/方法**: test_generate_personas_default, test_generate_personas_shared_style, test_engine_uses_dynamic_personas, test_engine_custom_personas_override_dynamic
- **依赖模块**:
  - `from harness_engine.persona_generator import PersonaGenerator`
  - `from harness_engine.engine import HarnessEngine`
  - `from core.topic import Topic`
  - `from harness_engine.agents.debater import DebaterAgent`

#### tests/test_redis_integration.py
- **职责**: Redis 集成测试
- **关键函数/方法**: redis_store, test_redis_store_save_and_get, test_redis_store_delete, test_redis_store_ttl, test_session_manager_with_redis, test_api_with_redis_env
- **依赖模块**:
  - `from session.store_redis import RedisSessionStore`
  - `from session.models import DiscussionSession`
  - `from session.manager import SessionManager`
  - `from core.topic import Topic`
  - `from harness_engine.engine import HarnessEngine`
  - `from model_router.router import ModelRouter`
  - `from api.server import app, session_manager as global_sm`

#### tests/test_session.py
- **职责**: 会话层测试
- **关键函数/方法**: test_session_manager_create_and_run, test_session_manager_latest_summary
- **依赖模块**:
  - `from core.topic import Topic`

#### tests/test_websocket.py
- **职责**: WebSocket 流式接口测试
- **类**: MockWS
- **关键函数/方法**: client, test_discuss_stream_websocket, __init__, receive, send, test_swagger_ui_endpoint
- **依赖模块**:
  - `from api.server import app`
  - `from api.server import sock, discuss_stream`
  - `from api.server import session_manager, router`

### tools

#### tools/__init__.py
- **职责**: 工具模块入口

#### tools/kimi_function_search.py
- **职责**: Kimi Function Calling 搜索实现
- **类**: KimiFunctionSearch, SearchToolWrapper
- **关键函数/方法**: __init__, run, _do_search, __init__, run, _do_search
- **依赖模块**:
  - `from tools.search import SearchTool`

#### tools/react_engine.py
- **职责**: ReAct 推理与工具调用引擎
- **类**: ReActEngine, ToolCallingEngine
- **关键函数/方法**: __init__, run, _execute_search, __init__, run, _search_wrapper
- **依赖模块**:
  - `from tools.search import SearchTool, get_free_search_tool`

#### tools/search.py
- **职责**: 付费搜索 API 封装（Tavily/Serper）
- **类**: SearchTool
- **关键函数/方法**: __init__, _get_api_key_from_env, search, _search_tavily, _search_serper, format_results, get_search_tool, get_free_search_tool
- **依赖模块**:
  - `from tools.search_free import FreeSearchTool`

#### tools/search_free.py
- **职责**: 免费搜索封装（DuckDuckGo/Bing）
- **类**: DuckDuckGoSearch, BingSearchFree, FreeSearchTool
- **关键函数/方法**: __init__, _get_client, search, format_results, __init__, search, __init__, search, format_results, get_free_search_tool

#### tools/vision.py
- **职责**: 多模态图片分析工具
- **类**: VisionAnalyzer
- **关键函数/方法**: __init__, analyze_image, analyze_image_url
- **依赖模块**:
  - `from model_router.router import ModelRouter`
  - `from model_router.providers.kimi import KimiProvider`

## 类索引

| 类名 | 文件 | 职责 |
|------|------|------|
| AnthropicProvider | model_router/providers/anthropic.py | Anthropic Claude API Provider |
| BaseAdapter | adapters/base.py | 前端适配器抽象基类，负责事件流转为前端特定格式 |
| BingSearchFree | tools/search_free.py | Bing 有限免费搜索实现 |
| ConsensusDetector | harness_engine/consensus_detector.py | 共识检测器，分析讨论后判断参与者是否达成一致 |
| ContextTruncator | drift_guard/truncator.py | 上下文截断器，保留关键信息丢弃过远发言 |
| DebaterAgent | harness_engine/agents/debater.py | 辩论型专家 Agent，个性由 TopicAnchor 注入 |
| DemoProvider | examples/run_consensus_demo.py | 演示用的 Mock Provider，模拟渐进式达成共识 |
| DiscussionEvent | core/event.py | 前端可订阅的事件模型，包装 Message 为事件 |
| DiscussionSession | session/models.py | 讨论会话数据模型 |
| DuckDuckGoSearch | tools/search_free.py | DuckDuckGo 免费搜索实现 |
| FeishuAdapter | adapters/feishu.py | 飞书机器人适配器，输出交互卡片格式消息 |
| FreeSearchTool | tools/search_free.py | 免费搜索工具主类，优先使用 DuckDuckGo |
| HarnessAgentSpec | harness_engine/agents/base.py | Harness 引擎中的 Agent 规格数据类 |
| HarnessEngine | harness_engine/engine.py | Harness 工程核心入口，运行受控多轮讨论并集成 DriftGuard |
| HarnessGroupChat | harness_engine/group_chat.py | 兼容层：优先使用 AutoGen 调度，否则退化为手动循环 |
| KimiFunctionSearch | tools/kimi_function_search.py | 使用 Kimi API Function Calling 实现搜索 |
| KimiProvider | model_router/providers/kimi.py | Kimi API Provider，支持 Moonshot API 和本地代理模式 |
| LLMProvider | model_router/providers/base.py | 底层模型 provider 统一抽象接口 |
| MemorySessionStore | session/store.py | 内存 session 存储实现 |
| Message | core/message.py | 消息数据模型，定义角色、内容、发送者及元数据 |
| MockProvider | benchmarks/benchmark_engine.py | 测试用的 Mock Provider，返回固定内容 |
| MockProvider | tests/conftest.py | 测试用的 Mock Provider，返回固定内容 |
| MockWS | tests/test_websocket.py |  |
| ModelRouter | model_router/router.py | 模型路由层，根据策略选择底层 Provider |
| ModelRouterChatCompletionClient | harness_engine/autogen_client.py | AutoGen ChatCompletionClient 到 ModelRouter 的桥接 |
| ModeratorAgent | harness_engine/agents/moderator.py | 主持人 Agent，把控讨论方向 |
| ModeratorCheckpoint | drift_guard/checkpoint.py | 对齐检查点，每轮结束后由 moderator 执行范围检查和摘要 |
| OpenAIProvider | model_router/providers/openai.py | OpenAI API Provider |
| PersonaGenerator | harness_engine/persona_generator.py | 动态生成 4 个平等讨论者的 persona |
| ProviderRegistry | model_router/registry.py | 模型 provider 注册表，支持别名注册和创建 |
| ReActEngine | tools/react_engine.py | ReAct (Reasoning + Acting) 推理引擎 |
| RedisSessionStore | session/store_redis.py | Redis session 存储实现 |
| RelevanceScorer | drift_guard/scorer.py | LLM-as-a-Judge 相关性评分器 |
| Role | core/message.py | 消息角色枚举（USER/SYSTEM/ASSISTANT/MODERATOR） |
| SearchTool | tools/search.py | 网页搜索工具，支持 Tavily/Serper 等 API |
| SearchToolWrapper | tools/kimi_function_search.py | 给不支持 function calling 模型的简化搜索包装器 |
| SessionManager | session/manager.py | 会话层，桥接前端适配器与 Harness Engine |
| ToolCallingEngine | tools/react_engine.py | OpenAI 风格 function calling 工具调用引擎 |
| Topic | core/topic.py | 议题数据模型，包含核心议题文本和三层讨论范围（核心/中间/外层） |
| TopicAnchor | drift_guard/anchor.py | 议题锚定器，注入 system prompt 硬约束并提取相关性评分 |
| TurnResult | core/event.py | 一轮 Harness 引擎的输出结果，包含消息列表和漂移检测 |
| VisionAnalyzer | tools/vision.py | 多模态图片分析器，使用 Kimi K2.5 |
| WebAdapter | adapters/web.py | Web 前端适配器，输出 JSON 供浏览器/小程序消费 |
| WechatAdapter | adapters/wechat.py | 企业微信/微信公众号适配器，输出简洁文本分段 |
| _FakeAnthropic | benchmarks/benchmark_engine.py |  |
| _FakeOpenAI | benchmarks/benchmark_engine.py |  |

## 关键函数索引

| 函数名 | 文件 | 说明 |
|--------|------|------|
| _agent_responses | examples/run_consensus_demo.py | - |
| _build_context | harness_engine/group_chat.py | - |
| _do_search | tools/kimi_function_search.py | - |
| _do_search | tools/kimi_function_search.py | - |
| _execute_search | tools/react_engine.py | - |
| _extract_topic | examples/run_consensus_demo.py | - |
| _fallback_check | harness_engine/consensus_detector.py | - |
| _generate_default | harness_engine/persona_generator.py | - |
| _generate_with_llm | harness_engine/persona_generator.py | - |
| _get_api_key_from_env | tools/search.py | - |
| _get_client | tools/search_free.py | - |
| _get_round_idx | examples/run_consensus_demo.py | - |
| _key | session/store_redis.py | - |
| _msg_to_event | api/server.py | - |
| _parse | harness_engine/consensus_detector.py | - |
| _run_manual | harness_engine/group_chat.py | - |
| _run_with_autogen | harness_engine/group_chat.py | - |
| _search_serper | tools/search.py | - |
| _search_tavily | tools/search.py | - |
| _search_wrapper | tools/react_engine.py | - |
| _try_import_autogen | harness_engine/group_chat.py | - |
| _turns_to_events | session/manager.py | - |
| actual_usage | harness_engine/autogen_client.py | - |
| analyze_image | tools/vision.py | - |
| analyze_image_url | tools/vision.py | - |
| anchor_prompt | core/topic.py | - |
| candidate_func | harness_engine/group_chat.py | - |
| capabilities | harness_engine/autogen_client.py | - |
| chat | model_router/router.py | - |
| chat_completion | benchmarks/benchmark_engine.py | - |
| chat_completion | examples/run_consensus_demo.py | - |
| chat_completion | model_router/providers/anthropic.py | - |
| chat_completion | model_router/providers/base.py | - |
| chat_completion | model_router/providers/kimi.py | - |
| chat_completion | model_router/providers/openai.py | - |
| chat_completion_with_tools | model_router/providers/kimi.py | - |
| chat_with_tools | model_router/router.py | - |
| check | drift_guard/checkpoint.py | - |
| check | harness_engine/consensus_detector.py | - |
| clean_response | drift_guard/anchor.py | - |
| count_tokens | harness_engine/autogen_client.py | - |
| create | model_router/registry.py | - |
| create_debater_agent_basic | harness_engine/autogen_agents.py | - |
| create_moderator_agent | harness_engine/autogen_agents.py | - |
| create_react_agent | harness_engine/autogen_agents.py | - |
| create_session | session/manager.py | - |
| delete | session/store.py | - |
| delete | session/store_redis.py | - |
| discuss | api/server.py | - |
| discuss_consensus | api/server.py | - |
| discuss_consensus_stream | api/server.py | - |
| discuss_stream | api/server.py | - |
| extract_relevance | drift_guard/anchor.py | - |
| extract_session_id | adapters/base.py | - |
| extract_session_id | adapters/feishu.py | - |
| extract_session_id | adapters/web.py | - |
| extract_session_id | adapters/wechat.py | - |
| extract_user_message | adapters/base.py | - |
| extract_user_message | adapters/feishu.py | - |
| extract_user_message | adapters/web.py | - |
| extract_user_message | adapters/wechat.py | - |
| feishu_discuss | api/server.py | - |
| format_results | tools/search.py | - |
| format_results | tools/search_free.py | - |
| format_results | tools/search_free.py | - |
| generate | harness_engine/persona_generator.py | - |
| get | model_router/registry.py | - |
| get | session/store.py | - |
| get | session/store_redis.py | - |
| get_free_search_tool | tools/search.py | - |
| get_free_search_tool | tools/search_free.py | - |
| get_search_tool | tools/search.py | - |
| health | api/server.py | - |
| index | api/server.py | - |
| inject_prompt | drift_guard/anchor.py | - |
| is_moderation | core/message.py | - |
| latest_summary | session/models.py | - |
| main | benchmarks/benchmark_engine.py | - |
| main | examples/run_consensus_demo.py | - |
| main | examples/run_debate.py | - |
| main | examples/run_real_debate.py | - |
| model_info | harness_engine/autogen_client.py | - |
| name | benchmarks/benchmark_engine.py | - |
| name | examples/run_consensus_demo.py | - |
| name | model_router/providers/anthropic.py | - |
| name | model_router/providers/base.py | - |
| name | model_router/providers/kimi.py | - |
| name | model_router/providers/openai.py | - |
| on_consensus | api/server.py | - |
| on_message | api/server.py | - |
| on_message | api/server.py | - |
| register | model_router/registry.py | - |
| relevance_score | core/message.py | - |
| remaining_tokens | harness_engine/autogen_client.py | - |
| render_events | adapters/base.py | - |
| render_events | adapters/feishu.py | - |
| render_events | adapters/web.py | - |
| render_events | adapters/wechat.py | - |
| run | harness_engine/engine.py | - |
| run | tools/kimi_function_search.py | - |
| run | tools/kimi_function_search.py | - |
| run | tools/react_engine.py | - |
| run | tools/react_engine.py | - |
| run_benchmark | benchmarks/benchmark_engine.py | - |
| run_discussion | session/manager.py | - |
| run_discussion_consensus | session/manager.py | - |
| run_round | harness_engine/group_chat.py | - |
| run_stream | harness_engine/engine.py | - |
| run_until_consensus | harness_engine/engine.py | - |
| run_until_consensus_stream | harness_engine/engine.py | - |
| save | session/store.py | - |
| save | session/store_redis.py | - |
| score | drift_guard/scorer.py | - |
| search | tools/search.py | - |
| search | tools/search_free.py | - |
| search | tools/search_free.py | - |
| search | tools/search_free.py | - |
| selector_func | harness_engine/group_chat.py | - |
| swagger_ui | api/server.py | - |
| total_usage | harness_engine/autogen_client.py | - |
| truncate | drift_guard/truncator.py | - |
