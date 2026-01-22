# STATAU - 云端计量经济学分析平台

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3.3-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

## 📖 项目简介

**STATAU** 是一个基于 Web 的在线数据分析平台，旨在为经济学研究者提供简易的 Stata 替代方案。用户无需安装任何软件，只需通过浏览器即可完成常见的计量经济学分析，并生成符合学术论文标准的回归结果表格。

### 🎯 核心特性

- **零代码操作**：通过可视化界面完成所有分析配置
- **学术标准输出**：自动生成 esttab 风格的 HTML 表格，支持直接复制到论文
- **多种分析方法**：支持 OLS、固定效应、Logit、Probit、描述统计、相关性分析、VIF 检验
- **灵活的标准误**：支持普通标准误、稳健标准误、聚类标准误
- **云端计算**：无需安装 Stata 或配置 Python 环境

---

## 🏗️ 项目架构

本项目采用 **Flask 应用工厂模式** 和 **三层架构** 设计，遵循"解耦优于复用"的设计理念。

```
STATAU/
├── app.py                    # 应用入口（工厂函数）
├── config.py                 # 配置模块（开发/生产/测试环境）
├── extensions.py             # Flask 扩展初始化（SQLAlchemy, Flask-Login）
├── requirements.txt          # Python 依赖
├── README.md                 # 本文件
├── ARCHITECTURE.md           # 详细架构说明
│
├── blueprints/               # 🔵 蓝图模块（路由层）
│   ├── __init__.py          # 蓝图注册入口
│   ├── pages.py             # 页面路由（首页、分析页、帮助页）
│   ├── auth.py              # 认证路由（登录、注册、登出、验证码）
│   └── analysis.py          # 分析路由（上传、分析、预览、清空）
│
├── services/                 # 🟢 服务层（业务逻辑）
│   ├── __init__.py          # 服务层入口
│   ├── file_service.py      # 文件服务（上传、读取、预览）
│   └── captcha_service.py   # 验证码服务（生成、验证）
│
├── core/                     # 🟠 核心模块（数据模型和算法）
│   ├── __init__.py          # 核心模块入口
│   ├── auth.py              # 用户模型（User）
│   ├── models.py            # 统计模型（StataModel）
│   └── table_generator.py   # 表格生成器
│
├── templates/                # 📄 Jinja2 模板
│   ├── base.html            # 基础模板（导航栏、登录框）
│   ├── home.html            # 首页
│   ├── analysis.html        # 数据分析页
│   ├── database.html        # 数据库页
│   └── help.html            # 帮助手册页
│
├── static/                   # 📁 静态资源
│   ├── css/                 # CSS 样式
│   ├── js/                  # JavaScript
│   └── bootstrap-icons/     # Bootstrap 图标
│
├── uploads/                  # 📤 用户上传文件目录
└── instance/                 # 🗄️ 实例配置和数据库
    └── statau.db            # SQLite 数据库
```

### 三层架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                   Blueprints (路由层)                        │
│  职责：处理 HTTP 请求/响应，参数验证，调用服务层               │
│  文件：blueprints/pages.py, auth.py, analysis.py            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Services (服务层)                         │
│  职责：封装可复用的业务逻辑，不依赖 Flask request/response    │
│  文件：services/file_service.py, captcha_service.py         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core (核心层)                           │
│  职责：数据模型定义、统计算法实现、表格生成                    │
│  文件：core/auth.py, models.py, table_generator.py          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/statau.git
cd statau

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python app.py
```

### 访问应用

打开浏览器访问：`http://localhost:5000`

---

## 📦 核心依赖

| 库名 | 版本 | 用途 |
|------|------|------|
| Flask | 2.3.3 | Web 框架 |
| Flask-Login | - | 用户登录管理 |
| Flask-SQLAlchemy | - | 数据库 ORM |
| pandas | 2.0.3 | 数据处理 |
| numpy | 1.24.3 | 数值计算 |
| statsmodels | 0.14.0 | 统计模型（OLS、Logit、Probit） |
| linearmodels | 4.31 | 面板数据模型（固定效应） |
| scipy | 1.10.1 | 科学计算（相关性分析） |
| captcha | - | 验证码生成 |
| Werkzeug | 2.3.7 | 密码哈希 |

### 安装核心依赖

```bash
pip install flask flask-login flask-sqlalchemy pandas numpy statsmodels linearmodels scipy captcha
```

