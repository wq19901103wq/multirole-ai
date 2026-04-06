import pytest
from harness_engine.persona_generator import PersonaGenerator
from harness_engine.engine import HarnessEngine
from core.topic import Topic


def test_generate_personas_tech_fallback():
    """无 LLM 时，技术话题应匹配到技术相关维度 + 通用维度"""
    personas = PersonaGenerator.generate("人工智能会取代程序员吗？")
    assert len(personas) == 4
    names = [p.name for p in personas]
    assert "技术实现" in names


def test_generate_personas_social_fallback():
    """无 LLM 时，社会话题应匹配到社会相关维度 + 通用维度"""
    personas = PersonaGenerator.generate("远程工作对家庭关系的影响")
    assert len(personas) == 4
    names = [p.name for p in personas]
    assert "社会影响" in names or "个体体验" in names


def test_generate_personas_business_fallback():
    personas = PersonaGenerator.generate("这个产品的商业模式是什么？")
    assert len(personas) == 4
    names = [p.name for p in personas]
    assert "经济影响" in names


def test_generate_personas_generic_fallback():
    """无明显特征的话题，应返回通用维度"""
    personas = PersonaGenerator.generate("随便聊聊")
    assert len(personas) == 4
    names = [p.name for p in personas]
    assert "核心逻辑" in names


def test_engine_uses_dynamic_personas(router):
    engine = HarnessEngine(router)
    topic = Topic(text="人工智能会取代程序员吗？")
    results = engine.run(topic, max_rounds=1, force_manual=True)

    assert len(results) == 1
    # 动态角色数量不一定是 4，但至少 2 个 debater + 1 moderator
    assert len(results[0].messages) >= 3

    # 验证动态生成的角色确实被使用了
    sender_ids = [m.sender_id for m in results[0].messages if not m.is_moderation]
    assert len(sender_ids) >= 2


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
