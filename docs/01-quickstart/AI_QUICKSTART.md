# AI 开发者快速上手

> 第一次接触 Multirole AI 项目？从这里开始。

---

## 什么是 Multirole AI？

Multirole AI 是一个**多代理 AI 讨论系统**，核心解决**多 bot 讨论离题（Topic Drift）**问题。

简单说：让多个 AI 角色围绕一个话题进行真正有意义的讨论，而不是各自独白或跑题。

---

## 5 分钟理解核心概念

### 1. 分层架构

```
Frontend (飞书/微信/Web)
         ↓
Session Layer (会话管理)
         ↓
Harness Engine (协调引擎)
         ↓
DriftGuard (防漂移)
         ↓
Model Router (模型路由)
```

### 2. DriftGuard - 防漂移机制

多代理讨论的最大问题是**话题漂移**。我们的解决方案：

| 组件 | 作用 |
|------|------|
| TopicAnchor | 强制 Agent 复述议题核心 |
| TopicAnchor.extract_relevance | 提取 Agent 自评相关性 (0-10) |
| ContextTruncator | 截断历史，防止递归稀释 |
| ModeratorCheckpoint | 每轮结束检查并纠正 |

### 3. 圆桌讨论模式

**不是**让四个职业角色各说一段（工程师角度、经济师角度...）

**而是**四个平等思考者自由对话：
- 思考者一提出观点
- 思考者二指出隐含假设
- 思考者三补充反例
- 思考者四尝试综合

---

## 10 分钟跑起来

### 1. 启动依赖

```bash
# 启动 Kimi Code 代理（如果还没有运行）
~/.openclaw/proxy/kimicode_proxy.py
```

### 2. 启动服务

```bash
cd ~/multirole-ai

# 方式一：直接启动（使用 mock 模式）
export MULTIROLE_DEMO_MODE=1
python api/server.py

# 方式二：使用真实 LLM（需要配置 API Key）
# export KIMI_API_KEY="your-key"
python api/server.py
```

### 3. 测试 API

```bash
# 健康检查
curl http://127.0.0.1:8890/health

# 发起讨论
curl -X POST http://127.0.0.1:8890/v1/discuss \
  -H "Content-Type: application/json" \
  -d '{
    "message": "人工智能会取代程序员吗？",
    "max_rounds": 2
  }'
```

---

## 20 分钟理解代码结构

### 关键文件速查

| 你想做什么 | 看哪个文件 |
|-----------|-----------|
| 了解整体架构 | `docs/02-architecture/ARCHITECTURE.md` |
| 找不到某个功能 | `docs/02-architecture/MODULE_INDEX.md` |
| 修改 Agent 行为 | `harness_engine/autogen_agents.py` |
| 修改防漂移逻辑 | `drift_guard/*.py` |
| 添加新模型支持 | `model_router/providers/*.py` |
| 添加新前端适配 | `adapters/*.py` |
| 查看日志设计 | `docs/03-guides/LOGGING_DESIGN.md` |

### 核心流程

```
用户请求 → WebAdapter → SessionManager → HarnessEngine
                                              ↓
                              PersonaGenerator.generate()
                                              ↓
                              HarnessGroupChat.run_round()
                                              ↓
                    ┌──────────────────────────────────────┐
                    ↓                                      ↓
            TopicAnchor.inject_prompt()       TopicAnchor.extract_relevance()
                    ↓                                      ↓
            run_manual_round()              ModeratorCheckpoint.check()
         /  run_autogen_round()                            ↓
                    ↓                              返回 moderator 摘要
            逐 Agent 调用 router.chat()
                    ↓
            返回 TurnResult
```

---

## 30 分钟开发第一个功能

### 示例：修改 Agent 的 ReAct 提示

打开 `harness_engine/autogen_agents.py`：

```python
REACT_PROMPT_TEMPLATE = """
【ReAct 模式 - 思考与行动】

你的工作流程：
1. Thought（思考）：分析当前问题
2. Action（行动）：使用搜索工具获取信息
3. Observation（观察）：分析结果
4. Final Answer（最终回答）：给出完整回答

使用格式：
Thought: 我需要...
SEARCH: <查询>
Observation: [结果]
Final Answer: ...
"""
```

修改后重启服务即可生效。

### 示例：添加新的搜索工具

打开 `tools/search_free.py`，添加新的搜索实现：

```python
class BingSearchFree:
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        # 实现 Bing 搜索
        ...
```

然后在 `DuckDuckGoSearch` 的 `providers` 中添加备用。

---

## 常见开发任务

### 运行测试

```bash
# 全部测试
pytest -q

# 特定模块
pytest tests/test_drift_guard.py -v

# 带 Redis 的集成测试
pytest tests/test_redis_integration.py -v
```

### 查看日志

```bash
# 实时查看
tail -f /tmp/server.log

# 只看错误
grep ERROR /tmp/server.log
```

### 调试模式

```python
# 在代码中启用详细日志
import logging
logging.getLogger("harness_engine").setLevel(logging.DEBUG)
```

---

## 下一步

- 深入了解架构：[ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
- 查看模块索引：[MODULE_INDEX.md](../02-architecture/MODULE_INDEX.md)
- 了解踩坑记录：[LESSONS_LEARNED.md](../04-troubleshooting/LESSONS_LEARNED.md)
- 阅读代码规范：[STANDARDS_DOCUMENTATION.md](../05-meta/STANDARDS_DOCUMENTATION.md)
