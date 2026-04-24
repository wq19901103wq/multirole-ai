# 架构设计

> 目标架构文档（Target Architecture），当前实际代码与此基本一致。

---

## 架构总览

Multirole AI 采用**分层架构**，从上到下依次是：

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend Layer (Adapters)                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                           │
│  │ Web     │ │ 飞书    │ │ 微信    │                           │
│  │ Adapter │ │ Adapter │ │ Adapter │                           │
│  └────┬────┘ └────┬────┘ └────┬────┘                           │
│       └─────────────┴───────────┘                               │
│                   │                                             │
│                   ↓                                             │
│              /v1/discuss                                        │
├─────────────────────────────────────────────────────────────────┤
│  Session Layer                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ SessionManager                                          │    │
│  │  ├─ DiscussionSession (领域模型)                       │    │
│  │  ├─ MemorySessionStore / RedisSessionStore             │    │
│  │  └─ run_discussion() → List[DiscussionEvent]                     │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  Harness Engineering                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ HarnessEngine                                           │    │
│  │  └─ HarnessGroupChat                                    │    │
│  │       ├─ run_round()                                    │    │
│  │       ├─ SelectorGroupChat (AutoGen)                    │    │
│  │       └─ Manual Fallback                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Agents                                                  │    │
│  │  ├─ DebaterAgent (Tool Calling 模式)                   │    │
│  │  │   ├─ run_with_tool_fallback                        │    │
│  │  │   └─ TOOL_CALL: search → 结果注入                   │    │
│  │  └─ ModeratorAgent (范围检查 + 摘要)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  DriftGuard (防漂移核心)                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │TopicAnchor  │ │TopicAnchor  │ │Context      │ │Moderator  │ │
│  │(议题锚定)   │ │(相关性提取) │ │Truncator    │ │Checkpoint │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Model Router                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ModelRouter                                             │    │
│  │  ├─ ProviderRegistry                                    │    │
│  │  ├─ OpenAICompatibleProvider                           │    │
│  │  │   ├─ KimiProvider (127.0.0.1:18790)                 │    │
│  │  │   └─ OpenAIProvider                                  │    │
│  │  └─ AnthropicProvider (直接继承 LLMProvider)            │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ AutoGen 兼容层                                          │    │
│  │  └─ ModelRouterChatCompletionClient                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 分层职责

### Layer 1: Frontend Layer (Adapters)

**职责**：协议转换，将外部请求转换为内部事件格式。

**关键类**：
- `BaseAdapter` - 抽象接口
- `WebAdapter` - HTTP/JSON 格式
- `FeishuAdapter` - 飞书卡片格式
- `WechatAdapter` - 微信消息格式

**设计原则**：
- Adapter 不处理业务逻辑
- Adapter 只负责格式转换
- 新增前端只需实现 `BaseAdapter`

### Layer 2: Session Layer

**职责**：会话生命周期管理，保持多轮对话状态。

**关键类**：
- `SessionManager` - 会话管理入口
- `DiscussionSession` - 会话领域模型
- `SessionStore` - 存储接口
- `MemorySessionStore` - 内存实现
- `RedisSessionStore` - Redis 实现

**数据流**：
```
用户请求 → SessionManager.run_discussion(session_id)
                ↓
         从 Store 恢复会话状态
                ↓
         调用 HarnessEngine
                ↓
         保存新状态到 Store
                ↓
         返回 DiscussionEvent
```

### Layer 3: Harness Engineering

**职责**：多代理协调，执行讨论流程。

**关键类**：
- `HarnessEngine` - 编排入口
- `HarnessGroupChat` - 讨论协调器
- `DebaterAgent` - 辩论者（Tool Calling 模式）
- `ModeratorAgent` - 主持人
- `PersonaGenerator` - 角色生成器（自动生成 4 个思考者角色）
- `ConsensusDetector` - 共识检测器（判断讨论是否达成一致）

