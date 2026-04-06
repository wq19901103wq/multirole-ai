import pytest
from harness_engine.persona_generator import PersonaGenerator
from harness_engine.engine import HarnessEngine
from core.topic import Topic


def test_detect_domain_tech():
    assert PersonaGenerator.detect_domain("如何设计一个高并发系统？") == "tech"


def test_detect_domain_business():
    assert PersonaGenerator.detect_domain("这个产品的商业模式是什么？") == "business"


def test_detect_domain_social():
    assert PersonaGenerator.detect_domain("当代年轻人的婚恋观变化") == "social"


def test_detect_domain_policy():
    assert PersonaGenerator.detect_domain("数据隐私保护的监管政策") == "policy"


def test_detect_domain_design():
    assert PersonaGenerator.detect_domain("这个 APP 的用户体验如何改进？") == "design"


def test_detect_domain_default():
    assert PersonaGenerator.detect_domain("随便聊聊") == "default"


def test_generate_personas_tech():
    personas = PersonaGenerator.generate("人工智能会取代程序员吗？")
    assert len(personas) == 4
    assert personas[0].agent_id == "planner"
    assert personas[1].agent_id == "engineer"
    assert personas[2].agent_id == "analyst"
    assert personas[3].agent_id == "writer"


def test_generate_personas_social():
    personas = PersonaGenerator.generate("远程工作对家庭关系的影响")
    assert len(personas) == 4
    assert personas[0].agent_id == "planner"
    assert personas[1].agent_id == "practitioner"
    assert personas[2].agent_id == "analyst"
    assert personas[3].agent_id == "writer"


def test_engine_uses_dynamic_personas(router):
    engine = HarnessEngine(router)
    topic = Topic(text="人工智能会取代程序员吗？")
    results = engine.run(topic, max_rounds=1, force_manual=True)

    assert len(results) == 1
    assert len(results[0].messages) == 5

    # 验证动态生成的角色确实被使用了
    sender_ids = [m.sender_id for m in results[0].messages if not m.is_moderation]
    assert "engineer" in sender_ids


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
