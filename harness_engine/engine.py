from typing import List, Optional, Callable
from core.topic import Topic
from core.event import TurnResult
from core.message import Message, Role
from model_router.router import ModelRouter
from drift_guard.anchor import TopicAnchor
from drift_guard.checkpoint import ModeratorCheckpoint
from drift_guard.truncator import ContextTruncator
from .group_chat import HarnessGroupChat
from .agents.debater import DebaterAgent
from .agents.moderator import ModeratorAgent
from .persona_generator import PersonaGenerator


class HarnessEngine:
    """
    Harness Engineering 核心入口。
    
    职责：
    1. 接收一个 Topic 和一组 Persona
    2. 通过 HarnessGroupChat 运行受控的多轮讨论
    3. 集成 DriftGuard 防止话题漂移
    4. 输出结构化的 TurnResult
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def run(
        self,
        topic: Topic,
        personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 2,
        force_manual: bool = False,
    ) -> List[TurnResult]:
        return list(self.run_stream(topic, personas, max_rounds, force_manual))

    def run_stream(
        self,
        topic: Topic,
        personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 2,
        force_manual: bool = False,
        on_message: Optional[Callable[[Message], None]] = None,
    ):
        """
        生成器版本：逐轮 yield TurnResult，同时支持逐消息回调 on_message。
        适合 WebSocket 实时推送场景。
        """
        if personas is None:
            personas = PersonaGenerator.generate(topic.text)
        moderator = ModeratorAgent()

        anchor = TopicAnchor(topic)
        checkpoint = ModeratorCheckpoint(self.router)
        truncator = ContextTruncator(max_history_turns=2)
        group_chat = HarnessGroupChat(self.router, anchor, checkpoint)

        prev_summary: Optional[str] = None

        for round_num in range(1, max_rounds + 1):
            round_messages = group_chat.run_round(
                round_num=round_num,
                participants=personas,
                moderator_spec=moderator,
                topic_text=topic.text,
                prev_summary=prev_summary,
                force_manual=force_manual,
                on_message=on_message,
            )

            # 解析 moderator 的结果
            mod_msg = [m for m in round_messages if m.is_moderation][-1]
            drift_detected = mod_msg.metadata.get("drift_detected", False)
            prev_summary = mod_msg.content  # 下一轮基于 moderator 摘要继续

            result = TurnResult(
                messages=round_messages,
                summary=prev_summary,
                drift_detected=drift_detected,
                drift_report=mod_msg.content if drift_detected else "",
                metadata={"round": round_num},
            )
            yield result
