from .base import HarnessAgentSpec


class DebaterAgent(HarnessAgentSpec):
    """
    辩论型专家 Agent。
    实际的角色个性由 harness engine 在运行前注入 TopicAnchor 后生成 system_prompt。
    """

    def __init__(self, agent_id: str, name: str, personality: str, style: str, emoji: str, color: str):
        super().__init__(
            agent_id=agent_id,
            name=name,
            system_prompt="",  # 运行前由 TopicAnchor 填充
            description=f"{personality}；说话风格：{style}",
            emoji=emoji,
            color=color,
        )
        self.personality = personality
        self.style = style
