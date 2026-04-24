"""Route registration entry point."""

from .health import health_bp
from .discuss import discuss_bp
from .feishu import feishu_bp


def register_routes(app, sock=None):
    """Register all blueprints and WebSocket handlers with the Flask app."""
    app.register_blueprint(health_bp)
    app.register_blueprint(discuss_bp)
    app.register_blueprint(feishu_bp)

    if sock is not None:
        from .stream import discuss_stream, discuss_consensus_stream
        sock.route('/v1/discuss/stream')(discuss_stream)
        sock.route('/v1/discuss/consensus/stream')(discuss_consensus_stream)
