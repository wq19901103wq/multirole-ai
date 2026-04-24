# API 接口定义

> 接口契约文档。任何接口变更必须同步更新本文档。

---

## HTTP API

### 健康检查

```http
GET /health
```

**响应**：
```json
{
  "status": "ok",
  "autogen_installed": true
}
```

---

### 统一讨论接口

```http
POST /v1/discuss
Content-Type: application/json
```

**请求体**：
```json
{
  "message": "string, required - 用户输入的话题",
  "session_id": "string, optional - 会话ID，默认 'default'",
  "max_rounds": "integer, optional - 讨论轮数，默认 2",
  "force_manual": "boolean, optional - 强制手动模式，默认 false",
  "agents": [
    {
      "name": "string - Agent 显示名称",
      "persona": "string - Agent 角色描述"
    }
  ],
  "allow_search": "boolean, optional - 允许搜索，默认 true"
}
```

**示例请求**：
```json
{
  "message": "人工智能会取代程序员吗？",
  "session_id": "demo-001",
  "max_rounds": 2,
  "agents": [
    {"name": "思考者一", "persona": "乐观主义者"},
    {"name": "思考者二", "persona": "怀疑论者"}
  ]
}
```

**响应**：
```json
{
  "events": [
    {
      "event_type": "message | moderation",
      "role_id": "string - Agent ID",
      "role_name": "string - 显示名称",
      "content": "string - 清洗后的发言内容",
      "raw_content": "string - 原始发言内容",
      "round": "integer - 轮次",
      "emoji": "string - 表情符号",
      "color": "string - 颜色代码",
      "relevance": "float | null - 相关性评分",
      "metadata": "Dict - 附加元数据"
    }
  ],
  "session_id": "string"
}
```

**错误响应**：
```json
{
  "error": "message is required"
}
```

状态码：400 (Bad Request), 500 (Internal Server Error)

---

### 共识讨论接口

```http
POST /v1/discuss/consensus
Content-Type: application/json
```

**说明**：持续多轮讨论直到达成一致或达到上限。

**请求体**：
```json
{
  "message": "string, required",
  "session_id": "string, optional",
  "max_rounds": "integer, optional, default 10",
  "force_manual": "boolean, optional"
}
```

**响应**：与普通讨论接口相同，但内部会检测共识。

---

### 飞书专用接口

```http
POST /v1/feishu/discuss
Content-Type: application/json
```

**请求体**：飞书事件回调 JSON

**响应**：飞书交互卡片格式

---

### Swagger UI

```http
GET /swagger-ui
GET /
```

启动服务后访问 Swagger 文档界面。

---

## WebSocket API

### 流式讨论

```
WS /v1/discuss/stream
```

**连接后发送**：
```json
{
  "message": "话题内容",
  "session_id": "可选",
  "max_rounds": 2
}
```

**消息类型**：

| 类型 | 格式 | 说明 |
|------|------|------|
| status | `{"type": "status", "text": "讨论开始"}` | 讨论开始 |
| event | `{"type": "event", "payload": {...}}` | 单条发言 |
| turn_end | `{"type": "turn_end", "round": 1}` | 本轮结束 |
| done | `{"type": "done", "session_id": "..."}` | 全部完成 |
| error | `{"type": "error", "message": "..."}` | 错误信息 |

---

### 共识流式讨论

```
WS /v1/discuss/consensus/stream
```

**说明**：持续多轮直到达成一致，逐条推送。

---

## 内部接口

### BaseAdapter

```python
class BaseAdapter(ABC):
    def render_events(self, events: List[DiscussionEvent]) -> Any:
        """将内部 DiscussionEvent 列表渲染为前端格式"""
        ...
    
    def extract_user_message(self, payload: Any) -> str:
        """从请求中提取用户消息"""
        ...
    
    def extract_session_id(self, payload: Any) -> str:
        """从请求中提取会话ID"""
        ...
```

### SessionManager

```python
class SessionManager:
    def __init__(self, engine: HarnessEngine, store = None)
    
    def create_session(self, session_id: str, user_message: str) -> DiscussionSession
    
    def run_discussion(
        self,
        session_id: str,
        user_message: str,
        max_rounds: int = 2,
        force_manual: bool = False,
    ) -> List[DiscussionEvent]
        """运行标准讨论"""
        ...
    
    def run_discussion_consensus(
        self,
        session_id: str,
        user_message: str,
        max_rounds: int = 10,
        force_manual: bool = False,
    ) -> List[DiscussionEvent]
        """运行共识讨论（持续多轮直到达成一致）"""
        ...
```

### HarnessEngine

```python
class HarnessEngine:
    def __init__(self, router: ModelRouter)
    
    def run(
        self,
        topic: Topic,
        personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 2,
        force_manual: bool = False,
    ) -> List[TurnResult]
        """运行完整讨论（阻塞式）"""
        ...
    
    def run_stream(
        self,
        topic: Topic,
        personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 2,
        force_manual: bool = False,
        on_message: Optional[Callable[[Message], None]] = None,
    )
        """运行完整讨论（流式，逐轮 yield + 逐消息回调）"""
        ...
    
    def run_until_consensus(
        self,
        topic: Topic,
        personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 10,
        force_manual: bool = False,
    ) -> List[TurnResult]
        """持续讨论直到达成共识或达到上限（阻塞式）"""
        ...
    
    def run_until_consensus_stream(
        self,
        topic: Topic,
        personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 10,
        force_manual: bool = False,
        on_message: Optional[Callable[[Message], None]] = None,
        on_consensus: Optional[Callable[[dict], None]] = None,
    )
        """共识讨论（流式，支持逐消息和共识达成回调）"""
        ...
```

