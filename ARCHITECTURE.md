# STATAU 项目架构说明

## 📁 目录结构

```
STATAU/
├── app.py                    # 应用入口（工厂函数）
├── config.py                 # 配置模块
├── extensions.py             # Flask 扩展初始化
├── requirements.txt          # Python 依赖
│
├── blueprints/               # 蓝图模块（路由层）
│   ├── __init__.py          # 蓝图注册入口
│   ├── pages.py             # 页面路由（首页、分析页等）
│   ├── auth.py              # 认证路由（登录、注册、登出）
│   └── analysis.py          # 分析路由（上传、分析、预览）
│
├── services/                 # 服务层（业务逻辑）
│   ├── __init__.py          # 服务层入口
│   ├── file_service.py      # 文件服务（上传、读取、预览）
│   └── captcha_service.py   # 验证码服务
│
├── core/                     # 核心模块（数据模型和算法）
│   ├── __init__.py          # 核心模块入口
│   ├── auth.py              # 用户模型 (User)
│   ├── models.py            # 统计模型 (StataModel)
│   └── table_generator.py   # 表格生成器
│
├── templates/                # Jinja2 模板
│   ├── base.html            # 基础模板
│   ├── home.html            # 首页
│   ├── analysis.html        # 分析页
│   ├── database.html        # 数据库页
│   └── help.html            # 帮助页
│
├── static/                   # 静态资源
│   ├── css/
│   ├── js/
│   └── bootstrap-icons/
│
├── uploads/                  # 上传文件目录
├── instance/                 # 实例配置和数据库
│   └── statau.db            # SQLite 数据库
│
└── docs/                     # 文档
    ├── ARCHITECTURE.md      # 本文件
    └── 部署.md              # 部署说明
```

## 🏗️ 架构设计理念

### 核心原则：解耦优于复用

1. **模块化**：每个功能模块（认证、分析、数据库管理）都是独立的
2. **反过度抽象**：宁愿代码有些许冗余，也不强行把逻辑不同的模块绑在一起
3. **明确性**：添加新功能时，不需要猜测哪些是公共组件

### 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Blueprints (路由层)                      │
│  处理 HTTP 请求/响应，参数验证，调用服务层                      │
│  pages.py | auth.py | analysis.py                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Services (服务层)                        │
│  封装可复用的业务逻辑，不依赖 Flask request/response           │
│  file_service.py | captcha_service.py                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Core (核心层)                          │
│  数据模型、统计算法、表格生成                                  │
│  auth.py (User) | models.py (StataModel) | table_generator  │
└─────────────────────────────────────────────────────────────┘
```

## 📦 模块详解

### 1. app.py - 应用入口

使用**应用工厂模式**，主要职责：
- 创建 Flask 应用实例
- 加载配置
- 初始化扩展
- 注册蓝图

```python
from app import create_app
app = create_app()  # 开发环境
app = create_app(ProductionConfig)  # 生产环境
```

### 2. config.py - 配置模块

包含三套配置：
- `DevelopmentConfig`: 开发环境
- `ProductionConfig`: 生产环境
- `TestingConfig`: 测试环境

### 3. extensions.py - 扩展初始化

集中管理 Flask 扩展：
- `db`: SQLAlchemy 数据库
- `login_manager`: Flask-Login 登录管理

### 4. blueprints/ - 蓝图模块

| 文件 | URL 前缀 | 职责 |
|------|----------|------|
| pages.py | / | 页面渲染（首页、分析页等） |
| auth.py | /api | 用户认证（登录、注册、登出） |
| analysis.py | / | 数据分析（上传、分析、预览） |

### 5. services/ - 服务层

| 文件 | 职责 |
|------|------|
| file_service.py | 文件上传、读取、预览 |
| captcha_service.py | 验证码生成和验证 |

### 6. core/ - 核心模块

| 文件 | 职责 |
|------|------|
| auth.py | User 数据模型 |
| models.py | StataModel 统计模型 |
| table_generator.py | HTML 表格生成 |

## 🔄 请求流程示例

### 用户登录流程

```
1. 用户提交登录表单
   POST /api/login {username, password}
   
2. blueprints/auth.py 接收请求
   - 参数验证
   - 查询 User 模型
   - 验证密码
   - 调用 Flask-Login 登录
   
3. 返回 JSON 响应
   {status: 'success', user: {...}}
```

### 数据分析流程

```
1. 用户上传文件
   POST /upload (multipart/form-data)
   
2. blueprints/analysis.py 接收请求
   - 调用 FileService.save_file()
   - 调用 FileService.read_datafile()
   - 返回列名列表
   
3. 用户配置分析参数并提交
   POST /analyze {filename, method, y_var, x_vars, ...}
   
4. blueprints/analysis.py 处理分析请求
   - 调用 FileService.read_datafile_by_name()
   - 创建 StataModel 实例
   - 调用 model.fit()
   - 调用 generate_merged_html()
   - 返回 HTML 表格
```

## 🚀 开发指南

### 添加新的分析方法

1. 在 `core/models.py` 的 `StataModel` 类中添加新方法
2. 在 `_fit_regression()` 或 `_fit_basic_analysis()` 中添加分支
3. 前端 `analysis.html` 添加对应的 UI 选项

### 添加新的 API 接口

1. 确定接口属于哪个蓝图（auth/analysis/pages）
2. 在对应蓝图文件中添加路由函数
3. 如果需要复用逻辑，在 services/ 中创建服务类

### 添加新的页面

1. 在 `templates/` 中创建新模板
2. 在 `blueprints/pages.py` 中添加路由
3. 更新 `base.html` 导航栏（如需要）

## ⚠️ 注意事项

### 本地版 vs 服务器版

代码中保留了两套实现：
- **本地版**：使用全局变量 `RESULT_CACHE` 存储分析结果
- **服务器版**：使用 Flask Session 存储（已注释）

部署到服务器时，需要：
1. 取消 `app.py` 中 Session 配置的注释
2. 取消 `blueprints/analysis.py` 中 session 相关代码的注释
3. 注释掉 `RESULT_CACHE` 相关代码

### 数据库迁移

当前使用 SQLite，生产环境建议：
1. 迁移到 PostgreSQL 或 MySQL
2. 修改 `config.py` 中的 `SQLALCHEMY_DATABASE_URI`

## 📝 代码风格

- 每个文件顶部都有详细的模块说明
- 函数和类都有 docstring
- 使用类型注解（Type Hints）
- 遵循 PEP 8 规范

## 启动方式
# 开发环境
python app.py

# 生产环境 (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"