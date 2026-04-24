# 踩坑记录

> 避免重复踩坑。记录开发过程中遇到的坑和解决方案。

---

## AutoGen 集成

### 坑 1: ToolUseAgent 版本不匹配

**现象**：
```
ImportError: cannot import name 'ToolUseAgent' from 'autogen_agentchat.agents'
```

**原因**：AutoGen v0.7+ 的 API 变化，ToolUseAgent 不存在或接口不同。

**解决**：使用 Prompt-based 工具调用
```python
# 不使用 ToolUseAgent
# 改用 prompt engineering 让 LLM 输出 SEARCH: 标记

REACT_PROMPT = """
搜索使用格式：
SEARCH: <你的搜索查询>

系统会自动执行搜索并将结果返回给你。
"""
```

---

### 坑 2: AutoGen 类型不匹配

**现象**：
```
TypeError: 'SystemMessage' object is not iterable
```

**原因**：AutoGen 的 Message 类型与自定义 Message 不兼容。

**解决**：在 autogen_client.py 中手动转换消息格式

---

## 搜索集成

### 坑 3: DuckDuckGo 包名变更

**现象**：
```
ModuleNotFoundError: No module named 'duckduckgo_search'
```

**原因**：包从 duckduckgo-search 改名为 ddgs。

**解决**：
```bash
pip uninstall duckduckgo-search
pip install ddgs
```

---

### 坑 4: DuckDuckGo 请求超时

**现象**：搜索偶尔返回空结果或超时。

**原因**：DuckDuckGo 免费服务不稳定，某些地区/IP 限制。

**解决**：添加重试机制和备用引擎

---

### 坑 5: ReAct 引擎解析失败

**现象**：Agent 输出了 SEARCH: 但没有触发搜索。

**原因**：解析正则表达式不够健壮，匹配失败。

**解决**：使用更灵活的正则

---

## 模型路由

### 坑 6: Kimi Code API 403

**现象**：
```
403 Forbidden: "只支持 Coding Agents"
```

**原因**：Kimi Code API 需要特定的 User-Agent。

**解决**：代理添加 Claude Code 的 User-Agent

---

### 坑 7: 超时时间太短

**现象**：复杂讨论时请求超时。

**原因**：默认 timeout 30s，多 Agent 并行生成可能超时。

**解决**：增加 timeout 到 60s

---

## 会话存储

### 坑 8: Redis 连接失败

**现象**：
```
ConnectionError: Error connecting to redis://localhost:6379
```

**原因**：Redis 未启动或配置错误。

**解决**：
1. 检查 Redis 是否运行
2. 使用内存存储回退
3. Docker 启动

---

### 坑 9: Session 序列化失败

**现象**：存储到 Redis 时报错。

**原因**：自定义对象不能直接 JSON 序列化。

**解决**：使用 dataclass + asdict

---

## 防漂移机制

### 坑 10: TopicAnchor 提示过长

**现象**：Agent 输出被截断或忽略议题锚定。

**原因**：Prompt 太长，LLM 注意力分散。

**解决**：精简议题锚定提示

---

### 坑 11: ContextTruncator 截断过度

**现象**：Round 2 后 Agent 忘记议题。

**原因**：截断后只保留摘要，丢失了议题原文。

**解决**：始终保留用户原始问题

---

## WebSocket

### 坑 12: WebSocket 连接假死

**现象**：连接显示 ready 但停止接收消息。

**原因**：飞书 SDK 心跳间隔 120 秒，无法检测静默断开。

**解决**：多层监控策略

---

## 部署相关

### 坑 13: 企业微信域名拦截

**现象**：该域名主体为第三方服务商

**原因**：企业微信不接受穿透域名（natapp/ngrok）。

**解决**：使用自有域名 + Cloudflare Tunnel

---

### 坑 14: Docker 构建失败

**现象**：
```
ModuleNotFoundError: No module named 'autogen_core'
```

**原因**：AutoGen 是可选依赖，但某些导入语句在非可选路径。

**解决**：使用条件导入

---

## 调试技巧

### 技巧 1: 快速测试搜索

```python
from tools.search_free import get_free_search_tool
s = get_free_search_tool()
print(s.search('2024 Nobel Prize'))
```

### 技巧 2: 模拟 LLM 响应

```bash
export MULTIROLE_DEMO_MODE=1
python api/server.py
```

---

## 总结

| 类别 | 主要教训 |
|------|----------|
| AutoGen | 版本兼容性是个坑，尽量用 prompt-based |
| 搜索 | 免费服务要加重试，解析要健壮 |
| 部署 | 域名要自有，超时设长点 |
| 调试 | DEMO_MODE 是好东西 |

