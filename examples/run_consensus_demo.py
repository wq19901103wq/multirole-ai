#!/usr/bin/env python3
"""
本地模拟：共识驱动多轮讨论效果演示（深度版）
使用 MockProvider 预设长文本对话内容，支持任意话题，展示 4 位思考者从分歧到共识的完整深度讨论过程。
"""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_router.providers.base import LLMProvider
from model_router.router import ModelRouter
from harness_engine.engine import HarnessEngine
from core.topic import Topic


class DemoProvider(LLMProvider):
    """为演示定制的 Mock Provider，模拟渐进式深度达成共识，支持任意话题"""

    def __init__(self):
        self.call_log = []
        self.topic_text = "远程工作是否值得推广？"

    @property
    def name(self) -> str:
        return "mock/demo"

    def _extract_topic(self, messages, system="") -> str:
        """从 prompt 中尽可能提取当前讨论话题"""
        text = system + "\n" + "\n".join(m.get("content", "") for m in messages if isinstance(m, dict))
        # 匹配 核心议题："..." 或 核心议题: "..."
        m = re.search(r'核心议题[：:]\s*"([^"]+)"', text)
        if m:
            return m.group(1)
        # 匹配 话题：... 或 议题：...
        m = re.search(r'(?:话题|议题)[：:]\s*([^\n]+)', text)
        if m:
            return m.group(1).strip()
        return self.topic_text

    def _get_round_idx(self, current_idx: int) -> int:
        """排除 persona generator 的首次调用后，计算当前属于第几轮（0-based）"""
        total = current_idx - 1
        return max(0, total) // 6

    def chat_completion(self, messages, system="", max_tokens=500, temperature=0.5, **kwargs):
        current_idx = len(self.call_log)
        self.call_log.append({"system": system[:80], "messages_count": len(messages)})

        # 动态提取当前话题
        extracted = self._extract_topic(messages, system)
        if extracted and extracted != self.topic_text:
            self.topic_text = extracted

        # PersonaGenerator 的启动提醒生成
        if "设计开放式讨论的专家" in system:
            return (
                "思考者一|可以从宏观趋势和个体体验的冲突切入\n"
                "思考者二|注意检验前面观点中可能存在的隐含假设\n"
                "思考者三|尝试把不同立场整合成一个更完整的视角\n"
                "思考者四|关注观点落地时可能遇到的现实约束"
            )

        # 判断是否是共识检测调用
        is_consensus_call = (
            "讨论观察员" in (messages[0]["content"] if messages else "")
            or "共识和分歧的专家" in system
        )

        if is_consensus_call:
            round_idx = self._get_round_idx(current_idx)
            if round_idx < 2:
                return (
                    '{\n'
                    '  "consensus_reached": false,\n'
                    '  "consensus_summary": "",\n'
                    '  "disagreement_points": "各方观点仍有差异，需要继续讨论",\n'
                    '  "confidence": 0.3\n'
                    '}'
                )
            return (
                '{\n'
                '  "consensus_reached": true,\n'
                f'  "consensus_summary": "{self.topic_text}值得认真对待，最佳路径是在充分认识风险的前提下科学推进",\n'
                '  "disagreement_points": "",\n'
                '  "confidence": 0.95\n'
                '}'
            )

        # 判断是否是 moderator 调用
        if "主持人" in system or " moderator" in system.lower():
            round_idx = self._get_round_idx(current_idx)
            round_num = round_idx + 1
            if round_idx < 2:
                return (
                    f"第 {round_num} 轮主持人总结：\n"
                    f"本轮讨论中，四位思考者分别从宏观趋势、潜在风险、制度设计和成本效益四个维度对『{self.topic_text}』展开了深入阐述。"
                    f"虽然立场各有侧重，但已经开始出现交叉与呼应——例如对‘科学推进’和‘风险管理’的提及表明分歧并非不可调和。"
                    f"目前的交锋点集中在推进力度与风险控制的边界应如何划定，共识尚未完全形成，需要进一步探讨。"
                )
            return (
                f"第 {round_num} 轮主持人总结：\n"
                f"经过深入交流，四位思考者的观点明显收敛。大家一致认为：『{self.topic_text}』不能简单否定或盲目推进，"
                f"而应该在充分认识风险的前提下，通过科学的制度设计和管理机制来有序推进。"
                f"此外，配套的工具、评估体系和文化保障被共同认定为落地的关键基础设施。讨论已经从分歧走向了基本一致。"
            )

        # Agent 发言模拟
        round_idx = self._get_round_idx(current_idx)
        call_num_in_round = max(0, current_idx - 1) % 6
        speaker_idx = min(call_num_in_round, 3)

        responses = self._agent_responses(self.topic_text, round_idx)
        return responses[speaker_idx]

    def _agent_responses(self, topic: str, round_idx: int):
        if round_idx == 0:
            return [
                f"我认为『{topic}』的底层价值在于它代表了一种不可逆转的时代趋势。"
                f"从宏观层面看，技术演进和社会需求的相互作用使得这一方向具备了强大的内生动力。"
                f"企业和社会如果不主动适应，就可能在未来竞争中失去先机。"
                f"当然，这并不意味着我们可以忽视过程中的阵痛，而是说其长期价值大于短期调整成本。"
                f"如果我们把视角拉远，这实际上是一场关于效率和可持续性的深层变革，值得大力推进。\n\n以上观点与核心议题的相关性：9/10",

                f"但我对此持保留态度。在推进『{topic}』的过程中，最大的隐患在于对潜在风险的低估。"
                f"历史和实践反复证明，任何重大变革如果缺乏充分的风险评估和渐进式试点，都可能带来意想不到的负面后果。"
                f"短期看，它可能带来某些便利；长期看，如果配套机制没有跟上，可能侵蚀现有的稳定结构和信任基础。"
                f"更严重的是，如果相关群体从未经历过充分的过渡适应期，他们的抵触情绪和损失感会显著上升。"
                f"这不是简单的‘乐观 vs 悲观’问题，而是关系到整体系统可持续竞争力的结构性风险。\n\n以上观点与核心议题的相关性：8/10",

                f"其实，我们不应该把『{topic}』二元对立起来。支持或反对并不是非此即彼的选择，关键在于如何设计科学的推进路径。"
                f"很多先行者的实践已经表明，通过分阶段试点、动态评估和及时调整，可以在探索中兼顾收益与风险。"
                f"制度设计的核心在于：哪些场景适合先行突破，哪些领域需要谨慎观望。"
                f"例如，在条件成熟的区域或群体中率先试点，同时建立清晰的反馈机制和风险对冲预案，负面效应是可以被控制的。"
                f"因此，问题的答案不应该是‘要不要做’，而应该是‘如何科学地推进』。\n\n以上观点与核心议题的相关性：9/10",

                f"我想补充一个现实维度的考量：成本效益分析。对于推动『{topic}』的各方而言，"
                f"前期的投入和资源消耗往往被低估，而中长期的收益又常常被过度乐观地估算。"
                f"有研究显示，任何大规模变革的成功与否，很大程度上取决于利益相关方能否在短期内看到可感知的正向反馈。"
                f"如果只有投入没有可见产出，支持的联盟很容易瓦解。"
                f"当然，这也要求我们建立更完善的评估体系和沟通机制。只有当成本收益的账算清楚了，我们才能判断『{topic}』是否‘值得’推广。"
                f"从目前的实证数据来看，综合优势是存在的，但前提是有配套投入。\n\n以上观点与核心议题的相关性：8/10",
            ]
        elif round_idx == 1:
            return [
                f"听了大家的观点，我觉得有一个可以整合的共识正在浮现。"
                f"思考者一强调了『{topic}』的趋势价值，思考者二则指出了风险控制的必要性。"
                f"这两者之间的矛盾，其实可以通过‘试点先行+动态评估’的渐进模式来缓解。"
                f"具体来说：先在条件成熟的场景中进行可控试点，收集数据和反馈，再逐步扩大范围。"
                f"这样既保留了对大趋势的追逐，又为潜在风险设置了缓冲带。"
                f"更进一步，可以根据不同群体的接受度和准备度差异化设定推进节奏："
                f"准备充分的区域可以加快步伐，而基础薄弱的领域则需要更多的预热和配套支持。"
                f"推进『{topic}』不是一刀切，而是精细化的系统工程。\n\n以上观点与核心议题的相关性：9/10",

                f"我非常同意思考者一的整合思路。渐进模式确实是一个更高阶的解决方案。"
                f"但我想进一步指出：如果『{topic}』缺乏制度化和数字化基础设施的支撑，它很容易流于形式。"
                f"例如，如果评估体系依然依赖旧有的指标框架，那么新措施就会变成新瓶装旧酒；"
                f"如果沟通机制不透明，利益相关方会面临信息不对称的不公平感。"
                f"因此，推广『{topic}』的前提是必须完成配套机制的升级：清晰的目标设定、基于数据的反馈闭环、"
                f"定期的多方对齐会议，以及灵活的纠错机制。没有这些制度配套，任何创新只会带来混乱而不是进步。\n\n以上观点与核心议题的相关性：9/10",

                f"对的，效率和效益的优势在渐进模式下依然成立，而且各方的接受度也更容易维持。"
                f"从成本角度看，分阶段推进可以让投入分批释放，降低一次性资源压力；"
                f"从收益角度看，早期试点如果能快速产生正面案例，就会形成示范效应，为后续推广铺平道路。"
                f"更重要的是，渐进模式保留了‘在探索中学习’的空间，让参与者有安全感和参与感，"
                f"这直接回应了思考者二关于抵触情绪和信任流失的担忧。"
                f"我认为，『{topic}』不仅是可行的，而且很可能是未来发展趋势中的主流形态。\n\n以上观点与核心议题的相关性：9/10",

                f"我的回应和思考者三类似，但我想补充一个关键的管理细节：评估与反馈体系的建设。"
                f"在推进『{topic}』的过程中，传统的静态评估模式已经不够用了，必须转向动态、多维度的评估体系。"
                f"这意味着决策者需要学会设定阶段性里程碑、建立定期的利益相关方反馈机制，"
                f"以及培养更强的快速迭代能力。此外，还需要关注参与者的适应成本："
                f"任何变革都会带来学习曲线和心理压力，提供培训支持、透明沟通和合理过渡期都是必要的配套措施。"
                f"总而言之，『{topic}』值得推广，但它需要一个完整的管理生态系统来支撑。\n\n以上观点与核心议题的相关性：9/10",
            ]
        else:
            return [
                f"综合前面所有讨论，我想做一个系统性的总结。"
                f"『{topic}』的推广与否，本质上是一个制度设计和风险管理问题，而不是一个简单的‘好’或‘坏’的判断。"
                f"从长期价值、成本效益和社会接受度三个维度来看，它具备显著的比较优势；"
                f"而潜在的风险和阵痛，则可以通过‘有管理的渐进推进’来有效对冲。"
                f"最佳路径是：以科学试点为起点，以制度升级和数字化工具为基础设施，以透明沟通和利益相关方参与为文化保障。"
                f"只有这样，『{topic}』才能真正释放其潜在价值。因此，我的最终判断是：『{topic}』值得认真对待，但推广的前提是建立配套的管理机制。\n\n以上观点与核心议题的相关性：10/10",

                f"我完全赞同思考者一的系统性总结。这实际上也是我们多轮讨论后逐渐收敛到的核心共识。"
                f"趋势价值、风险控制和成本效益这三者并非不可调和，"
                f"‘有管理的渐进推进’为它们提供了一个可以共存的框架。"
                f"同时，制度配套和清晰的评估体系被反复验证为成功的关键基础设施。"
                f"我没有什么需要补充的质疑，而是非常认可这个结论的完整性和现实可操作性。\n\n以上观点与核心议题的相关性：10/10",

                f"我也认同这个最终结论。回顾整个讨论，我们从最初的‘价值 vs 风险’的二元张力，"
                f"逐步过渡到了‘渐进推进+制度配套’的整合框架。这是一个典型的辩证法过程："
                f"正题（具备长期价值）、反题（存在潜在风险）、合题（科学推进+完善配套）。"
                f"『{topic}』值得认真对待，但推进的方式必须是科学的、分阶段的、有制度保障的。\n\n以上观点与核心议题的相关性：10/10",

                f"我想正式宣布我们达成了共识：『{topic}』值得认真对待，最佳路径是‘在充分认识风险的前提下科学推进’。"
                f"这个共识包含了三个子命题：第一，不能简单否定或盲目推进，而要采取渐进策略；"
                f"第二，制度配套、数字化工具和评估反馈体系是落地的必要基础设施；"
                f"第三，不同群体和场景应根据准备度差异化设定推进节奏。"
                f"这一结论既有理论依据，也有实践支撑，具有较强的现实指导意义。感谢各位思考者的深入交流和建设性对话。\n\n以上观点与核心议题的相关性：10/10",
            ]


