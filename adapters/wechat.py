from typing import List, Dict, Any
from core.event import DiscussionEvent
from drift_guard.anchor import TopicAnchor
from .base import BaseAdapter


class WechatAdapter(BaseAdapter):
    """
    企业微信 / 微信公众号适配器。
    输出简单的 XML 或 JSON 格式，便于上层服务包装后返回给微信服务器。
    """

    def render_events(self, events: List[DiscussionEvent]) -> Dict[str, Any]:
        """输出简洁的文本分段结果"""
        lines = []
        current_round = 0

        for evt in events:
            if evt.round_num != current_round:
                current_round = evt.round_num
                lines.append(
                    f"--- 第 {current_round} 轮 {'· 主持人对齐' if evt.event_type == 'moderation' else ''} ---"
                )

            msg = evt.payload
            is_mod = msg.is_moderation
            name = msg.sender_name or "Unknown"
            content = msg.content if is_mod else TopicAnchor.clean_response(msg.content)
            relevance = msg.relevance_score

            prefix = f"【{name}】"
            if not is_mod and relevance is not None:
                prefix += f"(相关性{relevance}/10)"
            lines.append(f"{prefix}\n{content}")

        return {
            "msgtype": "text",
            "text": {
                "content": "\n\n".join(lines)
            }
        }

    def extract_user_message(self, payload: Dict[str, Any]) -> str:
        """从微信消息 XML/JSON 中提取用户内容"""
        # 如果是企业微信 JSON
        content = payload.get("Content", "")
        if content:
            return str(content).strip()
        # 如果已经由上层解析成 text 字段
        return payload.get("text", "").strip()

    def extract_session_id(self, payload: Dict[str, Any]) -> str:
        """用 FromUserName + MsgId 组合作为 session_id"""
        from_user = payload.get("FromUserName", "unknown")
        msg_id = payload.get("MsgId", "default")
        return f"wechat:{from_user}:{msg_id}"
