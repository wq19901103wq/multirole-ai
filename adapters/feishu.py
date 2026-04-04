from typing import List, Dict, Any
from core.event import DiscussionEvent
from drift_guard.anchor import TopicAnchor
from .base import BaseAdapter


class FeishuAdapter(BaseAdapter):
    """
    飞书机器人适配器。
    飞书交互卡片格式参考：https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-json-structure
    """

    def render_events(self, events: List[DiscussionEvent]) -> Dict[str, Any]:
        """输出飞书机器人消息卡片"""
        elements = []
        current_round = 0

        for evt in events:
            if evt.round_num != current_round:
                current_round = evt.round_num
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "plain_text",
                        "content": f"--- 第 {current_round} 轮 {'· 主持人对齐' if evt.event_type == 'moderation' else ''} ---"
                    }
                })

            msg = evt.payload
            is_mod = msg.is_moderation
            name = msg.sender_name or "Unknown"
            content = msg.content if is_mod else TopicAnchor.clean_response(msg.content)
            relevance = msg.relevance_score

            header = f"**{name}**"
            if not is_mod and relevance is not None:
                header += f"  · 相关性 {relevance}/10"

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"{header}\n{content}"
                }
            })
            elements.append({"tag": "hr"})

        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "🤖 多角色 AI 讨论结果"},
                    "template": "blue"
                },
                "elements": elements
            }
        }

    def extract_user_message(self, payload: Dict[str, Any]) -> str:
        """从飞书事件回调中提取用户消息"""
        # 支持文本消息和卡片回调
        event = payload.get("event", {})
        message = event.get("message", {})
        content = message.get("content", "{}")
        import json
        try:
            c = json.loads(content)
            return c.get("text", "").strip()
        except Exception:
            return str(content).strip()

    def extract_session_id(self, payload: Dict[str, Any]) -> str:
        """从飞书事件回调中提取 session_id（用 open_id + message_id 组合）"""
        event = payload.get("event", {})
        sender = event.get("sender", {}).get("sender_id", {}).get("open_id", "unknown")
        message_id = event.get("message", {}).get("message_id", "default")
        return f"feishu:{sender}:{message_id}"
