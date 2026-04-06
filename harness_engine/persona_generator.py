from typing import List, Optional
from .agents.debater import DebaterAgent


class PersonaGenerator:
    """
    根据话题动态生成最自然的讨论维度，而不是硬套固定职业角色。

    核心思想：
    - 很多话题不需要"工程师"、"数据分析师"或"文案师"
    - 角色的存在是为了提供视角多样性，但视角必须贴合话题本身
    - 因此我们先分析话题的"自然讨论维度"，每个维度就是一个 Agent
    """

    @staticmethod
    def generate(topic_text: str, router=None) -> List[DebaterAgent]:
        """
        生成动态的、贴合话题的讨论角色。

        如果有 router（含真实 LLM），优先用 LLM 分析话题维度；
        如果没有 router，使用基于关键词的本地规则作为 fallback。
        """
        if router is not None:
            try:
                return PersonaGenerator._generate_by_llm(topic_text, router)
            except Exception:
                pass
        return PersonaGenerator._generate_by_rules(topic_text)

    @staticmethod
    def _generate_by_llm(topic_text: str, router) -> List[DebaterAgent]:
        """调用 LLM 分析话题最适合的 3-4 个讨论维度"""
        prompt = f"""请分析下面这个话题，指出最适合从哪3-4个不同的角度/维度进行深入讨论。

要求：
1. 每个角度必须是该话题的**自然思考维度**，不要生搬硬套固定职业角色
2. 如果话题不需要数据支撑，就不要出现"数据分析"角度
3. 如果话题不需要技术，就不要出现"技术"角度
4. 直接用该话题的内在维度命名，比如"社会变迁"、"个体心理"、"经济影响"、"伦理边界"、"历史演变"、"实践可行性"等
5. 每个角度的描述要简洁，说明这个角度会关注什么
6. 输出格式严格如下，每行一个角度，不要有多余内容：
角度名|角度描述

话题：{topic_text}
"""
        raw = router.chat(
            messages=[{"role": "user", "content": prompt}],
            system="你是一个善于多角度分析问题的思维框架专家。",
            max_tokens=300,
            temperature=0.3,
        )
        return PersonaGenerator._parse_llm_output(topic_text, raw)

    @staticmethod
    def _parse_llm_output(topic_text: str, raw: str) -> List[DebaterAgent]:
        """解析 LLM 返回的角度列表，生成 DebaterAgent"""
        agents = []
        emojis = ["👤", "🌿", "📐", "🔍", "💡", "🪞"]
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FDCB6E", "#A29BFE"]

        lines = [line.strip() for line in raw.strip().split("\n") if line.strip() and "|" in line]

        for idx, line in enumerate(lines[:4]):
            parts = line.split("|", 1)
            name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""

            # 清理可能的序号前缀
            name = name.lstrip("1234.- ")

            agent_id = f"angle_{idx}"
            agents.append(DebaterAgent(
                agent_id=agent_id,
                name=name,
                personality=desc or f"从{name}的角度深入思考",
                style=f"你是{name}视角的发言人。你的任务是从{name}切入，直接回应该议题。不要套用不相关的专业术语，如果该角度与话题关联较弱，就从普通人的常识逻辑出发。",
                emoji=emojis[idx % len(emojis)],
                color=colors[idx % len(colors)],
            ))

        if not agents:
            raise ValueError("LLM 未返回有效的讨论维度")

        return agents

    @staticmethod
    def _generate_by_rules(topic_text: str) -> List[DebaterAgent]:
        """无 LLM 时的本地规则 fallback，基于关键词匹配常见维度"""
        text = topic_text.lower()

        # 定义常见维度及其触发关键词
        dimension_keywords = {
            "技术实现": ["代码", "程序", "技术", "工程", "系统", "架构", "算法", "开发", "软件", "硬件", "数据库", "前端", "后端", "ai", "人工智能", "机器学习", "python", "java", "云", "服务器", "网络安全"],
            "经济影响": ["商业", "市场", "产品", "运营", "用户", "增长", "营销", "品牌", "销售", "商业模式", "盈利", "获客", "转化", "客户", "竞争", "战略", "创业", "投资", "融资", "成本", "价格", "收入"],
            "社会影响": ["社会", "文化", "心理", "教育", "伦理", "家庭", "婚姻", "婚恋", "人际关系", "情感", "价值观", "哲学", "历史", "艺术", "文学", "政治", "阶层", "性别", "代际", "传统", "习俗", "年轻人", "恋爱", "家庭关系"],
            "政策法规": ["政策", "法律", "法规", "政府", "监管", "合规", "税收", "劳动法", "知识产权", "隐私", "数据保护", "行业标准", "公共治理", "宏观调控", "国际关系", "外交"],
            "个体体验": ["个人", "体验", "感受", "情绪", "健康", "生活质量", "幸福感", "压力", "焦虑", "自我", "成长", "选择", "自由", "权利", "隐私"],
            "实践落地": ["怎么做", "方法", "步骤", "落地", "执行", "操作", "方案", "计划", "建议", "指南", "教程", "最佳实践"],
        }

        matched = []
        for dim_name, keywords in dimension_keywords.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > 0:
                matched.append((dim_name, score))

        # 按匹配分数排序
        matched.sort(key=lambda x: x[1], reverse=True)
        selected = [m[0] for m in matched]

        # 如果没有明显匹配，使用一组通用维度
        if not selected:
            selected = ["核心逻辑", "现实约束", "不同立场", "综合建议"]

        # 补充通用维度，确保总有 3-4 个自然角度
        generic_dims = ["关键权衡", "实际影响", "潜在风险", "不同立场"]
        for g in generic_dims:
            if len(selected) >= 4:
                break
            if g not in selected:
                selected.append(g)

        emojis = ["👤", "🌿", "📐", "🔍", "💡", "🪞"]
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FDCB6E", "#A29BFE"]

        agents = []
        for idx, dim_name in enumerate(selected[:4]):
            agents.append(DebaterAgent(
                agent_id=f"angle_{idx}",
                name=dim_name,
                personality=f"从{dim_name}的角度深入思考该议题",
                style=f"你是{dim_name}视角的发言人。你的任务是从{dim_name}切入，直接回应该议题。不要套用不相关的专业术语，如果该角度与话题关联较弱，就从普通人的常识逻辑出发。",
                emoji=emojis[idx % len(emojis)],
                color=colors[idx % len(colors)],
            ))

        return agents
