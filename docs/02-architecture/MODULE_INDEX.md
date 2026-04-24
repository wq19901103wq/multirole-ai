# 模块索引

> 不知道改哪个文件时，先查这个。

---

## 快速定位

| 我想做... | 看哪个模块 | 具体文件 |
|-----------|-----------|----------|
| 修改 Agent 发言行为 | `harness_engine` | `autogen_agents.py` |
| 修改 ReAct 提示词 | `harness_engine` | `autogen_agents.py` |
| 修改搜索工具调用 | `tools` | `search_free.py`, `react_engine.py` |
| 修改防漂移逻辑 | `drift_guard` | `anchor.py`, `scorer.py`, `truncator.py` |
| 修改议题锚定 Prompt | `drift_guard` | `anchor.py` |
| 修改相关性评分 | `drift_guard` | `scorer.py` |
| 修改上下文截断 | `drift_guard` | `truncator.py` |
| 添加新模型支持 | `model_router/providers` | 新建 `xxx.py` |
| 修改模型调用逻辑 | `model_router` | `router.py` |
| 添加新前端适配 | `adapters` | 新建 `xxx.py` |
| 修改会话存储 | `session` | `store.py` 或 `store_redis.py` |
| 修改 API 接口 | `api` | `server.py` |
| 修改讨论流程 | `harness_engine` | `group_chat.py` |
| 修改 Moderator 行为 | `harness_engine` | `autogen_agents.py` |

---

## 目录结构详解

### `adapters/` - 前端适配层

| 文件 | 职责 | 状态 |
|------|------|------|
| `base.py` | `BaseAdapter` 抽象接口 | ✅ 已上线 |
| `web.py` | `WebAdapter` HTTP/JSON 格式 | ✅ 已上线 |
| `feishu.py` | `FeishuAdapter` 飞书卡片格式 | ✅ 已上线 |
| `wechat.py` | `WechatAdapter` 微信消息格式 | 🚧 未实现 |

**何时修改**：
- 添加新前端渠道（钉钉、Slack 等）
- 修改响应格式（卡片 → 纯文本）

---

### `session/` - 会话层

| 文件 | 职责 | 状态 |
|------|------|------|
| `manager.py` | `SessionManager` 会话管理入口 | ✅ 已上线 |
| `store.py` | `MemorySessionStore` 内存存储 | ✅ 已上线 |
| `store_redis.py` | `RedisSessionStore` Redis 存储 | ✅ 已上线 |
| `models.py` | `DiscussionSession` 领域模型 | ✅ 已上线 |

**何时修改**：
- 添加新的存储后端（MongoDB、PostgreSQL）
- 修改会话生命周期管理

---

### `harness_engine/` - 核心协调引擎

| 文件 | 职责 | 状态 |
|------|------|------|
| `engine.py` | `HarnessEngine` 编排入口 | ✅ 已上线 |
| `group_chat.py` | `HarnessGroupChat` 讨论协调器 | ✅ 已上线 |
| `autogen_client.py` | `ModelRouterChatCompletionClient` AutoGen 兼容 | ✅ 已上线 |
| `autogen_agents.py` | Agent 配置（ReAct 模式） | ✅ 已上线 |

**关键函数**：
- `create_react_agent()` - 创建 ReAct 模式 Agent
- `create_moderator_agent()` - 创建主持人 Agent
- `HarnessGroupChat.run_round()` - 执行一轮讨论

**何时修改**：
- 修改 Agent 提示词模板
- 修改讨论流程（发言顺序、并行/串行）
- 添加新的 Agent 类型

---

### `drift_guard/` - 防漂移核心

| 文件 | 职责 | 关键类 |
|------|------|--------|
| `anchor.py` | 议题锚定 | `TopicAnchor` |
| `scorer.py` | 相关性评分 | `RelevanceScorer` |
| `truncator.py` | 上下文截断 | `ContextTruncator` |
| `checkpoint.py` | 对齐检查点 | `ModeratorCheckpoint` |

**TopicAnchor** (`anchor.py`):
```python
class TopicAnchor:
    def inject_prompt(self, name, personality, style) -> str:
        # 在 system_prompt 中注入议题锚定约束
        ...
```

**RelevanceScorer** (`scorer.py`):
```python
class RelevanceScorer:
    def score(self, response: str, topic: str) -> float:
        # 返回 0-10 的相关性评分
        ...
```

**ContextTruncator** (`truncator.py`):
```python
class ContextTruncator:
    def truncate(self, history: List[Message], summary: str) -> List[Message]:
        # Round 2+ 只保留摘要
        ...
```

**何时修改**：
- 调整议题锚定 Prompt
- 修改相关性评分算法
- 调整上下文截断策略

---

### `model_router/` - 模型路由层

| 文件 | 职责 | 关键类 |
|------|------|--------|
| `router.py` | 路由入口 | `ModelRouter` |
| `registry.py` | 注册表 | `ProviderRegistry` |
| `providers/base.py` | 抽象接口 | `LLMProvider` |
| `providers/kimi.py` | Kimi 实现 | `KimiProvider` |
| `providers/openai.py` | OpenAI 实现 | `OpenAIProvider` |
| `providers/anthropic.py` | Anthropic 实现 | `AnthropicProvider` |