def main():
    provider = DemoProvider()
    router = ModelRouter(default_provider=provider)
    engine = HarnessEngine(router)

    topic = Topic(text="远程工作是否值得推广？")

    print("=" * 70)
    print("🤝 共识驱动多轮深度讨论 — 模拟演示")
    print("=" * 70)
    print(f"议题：{topic.text}\n")

    for turn in engine.run_until_consensus_stream(topic, max_rounds=5, force_manual=True):
        round_num = turn.metadata.get("round", 0)
        consensus_reached = turn.metadata.get("consensus_reached", False)

        if consensus_reached:
            print(f"\n{'='*70}")
            print(f"✅ 第 {round_num} 轮 · 达成共识")
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print(f"🗣️ 第 {round_num} 轮讨论")
            print(f"{'='*70}")

        for msg in turn.messages:
            if msg.is_moderation:
                print(f"\n🛡️ 【主持人】{msg.sender_name}:")
                print(f"   {msg.content}")
            elif msg.metadata.get("type") == "consensus":
                print(f"\n🤝 {msg.sender_name}:")
                print(f"   {msg.content}")
            else:
                rel = f" [相关性 {msg.relevance_score}/10]" if msg.relevance_score is not None else ""
                print(f"\n   {msg.sender_name}{rel}:")
                print(f"   → {msg.content}")

        if not consensus_reached and turn.drift_detected:
            print(f"\n⚠️ 漂移警告：{turn.drift_report}")

        if consensus_reached:
            print("\n" + "=" * 70)
            print("🎉 讨论顺利结束，所有 Agent 已达成一致！")
            print("=" * 70)
            break

    else:
        print("\n" + "=" * 70)
        print("⏹ 已达到最大轮次，未能达成共识")
        print("=" * 70)


if __name__ == '__main__':
    main()
