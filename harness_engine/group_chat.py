from typing import List, Any, Optional
import asyncio
from core.message import Message, Role
from model_router.router import ModelRouter
from drift_guard.anchor import TopicAnchor
from drift_guard.checkpoint import ModeratorCheckpoint


class HarnessGroupChat:
    """
    兼容层：
    - 如果系统安装了 autogen，优先使用 AutoGen 的 SelectorGroupChat 做调度；
    - 否则退化为手动循环实现，保证不装 autogen 也能跑。
    """

    def __init__(
        self,
        router: ModelRouter,
        topic_anchor: TopicAnchor,
        checkpoint: ModeratorCheckpoint,
    ):
        self.router = router
        self.topic_anchor = topic_anchor
        self.checkpoint = checkpoint
        self._autogen_available = False
        self._try_import_autogen()

    def _try_import_autogen(self):
        try:
            import autogen_agentchat
            import autogen_core
            self._autogen_available = True
        except ImportError:
            self._autogen_available = False

    def run_round(
        self,
        round_num: int,
        participants: List[Any],  # HarnessAgentSpec
        moderator_spec: Any,
        topic_text: str,
        prev_summary: Optional[str] = None,
        force_manual: bool = False,
        on_message=None,
        full_history: Optional[List[Message]] = None,
    ) -> List[Message]:
        if self._autogen_available and not force_manual:
            # AutoGen 模式不支持逐消息回调，先跑完再批量回调（如有需要）
            msgs = self._run_with_autogen(
                round_num, participants, moderator_spec, topic_text, prev_summary
            )
            if on_message:
                for m in msgs:
                    on_message(m)
            return msgs
        else:
            return self._run_manual(
                round_num, participants, moderator_spec, topic_text, prev_summary, on_message=on_message, full_history=full_history
            )

    def _build_context(self, round_num: int, topic_text: str, prev_summary: Optional[str], full_history: Optional[List[Message]] = None) -> str:
        lines = [f"=== 核心议题 ===\n{topic_text}"]

        # 共识模式下，如果历史较多，提炼关键交锋点
        if full_history and len(full_history) > 5:
            lines.append("\n=== 前面轮次的关键讨论 ===")
            # 提取每轮 moderator 摘要 + 最后一个 debater 的收尾观点
            seen_rounds = set()
            for msg in full_history:
                if msg.is_moderation:
                    rnd = msg.metadata.get("round", 0)
                    if rnd not in seen_rounds:
                        seen_rounds.add(rnd)
                        lines.append(f"第 {rnd} 轮总结：{msg.content[:100]}...")
        elif prev_summary:
            lines.append(f"\n=== 上轮核心摘要 ===\n{prev_summary}")

        lines.append(f"\n当前是第 {round_num} 轮。请严格遵循议题锚定规则发言。")
        return "\n".join(lines)

    def _run_manual(
        self,
        round_num: int,
        participants: List[Any],
        moderator_spec: Any,
        topic_text: str,
        prev_summary: Optional[str],
        on_message=None,
        full_history: Optional[List[Message]] = None,
    ) -> List[Message]:
        messages: List[Message] = []
        context = self._build_context(round_num, topic_text, prev_summary, full_history)

        for spec in participants:
            system = self.topic_anchor.inject_prompt(spec.name, spec.personality, spec.style)

            # 构建对话历史：当前 Agent 能看到前面所有 Agent 的发言
            conversation = [{"role": "user", "content": context}]
            for prev_msg in messages:
                if prev_msg.is_moderation:
                    continue
                conversation.append({
                    "role": "assistant",
                    "content": f"{prev_msg.sender_name}: {prev_msg.content}"
                })

            raw = self.router.chat(
                messages=conversation,
                system=system,
                max_tokens=1000,
                temperature=0.7,
            )
            relevance = self.topic_anchor.extract_relevance(raw)
            msg = Message(
                role=Role.ASSISTANT,
                content=raw,
                sender_id=spec.agent_id,
                sender_name=spec.name,
                metadata={"relevance_score": relevance, "type": "response", "round": round_num},
            )
            messages.append(msg)
            if on_message:
                on_message(msg)

        ck = self.checkpoint.check(self.topic_anchor.topic, messages)
        mod_content = ck["summary"]
        mod_msg = Message(
            role=Role.MODERATOR,
            content=mod_content,
            sender_id=moderator_spec.agent_id,
            sender_name=moderator_spec.name,
            metadata={"type": "moderation", "drift_detected": ck["drift_detected"], "round": round_num},
        )
        messages.append(mod_msg)
        if on_message:
            on_message(mod_msg)
        return messages

    def _run_with_autogen(
        self,
        round_num: int,
        participants: List[Any],
        moderator_spec: Any,
        topic_text: str,
        prev_summary: Optional[str],
    ) -> List[Message]:
        """
        使用 AutoGen v0.7+ (autogen-agentchat) 实现受控轮次讨论。
        """
        import asyncio
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.teams import SelectorGroupChat
        from autogen_agentchat.conditions import MaxMessageTermination
        from autogen_agentchat.messages import TextMessage
        from autogen_core import AgentId, SingleThreadedAgentRuntime
        from harness_engine.autogen_client import ModelRouterChatCompletionClient

        model_client = ModelRouterChatCompletionClient(self.router)

        # 构建 debater agents
        debater_ids = [p.agent_id for p in participants]
        autogen_agents = []
        for spec in participants:
            system_prompt = self.topic_anchor.inject_prompt(spec.name, spec.personality, spec.style)
            agent = AssistantAgent(
                name=spec.agent_id,
                model_client=model_client,
                system_message=system_prompt,
            )
            autogen_agents.append(agent)

        # moderator agent
        mod_system = moderator_spec.system_prompt
        moderator_agent = AssistantAgent(
            name=moderator_spec.agent_id,
            model_client=model_client,
            system_message=mod_system,
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
        context = self._build_context(round_num, topic_text, prev_summary)
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
                our_messages.append(Message(
                    role=Role.MODERATOR,
                    content=content,
                    sender_id=sender_id,
                    sender_name=moderator_spec.name,
                    metadata={"type": "moderation", "round": round_num},
                ))
            else:
                relevance = self.topic_anchor.extract_relevance(content)
                our_messages.append(Message(
                    role=Role.ASSISTANT,
                    content=content,
                    sender_id=sender_id,
                    sender_name=next((p.name for p in participants if p.agent_id == sender_id), sender_id),
                    metadata={"relevance_score": relevance, "type": "response", "round": round_num},
                ))

        # 如果 moderator 没有产出内容（比如 AutoGen 内部吞了），fallback 到手动 moderator
        has_moderator = any(m.sender_id == moderator_spec.agent_id for m in our_messages)
        if not has_moderator and our_messages:
            debater_msgs = [m for m in our_messages if m.sender_id != moderator_spec.agent_id]
            ck = self.checkpoint.check(self.topic_anchor.topic, debater_msgs)
            our_messages.append(Message(
                role=Role.MODERATOR,
                content=ck["summary"],
                sender_id=moderator_spec.agent_id,
                sender_name=moderator_spec.name,
                metadata={"type": "moderation", "drift_detected": ck["drift_detected"], "round": round_num},
            ))

        return our_messages
