"""Feishu adapter routes."""

from flask import Blueprint, request, jsonify

from api import state

feishu_bp = Blueprint('feishu', __name__)


@feishu_bp.route('/v1/feishu/discuss', methods=['POST'])
def feishu_discuss():
    """
    飞书机器人统一讨论接口
    ---
    tags:
      - Discussion
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: 飞书交互卡片
    """
    data = request.json or {}
    user_message = state.feishu_adapter.extract_user_message(data)
    session_id = state.feishu_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2) if "max_rounds" in data else 2
    force_manual = data.get("force_manual", False)

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    events = state.session_manager.run_discussion(
        session_id=session_id,
        user_message=user_message,
        max_rounds=max_rounds,
        force_manual=force_manual,
    )

    rendered = state.feishu_adapter.render_events(events)
    return jsonify(rendered)