---

## 📁 模块详解

### 1. app.py - 应用入口

使用 **应用工厂模式**，主要职责：
- 创建 Flask 应用实例
- 加载配置（开发/生产/测试）
- 初始化扩展（SQLAlchemy、Flask-Login）
- 注册蓝图

```python
from app import create_app

# 开发环境
app = create_app()

# 生产环境
from config import ProductionConfig
app = create_app(ProductionConfig)
```

### 2. config.py - 配置模块

包含三套配置类：

| 配置类 | 用途 | DEBUG |
|--------|------|-------|
| `DevelopmentConfig` | 本地开发 | True |
| `ProductionConfig` | 服务器部署 | False |
| `TestingConfig` | 单元测试 | True |

关键配置项：
```python
SECRET_KEY = 'your-secret-key'
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/statau.db'
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
```

### 3. extensions.py - 扩展初始化

集中管理 Flask 扩展，避免循环导入：

```python
from extensions import db, login_manager

# 在 create_app() 中初始化
db.init_app(app)
login_manager.init_app(app)
```

### 4. blueprints/ - 蓝图模块

#### pages.py - 页面路由
| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页 |
| `/analysis` | GET | 数据分析页（需登录） |
| `/database` | GET | 数据库页 |
| `/help` | GET | 帮助手册页 |

#### auth.py - 认证路由
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/login` | POST | 用户登录 |
| `/api/register` | POST | 用户注册 |
| `/api/logout` | GET | 用户登出 |
| `/api/captcha` | GET | 获取验证码图片 |

#### analysis.py - 分析路由
| 路由 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传数据文件 |
| `/analyze` | POST | 执行分析 |
| `/preview` | GET | 数据预览 |
| `/clear_table` | POST | 清空结果表格 |

### 5. services/ - 服务层

#### FileService - 文件服务
```python
from services.file_service import FileService

file_service = FileService(upload_folder='uploads')

# 保存文件
filepath = file_service.save_file(file_storage, filename)

# 读取数据
df = file_service.read_datafile(filepath)

# 获取预览
preview = file_service.get_preview_data(filename, nrows=10)
```

#### CaptchaService - 验证码服务
```python
from services.captcha_service import CaptchaService

captcha_service = CaptchaService()

# 生成验证码
code, image_bytes = captcha_service.generate()

# 验证
is_valid = captcha_service.verify(user_input, stored_code)
```

### 6. core/ - 核心模块

#### User 模型 (core/auth.py)
```python
from core.auth import User

# 创建用户
user = User(username='test', email='test@example.com')
user.set_password('password123')

# 验证密码
if user.check_password('password123'):
    print('密码正确')
```

#### StataModel 统计模型 (core/models.py)
```python
from core.models import StataModel

# OLS 回归
model = StataModel(df, y_var='y', x_vars=['x1', 'x2'], method='ols')
result = model.fit(decimals=3)
coeffs, stats = model.get_coeffs_dataframe()

# 固定效应模型
model = StataModel(
    df, y_var='y', x_vars=['x1', 'x2'], method='fe',
    panel_ids={'entity': 'firm_id', 'time': 'year'},
    fe_vars=['firm_id', 'year'],
    se_options={'type': 'cluster', 'cluster_var': 'firm_id'}
)

# 描述统计
model = StataModel(df, y_var=None, x_vars=['x1', 'x2', 'x3'], method='desc')
model.fit()
html = model.custom_html
```

支持的分析方法：
| method | 说明 |
|--------|------|
| `ols` | 普通最小二乘回归 |
| `fe` | 固定效应模型 |
| `logit` | Logit 模型 |
| `probit` | Probit 模型 |
| `desc` | 描述性统计 |
| `corr` | 相关性分析（带显著性星号） |
| `vif` | VIF 共线性检验 |

#### 表格生成器 (core/table_generator.py)
```python
from core.table_generator import generate_merged_html

html = generate_merged_html(
    models_data,           # 模型数据列表
    title="Table 1",       # 表格标题
    decimals=3,            # 小数位数
    show_se=True,          # 显示标准误（False 则显示 t 值）
    export_options=['nobs', 'r2', 'adj_r2', 'f_stat']
)
```

---

## 🖥️ API 接口文档

### 用户认证

#### POST /api/login
登录接口

**请求体：**
```json
{
    "username": "用户名或邮箱",
    "password": "密码"
}
```

**响应：**
```json
// 成功
{"status": "success", "user": {"username": "xxx", "role": "user"}}

