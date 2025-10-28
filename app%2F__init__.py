#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常数据管理应用初始化
"""

from flask import Flask
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os

from database import init_database


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)

    # 加载配置
    from api_config import config
    app.config.from_object(config[config_name])

    # 启用CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # 配置日志
    setup_logging(app)

    # 初始化数据库
    init_database(app)

    # 注册蓝图
    register_blueprints(app)

    return app


def setup_logging(app):
    """配置日志"""
    if not app.debug and not app.testing:
        # 确保日志目录存在
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 配置文件日志处理器
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('异常数据管理系统启动')


def register_blueprints(app):
    """注册蓝图"""
    from app.routes import exception_bp
    app.register_blueprint(exception_bp, url_prefix='/api')