"""WebSocket streaming routes."""

import json
import logging

from api import state

logger = logging.getLogger(__name__)


def _msg_to_event(msg, round_num):
    """把内部 Message 对象转成前端事件 dict。"""
    return {
        "event_type": "moderation" if msg.is_moderation else "message",
        "role_name": msg.sender_name or msg.sender_id or "Agent",
        "content": msg.content,
        "relevance": msg.metadata.get("relevance_score"),
        "round": round_num,
        "emoji": msg.metadata.get("emoji", "🤖"),
        "color": msg.metadata.get("color", "#667eea"),
    }


def discuss_stream(ws):
    """
    WebSocket 实时流式讨论接口。
    客户端发送 JSON：{"message": "...", "session_id": "...", "max_rounds": 2}
    服务端逐条推送每个 Agent 的发言和 Moderator 总结。
    """
    try:
        raw = ws.receive(timeout=5)
        if not raw:
            ws.send(json.dumps({"error": "empty request"}))
            return
        data = json.loads(raw)
    except Exception as e:
        ws.send(json.dumps({"error": f"invalid json: {e}"}))
        return

    user_message = state.web_adapter.extract_user_message(data)
    session_id = state.web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2)

    if not user_message:
        ws.send(json.dumps({"error": "message is required"}))
        return

    ws.send(json.dumps({"type": "status", "text": "讨论开始"}))

    from core.topic import Topic
    topic_obj = Topic(text=user_message)

    def on_message(msg):
        evt = _msg_to_event(msg, msg.metadata.get("round", 0))
        ws.send(json.dumps({"type": "event", "payload": evt}))

    try:
        for turn in state.session_manager.engine.run_stream(
            topic=topic_obj,
            max_rounds=max_rounds,
            force_manual=True,
            on_message=on_message,
        ):
            ws.send(json.dumps({"type": "turn_end", "round": turn.metadata.get("round", 0)}))

        ws.send(json.dumps({"type": "done", "session_id": session_id}))
    except Exception as e:
        ws.send(json.dumps({"type": "error", "message": str(e)}))


def discuss_consensus_stream(ws):
    """
    WebSocket 共识讨论接口：持续多轮直到达成一致。
    客户端发送 JSON：{"message": "...", "session_id": "...", "max_rounds": 10}
    """
    try:
        raw = ws.receive(timeout=5)
        if not raw:
            ws.send(json.dumps({"error": "empty request"}))
            return
        data = json.loads(raw)
    except Exception as e:
        ws.send(json.dumps({"error": f"invalid json: {e}"}))
        return

    user_message = state.web_adapter.extract_user_message(data)
    session_id = state.web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 10)

    if not user_message:
        ws.send(json.dumps({"error": "message is required"}))
        return

    ws.send(json.dumps({"type": "status", "text": "共识讨论开始（最多 " + str(max_rounds) + " 轮）"}))

    from core.topic import Topic
    topic_obj = Topic(text=user_message)

    def on_message(msg):
        evt = _msg_to_event(msg, msg.metadata.get("round", 0))
        ws.send(json.dumps({"type": "event", "payload": evt}))

    def on_consensus(consensus):
        ws.send(json.dumps({
            "type": "consensus_check",
            "reached": consensus.get("consensus_reached", False),
            "confidence": consensus.get("confidence", 0),
        }))

    try:
        for turn in state.session_manager.engine.run_until_consensus_stream(
            topic=topic_obj,
            max_rounds=max_rounds,
            force_manual=True,
            on_message=on_message,
            on_consensus=on_consensus,
        ):
            ws.send(json.dumps({"type": "turn_end", "round": turn.metadata.get("round", 0)}))
            if turn.metadata.get("consensus_reached"):
                ws.send(json.dumps({
                    "type": "consensus",
                    "summary": turn.metadata.get("consensus_summary", ""),
                }))
                break
            elif turn.metadata.get("round") == max_rounds and not turn.metadata.get("consensus_reached"):
                ws.send(json.dumps({"type": "timeout"}))
                break

        ws.send(json.dumps({"type": "done", "session_id": session_id}))
    except Exception as e:
        ws.send(json.dumps({"type": "error", "message": str(e)}))
