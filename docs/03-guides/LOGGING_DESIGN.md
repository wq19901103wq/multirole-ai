# 日志设计

> 运行时日志与可观测性

---

## 日志层级

```
DEBUG   - 详细调试信息（开发时使用）
INFO    - 关键流程节点（生产默认级别）
WARNING - 非致命警告
ERROR   - 错误（需要关注）
CRITICAL - 致命错误（需要立即处理）
```

---

## 日志格式

```
2026-04-20 23:44:37,220 - api.server - INFO - [DISCUSS] 收到请求: session=default, max_rounds=2
```

格式：`时间 - 模块名 - 级别 - 消息`

---

## 各模块日志规范

### API 层 (`api/server.py`)

| 事件 | 级别 | 消息格式 |
|------|------|----------|
| 收到请求 | INFO | `[DISCUSS] 收到请求: session={id}, max_rounds={n}` |
| 参数错误 | WARNING | `[DISCUSS] 错误: 缺少 message 参数` |
| 讨论完成 | INFO | `[DISCUSS] 讨论完成，生成 {n} 个事件，耗时 {t}s` |
| 讨论失败 | ERROR | `[DISCUSS] 讨论失败: {error}, 耗时 {t}s` |

### Harness Engine (`harness_engine/`)

| 事件 | 级别 | 消息格式 |
|------|------|----------|
| 轮次开始 | INFO | `[Round {n}] 开始讨论，话题: {topic}` |
| Agent 开始 | INFO | `[Round {n}] Agent {i}/{total} ({name}) 开始生成...` |
| Agent 完成 | INFO | `[Round {n}] Agent {name} 生成完成，耗时 {t}s，内容长度: {len}` |
| 检测到搜索 | DEBUG | `[Search] 检测到 SEARCH: {query}` |
| 搜索完成 | DEBUG | `[Search] 找到 {n} 条结果` |

### Model Router (`model_router/`)

| 事件 | 级别 | 消息格式 |
|------|------|----------|
| 发送请求 | INFO | `[KimiProvider] 发送请求到 {url}` |
| 请求成功 | INFO | `[KimiProvider] 成功获取响应，长度: {len}` |
| 请求失败 | ERROR | `[KimiProvider] 请求失败: {error}` |
| 重试 | WARNING | `[KimiProvider] 第 {n} 次重试...` |

### DriftGuard (`drift_guard/`)

| 事件 | 级别 | 消息格式 |
|------|------|----------|
| 注入锚点 | DEBUG | `[TopicAnchor] 注入议题锚定到 {agent}` |
| 相关性评分 | DEBUG | `[TopicAnchor] {agent} 自评: {score}/10` |
| 截断上下文 | DEBUG | `[ContextTruncator] Round {n} 截断上下文` |
| 检测到漂移 | WARNING | `[ModeratorCheckpoint] 检测到话题漂移` |

---

## 日志文件位置

| 环境 | 位置 |
|------|------|
| 开发 | `/tmp/server.log` |
| Docker | 容器内 `/var/log/multirole-ai/` |
| 生产 | 配置 `LOG_FILE` 环境变量 |

---

## 查看日志命令

```bash
# 实时查看
tail -f /tmp/server.log

# 查看最近 100 行
tail -100 /tmp/server.log

# 只查看错误
grep ERROR /tmp/server.log

# 查看特定模块
grep "harness_engine" /tmp/server.log

# 查看特定会话
grep "session=demo-001" /tmp/server.log

# 按时间范围查看
awk '/2026-04-20 23:4[0-9]/' /tmp/server.log
```

---

## 结构化日志（JSON）

生产环境可以启用结构化日志：

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "session_id": getattr(record, "session_id", None),
        })
```

启用方式（需要手动在代码中配置）：
```python
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        import json
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
```

---

## 性能指标日志

关键性能指标自动记录：

```
[Perf] 讨论完成: session={id}, rounds={n}, total_time={t}s, tokens={n}
[Perf] Agent 生成: agent={name}, time={t}s, input_tokens={n}, output_tokens={n}
[Perf] 搜索: query_len={n}, results={n}, time={t}s
```

---

## 调试模式

开发时启用详细日志：

```python
# 在代码中
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

---

## 日志轮转

生产环境建议配置日志轮转：

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "/var/log/multirole-ai/server.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

或使用 `logrotate`：

```bash
# /etc/logrotate.d/multirole-ai
/var/log/multirole-ai/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 user user
}
```
