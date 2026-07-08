"""routes/ API 路由测试"""

import pytest


class TestConfigCheck:
    def test_config_check_returns_json(self, client):
        resp = client.get("/api/config-check")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "mimo" in data or "error" in data


class TestHistoryRoutes:
    def test_history_list_empty(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["records"] == []
        assert data["total"] == 0

    def test_history_pagination_params(self, client):
        resp = client.get("/api/history?page=1&per_page=5")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["page"] == 1

    def test_history_search(self, client):
        resp = client.get("/api/history?q=test")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_history_detail_not_found(self, client):
        resp = client.get("/api/history/nonexistent")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_history_delete_not_found(self, client):
        resp = client.delete("/api/history/nonexistent")
        assert resp.status_code == 404


class TestImageNotFound:
    def test_image_not_found(self, client):
        resp = client.get("/images/nonexistent.jpg")
        assert resp.status_code == 404
