"""历史记录路由 — 查询、详情、删除"""

from flask import Blueprint, jsonify, request

from services.history import get_history_by_id, delete_history, query_history

history_bp = Blueprint("history", __name__)


@history_bp.route("/api/history", methods=["GET"])
def api_get_history():
    """获取历史记录列表（支持搜索 + 分页）"""
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    data = query_history(q=q, page=page, per_page=per_page)
    return jsonify({"success": True, **data})


@history_bp.route("/api/history/<record_id>", methods=["GET"])
def api_get_history_detail(record_id):
    """获取单条历史记录详情"""
    record = get_history_by_id(record_id)
    if record:
        return jsonify({"success": True, "record": record})
    return jsonify({"success": False, "error": "记录不存在"}), 404


@history_bp.route("/api/history/<record_id>", methods=["DELETE"])
def api_delete_history(record_id):
    """删除一条历史记录"""
    if delete_history(record_id):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "记录不存在"}), 404
