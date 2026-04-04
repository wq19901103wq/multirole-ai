import pytest
from core.message import Message, Role
from core.event import DiscussionEvent
from adapters import WebAdapter, FeishuAdapter, WechatAdapter


def make_events() -> list:
    return [
        DiscussionEvent(
            event_type="message",
            payload=Message(role=Role.ASSISTANT, content="关于'议题'，我的观点是：内容A\n\n以上观点与核心议题的相关性：9/10", sender_id="planner", sender_name="规划师", metadata={"relevance_score": 9.0}),
            round_num=1,
        ),
        DiscussionEvent(
            event_type="moderation",
            payload=Message(role=Role.MODERATOR, content="摘要：内容A", sender_id="moderator", sender_name="主持人", metadata={"type": "moderation"}),
            round_num=1,
        ),
    ]


def test_web_adapter():
    adapter = WebAdapter()
    rendered = adapter.render_events(make_events())
    assert len(rendered) == 2
    assert rendered[0]["role_name"] == "规划师"
    assert rendered[0]["relevance"] == 9.0
    assert "内容A" in rendered[0]["content"]
    assert rendered[1]["event_type"] == "moderation"


def test_feishu_adapter():
    adapter = FeishuAdapter()
    payload = {"event": {"message": {"content": '{"text": "  你好  "}', "message_id": "m1"}, "sender": {"sender_id": {"open_id": "u1"}}}}
    assert adapter.extract_user_message(payload) == "你好"
    assert adapter.extract_session_id(payload) == "feishu:u1:m1"

    card = adapter.render_events(make_events())
    assert card["msg_type"] == "interactive"
    assert any("规划师" in str(elem) for elem in card["card"]["elements"])


def test_wechat_adapter():
    adapter = WechatAdapter()
    payload = {"FromUserName": "wx_user", "MsgId": "123", "Content": "  问题  "}
    assert adapter.extract_user_message(payload) == "问题"
    assert adapter.extract_session_id(payload) == "wechat:wx_user:123"

    msg = adapter.render_events(make_events())
    assert msg["msgtype"] == "text"
    assert "内容A" in msg["text"]["content"]
