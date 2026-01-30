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
- **多格式导出**：支持导出为 Word (.docx)、Excel (.xlsx)、TXT (.txt)、CSV (.csv) 格式
- **多种分析方法**：支持 OLS、固定效应、随机效应、混合效应、Logit、Probit、描述统计、分组描述统计、频数统计、相关性分析、VIF 检验
- **模型检验**：支持 F检验（固定效应 vs 混合OLS）、Hausman检验（固定效应 vs 随机效应，含sigmamore选项）
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
│   ├── analysis.html        # 数据分析页（模块化主框架）
│   ├── analysis_modules/    # 分析功能模块
│   │   ├── descriptive.html # 描述性统计模块
│   │   ├── grouped_descriptive.html # 分组描述性统计模块
│   │   ├── frequency.html   # 频数统计模块
│   │   ├── correlation.html # 相关性分析模块
│   │   ├── vif.html         # VIF检验模块
│   │   ├── regression.html  # 回归模型模块
│   │   └── model_test.html  # 模型检验模块
│   ├── database.html        # 数据库页
│   └── help.html            # 帮助手册页
│
├── static/                   # 📁 静态资源
│   ├── css/                 # CSS 样式
│   ├── js/                  # JavaScript 脚本
│   │   ├── export.js        # 导出功能模块
│   │   ├── FileSaver.min.js # 文件下载库
│   │   ├── html-docx.js     # Word导出库
│   │   └── xlsx.full.min.js # Excel导出库
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
| `/f_test` | POST | F检验（固定效应 vs 混合OLS） |
| `/hausman_test` | POST | Hausman检验（固定效应 vs 随机效应） |

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

# 随机效应模型
model = StataModel(
    df, y_var='y', x_vars=['x1', 'x2'], method='re',
    panel_ids={'entity': 'firm_id', 'time': 'year'},
    se_options={'type': 'robust'}
)

# 混合效应模型（Pooled OLS）
model = StataModel(
    df, y_var='y', x_vars=['x1', 'x2'], method='pooled',
    panel_ids={'entity': 'firm_id', 'time': 'year'},
    se_options={'type': 'cluster', 'cluster_var': 'firm_id'}
)

# 描述统计
model = StataModel(df, y_var=None, x_vars=['x1', 'x2', 'x3'], method='desc')
model.fit(decimals=3, table_title="Descriptive Statistics")
html = model.custom_html

# 分组描述统计
model = StataModel(
    df, y_var=None, x_vars=['x1', 'x2', 'x3'], method='grouped_desc',
    group_var='gender',
    desc_options=['mean', 'std', 'min', 'max', 'nobs']
)
model.fit(decimals=3, table_title="Grouped Descriptive Statistics")
html = model.custom_html

# 频数统计（单变量）
model = StataModel(df, y_var=None, x_vars=['category'], method='freq')
model.fit(decimals=2, table_title="Category Frequency Table")
html = model.custom_html

# 频数统计（多变量，分开展示）
model = StataModel(df, y_var=None, x_vars=['category', 'gender'], method='freq')
model.fit(decimals=2)
html = model.custom_html

