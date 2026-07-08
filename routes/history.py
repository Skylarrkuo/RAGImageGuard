"""历史记录路由 — 查询、详情、删除"""

from flask import Blueprint, jsonify

from services.history import load_history, delete_history

history_bp = Blueprint("history", __name__)


@history_bp.route("/api/history", methods=["GET"])
def api_get_history():
    """获取历史记录列表"""
    history = load_history()
    return jsonify({"success": True, "records": history})


@history_bp.route("/api/history/<record_id>", methods=["GET"])
def api_get_history_detail(record_id):
    """获取单条历史记录详情"""
    history = load_history()
    for record in history:
        if record.get("id") == record_id:
            return jsonify({"success": True, "record": record})
    return jsonify({"success": False, "error": "记录不存在"}), 404


@history_bp.route("/api/history/<record_id>", methods=["DELETE"])
def api_delete_history(record_id):
    """删除一条历史记录"""
    if delete_history(record_id):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "记录不存在"}), 404