// 失败
{"error": "用户不存在"} // 401
{"error": "密码错误"}   // 401
```

#### POST /api/register
注册接口

**请求体：**
```json
{
    "username": "用户名",
    "email": "邮箱",
    "password": "密码",
    "captcha": "验证码"
}
```

**响应：**
```json
// 成功
{"status": "success", "message": "注册成功，请登录"}

// 失败
{"error": "用户名已被使用"}  // 409
{"error": "验证码错误"}      // 400
```

### 数据分析

#### POST /upload
上传数据文件

**请求：** `multipart/form-data`，包含 `file` 字段

**响应：**
```json
{
    "message": "Success",
    "filename": "data.csv",
    "columns": ["x1", "x2", "y", "firm_id", "year"]
}
```

#### POST /analyze
执行分析

**请求体：**
```json
{
    "filename": "data.csv",
    "method": "ols",
    "action": "new",
    "y_var": "y",
    "x_vars": ["x1", "x2"],
    "decimals": 3,
    "show_se": true,
    "table_title": "Table 1",
    "se_type": "robust",
    "export_options": ["nobs", "r2", "adj_r2"]
}
```

**响应：**
```json
{
    "html_table": "<div class='table-editable-container'>...</div>",
    "raw_output": "OLS Regression Results...",
    "model_count": 1
}
```

#### GET /preview?filename=xxx
数据预览

**响应：**
```json
{
    "columns": ["x1", "x2", "y"],
    "dtypes": {"x1": "float64", "x2": "float64", "y": "float64"},
    "preview": [{"x1": 1.0, "x2": 2.0, "y": 3.0}, ...]
}
```

---

## 🌐 部署指南

### 开发环境

```bash
python app.py
# 访问 http://localhost:5000
```

### 生产环境（使用 Gunicorn）

```bash
# 安装 Gunicorn
pip install gunicorn

# 前台运行（测试用）
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# 后台运行（推荐）
nohup gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()" > gunicorn.log 2>&1 &
```

### 使用 systemd 管理服务

创建服务文件 `/etc/systemd/system/statau.service`：

```ini
[Unit]
Description=STATAU Gunicorn Service
After=network.target

[Service]
User=your_username
Group=your_group
WorkingDirectory=/path/to/statau
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable statau
sudo systemctl start statau
sudo systemctl status statau
```

### Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/statau/static;
        expires 30d;
    }
}
```

---

## ⚠️ 注意事项

### 本地版 vs 服务器版

代码中保留了两套实现：

1. **本地版**（默认）：使用全局变量 `RESULT_CACHE` 存储分析结果
2. **服务器版**：使用 Flask Session 存储（已注释）

部署到服务器时，需要在 `blueprints/analysis.py` 中：
- 取消 session 相关代码的注释
- 注释掉 `RESULT_CACHE` 相关代码

### 数据库

- 开发环境使用 SQLite（`instance/statau.db`）
- 生产环境建议迁移到 PostgreSQL 或 MySQL
- 修改 `config.py` 中的 `SQLALCHEMY_DATABASE_URI`

### 文件上传

- 支持格式：CSV、Excel（.xlsx, .xls）、Stata（.dta）
- 最大文件大小：50MB（可在 config.py 中修改）
- 上传目录：`uploads/`

---

## 🔧 开发指南

### 添加新的分析方法

1. 在 `core/models.py` 的 `StataModel` 类中添加新方法
2. 在 `_fit_regression()` 或 `_fit_basic_analysis()` 中添加分支
3. 在 `templates/analysis.html` 中添加对应的 UI 选项

### 添加新的 API 接口

1. 确定接口属于哪个蓝图（auth/analysis/pages）
2. 在对应蓝图文件中添加路由函数
3. 如果需要复用逻辑，在 `services/` 中创建服务类

### 添加新的页面

1. 在 `templates/` 中创建新模板（继承 `base.html`）
2. 在 `blueprints/pages.py` 中添加路由
3. 更新 `base.html` 导航栏（如需要）

---

## 📝 代码风格

- 每个文件顶部都有详细的模块说明注释
- 函数和类都有 docstring
- 使用类型注解（Type Hints）
- 遵循 PEP 8 规范

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

如有问题，请联系项目维护者。