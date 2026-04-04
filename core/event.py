from dataclasses import dataclass, field
from typing import List, Dict, Any
from .message import Message


@dataclass
class TurnResult:
    """一轮 harness 引擎的输出"""
    messages: List[Message] = field(default_factory=list)
    summary: str = ""                       # moderator 生成的摘要
    drift_detected: bool = False            # 本轮是否检测到漂移
    drift_report: str = ""                  # 漂移报告
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscussionEvent:
    """前端可订阅的事件"""
    event_type: str      # "message", "moderation", "summary", "drift_alert"
    payload: Message
    round_num: int = 0
