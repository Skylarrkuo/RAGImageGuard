"""历史记录存储 — SQLite 持久化"""

import json
import sqlite3
import threading
from pathlib import Path

from core.logging import logger

# 数据库路径
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "history.db"

# 线程安全锁（sqlite3 连接非线程安全）
_db_lock = threading.Lock()

MAX_RECORDS = 100


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接（每次调用新建，用完关闭）"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS history ("
        "  id TEXT PRIMARY KEY,"
        "  created_at TEXT NOT NULL,"
        "  data TEXT NOT NULL"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON history(created_at DESC)")
    conn.commit()
    return conn


def _migrate_from_json():
    """如 JSON 文件存在且 DB 为空，自动迁移"""
    json_path = DB_PATH.parent / "history.json"
    if not json_path.exists():
        return
    try:
        records = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if not records:
        return

    with _db_lock:
        conn = _get_conn()
        try:
            count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            if count > 0:
                return  # DB 已有数据，跳过迁移
            for record in records:
                rid = record.get("id", "")
                created = record.get("created_at", "")
                conn.execute(
                    "INSERT OR IGNORE INTO history (id, created_at, data) VALUES (?, ?, ?)",
                    (rid, created, json.dumps(record, ensure_ascii=False)),
                )
            conn.commit()
            logger.info(f"[History] 从 history.json 迁移了 {len(records)} 条记录到 SQLite")
        finally:
            conn.close()


# 启动时尝试迁移
_migrate_from_json()


def load_history() -> list:
    """读取所有历史记录（最新在前）"""
    with _db_lock:
        conn = _get_conn()
        try:
            rows = conn.execute(
                "SELECT data FROM history ORDER BY created_at DESC"
            ).fetchall()
            return [json.loads(row[0]) for row in rows]
        except Exception as e:
            logger.warning(f"[History] 读取失败: {e}")
            return []
        finally:
            conn.close()


def save_history(record: dict):
    """追加一条历史记录"""
    rid = record.get("id", "")
    created = record.get("created_at", "")
    logger.debug(f"[History] 保存记录: id={rid}, status={record.get('status')}")

    with _db_lock:
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO history (id, created_at, data) VALUES (?, ?, ?)",
                (rid, created, json.dumps(record, ensure_ascii=False)),
            )
            # 超过上限时删除最旧的
            count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            if count > MAX_RECORDS:
                conn.execute(
                    "DELETE FROM history WHERE id IN "
                    "(SELECT id FROM history ORDER BY created_at ASC LIMIT ?)",
                    (count - MAX_RECORDS,),
                )
            conn.commit()
            logger.debug(f"[History] 保存成功")
        finally:
            conn.close()


def update_history(record_id: str, patch: dict) -> bool:
    """按 id 更新历史记录中的字段"""
    with _db_lock:
        conn = _get_conn()
        try:
            row = conn.execute(
                "SELECT data FROM history WHERE id = ?", (record_id,)
            ).fetchone()
            if not row:
                logger.warning(f"[History] 未找到记录: id={record_id}")
                return False
            record = json.loads(row[0])
            record.update(patch)
            conn.execute(
                "UPDATE history SET data = ? WHERE id = ?",
                (json.dumps(record, ensure_ascii=False), record_id),
            )
            conn.commit()
            logger.debug(f"[History] 更新记录: id={record_id}, fields={list(patch.keys())}")
            return True
        finally:
            conn.close()


def delete_history(record_id: str) -> bool:
    """删除一条历史记录"""
    with _db_lock:
        conn = _get_conn()
        try:
            cursor = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.debug(f"[History] 删除记录: id={record_id}")
                return True
            logger.warning(f"[History] 未找到记录: id={record_id}")
            return False
        finally:
            conn.close()
