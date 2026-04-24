from typing import List, Any, Optional
from core.message import Message, Role
from model_router.router import ModelRouter
from drift_guard.anchor import TopicAnchor
from drift_guard.checkpoint import ModeratorCheckpoint
from harness_engine.group_chat_manual import run_manual_round
from harness_engine.group_chat_autogen import run_autogen_round


# 延迟导入 AutoGen，避免未安装时崩溃
_autogen_available = False
try:
    import autogen_agentchat  # noqa: F401
    import autogen_core  # noqa: F401
    _autogen_available = True
except ImportError:
    pass


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
        if _autogen_available and not force_manual:
            msgs = run_autogen_round(
                self.router,
                self.topic_anchor,
                self.checkpoint,
                round_num,
                participants,
                moderator_spec,
                topic_text,
                prev_summary,
            )
            if on_message:
                for m in msgs:
                    on_message(m)
            return msgs
        else:
            return run_manual_round(
                self.router,
                self.topic_anchor,
                self.checkpoint,
                round_num,
                participants,
                moderator_spec,
                topic_text,
                prev_summary,
                on_message=on_message,
                full_history=full_history,
            )