**添加新模型的步骤**：
1. 在 `providers/` 下新建 `xxx.py`
2. 继承 `LLMProvider`
3. 实现 `chat_completion()` 方法
4. 在 `__init__.py` 中注册

---

### `tools/` - 工具层

| 文件 | 职责 | 关键类/函数 |
|------|------|-------------|
| `search_free.py` | 免费搜索（DuckDuckGo / Bing） | `DuckDuckGoSearch`, `BingSearchFree`, `FreeSearchTool`, `get_free_search_tool()` |
| `search.py` | 付费搜索（Tavily/Serper） | `SearchTool`, `get_search_tool()` |
| `react_engine.py` | ReAct 引擎 | `ToolCallingEngine` |
| `kimi_function_search.py` | Kimi Function Calling 搜索 | `KimiFunctionSearch`, `SearchToolWrapper` |
| `vision.py` | 多模态图片分析 | `VisionAnalyzer` |

**DuckDuckGoSearch** (`search_free.py`):
```python
class DuckDuckGoSearch:
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        # 返回 [{"title": ..., "url": ..., "snippet": ...}]
        ...
```

**ToolCallingEngine** (`react_engine.py`):
```python
class ToolCallingEngine:
    def run(self, system_prompt, conversation, max_iterations=3):
        # 解析 SEARCH: 标记，执行搜索，返回结果
        ...
```

**何时修改**：
- 添加新的搜索引擎
- 修改 ReAct 执行逻辑

---

### `api/` - API 层

| 文件 | 职责 | 端点 |
|------|------|------|
| `server.py` | Flask HTTP 服务 | `/health`, `/v1/discuss`, `/v1/feishu/discuss`, `/v1/discuss/stream` |

**端点列表**：
```python
GET  /health                    # 健康检查
POST /v1/discuss               # 统一讨论接口
POST /v1/feishu/discuss        # 飞书专用接口
WS   /v1/discuss/stream        # WebSocket 流式
GET  /apidocs/                 # Swagger UI
GET  /apispec_1.json           # Swagger JSON
```

**何时修改**：
- 添加新 API 端点
- 修改请求/响应格式

---

### `tests/` - 测试套件

| 文件 | 测试内容 |
|------|----------|
| `test_adapters.py` | Adapter 层 |
| `test_api.py` | API 端点 |
| `test_drift_guard.py` | DriftGuard 组件 |
| `test_harness_engine.py` | Harness Engine |
| `test_model_router.py` | Model Router |
| `test_session.py` | Session 层 |
| `test_redis_integration.py` | Redis 集成 |
| `test_feishu_api.py` | 飞书 API |
| `test_websocket.py` | WebSocket |
| `test_persona_generator.py` | Persona 生成 |

---

### `examples/` - 示例脚本

| 文件 | 用途 |
|------|------|
| `run_debate.py` | 命令行示例（Mock 模式） |
| `run_real_debate.py` | 真实 LLM 端到端演示 |

---

### `benchmarks/` - 性能基准

| 文件 | 用途 |
|------|------|
| `benchmark_engine.py` | 测试不同配置的延迟 |

---

## 依赖关系

```
adapters/
    ↓ 依赖
session/
    ↓ 依赖
harness_engine/
    ↓ 依赖
drift_guard/
    ↓ 依赖
model_router/
    ↓ 依赖
tools/
```

**禁止循环依赖**：
- `drift_guard` 不能依赖 `harness_engine`
- `model_router` 不能依赖 `harness_engine`

---

## 文件命名规范

| 类型 | 命名示例 |
|------|----------|
| 模块入口 | `manager.py`, `router.py`, `engine.py` |
| 抽象基类 | `base.py` |
| 具体实现 | `kimi.py`, `web.py`, `store_redis.py` |
| 工具模块 | `search_free.py`, `react_engine.py` |
| 测试文件 | `test_xxx.py` |
| 配置/常量 | 放在对应模块的 `__init__.py` 或 `config.py` |

---

## 返回总纲

- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
- [AI_QUICKSTART.md](../01-quickstart/AI_QUICKSTART.md) - 快速上手

### `harness_engine/` 补充

| 文件 | 职责 | 状态 |
|------|------|------|
| `consensus_detector.py` | 共识检测器，检测多 Agent 是否达成一致 | ✅ 已上线 |
| `persona_generator.py` | Persona 生成器，自动生成 Agent 角色配置 | ✅ 已上线 |

### `tools/` 补充

| 文件 | 职责 | 状态 |
|------|------|------|
| `kimi_function_search.py` | 使用 Kimi API Function Calling 实现搜索（比文本解析更可靠） | ✅ 已上线 |
| `vision.py` | 多模态分析工具，使用 Kimi K2.5 API 分析图片 | ✅ 已上线 |