**HarnessEngine 接口**：
```python
def __init__(self, router: ModelRouter)

def run(topic: Topic, personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 2, force_manual: bool = False) -> List[TurnResult]:
    """阻塞式运行，返回全部结果"""

def run_stream(topic: Topic, personas: Optional[List[DebaterAgent]] = None,
               max_rounds: int = 2, force_manual: bool = False,
               on_message: Optional[Callable[[Message], None]] = None):
    """流式运行，逐轮 yield + 逐消息回调"""

def run_until_consensus(topic: Topic, personas: Optional[List[DebaterAgent]] = None,
                        max_rounds: int = 10, force_manual: bool = False) -> List[TurnResult]:
    """阻塞式共识讨论"""

def run_until_consensus_stream(topic: Topic, personas: Optional[List[DebaterAgent]] = None,
                               max_rounds: int = 10, force_manual: bool = False,
                               on_message: Optional[Callable[[Message], None]] = None,
                               on_consensus: Optional[Callable[[dict], None]] = None):
    """流式共识讨论，支持共识达成回调"""
```

**讨论流程** (简化伪代码, 实际代码在 `group_chat.py`):
```python
def run_round(
    round_num: int,
    participants: List[HarnessAgentSpec],
    moderator_spec: Any,
    topic_text: str,
    prev_summary: Optional[str] = None,
    force_manual: bool = False,
):
    # 1. 为每个 Agent 构建 system_prompt (含议题锚定)
    for spec in participants:
        prompt = TopicAnchor.inject_prompt(spec.name, spec.personality, spec.style)
    
    # 2. 创建 ToolCalling Agent (带搜索能力)
    agents = [create_toolcalling_agent(...) for spec in participants]
    moderator = create_moderator_agent(...)
    
    # 3. 运行讨论 (AutoGen 或手动模式)
    if autogen_available and not force_manual:
        messages = _run_with_autogen(agents, moderator, topic_text)
    else:
        messages = _run_manual(agents, moderator, topic_text)
    
    # 4. 返回本轮消息
    return messages
```

> ⚠️ **注意**: 这是简化伪代码。实际流程更复杂, 包含 AutoGen 兼容层、回调机制等。详见 `group_chat.py` 源码。

### Layer 4: DriftGuard (核心创新)

**职责**：防止话题漂移，确保讨论质量。

#### 4.1 TopicAnchor (议题锚定)

**作用**：在每次发言前强制 Agent 复述议题核心。

**Prompt 注入**：
```
【议题锚定】
本轮话题：{topic}

你在发言前必须：
1. 复述议题核心（一句话）
2. 自评相关性（0-10）
3. 回答与议题的关系

禁止使用的跑题高频词：
- "此外"
- "值得一提的是"
- "从另一个角度"
```

#### 4.2 相关性评分 (TopicAnchor.extract_relevance)

**作用**：Agent 在发言中自评相关性，由 `TopicAnchor.extract_relevance()` 从响应中提取评分。

**算法**：
```python
def extract_relevance(text: str) -> Optional[float]:
    # 从 Agent 响应中提取自评的相关性分数
    # 匹配模式: "相关性: 8/10" 或 "自评: 7"
    ...
```

#### 4.3 ContextTruncator (上下文截断)

**作用**：Round 2 及以后只保留 Moderator 摘要，切断"递归稀释效应"。

**策略**：
```python
def truncate(history: List[Message]) -> List[Message]:
    # 保留：系统提示 + 用户原始问题 + Moderator 摘要
    # 丢弃：Round 1 的详细发言
    return [
        system_message,
        user_message,
        Message(role="moderator", content=moderator_summary)
    ]
```

#### 4.4 ModeratorCheckpoint (对齐检查点)

**作用**：每轮结束生成范围检查报告。

**输出**：主持人生成的摘要和漂移检测报告，包含：
- `scope_check` - 范围检查说明
- `core_summary` - 核心摘要
- `drift_detected` - 是否检测到漂移
- `suggestions` - 纠正建议

### Layer 5: Model Router

**职责**：统一模型接口，支持多模型切换。

**架构**：
```
ModelRouter
├── ProviderRegistry (注册表)
├── OpenAICompatibleProvider (OpenAI 兼容基类)
│   ├── KimiProvider (默认，127.0.0.1:18790)
│   └── OpenAIProvider
└── AnthropicProvider (直接继承 LLMProvider)
```

