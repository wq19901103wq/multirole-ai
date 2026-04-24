from typing import List, Any, Optional
from core.message import Message, Role
from model_router.router import ModelRouter
from drift_guard.anchor import TopicAnchor
from drift_guard.checkpoint import ModeratorCheckpoint
from harness_engine.group_chat_manual import run_manual_round
from harness_engine.group_chat_autogen import run_autogen_round


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
