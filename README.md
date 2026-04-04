# Multirole AI - Harness Engine

一个分层架构的多代理 AI 讨论系统，核心解决**多 bot 讨论离题（Topic Drift）**问题。

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend Layer (Adapters)                                      │
│  飞书 / 微信 / Web / 小程序                                       │
├─────────────────────────────────────────────────────────────────┤
│  Session Layer                                                  │
│  SessionManager → MemorySessionStore / RedisSessionStore        │
│                 → DiscussionSession                             │
├─────────────────────────────────────────────────────────────────┤
│  Harness Engineering                                            │
│  HarnessEngine → HarnessGroupChat → (AutoGen or Manual Fallback)│
│                → DebaterAgent / ModeratorAgent                  │
├─────────────────────────────────────────────────────────────────┤
│  DriftGuard                                                     │
│  TopicAnchor + RelevanceScorer + ContextTruncator               │
│  + ModeratorCheckpoint                                          │
├─────────────────────────────────────────────────────────────────┤
│  Model Router                                                   │
│  ModelRouter → KimiProvider / OpenAIProvider / AnthropicProvider│
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
multirole-ai/
├── adapters/                 # 前端适配层
│   ├── base.py               # BaseAdapter 接口
│   ├── web.py                # WebAdapter
│   ├── feishu.py             # FeishuAdapter
│   └── wechat.py             # WechatAdapter
├── session/                  # 会话层
│   ├── manager.py            # SessionManager（编排入口）
│   ├── store.py              # MemorySessionStore
│   ├── store_redis.py        # RedisSessionStore
│   └── models.py             # DiscussionSession 领域模型
├── harness_engine/           # 核心协调引擎（含 AutoGen 兼容层）
│   ├── engine.py             # HarnessEngine
│   ├── group_chat.py         # HarnessGroupChat
│   ├── autogen_client.py     # ModelRouterChatCompletionClient
│   └── agents/
│       ├── base.py           # BaseAgent
│       ├── debater.py        # DebaterAgent
│       └── moderator.py      # ModeratorAgent
├── drift_guard/              # 防漂移核心
│   ├── anchor.py             # TopicAnchor
│   ├── scorer.py             # RelevanceScorer
│   ├── truncator.py          # ContextTruncator
│   └── checkpoint.py         # ModeratorCheckpoint
├── model_router/             # 模型路由层
│   ├── router.py             # ModelRouter
│   ├── registry.py           # ProviderRegistry
│   └── providers/
│       ├── base.py           # LLMProvider 抽象
│       ├── kimi.py           # KimiProvider
│       ├── openai.py         # OpenAIProvider
│       └── anthropic.py      # AnthropicProvider
├── core/                     # 共享领域模型
│   ├── message.py
│   ├── topic.py
│   └── event.py
├── api/
│   └── server.py             # Flask HTTP 统一入口
├── examples/
│   └── run_debate.py         # 命令行示例
├── tests/                    # 测试套件（25 项全通过）
│   ├── conftest.py
│   ├── test_adapters.py
│   ├── test_api.py
│   ├── test_feishu_api.py
│   ├── test_drift_guard.py
│   ├── test_harness_engine.py
│   ├── test_model_router.py
│   ├── test_session.py
│   └── test_redis_integration.py
└── requirements.txt
```

## 当前完成进度

| 模块 | 状态 | 说明 |
|------|------|------|
| **Adapters** | ✅ 完成 | Web、飞书、企业微信适配器 + 单测 |
| **Session Layer** | ✅ 完成 | SessionManager、Memory/Redis Store、DiscussionSession + 单测 |
| **Harness Engine** | ✅ 完成 | Engine、GroupChat、Debater/Moderator Agent、AutoGen 兼容层 + 单测 |
| **DriftGuard** | ✅ 完成 | TopicAnchor、RelevanceScorer、ContextTruncator、ModeratorCheckpoint + 单测 |
| **Model Router** | ✅ 完成 | Router、Registry、Kimi/OpenAI/Anthropic Provider + 单测 |
| **API** | ✅ 完成 | Flask Server (`/health`, `/v1/discuss`) + 单测 |
| **AutoGen 集成** | ✅ 完成 | `ModelRouterChatCompletionClient` 完整实现 `autogen_core.models.ChatCompletionClient` 接口 |
| **Redis 集成** | ✅ 完成 | `RedisSessionStore` + 真实 Redis 集成测试（5 项） |
| **OpenClaw 技能** | ✅ 完成 | 已注册为 OpenClaw 技能 `multirole-ai`，可直接调用 |
| **飞书 API 端点** | ✅ 完成 | `/v1/feishu/discuss` + 独立 `feishu_server.py` 回调服务 |
| **测试覆盖** | ✅ 25/25 通过 | `pytest -q` 全绿 |

## 核心创新：DriftGuard 防漂移机制

### 1. TopicAnchor（议题锚定）
- 每个 agent 发言前必须先复述核心议题
- 强制自评相关性分数（0-10）
- 禁止跑题高频词（"此外"、"值得一提的是"...）

### 2. ContextTruncator（上下文截断）
- Round 2 及以后只能看到 moderator 摘要，而非完整历史
- 切断"递归稀释效应"

### 3. ModeratorCheckpoint（对齐检查点）
- 每轮结束后 moderator 自动介入
- 生成范围检查报告 + 核心摘要
- 如果检测到漂移，标记 `drift_detected=True`

### 4. RelevanceScorer（二次评分）
- 当 agent 自评不可靠时，由独立 LLM 判定相关性

## 快速开始

### 安装依赖

```bash
cd multirole-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 配置 API Key

