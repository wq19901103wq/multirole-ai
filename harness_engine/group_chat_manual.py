from typing import List, Any, Optional
import time
import logging

from core.message import Message, Role
from tools.react_engine import run_with_tool_fallback


def build_context(
    round_num: int,
    topic_text: str,
    prev_summary: Optional[str],
    full_history: Optional[List[Message]] = None,
) -> str:
    lines = [f"=== 核心议题 ===\n{topic_text}"]

    # 共识模式下，如果历史较多，提炼关键交锋点
    if full_history and len(full_history) > 5:
        lines.append("\n=== 前面轮次的关键讨论 ===")
        # 提取每轮 moderator 摘要 + 最后一个 debater 的收尾观点
        seen_rounds = set()
        for msg in full_history:
            if msg.is_moderation:
                rnd = msg.metadata.get("round", 0)
                if rnd not in seen_rounds:
                    seen_rounds.add(rnd)
                    lines.append(f"第 {rnd} 轮总结：{msg.content[:100]}...")
    elif prev_summary:
        lines.append(f"\n=== 上轮核心摘要 ===\n{prev_summary}")

    lines.append(f"\n当前是第 {round_num} 轮。请严格遵循议题锚定规则发言。")
    return "\n".join(lines)


def run_manual_round(
    router,
    topic_anchor,
    checkpoint,
    round_num: int,
    participants: List[Any],
    moderator_spec: Any,
    topic_text: str,
    prev_summary: Optional[str],
    on_message=None,
    full_history: Optional[List[Message]] = None,
) -> List[Message]:
    logger = logging.getLogger(__name__)

    messages: List[Message] = []
    context = build_context(round_num, topic_text, prev_summary, full_history)

    logger.info(f"[Round {round_num}] 开始讨论，话题: {topic_text[:50]}...")
    logger.info(f"[Round {round_num}] 参与者数量: {len(participants)}")

    for i, spec in enumerate(participants):
        system = topic_anchor.inject_prompt(spec.name, "", spec.style)
        logger.info(
            f"[Round {round_num}] Agent {i + 1}/{len(participants)} ({spec.name}) 开始生成..."
        )

        # 构建对话历史：当前 Agent 能看到前面所有 Agent 的发言
        conversation = [{"role": "user", "content": context}]
        for prev_msg in messages:
            if prev_msg.is_moderation:
                continue
            conversation.append(
                {
                    "role": "assistant",
                    "content": f"{prev_msg.sender_name}: {prev_msg.content}",
                }
            )

        start_time = time.time()
        raw = run_with_tool_fallback(
            router,
            system_prompt=system,
            conversation=conversation,
            max_iterations=2,
            max_tokens=4000,
            temperature=0.7,
        )
        # 如果返回空内容或错误，重试一次（直接 LLM，跳过工具）
        if not raw or raw.startswith("【错误:") or len(raw.strip()) < 20:
            logger.warning(
                f"[Round {round_num}] Agent {spec.name} 首次生成异常（长度={len(raw)}），重试..."
            )
            raw = router.chat(
                messages=conversation,
                system=system,
                max_tokens=4000,
                temperature=0.7,
            )
        elapsed = time.time() - start_time
        logger.info(
            f"[Round {round_num}] Agent {spec.name} 生成完成，耗时 {elapsed:.2f}s，内容长度: {len(raw)}"
        )

        relevance = topic_anchor.extract_relevance(raw)
        msg = Message(
            role=Role.ASSISTANT,
            content=raw,
            sender_id=spec.agent_id,
            sender_name=spec.name,
            metadata={
                "relevance_score": relevance,
                "type": "response",
                "round": round_num,
            },
        )
        messages.append(msg)
        if on_message:
            on_message(msg)

        # 添加短暂延迟避免并发问题
        time.sleep(0.1)

    ck = checkpoint.check(topic_anchor.topic, messages)
    mod_content = ck["summary"]
    mod_msg = Message(
        role=Role.MODERATOR,
        content=mod_content,
        sender_id=moderator_spec.agent_id,
        sender_name=moderator_spec.name,
        metadata={
            "type": "moderation",
            "drift_detected": ck["drift_detected"],
            "round": round_num,
        },
    )
    messages.append(mod_msg)
    if on_message:
        on_message(mod_msg)
    return messages
