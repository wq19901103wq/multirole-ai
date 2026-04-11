from typing import List
from .agents.debater import DebaterAgent


class PersonaGenerator:
    """
    生成一组平等、自由的讨论者。

    不再预设固定角度或认知风格标签，
    4 个 Agent 都是善于深度思考的参与者，
    只是通过对话机制和互动 prompt 鼓励它们互相补充、质疑、反驳，
    最终推动讨论向更深入、更正确的方向发展。
    """

    PARTICIPANT_NAMES = [
        ("thinker_1", "思考者一", "🤔", "#FF6B6B"),
        ("thinker_2", "思考者二", "💡", "#4ECDC4"),
        ("thinker_3", "思考者三", "🔍", "#45B7D1"),
        ("thinker_4", "思考者四", "🌿", "#96CEB4"),
    ]

    SHARED_STYLE = """你是一个善于深度思考的智能体。

这是一个真实的圆桌讨论，不是各自独白。
你可以赞同、补充、质疑或反驳前面发言者的观点。
你的目标是推动讨论向更深入、更正确的方向发展。
如果某个观点有问题，请直接指出；如果某个观点有价值，请在此基础上进一步延伸。
不要生硬地套用固定角度，而是根据话题本身和前面的讨论内容自由思考。

【重要】每次发言请进行充分论述，尽量从多个层面展开深入分析，避免蜻蜓点水。字数建议在300字以上。"""

    @staticmethod
    def generate(topic_text: str, router=None) -> List[DebaterAgent]:
        """生成 4 个平等的讨论者"""
        # 如果有 LLM，可以让它为每个参与者写一句贴合话题的启动提示
        if router is not None:
            try:
                return PersonaGenerator._generate_with_llm(topic_text, router)
            except Exception:
                pass
        return PersonaGenerator._generate_default()

    @staticmethod
    def _generate_default() -> List[DebaterAgent]:
        return [
            DebaterAgent(
                agent_id=aid,
                name=name,
                personality="善于深度思考、批判性分析和建设性对话",
                style=PersonaGenerator.SHARED_STYLE,
                emoji=emoji,
                color=color,
            )
            for aid, name, emoji, color in PersonaGenerator.PARTICIPANT_NAMES
        ]

    @staticmethod
    def _generate_with_llm(topic_text: str, router) -> List[DebaterAgent]:
        """让 LLM 给 4 个思考者各写一句贴合话题的启动提醒"""
        prompt = f"""话题：{topic_text}

有 4 位思考者即将围绕这个话题展开自由讨论。
请为每位思考者写一句贴合该话题的启动提醒（不要分配固定角度，只是提醒他们在讨论时可以特别关注什么）。

格式：
思考者编号|提醒内容

例如：
思考者一|可以先从最明显的直觉判断切入
思考者二|注意检验前面观点中可能存在的隐含假设
"""
        # Kimi Code 模型默认启用 thinking 模式
        # 需要确保 max_tokens 足够容纳 thinking + 正式回复
        raw = router.chat(
            messages=[{"role": "user", "content": prompt}],
            system="你是一个善于设计开放式讨论的专家。",
            max_tokens=4000,
            temperature=0.5,
        )

        tweaks = {}
        for line in raw.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 1)
                key = parts[0].strip().lstrip("1234.- ")
                tweaks[key] = parts[1].strip()

        agents = []
        for aid, name, emoji, color in PersonaGenerator.PARTICIPANT_NAMES:
            tweak = tweaks.get(name, "")
            style = PersonaGenerator.SHARED_STYLE
            if tweak:
                style += f"\n启动提醒：{tweak}"
            agents.append(DebaterAgent(
                agent_id=aid,
                name=name,
                personality="善于深度思考、批判性分析和建设性对话",
                style=style,
                emoji=emoji,
                color=color,
            ))
        return agents
