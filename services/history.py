"""历史记录存储 — SQLite 持久化"""

import json
import sqlite3
import threading
from pathlib import Path

from core.logging import logger
from config.settings import UPLOAD_DIR

# 数据库路径
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "history.db"

# 线程安全锁（sqlite3 连接非线程安全）
_db_lock = threading.Lock()

MAX_RECORDS = 100

# 标记是否已执行过迁移（懒执行，避免模块导入时副作用）
_migration_done = False


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
    """如 JSON 文件存在且 DB 为空，自动迁移（懒执行，首次数据库操作时触发）"""
    global _migration_done
    if _migration_done:
        return
    _migration_done = True

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


def load_history() -> list:
    """读取所有历史记录（最新在前）"""
    _migrate_from_json()
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


def get_history_by_id(record_id: str) -> dict | None:
    """按 id 直接查询单条历史记录（O(1) 索引查询）"""
    _migrate_from_json()
    with _db_lock:
        conn = _get_conn()
        try:
            row = conn.execute(
                "SELECT data FROM history WHERE id = ?", (record_id,)
            ).fetchone()
            return json.loads(row[0]) if row else None
        except Exception as e:
            logger.warning(f"[History] 查询失败: {e}")
            return None
        finally:
            conn.close()


def save_history(record: dict):
    """追加一条历史记录"""
    _migrate_from_json()
    rid = record.get("id", "")
    created = record.get("created_at", "")
    logger.debug(f"[History] 保存记录: id={rid}, status={record.get('status')}")

    stale_records = []
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
                excess = count - MAX_RECORDS
                # 先查出待删除记录的图片路径
                rows = conn.execute(
                    "SELECT data FROM history ORDER BY created_at ASC LIMIT ?",
                    (excess,),
                ).fetchall()
                stale_records = [json.loads(r[0]) for r in rows]
                conn.execute(
                    "DELETE FROM history WHERE id IN "
                    "(SELECT id FROM history ORDER BY created_at ASC LIMIT ?)",
                    (excess,),
                )
            conn.commit()
            logger.debug(f"[History] 保存成功")
        finally:
            conn.close()

    # 清理被淘汰记录的图片文件（锁外执行）
    for sr in stale_records:
        _cleanup_image_files(sr)


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


def _cleanup_image_files(record: dict):
    """删除历史记录关联的图片文件（original / generated / refined / thumb）"""
    image_keys = ("original_image", "generated_image", "refined_image")
    for key in image_keys:
        rel_path = record.get(key)
        if not rel_path:
            continue
        # 删除主图文件
        file_path = UPLOAD_DIR / rel_path
        try:
            if file_path.is_file():
                file_path.unlink()
                logger.debug(f"[History] 已删除图片: {file_path}")
        except OSError as e:
            logger.warning(f"[History] 删除图片失败 {file_path}: {e}")
        # 删除对应缩略图：original/abc.jpg → thumb/thumb_abc.jpg
        stem = Path(rel_path).stem
        thumb_path = UPLOAD_DIR / "thumb" / f"thumb_{stem}.jpg"
        try:
            if thumb_path.is_file():
                thumb_path.unlink()
                logger.debug(f"[History] 已删除缩略图: {thumb_path}")
        except OSError as e:
            logger.warning(f"[History] 删除缩略图失败 {thumb_path}: {e}")


def delete_history(record_id: str) -> bool:
    """删除一条历史记录及其关联图片文件"""
    with _db_lock:
        conn = _get_conn()
        try:
            # 先查询记录以获取图片路径
            row = conn.execute(
                "SELECT data FROM history WHERE id = ?", (record_id,)
            ).fetchone()
            if not row:
                logger.warning(f"[History] 未找到记录: id={record_id}")
                return False
            record = json.loads(row[0])
            cursor = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
            conn.commit()
            logger.debug(f"[History] 删除记录: id={record_id}")
        finally:
            conn.close()

    # 在锁外清理文件（避免持锁做 IO）
    _cleanup_image_files(record)
    return True


def query_history(q: str = '', page: int = 1, per_page: int = 12) -> dict:
    """支持搜索 + 分页的历史记录查询。
    返回 { records: [...], total: N, page: N, pages: N }
    搜索在 SQL 层完成（LIKE 匹配 JSON blob 中的文本字段）。"""
    _migrate_from_json()
    with _db_lock:
        conn = _get_conn()
        try:
            if q:
                # SQL 层搜索：对 JSON blob 做 LIKE 匹配（覆盖 scene_description / edit_prompt / edit_summary / compliance_analysis）
                pattern = f"%{q}%"
                count_row = conn.execute(
                    "SELECT COUNT(*) FROM history WHERE data LIKE ? COLLATE NOCASE",
                    (pattern,),
                ).fetchone()
                total = count_row[0]

                pages = max(1, (total + per_page - 1) // per_page)
                page = max(1, min(page, pages))
                offset = (page - 1) * per_page

                rows = conn.execute(
                    "SELECT data FROM history WHERE data LIKE ? COLLATE NOCASE "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (pattern, per_page, offset),
                ).fetchall()
                records = [json.loads(row[0]) for row in rows]
            else:
                # 无搜索：直接分页
                total = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
                pages = max(1, (total + per_page - 1) // per_page)
                page = max(1, min(page, pages))
                offset = (page - 1) * per_page

                rows = conn.execute(
                    "SELECT data FROM history ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (per_page, offset),
                ).fetchall()
                records = [json.loads(row[0]) for row in rows]
        except Exception as e:
            logger.warning(f"[History] 查询失败: {e}")
            records, total, page, pages = [], 0, 1, 1
        finally:
            conn.close()

    return {'records': records, 'total': total, 'page': page, 'pages': pages}