### ModelRouter

```python
class ModelRouter:
    def __init__(self, default_provider: Optional[LLMProvider] = None)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = '',
        max_tokens: int = 500,
        temperature: float = 0.5,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str
        """统一对话接口"""
        ...
    
    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        system: str = '',
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 500,
        temperature: float = 0.5,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]
        """带工具调用的对话接口"""
        ...
```

### LLMProvider

```python
class LLMProvider(ABC):
    @abstractmethod
    def name(self) -> str
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = '',
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> str
        """模型调用接口"""
        ...
```

### OpenAICompatibleProvider

```python
class OpenAICompatibleProvider(LLMProvider):
    def _build_messages(self, messages: List[Dict[str, str]], system: str = '') -> List[Dict[str, str]]
        """组装 messages，插入 system prompt"""
        ...
    
    def _do_chat_request(self, url: str, headers: Dict, payload: Dict) -> Dict
        """发送 HTTP 请求并解析响应"""
        ...
```

### KimiProvider

```python
class KimiProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None)
    
    def name(self) -> str
    
    def chat_completion(self, messages, system = '', max_tokens = 500, temperature = 0.5, **kwargs) -> str
    
    def chat_completion_with_tools(
        self,
        messages: List[Dict[str, str]],
        system: str = '',
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 500,
        temperature: float = 0.5,
        **kwargs
    ) -> Dict[str, Any]
```

### OpenAIProvider

```python
class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str = None, base_url: str = 'https://api.openai.com/v1', model: str = 'gpt-4o')
    
    def name(self) -> str
    
    def chat_completion(self, messages, system = '', max_tokens = 500, temperature = 0.5, **kwargs) -> str
```

### ProviderRegistry

```python
class ProviderRegistry:
    @classmethod
    def register(cls, alias: str, provider_cls: Type[LLMProvider])
    
    @classmethod
    def get(cls, alias: str) -> Type[LLMProvider]
    
    @classmethod
    def create(cls, alias: str, **kwargs) -> LLMProvider
```

### ModelRouterChatCompletionClient

```python
class ModelRouterChatCompletionClient(ChatCompletionClient):
    def __init__(self, router: ModelRouter, model_name: str = 'kimi/kimi-k2.5')
    
    def model_info(self) -> ModelInfo
    
    def capabilities(self) -> ModelCapabilities
    
    def count_tokens(self, messages: Sequence[LLMMessage]) -> int
    
    def remaining_tokens(self, messages: Sequence[LLMMessage]) -> int
    
    def total_usage(self) -> RequestUsage
    
    def actual_usage(self) -> RequestUsage
    
    async def create(self, messages, tools, extra_create_args, cancellation_token)
    
    async def create_stream(self, messages, tools, extra_create_args, cancellation_token)
```

### TopicAnchor

```python
class TopicAnchor:
    def __init__(self, topic: Topic)
    
    def inject_prompt(self, role_name: str, role_personality: str, role_style: str) -> str
        """为指定角色注入议题锚定 prompt"""
        ...
    
    def extract_relevance(text: str) -> Optional[float]
        """从文本中提取自评相关性分数"""
        ...
    
    def clean_response(text: str) -> str
        """清洗响应，去除议题锚定标记"""
        ...
```

### ContextTruncator

```python
class ContextTruncator:
    def __init__(self, max_history_turns: int = 2)
    
    def truncate(self, history: List[Message]) -> List[Message]
        """截断历史上下文，保留最近 N 轮"""
        ...
```

### ModeratorCheckpoint

```python
class ModeratorCheckpoint:
    def __init__(self, router: ModelRouter)
    
    def check(self, topic: Topic, round_messages: List[Message]) -> dict
        """检查本轮是否漂移，返回检测报告"""
        ...
```

### BaseSearchProvider

```python
class BaseSearchProvider(ABC):
    def search(self, query: str, max_results: int = 5) -> List[Dict]
        """执行搜索"""
        ...
    
    def format_results(self, results: List[Dict]) -> str
        """格式化搜索结果为文本"""
        ...
```

### DuckDuckGoSearch

```python
class DuckDuckGoSearch(BaseSearchProvider):
    def __init__(self)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]
        """执行 DuckDuckGo 搜索"""
        ...
    
    def format_results(self, results: List[Dict]) -> str
        """格式化搜索结果为文本"""
        ...
```

### BingSearchFree

```python
class BingSearchFree(BaseSearchProvider):
    def __init__(self, api_key: Optional[str] = None)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]
        """执行 Bing 搜索"""
        ...
```

### FreeSearchTool

