from dataclasses import dataclass


@dataclass
class HarnessAgentSpec:
    """Harness 引擎中的 Agent 规格"""
    agent_id: str
    name: str
    system_prompt: str
    description: str = ""
    emoji: str = "🤖"
    color: str = "#667eea"
    is_moderator: bool = False
