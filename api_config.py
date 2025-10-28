import os
from datetime import timedelta

class Config:
    """应用配置类"""

    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

    # 数据库配置 - 使用现有配置文件中的数据库信息
    #DB_HOST = os.environ.get('DB_HOST') or '10.66.241.143'
    #DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    #DB_USER = os.environ.get('DB_USER') or 'root'
    #DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'XJscjsbt@2022'
    #DB_NAME = os.environ.get('DB_NAME') or 'RWDB_XJ'

        # 数据库配置 - 使用现有配置文件中的数据库信息
    DB_HOST = os.environ.get('DB_HOST') or '59.110.116.46'
    DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    DB_USER = os.environ.get('DB_USER') or 'ljw'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or '123456'
    DB_NAME = os.environ.get('DB_NAME') or 'mqtt'


    # 数据库连接URL
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_timeout': 30
    }

    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}