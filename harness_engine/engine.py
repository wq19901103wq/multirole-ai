from typing import List, Optional
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


class HarnessEngine:
    """
    Harness Engineering 核心入口。
    
    职责：
    1. 接收一个 Topic 和一组 Persona
    2. 通过 HarnessGroupChat 运行受控的多轮讨论
    3. 集成 DriftGuard 防止话题漂移
    4. 输出结构化的 TurnResult
    """

    DEFAULT_PERSONAS = [
        DebaterAgent("planner", "规划师", "善于分析需求、拆解任务、制定计划", "条理清晰，注重可行性", "👤", "#FF6B6B"),
        DebaterAgent("engineer", "工程师", "技术专家，关注实现细节", "务实直接，注重代码和方案", "👨‍💻", "#4ECDC4"),
        DebaterAgent("analyst", "分析师", "数据驱动，善于发现洞察", "用数据说话，理性客观", "📊", "#45B7D1"),
        DebaterAgent("writer", "文案师", "文字工作者，善于总结表达", "简洁有力，注重可读性", "📝", "#96CEB4"),
    ]

    def __init__(self, router: ModelRouter):
        self.router = router

    def run(
        self,
        topic: Topic,
        personas: Optional[List[DebaterAgent]] = None,
        max_rounds: int = 2,
        force_manual: bool = False,
    ) -> List[TurnResult]:
        personas = personas or self.DEFAULT_PERSONAS
        moderator = ModeratorAgent()

        anchor = TopicAnchor(topic)
        checkpoint = ModeratorCheckpoint(self.router)
        truncator = ContextTruncator(max_history_turns=2)
        group_chat = HarnessGroupChat(self.router, anchor, checkpoint)

        results: List[TurnResult] = []
        prev_summary: Optional[str] = None

        for round_num in range(1, max_rounds + 1):
            round_messages = group_chat.run_round(
                round_num=round_num,
                participants=personas,
                moderator_spec=moderator,
                topic_text=topic.text,
                prev_summary=prev_summary,
                force_manual=force_manual,
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
            results.append(result)

        return results