**ModelRouter 接口**：
```python
def chat(messages: List[Dict[str, str]], system: str = '', max_tokens: int = 500,
         temperature: float = 0.5, provider: Optional[LLMProvider] = None, **kwargs) -> str

def chat_with_tools(messages: List[Dict[str, str]], system: str = '',
                    tools: List[Dict[str, Any]] = None, max_tokens: int = 500,
                    temperature: float = 0.5, provider: Optional[LLMProvider] = None,
                    **kwargs) -> Dict[str, Any]
```

**AutoGen 兼容层**：
- `ModelRouterChatCompletionClient` 实现 `autogen_core.models.ChatCompletionClient`
- 支持 Tool Calling
- 支持流式输出

---

## 数据流

### 完整请求处理流程

```
┌─────────────┐
│ 用户请求     │
└──────┬──────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ WebAdapter   │────→│ 提取 message│
└──────┬──────┘     └─────────────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ SessionManager│───→│ 恢复会话状态│
└──────┬──────┘     └─────────────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ HarnessEngine│────→│ 创建 GroupChat│
└──────┬──────┘     └─────────────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ run_round()  │────→│ TopicAnchor.inject_prompt()│
└──────┬──────┘     └─────────────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ DebaterAgent │────→│ 检查 TOOL_CALL: │
│ 并行生成     │     │ 执行搜索     │
└──────┬──────┘     └─────────────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ ModeratorAgent│───→│ 检查漂移     │
│ 生成摘要     │     │ ContextTruncator│
└──────┬──────┘     └─────────────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ SessionStore │────→│ 保存状态     │
└──────┬──────┘     └─────────────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ WebAdapter   │────→│ 渲染响应     │
│ render_events│     │ 返回 JSON    │
└─────────────┘     └─────────────┘
```

---

## 扩展点

### 添加新的 Adapter

```python
# 示例：添加 Slack 适配器
from adapters.base import BaseAdapter

class SlackAdapter(BaseAdapter):
    def render_events(self, events: List[DiscussionEvent]) -> Dict:
        # 转换为 Slack Block Kit 格式
        ...
    
    def extract_user_message(self, payload: Dict) -> str:
        return payload["event"]["text"]
    
    def extract_session_id(self, payload: Dict) -> str:
        return payload["event"]["channel"]
```

### 添加新的 Provider

```python
# 示例：添加新的模型支持（OpenAI 兼容 API）
# 只需继承 OpenAICompatibleProvider，修改 base_url 和 model 即可
from model_router.providers.base import OpenAICompatibleProvider

class NewProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str = None, base_url: str = "https://api.example.com/v1",
                 model: str = "example-model"):
        self.api_key = api_key or os.getenv("EXAMPLE_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return f"example/{self.model}"

    def chat_completion(self, messages, system = '', max_tokens = 500, temperature = 0.5, **kwargs):
        msgs = self._build_messages(messages, system)
        payload = {"model": self.model, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        result = self._do_chat_request(f"{self.base_url}/chat/completions", headers=headers, payload=payload)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"] or "【无内容】"
        return "【无响应】"
```

### 添加新的搜索工具

```python
# 示例：添加 Google 搜索
class GoogleSearch:
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        # 调用 Google Custom Search API
        ...

# 在 DuckDuckGoSearch.providers 中添加
search_tool.providers.append(GoogleSearch())
```

---

## 与微信 RPA 架构对比

| 维度 | Multirole AI | 微信 RPA |
|------|--------------|----------|
| 核心问题 | 话题漂移 | 消息识别准确性 |
| 架构模式 | 分层 + 领域模型 | 分层 + 管道 |
| 关键创新 | DriftGuard | Vision OCR + 分层去重 |
| 状态管理 | Session + Store | Session + Layout |
| 扩展方式 | Adapter / Provider | Pipeline Stage |

---

## 文档索引

- [MODULE_INDEX.md](MODULE_INDEX.md) - 文件职责索引
- [API_SURFACE.md](API_SURFACE.md) - 接口定义
- [LOGGING_DESIGN.md](../03-guides/LOGGING_DESIGN.md) - 日志设计