# 频数统计（多变量，合并展示）
model = StataModel(
    df, y_var=None, x_vars=['category', 'gender'], method='freq',
    merge_freq_tables=True
)
model.fit(decimals=2, table_title="Merged Frequency Table")
html = model.custom_html
```

支持的分析方法：
| method | 说明 |
|--------|------|
| `ols` | 普通最小二乘回归 |
| `fe` | 固定效应模型 |
| `re` | 随机效应模型 |
| `pooled` | 混合效应模型（Pooled OLS） |
| `logit` | Logit 模型 |
| `probit` | Probit 模型 |
| `desc` | 描述性统计 |
| `grouped_desc` | 分组描述性统计 |
| `freq` | 频数统计（类似Stata的tab命令） |
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

### 模型检验

#### POST /f_test
F检验：固定效应模型 vs 混合OLS模型

**请求体：**
```json
{
    "filename": "data.csv",
    "y_var": "y",
    "x_vars": ["x1", "x2"],
    "panel_entity": "firm_id",
    "panel_time": "year",
    "decimals": 4
}
```

**响应：**
```json
{
    "result": {
        "test_name": "F Test (Fixed Effects vs Pooled OLS)",
        "f_statistic": 12.34,
        "df1": 13,
        "df2": 126,
        "p_value": 0.0000,
        "significance": "***",
        "conclusion": "强烈拒绝原假设，应使用固定效应模型"
    }
}
```

#### POST /hausman_test
Hausman检验：固定效应模型 vs 随机效应模型

**请求体：**
```json
{
    "filename": "data.csv",
    "y_var": "y",
    "x_vars": ["x1", "x2"],
    "panel_entity": "firm_id",
    "panel_time": "year",
    "decimals": 4,
    "sigmamore": true
}
```

**参数说明：**
- `sigmamore`（可选，默认false）：是否使用sigmamore选项
  - `false`：使用原始协方差矩阵，可能遇到"V_b-V_B is not positive definite"警告
  - `true`：使用基于随机效应的统一方差估计，解决协方差矩阵不正定问题，得到与Stata一致的结果

**响应：**
```json
{
    "result": {
        "test_name": "Hausman Test (Fixed Effects vs Random Effects)",
        "chi2_statistic": 68.29,
        "df": 10,
        "p_value": 0.0000,
        "significance": "***",
        "conclusion": "强烈拒绝原假设，应使用固定效应模型",
        "fe_coeffs": {...},
        "re_coeffs": {...},
        "coeff_diff": {...},
        "std_err_diff": {...}
    }
}
```

### 频数统计

#### POST /analyze (method='freq')
频数统计接口（类似Stata的tab命令）

**请求体：**
```json
{
    "filename": "data.csv",
    "method": "freq",
    "action": "new",
    "x_vars": ["category", "gender"],
    "decimals": 2,
    "table_title": "频数统计表",
    "merge_freq_tables": false
}
```

**参数说明：**
- `x_vars`：需要进行频数统计的变量列表（支持数值型和分类变量）
- `merge_freq_tables`（可选，默认false）：是否合并多个变量的频数表
  - `false`：每个变量生成独立的频数表
  - `true`：所有变量合并在一个表格中展示
- `decimals`：百分比的小数位数

**响应：**
```json
{
    "html_table": "<div class='table-editable-container'>...</div>",
    "raw_output": "Descriptive/Correlation/VIF Analysis Completed.",
    "model_count": 0
}
```

**频数表格式（分开展示）：**
```
Category Frequency Table
-------------------------
category | Freq. | Percent | Cum.
---------|-------|---------|------
A        | 25    | 25.00   | 25.00
B        | 30    | 30.00   | 55.00
C        | 25    | 25.00   | 80.00
D        | 20    | 20.00   | 100.00
Total    | 100   | 100.00  | 100.00
```

**频数表格式（合并展示）：**
```
Merged Frequency Table
----------------------
Variable | Value  | Freq. | Percent | Cum.
---------|--------|-------|---------|------
category | A      | 25    | 25.00   | 25.00
         | B      | 30    | 30.00   | 55.00
         | C      | 25    | 25.00   | 80.00
         | D      | 20    | 20.00   | 100.00
category | Subtotal| 100  | 100.00  | 100.00
---------|--------|-------|---------|------
gender   | Female | 48    | 48.00   | 48.00
         | Male   | 52    | 52.00   | 100.00
gender   | Subtotal| 100  | 100.00  | 100.00
```

**大数据量警告机制：**

当某个变量的分类数量超过10000时，系统会先返回警告信息：

```json
{
    "warning": "large_categories",
    "message": "检测到以下变量的分类数量超过10000，生成频数表可能需要较长时间：",
    "details": [
        {
            "variable": "user_id",
            "unique_count": 15234
        }
    ]
}
```

用户确认后，需要在请求中添加 `"freq_confirmed": true` 参数重新提交。

---

## 📤 导出功能

### 功能概述

STATAU 支持将分析结果导出为多种格式，方便用户在不同场景下使用：

| 格式 | 扩展名 | 用途 | 特点 |
|------|--------|------|------|
| Word | .docx | 论文写作 | 保留学术表格格式，可直接插入论文 |
| Excel | .xlsx | 数据处理 | 可进一步编辑和计算 |
| TXT | .txt | 纯文本 | 跨平台兼容，易于分享 |
| CSV | .csv | 数据交换 | 标准格式，可导入其他统计软件 |

### 技术实现

导出功能采用**纯前端实现**，无需后端支持：

#### 核心文件
- **导出脚本**：[`static/js/export.js`](static/js/export.js) - 导出功能核心逻辑
- **依赖库**（本地化）：
  - [`FileSaver.min.js`](static/js/FileSaver.min.js) - 文件下载功能
  - [`html-docx.js`](static/js/html-docx.js) - Word文档生成
  - [`xlsx.full.min.js`](static/js/xlsx.full.min.js) - Excel表格生成

#### 核心函数
```javascript
// 获取当前激活模块
getCurrentActiveModule()

