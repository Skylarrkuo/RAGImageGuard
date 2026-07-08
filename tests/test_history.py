"""services/history.py 历史记录存储测试"""

import json
import pytest

import services.history as hist_mod


def _make_record(rid, description="测试场景", status="completed"):
    """创建测试用历史记录"""
    return {
        "id": rid,
        "created_at": "2026-07-08T12:00:00",
        "status": status,
        "scene_description": description,
        "edit_prompt": "remove trash",
    }


class TestSaveAndLoad:
    def test_save_and_load(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        record = _make_record("r1")
        hist_mod.save_history(record)
        records = hist_mod.load_history()
        assert len(records) == 1
        assert records[0]["id"] == "r1"

    def test_save_multiple(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        for i in range(5):
            hist_mod.save_history(_make_record(f"r{i}"))
        records = hist_mod.load_history()
        assert len(records) == 5


class TestUpdateHistory:
    def test_update_existing(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        hist_mod.save_history(_make_record("r1"))
        result = hist_mod.update_history("r1", {"status": "refined"})
        assert result is True
        records = hist_mod.load_history()
        assert records[0]["status"] == "refined"

    def test_update_nonexistent(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        result = hist_mod.update_history("missing", {"status": "x"})
        assert result is False


class TestDeleteHistory:
    def test_delete_existing(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        hist_mod.save_history(_make_record("r1"))
        result = hist_mod.delete_history("r1")
        assert result is True
        assert len(hist_mod.load_history()) == 0

    def test_delete_nonexistent(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        result = hist_mod.delete_history("missing")
        assert result is False


class TestMaxRecordsPrune:
    def test_prune_excess(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        monkeypatch.setattr(hist_mod, "MAX_RECORDS", 5)
        for i in range(8):
            hist_mod.save_history(_make_record(f"r{i}"))
        records = hist_mod.load_history()
        assert len(records) == 5


class TestQueryHistory:
    def test_search_by_description(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        hist_mod.save_history(_make_record("r1", "景区入口标识"))
        hist_mod.save_history(_make_record("r2", "停车场管理"))
        result = hist_mod.query_history(q="标识")
        assert result["total"] == 1
        assert result["records"][0]["id"] == "r1"

    def test_search_case_insensitive(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        hist_mod.save_history(_make_record("r1", "Hello World"))
        result = hist_mod.query_history(q="hello")
        assert result["total"] == 1

    def test_search_no_match(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        hist_mod.save_history(_make_record("r1", "景区入口"))
        result = hist_mod.query_history(q="不存在的关键词")
        assert result["total"] == 0
        assert result["records"] == []

    def test_pagination(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        for i in range(10):
            hist_mod.save_history(_make_record(f"r{i}"))
        result = hist_mod.query_history(page=1, per_page=3)
        assert len(result["records"]) == 3
        assert result["total"] == 10
        assert result["pages"] == 4
        assert result["page"] == 1

    def test_pagination_last_page(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        for i in range(10):
            hist_mod.save_history(_make_record(f"r{i}"))
        result = hist_mod.query_history(page=4, per_page=3)
        assert len(result["records"]) == 1

    def test_empty_query(self, _clean_env, monkeypatch):
        monkeypatch.setattr(hist_mod, "DB_PATH", _clean_env)
        for i in range(3):
            hist_mod.save_history(_make_record(f"r{i}"))
        result = hist_mod.query_history()
        assert result["total"] == 3
