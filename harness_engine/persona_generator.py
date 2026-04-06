from typing import List, Dict
from .agents.debater import DebaterAgent


class PersonaGenerator:
    """
    根据话题动态生成 4 个 DebaterAgent 的角色配置。

    核心思想：固定 4 个功能视角不变（框架、专业/执行、数据、表达），
    但第 2 个"专业/执行"视角的具体身份会根据话题类型动态匹配，
    避免工程师去讨论爱情、文案师去讨论架构的错位问题。
    """

    # 关键词 -> 角色配置的映射
    DOMAIN_KEYWORDS: Dict[str, Dict] = {
        "tech": {
            "keywords": ["代码", "程序", "技术", "工程", "系统", "架构", "算法", "开发", "软件", "硬件", "数据库", "前端", "后端", "ai", "人工智能", "机器学习", "python", "java", "云", "服务器", "网络安全"],
            "agent": {
                "agent_id": "engineer",
                "name": "工程师",
                "personality": "技术专家，关注实现细节和系统可行性",
                "style": "务实直接，给出可落地的技术方案或代码思路",
                "emoji": "👨‍💻",
                "color": "#4ECDC4",
            },
        },
        "business": {
            "keywords": ["商业", "市场", "产品", "运营", "用户", "增长", "营销", "品牌", "销售", "商业模式", "盈利", "获客", "转化", "客户", "竞争", "战略", "创业", "投资", "融资"],
            "agent": {
                "agent_id": "operator",
                "name": "运营专家",
                "personality": "商业嗅觉敏锐，关注用户需求和商业模式",
                "style": "从市场验证、资源整合和落地执行角度分析",
                "emoji": "🚀",
                "color": "#FF9F43",
            },
        },
        "social": {
            "keywords": ["社会", "文化", "心理", "教育", "伦理", "家庭", "婚姻", "婚恋", "人际关系", "情感", "价值观", "哲学", "历史", "艺术", "文学", "政治", "阶层", "性别", "代际", "传统", "习俗", "年轻人", "恋爱", "家庭关系"],
            "agent": {
                "agent_id": "practitioner",
                "name": "实践者",
                "personality": "关注社会现象和真实人群的行为模式",
                "style": "从日常生活经验、社会案例或教育实践出发，避免空谈理论",
                "emoji": "🌱",
                "color": "#A8E6CF",
            },
        },
        "policy": {
            "keywords": ["政策", "法律", "法规", "政府", "监管", "合规", "税收", "劳动法", "知识产权", "隐私", "数据保护", "行业标准", "公共治理", "宏观调控", "国际关系", "外交"],
            "agent": {
                "agent_id": "policy_analyst",
                "name": "政策分析师",
                "personality": "熟悉政策环境和法律框架",
                "style": "从制度设计、合规风险和公共利益角度分析",
                "emoji": "⚖️",
                "color": "#74B9FF",
            },
        },
        "design": {
            "keywords": ["设计", "用户体验", "ui", "ux", "交互", "视觉", "美学", "创意", "广告", "包装", "空间", "建筑", "工业设计", "材质", "色彩", "排版", "app", "界面", "用户界面"],
            "agent": {
                "agent_id": "designer",
                "name": "设计师",
                "personality": "关注用户体验和视觉表达",
                "style": "从人本设计、可用性和美学原则出发，给出具体设计思路",
                "emoji": "🎨",
                "color": "#FD79A8",
            },
        },
    }

    # 默认角色（当没有明显领域特征时使用）
    DEFAULT_SPECIALIST = {
        "agent_id": "specialist",
        "name": "领域实践者",
        "personality": "具备跨领域常识，关注问题的可执行性和现实约束",
        "style": "从落地执行和实际操作角度提出见解，避免过度抽象",
        "emoji": "🔧",
        "color": "#95A5A6",
    }

    @classmethod
    def detect_domain(cls, topic_text: str) -> str:
        """根据话题文本匹配最合适的领域"""
        text = topic_text.lower()
        scores = {}
        for domain, config in cls.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in config["keywords"] if kw.lower() in text)
            if score > 0:
                scores[domain] = score
        if not scores:
            return "default"
        return max(scores, key=scores.get)

    @classmethod
    def generate(cls, topic_text: str) -> List[DebaterAgent]:
        """生成 4 个动态匹配的 DebaterAgent"""
        domain = cls.detect_domain(topic_text)
        specialist = cls.DOMAIN_KEYWORDS.get(domain, {}).get("agent", cls.DEFAULT_SPECIALIST)

        return [
            DebaterAgent(
                agent_id="planner",
                name="规划师",
                personality="善于分析需求、拆解任务、制定框架",
                style="条理清晰，先把问题拆成几个维度再逐个分析",
                emoji="👤",
                color="#FF6B6B",
            ),
            DebaterAgent(
                agent_id=specialist["agent_id"],
                name=specialist["name"],
                personality=specialist["personality"],
                style=specialist["style"],
                emoji=specialist["emoji"],
                color=specialist["color"],
            ),
            DebaterAgent(
                agent_id="analyst",
                name="分析师",
                personality="数据驱动，善于发现洞察和验证假设",
                style="用数据、案例或逻辑推演说话，理性客观",
                emoji="📊",
                color="#45B7D1",
            ),
            DebaterAgent(
                agent_id="writer",
                name="表达者",
                personality="文字工作者，善于总结、提炼和传播观点",
                style="简洁有力，把复杂观点转化成易懂的语言，注意受众感受",
                emoji="📝",
                color="#96CEB4",
            ),
        ]
