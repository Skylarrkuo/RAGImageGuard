"""系统路由 — 配置检查、图片服务"""

from pathlib import Path

from flask import Blueprint, Response, jsonify

from config.settings import settings
from core.logging import logger
from core.utils import get_mime

system_bp = Blueprint("system", __name__)

# 图片保存目录（与 pipeline.py 中的 UPLOAD_DIR 一致）
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads" / "images"


@system_bp.route("/images/<filename>")
def serve_image(filename):
    """提供上传/生成的图片"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "图片不存在"}), 404
    mime = get_mime(file_path.suffix.lstrip("."))
    return Response(file_path.read_bytes(), mimetype=mime)


@system_bp.route("/api/config-check")
def api_config_check():
    """检查配置是否完整"""
    logger.info("[API] GET /api/config-check")
    return jsonify({
        "mimo": {
            "api_key_configured": bool(settings.MIMO_API_KEY),
            "api_base": settings.MIMO_API_BASE,
        },
        "maxkb": {
            "standard_key_configured": bool(settings.MAXKB_STANDARD_API_KEY),
            "pro_key_configured": bool(settings.MAXKB_PRO_API_KEY),
            "standard_url": settings.MAXKB_STANDARD_BASE_URL,
        },
        "openai": {
            "api_key_configured": bool(settings.OPENAI_API_KEY),
            "api_base": settings.OPENAI_API_BASE,
            "model": settings.OPENAI_MODEL_NAME,
        },
    })
