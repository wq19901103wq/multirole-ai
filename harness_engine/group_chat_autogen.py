from typing import List, Any, Optional
import asyncio

from core.message import Message, Role
from harness_engine.group_chat_manual import build_context
from autogen_core.tools import FunctionTool
from tools.search_free import search_web


def run_autogen_round(
    router,
    topic_anchor,
    checkpoint,
    round_num: int,
    participants: List[Any],
    moderator_spec: Any,
    topic_text: str,
    prev_summary: Optional[str],
) -> List[Message]:
    """
    使用 AutoGen v0.7+ (autogen-agentchat) 实现受控轮次讨论。
    """
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import SelectorGroupChat
    from autogen_agentchat.conditions import MaxMessageTermination
    from autogen_agentchat.messages import TextMessage
    from autogen_core import AgentId, SingleThreadedAgentRuntime
    from harness_engine.autogen_client import ModelRouterChatCompletionClient

    model_client = ModelRouterChatCompletionClient(router)

    # 创建搜索工具（FunctionTool 格式，供 AutoGen 调用）
    search_tool = FunctionTool(
        search_web,
        description="搜索网络获取实时信息。当需要验证事实、获取最新数据、确认人名日期等不确定信息时使用。",
        name="search_web",
    )
    debater_ids = [p.agent_id for p in participants]
    autogen_agents = []

    from harness_engine.autogen_agents import create_react_agent

    for spec in participants:
        system_prompt = topic_anchor.inject_prompt(
            spec.name, spec.personality, spec.style
        )

        agent = create_react_agent(
            agent_id=spec.agent_id,
            name=spec.name,
            system_prompt=system_prompt,
            model_client=model_client,
            tools=[search_tool],
        )

        autogen_agents.append(agent)

    # moderator agent - 也使用 ReAct 模式
    from harness_engine.autogen_agents import create_moderator_agent

    moderator_agent = create_moderator_agent(
        agent_id=moderator_spec.agent_id,
        name="主持人",
        system_prompt=moderator_spec.system_prompt,
        model_client=model_client,
        tools=[search_tool],
    )
    autogen_agents.append(moderator_agent)

    # 当前轮次的发言顺序控制器
    round_state = {"spoken_in_round": [], "current_round": round_num}
    all_agents = autogen_agents.copy()
    max_turns_in_round = len(participants) + 1

    def candidate_func(messages) -> List[str]:
        """控制当前哪些 agent 可以发言"""
        if not messages:
            # 第一轮第一条消息开始时，只允许 debaters
            return debater_ids

        last_sender = None
        for m in reversed(messages):
            if isinstance(m, TextMessage):
                last_sender = m.source
                break

        spoken = round_state["spoken_in_round"]

        if last_sender == moderator_spec.agent_id:
            # moderator 刚说完，本轮结束，理论上不应该再有发言（由 termination 控制）
            return []

        if last_sender and last_sender not in spoken:
            spoken.append(last_sender)

        if len(spoken) >= len(participants):
            # 所有 debaters 都说完了，轮到 moderator
            return [moderator_spec.agent_id]
        else:
            # 还有 debaters 没说话
            remaining = [aid for aid in debater_ids if aid not in spoken]
            return remaining

    def selector_func(messages) -> Optional[str]:
        """从候选中选下一个发言人：按轮次顺序挑第一个可用的"""
        candidates = candidate_func(messages)
        if not candidates:
            return None
        # 按 participants 的原始顺序选择第一个可用候选人
        for p in participants:
            if p.agent_id in candidates:
                return p.agent_id
        if moderator_spec.agent_id in candidates:
            return moderator_spec.agent_id
        return candidates[0]

    # 构造初始消息（把核心议题作为 user 消息注入）
    context = build_context(round_num, topic_text, prev_summary)
    initial_task = f"请围绕以下议题进行讨论。{context}"

    team = SelectorGroupChat(
        participants=all_agents,
        model_client=model_client,
        selector_func=selector_func,
        allow_repeated_speaker=False,
        max_turns=max_turns_in_round,
        termination_condition=MaxMessageTermination(max_messages=max_turns_in_round),
    )

    async def _run():
        result = await team.run(task=initial_task)
        return result.messages

    autogen_messages = asyncio.run(_run())

    # 转换回我们的 Message 模型
    our_messages: List[Message] = []
    for m in autogen_messages:
        if not isinstance(m, TextMessage):
            continue
        sender_id = m.source
        content = m.content or ""

        if sender_id == moderator_spec.agent_id:
            our_messages.append(
                Message(
                    role=Role.MODERATOR,
                    content=content,
                    sender_id=sender_id,
                    sender_name=moderator_spec.name,
                    metadata={"type": "moderation", "round": round_num},
                )
            )
        else:
            relevance = topic_anchor.extract_relevance(content)
            our_messages.append(
                Message(
                    role=Role.ASSISTANT,
                    content=content,
                    sender_id=sender_id,
                    sender_name=next(
                        (p.name for p in participants if p.agent_id == sender_id),
                        sender_id,
                    ),
                    metadata={
                        "relevance_score": relevance,
                        "type": "response",
                        "round": round_num,
                    },
                )
            )

    # 如果 moderator 没有产出内容（比如 AutoGen 内部吞了），fallback 到手动 moderator
    has_moderator = any(m.sender_id == moderator_spec.agent_id for m in our_messages)
    if not has_moderator and our_messages:
        debater_msgs = [m for m in our_messages if m.sender_id != moderator_spec.agent_id]
        ck = checkpoint.check(topic_anchor.topic, debater_msgs)
        our_messages.append(
            Message(
                role=Role.MODERATOR,
                content=ck["summary"],
                sender_id=moderator_spec.agent_id,
                sender_name=moderator_spec.name,
                metadata={
                    "type": "moderation",
                    "drift_detected": ck["drift_detected"],
                    "round": round_num,
                },
            )
        )

    return our_messages
