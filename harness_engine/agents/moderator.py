from .base import HarnessAgentSpec


class ModeratorAgent(HarnessAgentSpec):
    def __init__(self):
        super().__init__(
            agent_id="moderator",
            name="主持人",
            system_prompt=(
                "你是主持人，严格把控讨论方向，不做价值判断，只做流程和范围控制。"
                "回复简洁，80字以内。"
            ),
            description="严格把控讨论方向的主持人",
            emoji="⚖️",
            color="#F39C12",
            is_moderator=True,
        )
