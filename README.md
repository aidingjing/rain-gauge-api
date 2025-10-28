# 雨量站API系统 (Rain Gauge API System)

基于Python Flask的雨量监测数据API服务，提供完整的雨量站数据管理和异常监测功能。

## 🚀 功能特性

### 核心功能
- **雨量站管理**: 站点信息、行政区划、经纬度坐标管理
- **实时数据监测**: 雨量数据采集、存储和查询
- **异常检测**: 自动识别异常数据，支持反馈和修正
- **统计分析**: 多维度数据统计和可视化支持
- **数据导出**: 支持多种格式的数据导出

### API端点
- `GET /api/stations` - 获取雨量站列表
- `GET /api/stations/exception` - 获取异常数据
- `GET /api/stations/statistics` - 获取统计信息
- `POST /api/stations/{stcd}/feedback` - 提交异常反馈
- `GET /api/health` - 系统健康检查

## 🛠️ 技术架构

### 后端技术栈
- **框架**: Flask + Flask-RESTX
- **数据库**: MySQL
- **ORM**: SQLAlchemy
- **数据验证**: Marshmallow
- **API文档**: Swagger/OpenAPI

### 项目结构
```
├── app/
│   ├── __init__.py          # Flask应用工厂
│   ├── models.py            # 数据模型
│   ├── routes.py            # API路由
│   ├── schemas.py           # 数据序列化模式
│   ├── validators.py        # 输入验证
│   └── database.py          # 数据库管理
├── database.py              # 数据库配置
├── api_config.py            # API配置
├── run.py                   # 应用启动入口
└── README.md               # 项目文档
```

## 📦 安装部署

### 环境要求
- Python 3.8+
- MySQL 5.7+
- Redis (可选，用于缓存)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/aidingjing/rain-gauge-api.git
cd rain-gauge-api
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置数据库**
```bash
# 编辑 database.py 配置数据库连接
# 或设置环境变量
export DATABASE_URL="mysql://user:password@localhost/rain_gauge"
```

4. **初始化数据库**
```bash
python -c "from database import init_database; init_database()"
```

5. **启动应用**
```bash
python run.py
```

## 🔧 配置说明

### 数据库配置
在 `database.py` 中配置MySQL连接参数：
- 主机地址
- 端口号
- 数据库名
- 用户名和密码

### API配置
在 `api_config.py` 中配置：
- API版本
- 响应格式
- 分页参数
- 日志级别

## 📊 API使用示例

### 获取雨量站列表
```bash
curl "http://localhost:5000/api/stations?page=1&page_size=20"
```

### 获取异常数据
```bash
curl "http://localhost:5000/api/stations/exception?status=0&page=1"
```

### 提交异常反馈
```bash
curl -X POST "http://localhost:5000/api/stations/ST001/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "数据正常，误报"}'
```

## 🔍 数据模型

### 雨量站信息 (ST_STBPRP_B)
- 站码 (stcd)
- 站名 (stnm)
- 河流名称 (rvnm)
- 行政区划代码 (adcd)
- 经纬度坐标 (lgtd, lttd)

### 异常数据 (TZX_STCD_EXCE)
- 异常ID (eid)
- 站码 (stcd)
- 时间戳 (tm)
- 异常类型
- 反馈信息 (rem)

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 更新日志

### v1.0.0 (2025-10-28)
- ✨ 初始版本发布
- 🚀 完整的雨量站管理功能
- 🔍 异常检测和反馈系统
- 📊 数据统计和导出功能
- 🛠️ 完善的错误处理和日志记录

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者

**aidingjing** - GitHub: [@aidingjing](https://github.com/aidingjing)

## 🙏 致谢

感谢所有为雨量监测事业做出贡献的开发者和数据维护人员。

---

⚡ **快速开始**: `python run.py` 即可启动API服务！