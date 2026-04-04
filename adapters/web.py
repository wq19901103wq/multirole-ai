from typing import List, Dict, Any
from core.event import DiscussionEvent
from drift_guard.anchor import TopicAnchor
from .base import BaseAdapter


class WebAdapter(BaseAdapter):
    """
    Web 前端适配器：输出 JSON 供浏览器/小程序消费。
    """

    def render_events(self, events: List[DiscussionEvent]) -> List[Dict[str, Any]]:
        result = []
        colors = {
            "planner": "#FF6B6B",
            "engineer": "#4ECDC4",
            "analyst": "#45B7D1",
            "writer": "#96CEB4",
            "moderator": "#F39C12",
        }
        emojis = {
            "planner": "👤",
            "engineer": "👨‍💻",
            "analyst": "📊",
            "writer": "📝",
            "moderator": "⚖️",
        }

        for evt in events:
            msg = evt.payload
            is_mod = msg.is_moderation
            relevance = msg.relevance_score

            item = {
                "event_type": evt.event_type,
                "round": evt.round_num,
                "role_id": msg.sender_id or "unknown",
                "role_name": msg.sender_name or "Unknown",
                "emoji": emojis.get(msg.sender_id, "🤖"),
                "color": colors.get(msg.sender_id, "#667eea"),
                "content": msg.content if is_mod else TopicAnchor.clean_response(msg.content),
                "raw_content": msg.content,
                "relevance": relevance,
                "metadata": msg.metadata,
            }
            result.append(item)
        return result

    def extract_user_message(self, payload: Dict[str, Any]) -> str:
        return payload.get("message", "").strip()

    def extract_session_id(self, payload: Dict[str, Any]) -> str:
        return payload.get("session_id", "default")
