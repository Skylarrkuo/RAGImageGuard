# ============================================================
# 景区图片合规检查 + AI 改图 — Flask API 后端
# 启动：python app.py
# API 文档：http://localhost:8001/api/config-check
# ============================================================

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS

from config.settings import settings
from core.logging import setup_logging
from routes import register_all_blueprints


def create_app() -> Flask:
    """应用工厂函数"""
    setup_logging()

    app = Flask(__name__)

    # 上传大小限制（防止 OOM）
    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_UPLOAD_MB * 1024 * 1024

    # CORS 配置 — 仅允许可信来源
    allowed = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    CORS(app, origins=allowed)

    # API Key 认证中间件（配置了 API_KEY 时生效）
    @app.before_request
    def _check_api_key():
        if settings.API_KEY:
            # 仅保护业务 API，放行健康检查和图片服务
            if request.path.startswith("/api/config-check") or request.path.startswith("/images"):
                return
            key = request.headers.get("X-API-Key", "")
            if key != settings.API_KEY:
                return jsonify({"error": "未授权：缺少或无效的 API Key"}), 401

    register_all_blueprints(app)

    # ---- 全局异常处理 ----
    from core.logging import logger as _logger

    @app.errorhandler(413)
    def _handle_413(e):
        return jsonify({"error": f"文件大小超过限制（{settings.MAX_UPLOAD_MB}MB）"}), 413

    @app.errorhandler(404)
    def _handle_404(e):
        return jsonify({"error": "资源不存在"}), 404

    @app.errorhandler(500)
    def _handle_500(e):
        _logger.error(f"服务器内部错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500

    @app.errorhandler(Exception)
    def _handle_exception(e):
        _logger.exception(f"未捕获异常: {type(e).__name__}: {e}")
        return jsonify({"error": f"服务器错误: {type(e).__name__}"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("景区图片合规检查 Flask API")
    print("API 端点: http://localhost:8001/api/config-check")
    print("前端开发: cd frontend && npm run dev")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8001, debug=True)
