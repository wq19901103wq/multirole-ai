import pytest
from core.topic import Topic
from harness_engine import HarnessEngine
from harness_engine.agents.debater import DebaterAgent


def test_harness_engine_manual_fallback(router):
    """HarnessEngine 手动模式能产出完整轮次"""
    engine = HarnessEngine(router)
    topic = Topic(text="测试议题")
    results = engine.run(topic, max_rounds=2, force_manual=True)

    assert len(results) == 2
    for turn in results:
        # 每轮应该有 4 个 debater + 1 个 moderator = 5 条消息
        assert len(turn.messages) == 5
        moderator_msgs = [m for m in turn.messages if m.is_moderation]
        assert len(moderator_msgs) == 1
        # moderator 的摘要应存在
        assert turn.summary != ""


def test_harness_engine_custom_personas(router):
    engine = HarnessEngine(router)
    topic = Topic(text="测试议题")
    custom = [
        DebaterAgent("security", "安全专家", "关注安全", "谨慎", "🔒", "#333"),
        DebaterAgent("pm", "产品经理", "关注需求", "积极", "📱", "#666"),
    ]
    results = engine.run(topic, personas=custom, max_rounds=1, force_manual=True)
    assert len(results) == 1
    assert len(results[0].messages) == 3  # 2 debaters + 1 moderator


def test_harness_engine_with_autogen_installed(router):
    """
    如果 AutoGen 已安装，验证 HarnessGroupChat 能正确 import 并返回结构化 Message。
    由于 AutoGen 是异步的且依赖外部 API，这里只验证接口和类型，不验证内容。
    """
    try:
        import autogen_agentchat
    except ImportError:
        pytest.skip("AutoGen not installed")

    from harness_engine.group_chat import HarnessGroupChat
    from harness_engine.agents.moderator import ModeratorAgent
    from drift_guard.anchor import TopicAnchor
    from drift_guard.checkpoint import ModeratorCheckpoint

    topic = Topic(text="测试 AutoGen 集成")
    anchor = TopicAnchor(topic)
    checkpoint = ModeratorCheckpoint(router)
    gc = HarnessGroupChat(router, anchor, checkpoint)

    personas = [
        DebaterAgent("a", "A", "", "", "", "#000"),
        DebaterAgent("b", "B", "", "", "", "#000"),
    ]
    moderator = ModeratorAgent()

    msgs = gc.run_round(1, personas, moderator, topic.text, force_manual=True)
    assert len(msgs) >= 2  # 至少 debaters + moderator
    assert any(m.is_moderation for m in msgs)
