from typing import List
from core.message import Message


class ContextTruncator:
    """
    上下文截断器：只保留对当前轮次最关键的信息。
    策略：
    - 保留核心议题
    - 只保留最近 N 条 moderator 摘要
    - 丢弃过远的原始发言
    """

    def __init__(self, max_history_turns: int = 2):
        self.max_history_turns = max_history_turns

    def truncate(self, history: List[Message]) -> List[Message]:
        """返回截断后的历史"""
        # 保留用户问题
        user_msgs = [m for m in history if m.role.value == "user"]
        # 保留最近的 moderator 摘要
        mod_msgs = [m for m in history if m.is_moderation][-self.max_history_turns:]
        # 保留最近一轮的普通发言（如果需要，当前设计由 moderator 摘要替代）
        return user_msgs + mod_msgs
