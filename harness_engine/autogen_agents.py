"""
AutoGen Agent 配置 - 真 ReAct 模式（Function Calling）

使用 AutoGen v0.7+ AssistantAgent 的 tools 参数实现真正的工具调用循环：
模型输出 function call → 系统执行工具 → 结果注入对话 → 模型继续推理
"""
from autogen_agentchat.agents import AssistantAgent


def create_react_agent(
    agent_id: str,
    name: str,
    system_prompt: str,
    model_client,
    tools=None,
):
    """
    创建真 ReAct 模式的 Agent（Function Calling）

    当 tools 不为空时，AssistantAgent 会自动：
    1. 让模型判断是否需要调用工具
    2. 解析 function call 参数
    3. 执行对应工具函数
    4. 把结果注入对话
    5. 模型基于结果继续推理
    6. 重复直到模型给出最终答案
    """
    return AssistantAgent(
        name=agent_id,
        model_client=model_client,
        system_message=system_prompt,
        tools=tools or [],
        reflect_on_tool_use=True,
        max_tool_iterations=3,
    )


# 保持兼容性 - 别名
create_debater_agent_with_tools = create_react_agent


def create_moderator_agent(
    agent_id: str,
    name: str,
    system_prompt: str,
    model_client,
    tools=None,
):
    """
    创建 ReAct 模式的主持人 Agent

    主持人也需要搜索能力来验证事实、获取最新信息。
    """
    return AssistantAgent(
        name=agent_id,
        model_client=model_client,
        system_message=system_prompt,
        tools=tools or [],
        reflect_on_tool_use=True,
        max_tool_iterations=2,
    )


def create_debater_agent_basic(
    agent_id: str,
    name: str,
    system_prompt: str,
    model_client
):
    """创建基础的辩论 Agent（无工具）"""
    return AssistantAgent(
        name=agent_id,
        model_client=model_client,
        system_message=system_prompt,
    )
