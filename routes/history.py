"""历史记录路由 — 查询、详情、删除"""

import json

from flask import Blueprint, jsonify

from services.history import load_history, HISTORY_FILE

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
    history = load_history()
    new_history = [r for r in history if r.get("id") != record_id]
    if len(new_history) == len(history):
        return jsonify({"success": False, "error": "记录不存在"}), 404
    HISTORY_FILE.write_text(json.dumps(new_history, ensure_ascii=False, indent=2), encoding="utf-8")
    return jsonify({"success": True})
