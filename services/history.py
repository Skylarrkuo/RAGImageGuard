"""历史记录存储 — JSON 文件持久化"""

import json
from pathlib import Path

from core.logging import logger

# 历史记录文件路径
HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "history.json"


def load_history() -> list:
    """读取历史记录"""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_history(record: dict):
    """追加一条历史记录"""
    logger.debug(f"[History] 保存记录: id={record.get('id')}, status={record.get('status')}")
    history = load_history()
    history.insert(0, record)  # 最新在前
    # 最多保留 100 条
    if len(history) > 100:
        history = history[:100]
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.debug(f"[History] 保存成功，当前共 {len(history)} 条记录")


def update_history(record_id: str, patch: dict):
    """按 id 更新历史记录中的字段"""
    history = load_history()
    for record in history:
        if record.get("id") == record_id:
            record.update(patch)
            HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.debug(f"[History] 更新记录: id={record_id}, fields={list(patch.keys())}")
            return True
    logger.warning(f"[History] 未找到记录: id={record_id}")
    return False
