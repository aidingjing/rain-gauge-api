#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
"""

import pymysql
from pymysql import Error, MySQLError
from pymysql.cursors import DictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging
from database import UnifiedDatabaseManager, QueryBuilder, TransactionManager

logger = logging.getLogger(__name__)


def get_region_info_by_aid(aid):
    """根据aid获取市县信息"""
    if aid is None:
        return '', '', None, None

    # 第一师行政区划映射 - 使用正确的adcd编码
    # 第一师adcd前四位是6611，各团前6位为661101-661116
    region_mapping = {
        661101: ('第一师', '第一团', 80.1, 40.2),
        661102: ('第一师', '第二团', 80.3, 40.4),
        661103: ('第一师', '第三团', 80.5, 40.6),
        661104: ('第一师', '第四团', 80.7, 40.8),
        661105: ('第一师', '第五团', 80.9, 40.3),
        661106: ('第一师', '第六团', 81.1, 40.7),
        661107: ('第一师', '第七团', 81.3, 40.9),
        661108: ('第一师', '第八团', 81.5, 41.1),
        661109: ('第一师', '第九团', 81.7, 41.3),
        661110: ('第一师', '第十团', 81.9, 41.5),
        661111: ('第一师', '第十一团', 82.1, 41.7),
        661112: ('第一师', '第十二团', 82.3, 41.9),
        661113: ('第一师', '第十三团', 82.5, 42.1),
        661115: ('第一师', '第十五团', 82.7, 42.3),
        661116: ('第一师', '第十六团', 82.9, 42.5),
        123123: ('测试市', '测试县', 120.0, 30.0),  # 原有测试数据
    }

    return region_mapping.get(int(aid), ('第一师', f'第{aid}团', 80.0, 40.0))


class BaseModel:
    """基础模型类"""

    def __init__(self, db_manager: UnifiedDatabaseManager):
        self.db_manager = db_manager

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        raise NotImplementedError("子类必须实现to_dict方法")


class ST_STBPRP_B(BaseModel):
    """测站基本信息表"""

    __tablename__ = 'ST_STBPRP_B'

    def __init__(self, db_manager: UnifiedDatabaseManager):
        super().__init__(db_manager)

    @staticmethod
    def get_by_stcd(db_manager: UnifiedDatabaseManager, stcd: str) -> Optional[Dict]:
        """根据测站编码获取测站信息"""
        try:
            sql = QueryBuilder.build_select(
                table='ST_STBPRP_B',
                columns=['stcd', 'stnm', 'lgtd', 'lttd'],
                where_clause='stcd = %s'
            )
            results = db_manager.execute_query(sql, (stcd,))

            if results:
                return {
                    'stcd': results[0]['stcd'],
                    'stnm': results[0]['stnm'],
                    'lgtd': float(results[0]['lgtd']) if results[0]['lgtd'] else None,
                    'lttd': float(results[0]['lttd']) if results[0]['lttd'] else None
                }
            return None

        except Exception as e:
            logger.error(f"获取测站信息失败: {e}")
            return None

    @staticmethod
    def get_all_stations(db_manager: UnifiedDatabaseManager) -> List[Dict]:
        """获取所有测站信息"""
        try:
            sql = QueryBuilder.build_select(
                table='ST_STBPRP_B',
                columns=['stcd', 'stnm', 'lgtd', 'lttd'],
                order_by='stcd'
            )
            results = db_manager.execute_query(sql)

            return [
                {
                    'stcd': row['stcd'],
                    'stnm': row['stnm'],
                    'lgtd': float(row['lgtd']) if row['lgtd'] else None,
                    'lttd': float(row['lttd']) if row['lttd'] else None
                }
                for row in results['results'] if results.get('success')
            ]

        except Exception as e:
            logger.error(f"获取所有测站信息失败: {e}")
            return []


class AD_CD_B(BaseModel):
    """行政区划表"""

    __tablename__ = 'AD_CD_B'

    def __init__(self, db_manager: UnifiedDatabaseManager):
        super().__init__(db_manager)

    @staticmethod
    def get_by_adcd(db_manager: UnifiedDatabaseManager, adcd: str) -> Optional[Dict]:
        """根据行政区划代码获取信息"""
        try:
            sql = QueryBuilder.build_select(
                table='AD_CD_B',
                columns=['aid', 'adcd', 'adnm', 'lgtd', 'lttd'],
                where_clause='adcd = %s'
            )
            results = db_manager.execute_query(sql, (adcd,))

            if results:
                return {
                    'aid': results[0]['aid'],
                    'adcd': results[0]['adcd'],
                    'adnm': results[0]['adnm'],
                    'lgtd': float(results[0]['lgtd']) if results[0]['lgtd'] else None,
                    'lttd': float(results[0]['lttd']) if results[0]['lttd'] else None
                }
            return None

        except Exception as e:
            logger.error(f"获取行政区划信息失败: {e}")
            return None

    @staticmethod
    def get_all_regions(db_manager: UnifiedDatabaseManager) -> List[Dict]:
        """获取所有行政区划"""
        try:
            sql = QueryBuilder.build_select(
                table='AD_CD_B',
                columns=['aid', 'adcd', 'adnm'],
                order_by='aid'
            )
            results = db_manager.execute_query(sql)

            return [
                {
                    'aid': row['aid'],
                    'adcd': row['adcd'],
                    'adnm': row['adnm']
                }
                for row in results['results'] if results.get('success')
            ]

        except Exception as e:
            logger.error(f"获取所有行政区划失败: {e}")
            return []


class ExceptionData(BaseModel):
    """异常数据表"""

    __tablename__ = 'TZX_STCD_EXCE'

    def __init__(self, db_manager: UnifiedDatabaseManager):
        super().__init__(db_manager)

    @staticmethod
    def create_table_if_not_exists(db_manager: UnifiedDatabaseManager):
        """创建表（如果不存在）"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS TZX_STCD_EXCE (
                stcd VARCHAR(50) NOT NULL COMMENT '测站编码',
                tm DATETIME NOT NULL COMMENT '异常时间',
                stnm VARCHAR(100) NOT NULL COMMENT '测站名称',
                aid VARCHAR(20) DEFAULT NULL COMMENT '行政区代码',
                val FLOAT NOT NULL COMMENT '异常值',
                rem TEXT DEFAULT NULL COMMENT '备注/异常原因',
                insert_tm DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '插入时间',
                re_name VARCHAR(100) DEFAULT NULL COMMENT '反馈人员姓名',
                status INT DEFAULT NULL COMMENT '处理状态',
                re_time DATETIME DEFAULT NULL COMMENT '反馈时间',
                PRIMARY KEY (stcd, tm),
                INDEX idx_stcd_tm (stcd, tm),
                INDEX idx_aid (aid),
                INDEX idx_status (status),
                INDEX idx_rem (rem(100))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            db_manager.execute_query(create_table_sql)
            logger.info("异常数据表创建成功或已存在")

        except Exception as e:
            logger.error(f"创建异常数据表失败: {e}")

    @staticmethod
    def insert_exception(db_manager: UnifiedDatabaseManager, stcd: str, stnm: str, aid: str,
                      tm: datetime, val: float, rem: str = None,
                      re_name: str = None, status: int = 0) -> bool:
        """插入异常记录"""
        try:
            sql = QueryBuilder.build_insert(
                table='TZX_STCD_EXCE',
                data={
                    'stcd': stcd,
                    'stnm': stnm,
                    'aid': aid,
                    'tm': tm.strftime('%Y-%m-%d %H:%M:%S'),
                    'val': val,
                    'rem': rem,
                    're_name': re_name,
                    'status': status
                }
            )

            with TransactionManager(db_manager) as tx:
                result = db_manager.execute_query(sql)
                logger.info(f"异常记录插入成功: {stcd}, {tm}")
                return True

        except Exception as e:
            logger.error(f"插入异常记录失败: {e}")
            return False

    @staticmethod
    def get_pending_exceptions(db_manager: UnifiedDatabaseManager, page: int = 1, page_size: int = 20,
                               adcd: str = None, stcd: str = None,
                               start_time: datetime = None, end_time: datetime = None,
                               name: str = None, status: int = 0) -> Dict[str, Any]:
        """获取异常数据（支持按status过滤），对相同测站去重只保留最新异常"""
        try:
            # 构建基础查询
            base_sql = QueryBuilder.build_select(
                table='TZX_STCD_EXCE',
                columns=['stcd', 'stnm', 'aid', 'tm', 'val', 'rem',
                       'insert_tm', 're_name', 'status', 're_time'],
                where_clause='1=1'
            )

            # 添加筛选条件
            conditions = []
            params = []

            if adcd:
                conditions.append("AND aid LIKE %s")
                params.append(f"{adcd}%")

            if stcd:
                conditions.append("AND stcd = %s")
                params.append(stcd)

            if name:
                conditions.append("AND stnm LIKE %s")
                params.append(f"%{name}%")

            if start_time:
                conditions.append("AND tm >= %s")
                params.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))

            if end_time:
                conditions.append("AND tm <= %s")
                params.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))

            # 添加状态过滤条件
            if status is not None:
                if status == 0:
                    conditions.append("AND rem IS NULL")
                elif status == 1:
                    conditions.append("AND rem IS NOT NULL")
                # status == 2 不添加过滤条件

            # 应用筛选条件
            for condition in conditions:
                base_sql += f" {condition}"

            # 根据status决定是否去重：只有待反馈记录(status=0)才进行去重
            if status == 0:
                # 对于待反馈的记录，对相同测站去重只保留最新异常
                final_sql = f"""
                SELECT a.* FROM (
                    SELECT * FROM ({base_sql}) as base_data
                ) a
                LEFT JOIN (
                    SELECT stcd, MAX(tm) as max_tm
                    FROM ({base_sql}) as base_data
                    GROUP BY stcd
                ) b ON a.stcd = b.stcd AND a.tm = b.max_tm
                WHERE b.stcd IS NOT NULL
                ORDER BY a.tm DESC
                LIMIT {page_size} OFFSET {(page-1) * page_size}
                """
                # 为子查询准备双倍的参数（因为有两个相同的子查询）
                all_params = tuple(params * 2)
            else:
                # 对于已处理记录(status=1)或全部记录(status=2)，不进行去重
                final_sql = f"{base_sql} ORDER BY tm DESC LIMIT {page_size} OFFSET {(page-1) * page_size}"
                # 不需要去重，只需要一套参数
                all_params = tuple(params)

            # 执行查询
            results = db_manager.execute_query(final_sql, all_params)

            # 检查查询结果
            if not results.get('success'):
                logger.error(f"查询失败: {results.get('error', 'Unknown error')}")
                return {
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'pages': 0,
                    'items': []
                }

            # 根据status决定计数逻辑
            if status == 0:
                # 对于待反馈记录，按去重后的测站数量计数
                count_sql = f"""
                SELECT COUNT(DISTINCT stcd) as total
                FROM ({base_sql}) as count_data
                """
            else:
                # 对于已处理记录或全部记录，按实际记录数量计数
                count_sql = f"""
                SELECT COUNT(*) as total
                FROM ({base_sql}) as count_data
                """

            count_result = db_manager.execute_query(count_sql, tuple(params))
            total = count_result['results'][0]['total'] if count_result['success'] and count_result['results'] else 0

            # 转换为字典格式
            def parse_datetime(value):
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value.strftime('%Y-%m-%d %H:%M:%S')
                if isinstance(value, str):
                    # 验证并标准化时间格式
                    try:
                        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        return value  # 如果无法解析，返回原值
                return value

            items = []
            for row in results['results']:
                # 根据aid判断市县信息和经度纬度
                aid = row['aid']
                shi, xian, lgtd, lttd = get_region_info_by_aid(aid)

                items.append({
                    'stcd': row['stcd'],
                    'stnm': row['stnm'],
                    'aid': row['aid'],
                    'val': float(row['val']) if row['val'] else None,
                    'rem': row['rem'],
                    'tm': parse_datetime(row['tm']),
                    'insert_tm': parse_datetime(row['insert_tm']),
                    're_name': row['re_name'],
                    'status': int(row['status']) if row['status'] else None,
                    're_time': parse_datetime(row['re_time']),
                    'shi': shi,
                    'xian': xian,
                    'lgtd': lgtd,
                    'lttd': lttd
                })

            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size,
                'items': items
            }

        except Exception as e:
            logger.error(f"获取待反馈异常数据失败: {e}")
            return {
                'total': 0,
                'page': page,
                'page_size': page_size,
                'pages': 0,
                'items': []
            }

    @staticmethod
    def get_all_filtered_exceptions(db_manager: UnifiedDatabaseManager, adcd: str = None, stcd: str = None,
                                   start_time: datetime = None, end_time: datetime = None,
                                   name: str = None, status: int = 0) -> List[Dict]:
        """获取所有过滤后的异常数据（不分页，用于导出）"""
        try:
            # 构建基础查询
            base_sql = QueryBuilder.build_select(
                table='TZX_STCD_EXCE',
                columns=['stcd', 'stnm', 'aid', 'tm', 'val', 'rem',
                       'insert_tm', 're_name', 'status', 're_time'],
                where_clause='1=1'
            )

            # 添加筛选条件
            conditions = []
            params = []

            if adcd:
                conditions.append("AND aid LIKE %s")
                params.append(f"{adcd}%")

            if stcd:
                conditions.append("AND stcd = %s")
                params.append(stcd)

            if name:
                conditions.append("AND stnm LIKE %s")
                params.append(f"%{name}%")

            if start_time:
                conditions.append("AND tm >= %s")
                params.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))

            if end_time:
                conditions.append("AND tm <= %s")
                params.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))

            if status is not None:
                if status == 0:
                    conditions.append("AND rem IS NULL")
                elif status == 1:
                    conditions.append("AND rem IS NOT NULL")
                # status == 2 不添加过滤条件

            # 应用筛选条件
            for condition in conditions:
                base_sql += f" {condition}"

            # 排序
            final_sql = f"{base_sql} ORDER BY tm DESC"

            # 执行查询
            results = db_manager.execute_query(final_sql, tuple(params))

            # 检查查询结果
            if not results.get('success'):
                logger.error(f"查询失败: {results.get('error', 'Unknown error')}")
                return []

            # 转换为字典格式
            def parse_datetime(value):
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value.strftime('%Y-%m-%d %H:%M:%S')
                if isinstance(value, str):
                    # 验证并标准化时间格式
                    try:
                        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        return value  # 如果无法解析，返回原值
                return value

            items = []
            for row in results['results']:
                # 根据aid判断市县信息和经度纬度
                aid = row['aid']
                shi, xian, lgtd, lttd = get_region_info_by_aid(aid)

                items.append({
                    'stcd': row['stcd'],
                    'stnm': row['stnm'],
                    'aid': row['aid'],
                    'val': float(row['val']) if row['val'] else None,
                    'rem': row['rem'],
                    'tm': parse_datetime(row['tm']),
                    'insert_tm': parse_datetime(row['insert_tm']),
                    're_name': row['re_name'],
                    'status': int(row['status']) if row['status'] else None,
                    're_time': parse_datetime(row['re_time']),
                    'shi': shi,
                    'xian': xian,
                    'lgtd': lgtd,
                    'lttd': lttd
                })

            return items

        except Exception as e:
            logger.error(f"获取所有过滤异常数据失败: {e}")
            return []

    @staticmethod
    def get_by_station_and_time(db_manager: UnifiedDatabaseManager, stcd: str, tm: datetime) -> Optional[Dict]:
        """根据测站编码和时间获取异常记录"""
        try:
            sql = QueryBuilder.build_select(
                table='TZX_STCD_EXCE',
                columns=['stcd', 'stnm', 'aid', 'tm', 'val', 'rem', 'insert_tm', 'status'],
                where_clause='stcd = %s AND tm = %s AND rem IS NULL AND (status = 0 OR status IS NULL)',
                order_by='insert_tm DESC'
            )

            # 调试：记录查询参数
            formatted_time = tm.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"查询参数: stcd={stcd}, tm={formatted_time}")
            logger.info(f"执行SQL: {sql}")

            result = db_manager.execute_query(sql, (stcd, formatted_time))

            # 调试：记录查询结果
            if result['success']:
                results = result['results']
                logger.info(f"查询结果数量: {len(results)}")
                if len(results) > 0:
                    logger.info(f"第一条记录: {results[0]}")
                else:
                    # 尝试查找所有该测站的记录进行对比
                    debug_sql = "SELECT stcd, tm, rem, status FROM TZX_STCD_EXCE WHERE stcd = %s ORDER BY tm DESC LIMIT 5"
                    debug_result = db_manager.execute_query(debug_sql, (stcd,))
                    debug_results = debug_result['results']
                    logger.info(f"测站 {stcd} 的所有记录: {debug_results}")
            else:
                logger.error(f"查询失败: {result.get('error', '未知错误')}")
                results = []
            if results:
                return {
                    'stcd': results[0]['stcd'],
                    'stnm': results[0]['stnm'],
                    'aid': results[0]['aid'],
                    'val': float(results[0]['val']) if results[0]['val'] else None,
                    'rem': results[0]['rem'],
                    'tm': results[0]['tm'] if isinstance(results[0]['tm'], datetime) else datetime.strptime(results[0]['tm'], '%Y-%m-%d %H:%M:%S'),
                    'insert_tm': results[0]['insert_tm'] if isinstance(results[0]['insert_tm'], datetime) else datetime.strptime(results[0]['insert_tm'], '%Y-%m-%d %H:%M:%S')
                }
            return None

        except Exception as e:
            logger.error(f"获取异常记录失败: {e}")
            return None

    @staticmethod
    def update_remark(db_manager: UnifiedDatabaseManager, stcd: str, rem: str, tm: datetime,
                       re_name: str, status: int) -> Dict[str, Any]:
        """更新异常记录的备注信息"""
        try:
            # 移除不合理的时间验证，允许处理历史异常数据
            # 注释：异常数据可能是几天前的，不应该用当前时间来限制
            logger.info(f"准备更新异常记录: 测站={stcd}, 异常时间={tm}")

            # 获取当前记录
            current_exception = ExceptionData.get_by_station_and_time(db_manager, stcd, tm)
            if not current_exception:
                raise ValueError(f"测站 {stcd} 没有待反馈的异常数据")

            # 更新记录
            update_sql = QueryBuilder.build_update(
                table='TZX_STCD_EXCE',
                data={
                    'rem': rem,
                    're_name': re_name,
                    'status': status,
                    're_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                where_clause='stcd = %s AND tm = %s'
            )

            # 直接执行更新，不使用事务管理器避免rollback问题
            # 准备更新数据
            update_data = {
                'rem': rem,
                're_name': re_name,
                'status': status,
                're_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 重新构建SQL
            update_sql = QueryBuilder.build_update(
                table='TZX_STCD_EXCE',
                data=update_data,
                where_clause='stcd = %s AND tm = %s'
            )

            # 准备参数：SET数据参数在前，WHERE条件参数在后
            set_params = tuple(update_data.values())
            where_params = (stcd, tm.strftime('%Y-%m-%d %H:%M:%S'))
            all_params = set_params + where_params

            # 执行更新并获取结果
            result = db_manager.execute_query(update_sql, all_params)

            # 检查更新结果
            if not result['success']:
                raise Exception(f"数据库更新失败: {result.get('error', '未知错误')}")

            if result['affected_rows'] == 0:
                raise ValueError(f"未找到匹配的异常记录进行更新，测站={stcd}, 时间={tm}")

            logger.info(f"异常记录更新成功: {stcd}, {tm}, 影响行数: {result['affected_rows']}")

            return {
                'updated_count': result['affected_rows'],
                'detail': {
                    'stcd': stcd,
                    'stnm': current_exception['stnm'],
                    'exception_time': tm.strftime('%Y-%m-%d %H:%M:%S'),
                    'old_remark': current_exception['rem'],
                    'new_remark': rem,
                    're_name': re_name,
                    'status': status,
                    're_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

        except ValueError as e:
            # 重新抛出ValueError，让上层处理
            raise e
        except Exception as e:
            logger.error(f"更新异常记录失败: {e}")
            raise e

    @staticmethod
    def get_statistics(db_manager: UnifiedDatabaseManager) -> Dict[str, Any]:
        """获取异常数据统计信息"""
        try:
            # 统计待反馈异常数据总数
            pending_sql = "SELECT COUNT(*) as total_pending FROM TZX_STCD_EXCE WHERE 1=1 AND rem IS NULL"
            pending_result = db_manager.execute_query(pending_sql)
            total_pending = pending_result['results'][0]['total_pending'] if pending_result and pending_result.get('success') and pending_result.get('results') else 0

            # 统计涉及的测站数量
            station_sql = "SELECT COUNT(DISTINCT stcd) as station_count FROM TZX_STCD_EXCE WHERE 1=1 AND rem IS NULL"
            station_result = db_manager.execute_query(station_sql)
            station_count = station_result['results'][0]['station_count'] if station_result and station_result.get('success') and station_result.get('results') else 0

            # 统计涉及的团场数量
            farm_sql = "SELECT COUNT(DISTINCT aid) as farm_count FROM TZX_STCD_EXCE WHERE 1=1 AND rem IS NULL AND aid IS NOT NULL"
            farm_result = db_manager.execute_query(farm_sql)
            farm_count = farm_result['results'][0]['farm_count'] if farm_result and farm_result.get('success') and farm_result.get('results') else 0

            # 获取最新异常时间
            latest_sql = "SELECT MAX(tm) as latest_time FROM TZX_STCD_EXCE WHERE 1=1"
            latest_result = db_manager.execute_query(latest_sql)
            latest_time = latest_result['results'][0]['latest_time'] if latest_result and latest_result.get('success') and latest_result.get('results') else None

            return {
                'total_pending': total_pending,
                'station_count': station_count,
                'farm_count': farm_count,
                'latest_time': latest_time.strftime('%Y-%m-%d %H:%M:%S') if latest_time else None
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_pending': 0,
                'station_count': 0,
                'farm_count': 0,
                'latest_time': None
            }

    @staticmethod
    def health_check(db_manager: UnifiedDatabaseManager) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 执行简单查询测试连接
            result = db_manager.execute_query("SELECT 1 as health_check FROM TZX_STCD_EXCE LIMIT 1")

            return {
                'status': 'healthy' if result and result.get('success') else 'unhealthy',
                'message': '数据库连接正常' if result and result.get('success') else '数据库连接异常',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'健康检查失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }


# 表创建脚本
def create_all_tables(db_manager: UnifiedDatabaseManager):
    """创建所有必需的表"""
    try:
        # 创建异常数据表
        ExceptionData.create_table_if_not_exists(db_manager)
        logger.info("所有数据表创建完成")

    except Exception as e:
        logger.error(f"创建数据表失败: {e}")
        raise e