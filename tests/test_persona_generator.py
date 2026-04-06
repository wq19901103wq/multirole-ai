import pytest
from harness_engine.persona_generator import PersonaGenerator
from harness_engine.engine import HarnessEngine
from core.topic import Topic


def test_generate_personas_default():
    """无 LLM 时，应返回 4 个平等的思考者"""
    personas = PersonaGenerator.generate("人工智能会取代程序员吗？")
    assert len(personas) == 4
    names = [p.name for p in personas]
    assert names == ["思考者一", "思考者二", "思考者三", "思考者四"]


def test_generate_personas_shared_style():
    """所有思考者都应带有互动讨论的 style"""
    personas = PersonaGenerator.generate("随便聊聊")
    for p in personas:
        assert "圆桌讨论" in p.style
        assert "赞同、补充、质疑或反驳" in p.style


def test_engine_uses_dynamic_personas(router):
    engine = HarnessEngine(router)
    topic = Topic(text="人工智能会取代程序员吗？")
    results = engine.run(topic, max_rounds=1, force_manual=True)

    assert len(results) == 1
    # 4 个思考者 + 1 个 moderator
    assert len(results[0].messages) == 5

    sender_ids = [m.sender_id for m in results[0].messages if not m.is_moderation]
    assert "thinker_1" in sender_ids


def test_engine_custom_personas_override_dynamic(router):
    from harness_engine.agents.debater import DebaterAgent

    engine = HarnessEngine(router)
    custom = [
        DebaterAgent("a", "A", "", "", "", "#000"),
        DebaterAgent("b", "B", "", "", "", "#000"),
    ]
    topic = Topic(text="人工智能会取代程序员吗？")
    results = engine.run(topic, personas=custom, max_rounds=1, force_manual=True)

    sender_ids = [m.sender_id for m in results[0].messages if not m.is_moderation]
    assert sender_ids == ["a", "b"]