// 获取当前表格
getCurrentTable()

// 导出函数
exportToWord()   // 导出为Word
exportToExcel()  // 导出为Excel
exportToTxt()    // 导出为TXT
exportToCSV()    // 导出为CSV
```

### 使用方法

1. **运行分析**：在任意分析模块中完成数据分析
2. **查看结果**：结果表格上方会自动显示导出按钮
3. **选择格式**：点击相应按钮导出为所需格式
4. **下载文件**：浏览器自动下载文件

### 文件命名规则

导出的文件名格式：`表格标题_时间戳.扩展名`

示例：
- `Regression_Results_20260123_153045.docx`
- `描述性统计_20260123_153045.xlsx`

### 支持的模块

导出功能支持所有分析模块：

- ✅ 描述性统计
- ✅ 分组描述性统计
- ✅ 频数统计
- ✅ 相关性分析
- ✅ VIF共线性检验
- ✅ 回归模型（OLS、固定效应、随机效应、混合效应、Logit、Probit）
- ✅ 模型检验（F检验、Hausman检验）

### 特殊处理

#### 中文支持
- CSV和TXT文件添加UTF-8 BOM（`\ufeff`），确保中文正确显示
- Word和Excel使用UTF-8编码

#### 表格格式
- Word导出保留学术表格样式（Times New Roman字体，标准边框）
- Excel自动调整列宽（默认15个字符）
- TXT使用固定宽度对齐
- CSV遵循RFC 4180标准

#### 性能优化
- 使用防抖机制（100ms延迟）避免频繁更新
- 只监听必要的DOM变化
- 避免重复设置样式触发循环

### 技术细节

#### 模块激活检测
```javascript
// 只导出当前激活模块的表格
const activeModule = document.querySelector('.analysis-module.active');
const resultContainer = activeModule.querySelector('[id$="-result-container"]');
const table = resultContainer.querySelector('.academic-table, table');
```

#### 按钮显示逻辑
```javascript
// 自动显示/隐藏导出按钮
function updateExportButtonsVisibility() {
    // 1. 隐藏所有导出按钮
    // 2. 只显示当前激活模块的导出按钮
    // 3. 检查是否有表格内容
}
```

#### 防抖机制
```javascript
// 避免频繁触发更新
let updateTimeout = null;
const debouncedUpdate = function() {
    if (updateTimeout) clearTimeout(updateTimeout);
    updateTimeout = setTimeout(updateExportButtonsVisibility, 100);
};
```

### 故障排除

#### 问题：导出按钮不显示
**解决方案**：
1. 确认已生成分析结果
2. 检查浏览器控制台是否有JavaScript错误
3. 确认 `export.js` 文件已正确加载

#### 问题：导出文件无法打开
**解决方案**：
- Word文件：使用Office 2010+或WPS打开
- Excel文件：使用Excel 2010+或WPS打开
- 确认文件大小正常（不为0字节）

#### 问题：中文显示乱码
**解决方案**：
- CSV文件：使用Excel打开时选择UTF-8编码
- TXT文件：使用支持UTF-8的文本编辑器

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

### 前端模块化架构

分析页面采用**模块化设计**，每个功能拥有独立的前端模块文件：

- **模块目录**：`templates/analysis_modules/`
- **主框架**：[`templates/analysis.html`](templates/analysis.html) - 负责文件上传和模块切换
- **模块文件**：每个功能模块独立，包含自己的HTML、CSS和JavaScript

**模块特点**：
- ✅ 完全独立，互不干扰
- ✅ 命名规范化（带模块前缀）
- ✅ 易于维护和扩展
- ✅ 即使某个模块出bug也不影响其他模块

详细说明请查看：[`说明文件汇总/前端模块化重构说明.md`](说明文件汇总/前端模块化重构说明.md)

### 频数统计功能示例

频数统计功能是一个完整的模块化功能实现示例，展示了如何添加新的分析功能：

#### 功能特点
1. **支持多种数据类型**：数值型和分类变量
2. **灵活的展示方式**：分开展示或合并展示
3. **大数据量保护**：超过10000个分类时提示用户确认
4. **学术标准输出**：包含频数、百分比、累计百分比

#### 实现文件
- **后端模型**：[`core/models.py`](core/models.py) - `_fit_frequency()`, `_fit_frequency_single()`, `_fit_frequency_multiple()`, `_fit_frequency_merged()`
- **前端模块**：[`templates/analysis_modules/frequency.html`](templates/analysis_modules/frequency.html)
- **路由处理**：[`blueprints/analysis.py`](blueprints/analysis.py) - 包含大数据量预检查逻辑

#### 使用流程
1. 用户选择变量
2. 可选择是否合并表格
3. 系统检查分类数量（>10000时警告）
4. 用户确认后生成频数表
5. 显示包含频数、百分比、累计百分比的表格

### 分组描述性统计功能

分组描述性统计功能允许用户按照分类变量对数值型变量进行分组统计，是一个完整的模块化功能实现。

#### 功能特点
1. **按分组展示**：每个分组独立显示，清晰易读
2. **默认统计量**：默认输出均值和标准差
3. **灵活配置**：可自定义选择其他统计量（最小值、最大值、中位数、观测数）
4. **健壮的缺失值处理**：即使某个变量在某个分组中全是缺失值，也会显示（N=0，其他统计量显示"-"）

#### 实现文件
- **后端模型**：[`core/models.py`](core/models.py) - `_fit_grouped_descriptive()`, `_generate_grouped_descriptive_html_vertical()`
- **前端模块**：[`templates/analysis_modules/grouped_descriptive.html`](templates/analysis_modules/grouped_descriptive.html)
- **路由处理**：[`blueprints/analysis.py`](blueprints/analysis.py) - 包含`group_var`参数处理

#### 使用流程
1. 用户选择分组变量（如：性别、地区等分类变量）
2. 选择需要统计的数值型变量（可多选）
3. 选择需要输出的统计量（默认均值和标准差）
4. 点击"生成分组描述性统计"按钮
5. 显示按分组展示的描述性统计结果

#### 示例输出
```
性别 = 男
-------------------------
Variable    N    Mean    Std.Dev
收入       150   5234.56  1234.56
年龄       150   35.23    8.45
-------------------------

