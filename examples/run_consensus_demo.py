#!/usr/bin/env python3
"""
本地模拟：共识驱动多轮讨论效果演示（深度版）
使用 MockProvider 预设长文本对话内容，展示 4 位思考者从分歧到共识的完整深度讨论过程。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_router.providers.base import LLMProvider
from model_router.router import ModelRouter
from harness_engine.engine import HarnessEngine
from core.topic import Topic


class DemoProvider(LLMProvider):
    """为演示定制的 Mock Provider，模拟渐进式深度达成共识"""

    def __init__(self):
        self.call_log = []

    @property
    def name(self) -> str:
        return "mock/demo"

    def _get_round_idx(self, current_idx: int) -> int:
        """排除 persona generator 的首次调用后，计算当前属于第几轮（0-based）"""
        total = current_idx - 1  # 减去 persona generator 的 call 0
        return max(0, total) // 6

    def chat_completion(self, messages, system="", max_tokens=500, temperature=0.5, **kwargs):
        current_idx = len(self.call_log)
        self.call_log.append({"system": system[:80], "messages_count": len(messages)})

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
                '  "consensus_summary": "远程工作值得推广，最佳形式是有管理的混合办公",\n'
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
                    f"本轮讨论中，四位思考者分别从人才流动性、团队凝聚力、制度设计和成本效率四个维度展开了深入阐述。"
                    f"虽然立场各有侧重，但已经开始出现交叉与呼应——例如对‘混合办公’的提及表明分歧并非不可调和。"
                    f"目前的交锋点集中在‘远程’与‘集中’的边界应如何划定，共识尚未完全形成，需要进一步探讨。"
                )
            return (
                f"第 {round_num} 轮主持人总结：\n"
                f"经过深入交流，四位思考者的观点明显收敛。大家一致认为：单纯的‘全远程’或‘全集中’都不是最优解，"
                f"‘有管理的混合办公’才是可行路径。此外，配套的管理机制、数字化工具和绩效评估体系被共同认定为落地的关键基础设施。"
                f"讨论已经从分歧走向了基本一致。"
            )

        # Agent 发言模拟
        round_idx = self._get_round_idx(current_idx)
        call_num_in_round = max(0, current_idx - 1) % 6
        speaker_idx = min(call_num_in_round, 3)

        responses = self._agent_responses(round_idx)
        return responses[speaker_idx]

    def _agent_responses(self, round_idx):
        if round_idx == 0:
            return [
                "我认为远程工作的核心价值在于它彻底解构了传统雇佣关系中的地理刚性。"
                "从宏观层面看，全球化人才市场因此得以真正形成：企业不再局限于本地招聘，"
                "个体也不再因为居住城市的机会匮乏而被迫迁徙。"
                "这种解构带来的不仅是成本节约，更是一种人力资源配置效率的质变。"
                "当然，这并不意味着远程工作没有代价，而是说它的底层逻辑符合数字经济时代对灵活性和最优匹配的追求。"
                "如果我们把视角拉远，远程工作实际上是在用技术替代空间约束，这是一个不可逆的趋势。\n\n以上观点与核心议题的相关性：9/10",

                "但我对此持保留态度。长期远程办公最大的隐患在于‘社会资本’的流失。"
                "组织行为学的研究反复证明，非正式的面对面互动是创新火花最主要的发生场景。"
                "当团队成员只在视频会议中见面，那种走廊里的偶遇、午餐时的闲聊、白板前的即兴碰撞都会大幅减少。"
                "短期看，远程工作提升了效率；长期看，它可能侵蚀组织的创新能力和文化凝聚力。"
                "更严重的是，新员工如果从未体验过办公室的社群氛围，他们对组织的归属感和忠诚度会显著下降。"
                "这不是简单的‘个人偏好’问题，而是关系到组织可持续竞争力的结构性风险。\n\n以上观点与核心议题的相关性：8/10",

                "其实，我们不应该把这个问题二元对立起来。远程工作和集中办公并不是非此即彼的选择，"
                "关键在于企业如何设计混合办公制度。很多跨国公司的实践已经表明，‘核心日集中+弹性日远程’的混合模式可以兼顾两者的优势。"
                "制度设计的核心在于：哪些工作适合异步远程完成，哪些任务必须依赖同步协作。"
                "例如，深度思考型工作适合远程，而创意风暴和战略对齐则更适合面对面。"
                "如果企业能够建立清晰的协作协议、沟通节奏和成果评估标准，远程工作的负面效应是可以被制度所对冲的。"
                "因此，问题的答案不应该是‘要不要远程’，而应该是‘如何科学地远程’。\n\n以上观点与核心议题的相关性：9/10",

                "我想补充一个现实维度的考量：成本。对于企业而言，远程办公意味着办公场地租赁费用的显著下降，"
                "尤其是一线城市的高昂写字楼租金；对于员工而言，通勤成本和时间损耗被大幅削减，"
                "这部分隐性收益往往被低估。有研究显示，平均每个远程员工每年可以节省约 200 小时的通勤时间，"
                "这些时间如果被有效利用，无论是用于工作还是生活，都会提升整体社会福利。"
                "当然，这也要求企业在远程协作工具、网络安全和员工心理健康支持上追加投入。"
                "只有当成本收益的账算清楚了，我们才能判断远程工作是否‘值得’推广。"
                "从目前的实证数据来看，综合成本优势是存在的，但前提是有配套投入。\n\n以上观点与核心议题的相关性：8/10",
            ]
        elif round_idx == 1:
            return [
                "听了大家的观点，我觉得有一个可以整合的共识正在浮现。"
                "思考者一强调了远程工作的人才配置效率，思考者二则指出了社会资本流失的风险。"
                "这两者之间的矛盾，其实可以通过‘核心日聚集+其余日远程’的混合模式来缓解。"
                "具体来说：每周设定 2-3 个核心日用于面对面协作、团队建设和创意碰撞，"
                "其余时间允许员工远程完成深度工作。这样既保留了对创新至关重要的非正式互动，"
                "又赋予了员工足够的灵活性。更进一步，企业可以根据职能特点差异化设定混合比例："
                "研发团队可能需要更多的共处时间，而客户服务或内容创作团队则可以更高比例远程。"
                "混合办公不是一刀切，而是精细化的人力资源管理策略。\n\n以上观点与核心议题的相关性：9/10",

                "我非常同意思考者一的整合思路。混合模式确实是一个更高阶的解决方案。"
                "但我想进一步指出：如果混合办公缺乏数字化基础设施和管理机制的支撑，它很容易流于形式。"
                "例如，如果企业的项目管理依然依赖线下口头沟通，那么远程日就会变成信息孤岛；"
                "如果绩效评估还是以‘工时’和‘在场’为标准，那么远程员工会面临隐形的不公平。"
                "因此，推广混合办公的前提是企业必须完成数字化转型：统一的协作平台、清晰的文档规范、"
                "基于成果的 OKR 体系，以及定期的全员对齐会议。没有这些制度配套，混合办公只会带来混乱而不是效率。\n\n以上观点与核心议题的相关性：9/10",

                "对的，成本和效率的优势在混合模式下依然成立，而且团队的归属感也更容易维持。"
                "从成本角度看，混合办公可以让企业压缩办公面积，采用‘共享工位’模式，"
                "进一步降低固定成本；从效率角度看，员工可以把需要深度专注的任务安排在远程日，"
                "把需要协作的任务安排在核心日，实现时间管理的优化。"
                "更重要的是，混合模式保留了‘办公室作为社交场所’的功能，让员工仍然有实体归属感，"
                "这直接回应了思考者二关于社会资本流失的担忧。"
                "我认为，混合办公不仅是可行的，而且很可能是未来十年最主流的工作形态。\n\n以上观点与核心议题的相关性：9/10",

                "我的回应和思考者三类似，但我想补充一个关键的管理细节：绩效评估体系的重建。"
                "在远程或混合环境下，传统的‘管理者在场监督’模式彻底失效，"
                "必须转向以结果为导向的评估体系。这意味着管理者需要学会设定清晰可衡量的目标、"
                "建立定期的反馈机制，以及培养更强的异步沟通能力。"
                "此外，企业还需要关注员工的心理健康：远程工作带来的孤独感和工作-生活边界模糊是真实存在的。"
                "提供心理咨询、虚拟团建和强制休假政策，都是必要的配套措施。"
                "总而言之，远程工作值得推广，但它需要一个完整的管理生态系统来支撑。\n\n以上观点与核心议题的相关性：9/10",
            ]
        else:
            return [
                "综合前面所有讨论，我想做一个系统性的总结。"
                "远程工作的推广与否，本质上是一个制度设计问题，而不是一个简单的‘好’或‘坏’的判断。"
                "从人才效率、成本优化和员工福祉三个维度来看，远程工作具备显著的比较优势；"
                "而团队凝聚力下降和创新火花减少的风险，则可以通过‘有管理的混合办公’来有效对冲。"
                "最佳路径是：以混合办公为默认形态，以数字化工具和绩效评估体系为基础设施，"
                "以员工心理健康支持为文化保障。只有这样，远程工作才能真正释放其潜在价值。"
                "因此，我的最终判断是：远程工作值得推广，但推广的前提是建立配套的管理机制。\n\n以上观点与核心议题的相关性：10/10",

                "我完全赞同思考者一的系统性总结。这实际上也是我们多轮讨论后逐渐收敛到的核心共识。"
                "人才效率、成本控制、团队凝聚力这三者并非不可调和，"
                "‘有管理的混合办公’为它们提供了一个可以共存的框架。"
                "同时，数字化工具和清晰的绩效评估制度被反复验证为成功的关键基础设施。"
                "我没有什么需要补充的质疑，而是非常认可这个结论的完整性和现实可操作性。\n\n以上观点与核心议题的相关性：10/10",

                "我也认同这个最终结论。回顾整个讨论，我们从最初的‘效率 vs 凝聚力’的二元张力，"
                "逐步过渡到了‘混合办公+制度配套’的整合框架。这是一个典型的辩证法过程："
                "正题（远程效率高）、反题（远程损害社会资本）、合题（混合办公+管理机制）。"
                "远程工作值得推广，但推广的方式必须是科学的、分阶段的、有制度保障的。\n\n以上观点与核心议题的相关性：10/10",

                "我想正式宣布我们达成了共识：远程工作值得推广，最佳形态是‘有管理的混合办公’。"
                "这个共识包含了三个子命题：第一，混合办公是兼顾效率与凝聚力的最优解；"
                "第二，数字化工具、绩效评估和心理健康支持是落地的必要基础设施；"
                "第三，不同职能应根据工作性质差异化设定远程比例。"
                "这一结论既有理论依据，也有大量企业实践的支撑，具有较强的现实指导意义。"
                "感谢各位思考者的深入交流和建设性对话。\n\n以上观点与核心议题的相关性：10/10",
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
