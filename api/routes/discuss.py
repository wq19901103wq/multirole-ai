"""Discussion routes."""

import logging
import time
from flask import Blueprint, request, jsonify

from api import state

logger = logging.getLogger(__name__)
discuss_bp = Blueprint('discuss', __name__)


@discuss_bp.route('/v1/discuss', methods=['POST'])
def discuss():
    """
    统一讨论接口
    ---
    tags:
      - Discussion
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
              example: "人工智能会取代程序员吗？"
            session_id:
              type: string
              example: "default"
            max_rounds:
              type: integer
              example: 2
            force_manual:
              type: boolean
              example: false
    responses:
      200:
        description: 讨论结果
        schema:
          type: object
          properties:
            events:
              type: array
            session_id:
              type: string
    """
    start_time = time.time()

    data = request.json or {}
    user_message = state.web_adapter.extract_user_message(data)
    session_id = state.web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2)
    force_manual = data.get("force_manual", False)

    logger.info(f"=" * 60)
    logger.info(f"[DISCUSS] 收到请求: session={session_id}, max_rounds={max_rounds}")
    logger.info(f"[DISCUSS] 用户消息: {user_message[:100]}...")

    if not user_message:
        logger.warning("[DISCUSS] 错误: 缺少 message 参数")
        return jsonify({"error": "message is required"}), 400

    try:
        logger.info("[DISCUSS] 开始运行讨论...")
        events = state.session_manager.run_discussion(
            session_id=session_id,
            user_message=user_message,
            max_rounds=max_rounds,
            force_manual=force_manual,
        )

        elapsed = time.time() - start_time
        logger.info(f"[DISCUSS] 讨论完成，生成 {len(events)} 个事件，耗时 {elapsed:.2f}s")

        rendered = state.web_adapter.render_events(events)
        logger.info(f"[DISCUSS] 渲染完成，返回 {len(rendered)} 个事件")
        logger.info(f"=" * 60)

        return jsonify({
            "events": rendered,
            "session_id": session_id,
        })
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[DISCUSS] 讨论失败: {e}, 耗时 {elapsed:.2f}s")
        logger.exception(e)
        return jsonify({"error": str(e)}), 500


@discuss_bp.route('/v1/discuss/consensus', methods=['POST'])
def discuss_consensus():
    """
    共识讨论接口：持续多轮讨论直到达成一致或达到上限
    ---
    tags:
      - Discussion
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
              example: "远程工作是否值得推广？"
            session_id:
              type: string
              example: "default"
            max_rounds:
              type: integer
              example: 10
            force_manual:
              type: boolean
              example: false
    responses:
      200:
        description: 讨论结果（含 consensus_reached 标记）
    """
    data = request.json or {}
    user_message = state.web_adapter.extract_user_message(data)
    session_id = state.web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 10)
    force_manual = data.get("force_manual", False)

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    events = state.session_manager.run_discussion_consensus(
        session_id=session_id,
        user_message=user_message,
        max_rounds=max_rounds,
        force_manual=force_manual,
    )

    rendered = state.web_adapter.render_events(events)
    return jsonify({
        "events": rendered,
        "session_id": session_id,
    })
