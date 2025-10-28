#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常数据管理API启动文件
"""

from app import create_app

# 创建应用实例
app = create_app('development')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True) 