```python
class FreeSearchTool(BaseSearchProvider):
    def __init__(self)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]
        """自动尝试多个免费搜索源"""
        ...
    
    def format_results(self, results: List[Dict]) -> str
        """格式化搜索结果为文本"""
        ...
```

### KimiFunctionSearch

```python
class KimiFunctionSearch:
    def __init__(self, router: ModelRouter)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]
        """使用 Kimi API Function Calling 实现搜索"""
        ...
```

### SearchToolWrapper

```python
class SearchToolWrapper:
    def __init__(self, search_impl)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]
        """给不支持 function calling 的模型用的简化版搜索"""
        ...
    
    def format_results(self, results: List[Dict]) -> str
        """格式化搜索结果为文本"""
        ...
```

### VisionAnalyzer

```python
class VisionAnalyzer:
    def __init__(self, router: ModelRouter, model: str = "kimi-k2.5")
    
    def analyze(self, image_path: str, prompt: str = "") -> str
        """分析本地图片"""
        ...
```

### ReActEngine / ToolCallingEngine

```python
def run_with_tool_fallback(
    router,
    system_prompt: str,
    conversation: List[Dict[str, str]],
    max_iterations: int = 2,
) -> str:
    """统一的 ReAct 调用 + 降级逻辑"""
    ...

class ToolCallingEngine:
    def __init__(self, router, search_tool: Optional[SearchTool] = None)
    
    def run(self, system_prompt: str, conversation: List[Dict[str, str]], max_iterations: int = 3) -> str
        """运行工具调用引擎，返回最终回答"""
        ...
```

---

## 数据结构

### DiscussionEvent

```python
@dataclass
class DiscussionEvent:
    """前端可订阅的事件"""
    event_type: str      # "message", "moderation", "summary", "drift_alert"
    payload: Message     # 消息内容
    round_num: int = 0   # 轮次
```

### TurnResult

```python
@dataclass
class TurnResult:
    """一轮 harness 引擎的输出"""
    messages: List[Message] = field(default_factory=list)
    summary: str = ""                       # moderator 生成的摘要
    drift_detected: bool = False            # 本轮是否检测到漂移
    drift_report: str = ""                  # 漂移报告
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### HarnessAgentSpec

```python
@dataclass
class HarnessAgentSpec:
    """Harness 引擎中的 Agent 规格"""
    agent_id: str
    name: str
    system_prompt: str
    description: str = ""
    emoji: str = "🤖"
    color: str = "#667eea"
    is_moderator: bool = False
```

### Message

```python
@dataclass
class Message:
    """消息模型"""
    role: Role           # Role 枚举: system, user, assistant
    content: str
    sender_id: Optional[str] = None      # 发送者 ID
    sender_name: Optional[str] = None    # 发送者名称
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def relevance_score(self) -> Optional[float]
    
    @property
    def is_moderation(self) -> bool
```

### Topic

```python
@dataclass
class Topic:
    """话题模型"""
    text: str
    
    def anchor_prompt(self) -> str
        """生成议题锚定 prompt"""
        ...
```

### DiscussionSession

```python
@dataclass
class DiscussionSession:
    """会话领域模型"""
    session_id: str
    topic: Topic
    turn_results: List[TurnResult] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def latest_summary(self) -> str
        """获取最新摘要"""
        ...
```

### MemorySessionStore / RedisSessionStore

```python
class MemorySessionStore:
    def get(self, session_id: str) -> Optional[DiscussionSession]
    def save(self, session: DiscussionSession)
    def delete(self, session_id: str)

class RedisSessionStore:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0,
                 password: Optional[str] = None, key_prefix: str = 'multirole:session:',
                 ttl_seconds: int = 3600 * 24)
    def get(self, session_id: str) -> Optional[DiscussionSession]
    def save(self, session: DiscussionSession)
    def delete(self, session_id: str)
```

---

## 变更记录

| 日期 | 变更 | 影响 |
|------|------|------|
| 2024-04-22 | 重构 Provider 层级 | 新增 OpenAICompatibleProvider，KimiProvider/OpenAIProvider 改继承它 |
| 2024-04-22 | 删除 ReActEngine | 改为 `run_with_tool_fallback` 统一降级逻辑 |
| 2024-04-22 | 抽象搜索基类 | 新增 BaseSearchProvider，统一搜索工具接口 |
| 2024-04-20 | 添加 ReAct 模式 | Agent 提示词新增 SEARCH: 标记 |
| 2024-04-20 | 添加免费搜索 | 新增 `allow_search` 参数 |
| 2024-04-15 | 添加 WebSocket 流式 | 新增 `/v1/discuss/stream` |
| 2024-04-10 | 添加飞书接口 | 新增 `/v1/feishu/discuss` |
| 2024-04-01 | 初始版本 | 基础接口 |

---

## 可复制粘贴测试

以下代码块可以直接复制到 Python 中运行：

```python
import requests

# 测试健康检查
resp = requests.get("http://127.0.0.1:8890/health")
print(resp.json())

# 测试讨论接口
resp = requests.post(
    "http://127.0.0.1:8890/v1/discuss",
    json={"message": "测试", "max_rounds": 1}
)
print(resp.json())
```
