#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整修复版本的数据库连接管理器 - 修复execute_query方法并保留所有原有功能
"""

import pymysql
from pymysql import Error, MySQLError
from pymysql.cursors import DictCursor
from datetime import datetime
import logging
import time
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager

logger = logging.getLogger(__name__)
 

class DatabaseConnection:
    """数据库连接类 - 基于pymysql"""

    def __init__(self, host: str, port: int, database: str,
                 user: str, password: str, charset: str = 'utf8mb4',
                 autocommit: bool = True):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.charset = charset
        self.autocommit = autocommit
        self.connection = None

    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                charset=self.charset,
                autocommit=self.autocommit,
                cursorclass=DictCursor,
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30
            )
            logger.info(f"数据库连接成功: {self.host}:{self.port}/{self.database}")
            return True
        except (Error, MySQLError) as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def is_connected(self) -> bool:
        """检查连接是否有效"""
        if not self.connection:
            return False
        try:
            self.connection.ping(reconnect=False)
            return True
        except:
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("数据库连接已断开")


class UnifiedDatabaseManager:
    """统一数据库管理器 - 修复版本"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = DatabaseConnection(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 3306),
            database=db_config.get('database', 'test'),
            user=db_config.get('user', 'root'),
            password=db_config.get('password', ''),
            charset=db_config.get('charset', 'utf8mb4'),
            autocommit=db_config.get('autocommit', True)
        )

        # 统计信息
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'connection_attempts': 0,
            'reconnections': 0
        }

    def connect(self) -> bool:
        """建立数据库连接"""
        self.stats['connection_attempts'] += 1
        return self.connection.connect()

    def disconnect(self):
        """关闭数据库连接"""
        self.connection.disconnect()

    def reconnect(self) -> bool:
        """重新连接数据库"""
        self.stats['reconnections'] += 1
        logger.info("重新连接数据库...")
        self.disconnect()
        return self.connect()

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connection.is_connected()

    def execute_query(self, sql: str, params: tuple = None) -> Dict[str, Any]:
        """
        执行SQL查询 - 增强版本
        返回包含结果和影响行数的字典
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.is_connected():
                    if not self.connect():
                        raise Exception("无法建立数据库连接")

                self.stats['total_queries'] += 1

                # 确保参数类型正确
                if params:
                    # 将所有参数转换为字符串，避免类型问题
                    processed_params = []
                    for param in params:
                        if isinstance(param, datetime):
                            processed_params.append(param.strftime('%Y-%m-%d %H:%M:%S'))
                        else:
                            processed_params.append(str(param) if param is not None else None)
                    params = tuple(processed_params)

                with self.connection.connection.cursor() as cursor:
                    cursor.execute(sql, params)

                # 获取影响行数
                affected_rows = cursor.rowcount

                # 判断查询类型并获取相应结果
                sql_upper = sql.strip().upper()
                if sql_upper.startswith('SELECT'):
                    results = cursor.fetchall()
                elif sql_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
                    # 对于INSERT/UPDATE/DELETE，返回影响行数
                    results = []
                    logger.info(f"SQL执行成功，影响行数: {affected_rows}")
                else:
                    results = []

                # 提交事务（如果autocommit为False）
                if not self.connection.autocommit:
                    self.connection.connection.commit()

                self.stats['successful_queries'] += 1
                logger.debug(f"查询执行成功: {len(results)}条结果")

                return {
                    'results': results,
                    'affected_rows': affected_rows,
                    'success': True
                }

            except (Error, MySQLError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"SQL执行失败，正在重试 ({attempt + 1}/{max_retries}): {e}")
                    logger.warning(f"SQL语句: {sql}")
                    logger.warning(f"参数: {params}")

                    # 尝试重新连接
                    try:
                        self.disconnect()
                        time.sleep(0.5 * (attempt + 1))  # 递增延迟
                        continue
                    except Exception as reconnect_error:
                        logger.error(f"重连失败: {reconnect_error}")
                        continue
                else:
                    # 最后一次重试失败
                    self.stats['failed_queries'] += 1
                    logger.error(f"SQL执行失败（已重试{max_retries}次）: {e}")
                    logger.error(f"SQL语句: {sql}")
                    logger.error(f"参数: {params}")

                    # 检查是否是连接问题
                    if "Packet sequence number wrong" in str(e) or "MySQL server has gone away" in str(e):
                        try:
                            self.disconnect()
                            self.connect()
                            logger.info("已尝试重新连接数据库")
                        except Exception as reconnect_error:
                            logger.error(f"重新连接失败: {reconnect_error}")

                    return {
                        'results': [],
                        'affected_rows': 0,
                        'success': False,
                        'error': str(e)
                    }

    def execute_many(self, sql: str, params_list: List[tuple]) -> Dict[str, Any]:
        """批量执行SQL - 修复版本"""
        if not self.is_connected():
            if not self.connect():
                raise Exception("无法建立数据库连接")

        try:
            self.stats['total_queries'] += 1
            with self.connection.connection.cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)

                if not self.connection.autocommit:
                    self.connection.connection.commit()

                self.stats['successful_queries'] += 1
                logger.info(f"批量执行成功: {len(params_list)}条记录，影响行数: {affected_rows}")

                return {
                    'affected_rows': affected_rows,
                    'success': True
                }

        except (Error, MySQLError) as e:
            self.stats['failed_queries'] += 1
            logger.error(f"批量执行失败: {e}")
            if not self.connection.autocommit:
                self.connection.connection.rollback()
            return {
                'affected_rows': 0,
                'success': False,
                'error': str(e)
            }

    def execute_insert(self, table: str, data: List[Dict[str, Any]]) -> int:
        """执行批量插入"""
        if not data:
            return 0

        # 构建INSERT语句
        columns = list(data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        # 准备参数
        params_list = [tuple(item.values()) for item in data]

        result = self.execute_many(sql, params_list)
        return result['affected_rows']

    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            'host': self.db_config.get('host'),
            'port': self.db_config.get('port'),
            'database': self.db_config.get('database'),
            'user': self.db_config.get('user'),
            'is_connected': self.is_connected(),
            'stats': self.stats
        }


class QueryBuilder:
    """SQL查询构建器"""

    @staticmethod
    def build_update(table: str, data: Dict[str, Any],
                    where_clause: str = None) -> str:
        """构建UPDATE查询"""
        if not data:
            raise ValueError("更新数据不能为空")

        set_clauses = []
        for column in data.keys():
            set_clauses.append(f"{column} = %s")

        sql = f"UPDATE {table} SET {', '.join(set_clauses)}"

        if where_clause:
            sql += f" WHERE {where_clause}"

        return sql

    @staticmethod
    def build_insert(table: str, data: Dict[str, Any]) -> str:
        """构建INSERT查询"""
        if not data:
            raise ValueError("插入数据不能为空")

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))

        return f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    @staticmethod
    def build_select(table: str, columns='*', where_clause: str = None,
                    order_by: str = None, limit: int = None) -> str:
        """构建SELECT查询"""
        # 处理columns参数，支持字符串或列表
        if isinstance(columns, list):
            columns_str = ', '.join(columns)
        else:
            columns_str = columns

        sql = f"SELECT {columns_str} FROM {table}"

        if where_clause:
            sql += f" WHERE {where_clause}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        if limit:
            sql += f" LIMIT {limit}"

        return sql


class TransactionManager:
    """事务管理器"""

    def __init__(self, db_manager: UnifiedDatabaseManager):
        self.db_manager = db_manager
        self.transaction_active = False

    def __enter__(self):
        if not self.db_manager.is_connected():
            if not self.db_manager.connect():
                raise Exception("无法建立数据库连接")

        # 开始事务
        self.db_manager.connection.connection.autocommit = False
        self.transaction_active = True
        logger.debug("事务开始")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.transaction_active:
            if exc_type is None:
                # 提交事务
                self.db_manager.connection.connection.commit()
                logger.debug("事务提交")
            else:
                # 回滚事务
                self.db_manager.connection.connection.rollback()
                logger.error(f"事务回滚: {exc_val}")

            # 恢复自动提交
            self.db_manager.connection.connection.autocommit = True
            self.transaction_active = False

    def commit(self):
        """手动提交事务"""
        if self.transaction_active:
            self.db_manager.connection.connection.commit()
            logger.debug("事务手动提交")
            self.transaction_active = False
            self.db_manager.connection.connection.autocommit = True

    def rollback(self):
        """手动回滚事务"""
        if self.transaction_active:
            self.db_manager.connection.connection.rollback()
            logger.debug("事务手动回滚")
            self.transaction_active = False
            self.db_manager.connection.connection.autocommit = True


# 数据库工厂函数
def create_database_manager(config_name: str = 'default') -> UnifiedDatabaseManager:
    """创建数据库管理器实例"""
    from api_config import config

    # 获取配置类
    config_class = config[config_name]

    # 转换为pymysql需要的配置格式
    db_config = {
        'host': getattr(config_class, 'DB_HOST', 'localhost'),
        'port': getattr(config_class, 'DB_PORT', 3306),
        'database': getattr(config_class, 'DB_NAME', 'mqtt'),
        'user': getattr(config_class, 'DB_USER', 'root'),
        'password': getattr(config_class, 'DB_PASSWORD', ''),
        'charset': 'utf8mb4',
        'autocommit': True
    }

    return UnifiedDatabaseManager(db_config)


# 全局数据库管理器实例
default_db_manager = None


def get_db_manager() -> UnifiedDatabaseManager:
    """获取默认数据库管理器"""
    global default_db_manager
    if default_db_manager is None:
        default_db_manager = create_database_manager()
    return default_db_manager


def init_database(app=None):
    """初始化数据库（可选Flask应用集成）"""
    if app:
        # Flask应用集成
        app.config['DATABASE_MANAGER'] = get_db_manager()

        # 在应用上下文中自动管理连接
        @app.before_request
        def before_request():
            # 可以在这里做连接检查或预热
            pass

        @app.teardown_appcontext
        def teardown_appcontext(exception=None):
            # 在请求结束时清理资源
            pass

    # 确保数据库连接可用
    db_manager = get_db_manager()
    if not db_manager.connect():
        raise Exception("数据库初始化失败")

    logger.info("数据库初始化完成")