"""Health check and system routes."""

from flask import Blueprint, jsonify

from api import state

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health():
    """
    健康检查
    ---
    tags:
      - System
    responses:
      200:
        description: 服务状态
    """
    return jsonify({
        "status": "ok",
        "autogen_installed": state.engine.router.default_provider is not None,
    })


@health_bp.route('/swagger-ui')
def swagger_ui():
    """兼容旧版 Swagger UI 重定向"""
    return jsonify({"swagger_url": "/apidocs/", "flasgger": True})


HTML_DEMO = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Multirole AI - Harness Engine Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; height: 100vh; display: flex; flex-direction: column; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; max-width: 900px; margin: 0 auto; width: 100%; }
        .discussion-round { margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .round-title { font-size: 18px; font-weight: bold; color: #667eea; margin-bottom: 15px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        .message { margin-bottom: 12px; }
        .message-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
        .avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; }
        .role-name { font-weight: 600; font-size: 14px; }
        .message-content { background: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 3px solid; margin-left: 42px; line-height: 1.6; }
        .moderator-content { background: #fff8e1; }
        .consensus-content { background: #e8f5e9; font-weight: 500; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 8px; }
        .badge-drift { background: #ffebee; color: #c62828; }
        .badge-good { background: #e8f5e9; color: #2e7d32; }
        .input-area { background: white; padding: 20px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; max-width: 900px; margin: 0 auto; width: 100%; }
        .input-area textarea { flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; resize: none; font-size: 14px; min-height: 60px; }
        .btn { padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-secondary { background: #e0e0e0; color: #333; }
        .divider { margin: 10px 0; text-align: center; color: #999; font-size: 12px; }
        .links { text-align: center; padding: 10px; font-size: 12px; }
        .links a { color: #667eea; margin: 0 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Multirole AI - Harness Engine</h1>
        <p>分层架构：Adapters → Session → Harness(AutoGen) → ModelRouter → Kimi</p>
    </div>
    <div class="chat-container" id="chatContainer">
        <div class="discussion-round">
            <div class="round-title">💡 架构说明</div>
            <ul style="color: #666; line-height: 1.8; margin-left: 20px;">
                <li><b>Adapters</b>：前端适配层（Web / 飞书 / 微信 / 小程序）</li>
                <li><b>Session Layer</b>：会话状态管理与事件流转</li>
                <li><b>Harness Engine</b>：基于 AutoGen 的多代理协调（含防漂移）</li>
                <li><b>DriftGuard</b>：TopicAnchor + ModeratorCheckpoint + ContextTruncator</li>
                <li><b>Model Router</b>：统一路由 Kimi / OpenAI / Claude 等模型</li>
            </ul>
            <div class="links">
                <a href="/apidocs/" target="_blank">📘 Swagger API 文档</a>
                <a href="/swagger-ui" target="_blank">🔍 Swagger UI</a>
            </div>
        </div>
    </div>
    <div class="input-area">
        <textarea id="userInput" rows="2" placeholder="输入问题，发起多代理讨论..."></textarea>
        <button class="btn" id="sendBtn" onclick="startDiscussion()">发起讨论</button>
        <button class="btn btn-secondary" id="streamBtn" onclick="startStreamDiscussion()">实时流式讨论</button>
        <button class="btn btn-secondary" id="consensusBtn" onclick="startConsensusDiscussion()">🤝 共识讨论</button>
    </div>
    <script>
        async function startDiscussion() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('sendBtn');
            const msg = input.value.trim();
            if (!msg) return;
            btn.disabled = true; btn.textContent = '讨论中...'; input.value = '';
            const container = document.getElementById('chatContainer');
            const roundDiv = document.createElement('div');
            roundDiv.className = 'discussion-round';
            roundDiv.innerHTML = `<div class="round-title">🗣️ ${msg.substring(0,30)}...</div><div style="padding:20px;color:#666;">讨论中...</div>`;
            container.appendChild(roundDiv); container.scrollTop = container.scrollHeight;

            const res = await fetch('/v1/discuss', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg, max_rounds: 2})
            });
            const data = await res.json();
            roundDiv.innerHTML = `<div class="round-title">🗣️ ${msg.substring(0,30)}${msg.length>30?'...':''}</div>`;

            let currentRound = 0;
            data.events.forEach(evt => {
                if (evt.round !== currentRound) {
                    currentRound = evt.round;
                    const d = document.createElement('div');
                    d.className = 'divider'; d.textContent = `--- 第 ${currentRound} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                    roundDiv.appendChild(d);
                }
                appendEvent(roundDiv, evt);
            });
            btn.disabled = false; btn.textContent = '发起讨论'; container.scrollTop = container.scrollHeight;
        }

        function appendEvent(container, evt) {
            const isMod = evt.event_type === 'moderation';
            const isConsensus = evt.event_type === 'consensus';
            const meta = !isMod && !isConsensus && evt.relevance !== undefined
                ? `<span class="badge ${evt.relevance < 8 ? 'badge-drift' : 'badge-good'}">相关性 ${evt.relevance}/10</span>` : '';
            const div = document.createElement('div'); div.className = 'message';
            div.innerHTML = `
                <div class="message-header">
                    <div class="avatar" style="background:${evt.color}20;color:${evt.color};">${evt.emoji}</div>
                    <span class="role-name" style="color:${evt.color};">${evt.role_name}</span>${meta}
                </div>
                <div class="message-content ${isMod?'moderator-content':''} ${isConsensus?'consensus-content':''}" style="border-color:${evt.color};">${evt.content}</div>
            `;
            container.appendChild(div);
        }

        function startStreamDiscussion() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('streamBtn');
            const msg = input.value.trim();
            if (!msg) return;
            btn.disabled = true; btn.textContent = '流式讨论中...'; input.value = '';
            const container = document.getElementById('chatContainer');
            const roundDiv = document.createElement('div');
            roundDiv.className = 'discussion-round';
            roundDiv.innerHTML = `<div class="round-title">🗣️ ${msg.substring(0,30)}... (WebSocket 实时)</div>`;
            container.appendChild(roundDiv); container.scrollTop = container.scrollHeight;

            const ws = new WebSocket(`ws://${location.host}/v1/discuss/stream`);
            ws.onopen = () => {
                ws.send(JSON.stringify({message: msg, max_rounds: 2}));
            };
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.type === 'event') {
                    const evt = data.payload;
                    if (roundDiv.lastChild && roundDiv.lastChild.className === 'divider') {
                        const lastRoundText = roundDiv.lastChild.textContent;
                        const expected = `--- 第 ${evt.round} 轮`;
                        if (!lastRoundText.startsWith(expected)) {
                            const d = document.createElement('div');
                            d.className = 'divider';
                            d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                            roundDiv.appendChild(d);
                        }
                    } else {
                        const d = document.createElement('div');
                        d.className = 'divider';
                        d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                        roundDiv.appendChild(d);
                    }
                    appendEvent(roundDiv, evt);
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'done') {
                    btn.disabled = false; btn.textContent = '实时流式讨论';
                    ws.close();
                } else if (data.type === 'error') {
                    roundDiv.innerHTML += `<div style="color:red">错误: ${data.message}</div>`;
                    btn.disabled = false; btn.textContent = '实时流式讨论';
                    ws.close();
                }
            };
            ws.onerror = (err) => {
                roundDiv.innerHTML += `<div style="color:red">WebSocket 连接失败</div>`;
                btn.disabled = false; btn.textContent = '实时流式讨论';
            };
        }

        function startConsensusDiscussion() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('consensusBtn');
            const msg = input.value.trim();
            if (!msg) return;
            btn.disabled = true; btn.textContent = '共识讨论中...'; input.value = '';
            const container = document.getElementById('chatContainer');
            const roundDiv = document.createElement('div');
            roundDiv.className = 'discussion-round';
            roundDiv.innerHTML = `<div class="round-title">🤝 ${msg.substring(0,30)}... (共识模式)</div>`;
            container.appendChild(roundDiv); container.scrollTop = container.scrollHeight;

            const ws = new WebSocket(`ws://${location.host}/v1/discuss/consensus/stream`);
            ws.onopen = () => {
                ws.send(JSON.stringify({message: msg, max_rounds: 8}));
            };
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.type === 'event') {
                    const evt = data.payload;
                    if (evt.event_type === 'consensus') {
                        const d = document.createElement('div');
                        d.className = 'divider';
                        d.style.color = '#2e7d32';
                        d.style.fontWeight = 'bold';
                        d.textContent = '--- ✅ 达成共识 ---';
                        roundDiv.appendChild(d);
                        appendEvent(roundDiv, evt);
                        container.scrollTop = container.scrollHeight;
                        return;
                    }
                    if (roundDiv.lastChild && roundDiv.lastChild.className === 'divider') {
                        const lastRoundText = roundDiv.lastChild.textContent;
                        const expected = `--- 第 ${evt.round} 轮`;
                        if (!lastRoundText.startsWith(expected)) {
                            const d = document.createElement('div');
                            d.className = 'divider';
                            d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                            roundDiv.appendChild(d);
                        }
                    } else {
                        const d = document.createElement('div');
                        d.className = 'divider';
                        d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                        roundDiv.appendChild(d);
                    }
                    appendEvent(roundDiv, evt);
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'consensus_check') {
                    const d = document.createElement('div');
                    d.className = 'divider';
                    d.style.fontSize = '11px';
                    d.style.color = data.reached ? '#2e7d32' : '#999';
                    d.textContent = data.reached ? `--- 共识检测通过 (置信度 ${Math.round(data.confidence*100)}%) ---` : `--- 尚未达成共识 (置信度 ${Math.round(data.confidence*100)}%)，继续讨论 ---`;
                    roundDiv.appendChild(d);
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'timeout') {
                    roundDiv.innerHTML += `<div style="color:#c62828;padding:10px;">⏹ 已达到最大轮次，未能达成共识</div>`;
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'done') {
                    btn.disabled = false; btn.textContent = '🤝 共识讨论';
                    ws.close();
                } else if (data.type === 'error') {
                    roundDiv.innerHTML += `<div style="color:red">错误: ${data.message}</div>`;
                    btn.disabled = false; btn.textContent = '🤝 共识讨论';
                    ws.close();
                }
            };
            ws.onerror = (err) => {
                roundDiv.innerHTML += `<div style="color:red">WebSocket 连接失败</div>`;
                btn.disabled = false; btn.textContent = '🤝 共识讨论';
            };
        }
    </script>
</body>
</html>
"""


@health_bp.route('/')
def index():
    return HTML_DEMO
