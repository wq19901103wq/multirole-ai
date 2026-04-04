import pytest
from core.topic import Topic
from drift_guard import TopicAnchor, ContextTruncator, ModeratorCheckpoint
from core.message import Message, Role


def test_topic_anchor_injects_forbidden_words():
    topic = Topic(text="如何设计高性能网站？")
    anchor = TopicAnchor(topic)
    prompt = anchor.inject_prompt("工程师", "技术专家", "务实")
    assert "关于'如何设计高性能网站？'，我的观点是：" in prompt
    assert "此外" in prompt
    assert "值得一提的是" in prompt
    assert "相关性：X/10" in prompt


def test_extract_relevance():
    text = "关于'xxx'，我的观点是：yyy。\n\n以上观点与核心议题的相关性：8/10"
    assert TopicAnchor.extract_relevance(text) == 8.0
    assert TopicAnchor.extract_relevance("没有评分") is None


def test_clean_response():
    raw = "关于'议题'，我的观点是：核心内容。\n\n以上观点与核心议题的相关性：9/10"
    clean = TopicAnchor.clean_response(raw)
    assert "关于'议题'，我的观点是：" not in clean
    assert "相关性：9/10" not in clean
    assert "核心内容。" in clean


def test_context_truncator():
    truncator = ContextTruncator(max_history_turns=1)
    history = [
        Message(role=Role.USER, content="用户问题", sender_id="user", sender_name="用户"),
        Message(role=Role.ASSISTANT, content="发言1", sender_id="a1", sender_name="A", metadata={"type": "response"}),
        Message(role=Role.MODERATOR, content="摘要1", sender_id="mod", sender_name="主持人", metadata={"type": "moderation"}),
        Message(role=Role.ASSISTANT, content="发言2", sender_id="a2", sender_name="B", metadata={"type": "response"}),
        Message(role=Role.MODERATOR, content="摘要2", sender_id="mod", sender_name="主持人", metadata={"type": "moderation"}),
    ]
    result = truncator.truncate(history)
    # 保留用户消息 + 最近1条 moderator
    assert len(result) == 2
    assert result[-1].content == "摘要2"


def test_moderator_checkpoint(router):
    topic = Topic(text="测试议题")
    checkpoint = ModeratorCheckpoint(router)
    round_msgs = [
        Message(role=Role.ASSISTANT, content="观点1", sender_id="a1", sender_name="A", metadata={"relevance_score": 9.0}),
        Message(role=Role.ASSISTANT, content="观点2", sender_id="a2", sender_name="B", metadata={"relevance_score": 7.0}),
    ]
    result = checkpoint.check(topic, round_msgs)
    assert "summary" in result
    assert isinstance(result["drift_detected"], bool)
    # mock provider 会返回默认字符串
    assert "默认测试回复" in result["summary"]