性别 = 女
-------------------------
Variable    N    Mean    Std.Dev
收入       120   4856.78  1156.78
年龄       120   33.45    7.89
-------------------------
```

#### 缺失值处理
如果某个变量在某个分组中全是缺失值，仍会显示该变量：
```
性别 = 男
-------------------------
Variable    N    Mean    Std.Dev
收入       150   5234.56  1234.56
年龄         0   -        -
-------------------------
```

### 添加新的分析功能

#### 1. 后端实现
1. 在 [`core/models.py`](core/models.py) 的 `StataModel` 类中添加新方法
2. 在 `_fit_regression()` 或 `_fit_basic_analysis()` 中添加分支

#### 2. 前端实现（模块化）
1. 在 `templates/analysis_modules/` 创建新模块文件（如 `new_feature.html`）
2. 定义模块容器：`<div id="module-新功能名" class="analysis-module">`
3. 实现初始化函数：`function init新功能Module(columns) { ... }`
4. 实现运行函数：`function run新功能Analysis() { ... }`
5. 在 [`templates/analysis.html`](templates/analysis.html) 中：
   - 添加 `{% include 'analysis_modules/new_feature.html' %}`
   - 在 `initAllModules()` 中添加初始化调用
   - 在左侧导航栏添加入口链接

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