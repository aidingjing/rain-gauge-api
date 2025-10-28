#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本的数据库连接管理器
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


class DatabaseConnectionFixed:
    """修复版本的数据库连接类"""

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

    def execute_query(self, sql: str, params: tuple = None) -> Dict[str, Any]:
        """
        执行SQL查询 - 修复版本
        返回包含结果和影响行数的字典
        """
        if not self.is_connected():
            if not self.connect():
                raise Exception("无法建立数据库连接")

        try:
            with self.connection.cursor() as cursor:
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
                if not self.autocommit:
                    self.connection.commit()

                return {
                    'results': results,
                    'affected_rows': affected_rows,
                    'success': True
                }

        except (Error, MySQLError) as e:
            logger.error(f"SQL执行失败: {e}")
            logger.error(f"SQL语句: {sql}")
            logger.error(f"参数: {params}")
            if not self.autocommit:
                self.connection.rollback()
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
            with self.connection.cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)

                if not self.autocommit:
                    self.connection.commit()

                logger.info(f"批量执行成功: {len(params_list)}条记录，影响行数: {affected_rows}")

                return {
                    'affected_rows': affected_rows,
                    'success': True
                }

        except (Error, MySQLError) as e:
            logger.error(f"批量执行失败: {e}")
            if not self.autocommit:
                self.connection.rollback()
            return {
                'affected_rows': 0,
                'success': False,
                'error': str(e)
            }


class QueryBuilder:
    """SQL查询构建器 - 保持原有实现"""

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