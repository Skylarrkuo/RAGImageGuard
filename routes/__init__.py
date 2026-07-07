"""Blueprint 注册中心"""

from flask import Flask

from .pipeline import pipeline_bp
from .history import history_bp
from .system import system_bp


def register_all_blueprints(app: Flask):
    """注册所有 Blueprint"""
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(system_bp)