```bash
export KIMI_API_KEY="your-api-key"
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 运行 Web 服务

```bash
python api/server.py
```

浏览器打开 `http://localhost:8890`

### 运行命令行示例

```bash
python examples/run_debate.py
```

### 运行测试

```bash
pytest -q
```

## 使用 Redis 持久化

默认使用内存存储会话。切换到 Redis：

```bash
export MULTIROLE_REDIS_URL="redis://localhost:6379/0"
python api/server.py
```

集成测试已覆盖真实 Redis（使用 db=15 避免污染数据）：

```bash
pytest tests/test_redis_integration.py -v
```

## 作为 OpenClaw 技能使用

multirole-ai 已注册为 OpenClaw 技能，支持通过企业微信/飞书等渠道直接触发多代理讨论。

### 状态检查

```bash
openclaw skills info multirole-ai
```

### 直接调用

```bash
python3 ~/.local/node/lib/node_modules/openclaw/skills/multirole-ai/scripts/discuss.py "四天工作制是否合理？"
```

### OpenClaw Agent 中调用

当用户说"让几个 AI 讨论一下 XX"时，OpenClaw 会自动触发该 skill，调用本地 API 并返回讨论结果。

### 企业微信直接接入

`~/.openclaw/workspace/openclaw_wechat_server.py` 已集成 Multirole AI。当企业微信用户发送包含以下关键词的消息时：
- `/discuss <话题>`
- "讨论一下 <话题>"
- "让几个 AI 讨论一下 <话题>"
- "多角度分析 <话题>"

企业微信会立即回复提示，并在后台异步调用 multirole-ai 的讨论引擎，完成后主动推送讨论结果给用户。

### 飞书直接接入

`~/.openclaw/workspace/feishu_server.py` 已集成 Multirole AI。当飞书用户（单聊或群聊）发送包含以下关键词的消息时：
- `/discuss <话题>`
- "讨论一下 <话题>"
- "多角度分析 <话题>"
- "brainstorm <话题>"

飞书机器人会立即返回提示，并在后台异步调用 multirole-ai，完成后通过飞书 API 推送讨论结果。

#### 启动飞书服务

```bash
python ~/.openclaw/workspace/feishu_server.py
```

默认监听 `http://0.0.0.0:8090/feishu/webhook`，需在飞书开发者平台配置事件订阅地址。

#### 飞书 API 端点

multirole-ai 本身也暴露了原生飞书接口：

```bash
POST /v1/feishu/discuss
```

接收飞书事件回调 JSON，返回飞书交互卡片格式，便于直接在机器人中调用。

## Docker 部署

项目已提供 `Dockerfile` 和 `docker-compose.yml`，支持一键启动（含 Redis）。

```bash
# 构建并启动（包含 Redis）
docker-compose up --build

# 仅构建镜像
docker build -t multirole-ai .

# 运行容器（连接外部 Redis）
docker run -p 8890:8890 -e MULTIROLE_REDIS_URL=redis://host.docker.internal:6379/0 multirole-ai
```

服务将在 `http://localhost:8890` 可用。

## 性能基准测试

```bash
python benchmarks/benchmark_engine.py
```

该脚本会测试 `HarnessEngine.run()` 在不同 `max_rounds` 和 `force_manual` 配置下的平均延迟，结果输出到 `benchmarks/results.json`。

## 使用 AutoGen

Harness Engine 内部做了 AutoGen 兼容层：
- 如果系统安装了 `autogen-agentchat>=0.7.5`，会自动使用 AutoGen 的 `SelectorGroupChat` 做调度
- 如果未安装，会优雅 fallback 到手动循环，**不影响运行**
- 测试时可通过 `force_manual=True` 强制走手动路径

安装 AutoGen：

```bash
pip install autogen-agentchat==0.7.5 autogen-core==0.7.5 autogen-ext==0.7.5
```

## 扩展新前端

实现 `BaseAdapter` 即可：

```python
from adapters.base import BaseAdapter

class MyAdapter(BaseAdapter):
    def render_events(self, events): ...
    def extract_user_message(self, payload): ...
    def extract_session_id(self, payload): ...
```

然后在 `api/server.py` 中新增路由：

```python
@app.route('/v1/my/discuss', methods=['POST'])
def my_discuss():
    ...
```

## 扩展新模型

```python
from model_router.providers.base import LLMProvider
from model_router.registry import ProviderRegistry

class MyProvider(LLMProvider):
    ...

ProviderRegistry.register("myprovider", MyProvider)
```

## 设计原则

1. **关注点分离**：DriftGuard 不依赖 Harness，Harness 不依赖 Adapter
2. **可替换性**：任何一层都可以单独替换（比如把 MemoryStore 换成 Redis）
3. **可观测性**：每一轮都产出结构化的 `TurnResult`，包含漂移检测报告
