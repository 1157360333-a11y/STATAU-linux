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
│   ├── analysis.html        # 分析页（模块化主框架）
│   ├── analysis_modules/    # 分析功能模块
│   │   ├── descriptive.html # 描述性统计模块
│   │   ├── grouped_descriptive.html # 分组描述性统计模块
│   │   ├── frequency.html   # 频数统计模块
│   │   ├── correlation.html # 相关性分析模块
│   │   ├── vif.html         # VIF检验模块
│   │   ├── regression.html  # 回归模型模块
│   │   └── model_test.html  # 模型检验模块
│   ├── database.html        # 数据库页
│   └── help.html            # 帮助页
│
├── static/                   # 静态资源
│   ├── css/
│   ├── js/
│   │   ├── export.js        # 导出功能模块
│   │   ├── FileSaver.min.js # 文件下载库
│   │   ├── html-docx.js     # Word导出库
│   │   └── xlsx.full.min.js # Excel导出库
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

### 前端模块化架构

分析页面采用**模块化设计**，每个功能拥有独立的前端模块文件：

- **模块目录**：`templates/analysis_modules/`
- **主框架**：`templates/analysis.html` - 负责文件上传和模块切换
- **模块文件**：每个功能模块独立，包含自己的HTML、CSS和JavaScript

**模块特点**：
- ✅ 完全独立，互不干扰
- ✅ 命名规范化（带模块前缀）
- ✅ 易于维护和扩展
- ✅ 即使某个模块出bug也不影响其他模块

### 添加新的分析方法

#### 1. 后端实现
1. 在 `core/models.py` 的 `StataModel` 类中添加新方法
2. 在 `_fit_regression()` 或 `_fit_basic_analysis()` 中添加分支

#### 2. 前端实现（模块化）
1. 在 `templates/analysis_modules/` 创建新模块文件（如 `new_feature.html`）
2. 定义模块容器：`<div id="module-新功能名" class="analysis-module">`
3. 实现初始化函数：`function init新功能Module(columns) { ... }`
4. 实现运行函数：`function run新功能Analysis() { ... }`
5. 在 `templates/analysis.html` 中：
   - 添加 `{% include 'analysis_modules/new_feature.html' %}`
   - 在 `initAllModules()` 中添加初始化调用
   - 在左侧导航栏添加入口链接

### 功能示例：分组描述性统计

分组描述性统计是一个完整的模块化功能实现示例：

**功能特点**：
- 按分组变量对数值型变量进行分组统计
- 竖式布局，每个分组独立显示
- 默认输出均值和标准差
- 健壮的缺失值处理

**实现文件**：
- **后端**：`core/models.py` - `_fit_grouped_descriptive()`, `_generate_grouped_descriptive_html_vertical()`
- **前端**：`templates/analysis_modules/grouped_descriptive.html`
- **路由**：`blueprints/analysis.py` - 添加`group_var`参数处理

**使用流程**：
1. 选择分组变量（如：性别、地区）
2. 选择分析变量（可多选）
3. 选择统计量（默认均值和标准差）
4. 生成按分组展示的描述性统计结果

### 导出功能架构

导出功能采用**纯前端实现**，无需后端支持，实现了分析结果的多格式导出。

#### 技术栈
- **FileSaver.js**：文件下载功能
- **html-docx-js**：HTML转Word文档
- **SheetJS (xlsx.js)**：Excel表格生成
- **原生JavaScript**：TXT和CSV导出

#### 核心模块：export.js

**主要功能**：
1. **模块激活检测**：`getCurrentActiveModule()` - 获取当前激活的分析模块
2. **表格查找**：`getCurrentTable()` - 从当前模块中查找表格
3. **标题获取**：`getTableTitle()` - 获取表格标题用于文件命名
4. **导出函数**：
   - `exportToWord()` - 导出为Word文档
   - `exportToExcel()` - 导出为Excel表格
   - `exportToTxt()` - 导出为纯文本
   - `exportToCSV()` - 导出为CSV文件

**关键设计**：
```javascript
// 1. 只导出当前激活模块的表格
const activeModule = document.querySelector('.analysis-module.active');

// 2. 支持多种表格类型
const table = resultContainer.querySelector('.academic-table, table');

// 3. 防抖机制避免频繁更新
let updateTimeout = null;
const debouncedUpdate = function() {
    if (updateTimeout) clearTimeout(updateTimeout);
    updateTimeout = setTimeout(updateExportButtonsVisibility, 100);
};

// 4. 避免重复设置样式
if (btn.style.display !== 'none') {
    btn.style.display = 'none';
}
```

#### 按钮集成

每个分析模块的结果容器中都包含导出按钮组：

```html
<!-- 导出按钮组 -->
<div id="export-buttons-模块名" class="my-3">
    <div class="card shadow-sm">
        <div class="card-body py-2">
            <div class="d-flex align-items-center justify-content-between">
                <strong><i class="bi bi-download"></i> 导出结果</strong>
                <div class="btn-group btn-group-sm">
                    <button onclick="exportToWord()">Word</button>
                    <button onclick="exportToExcel()">Excel</button>
                    <button onclick="exportToTxt()">TXT</button>
                    <button onclick="exportToCSV()">CSV</button>
                </div>
            </div>
        </div>
    </div>
</div>
```

**唯一ID设计**：
- `export-buttons-regression` - 回归模型
- `export-buttons-descriptive` - 描述性统计
- `export-buttons-grouped-desc` - 分组描述性统计
- `export-buttons-correlation` - 相关性分析
- `export-buttons-vif` - VIF检验
- `export-buttons-frequency` - 频数统计
- `export-buttons-test` - 模型检验

#### 自动显示/隐藏逻辑

```javascript
function updateExportButtonsVisibility() {
    const activeModule = getCurrentActiveModule();
    
    // 1. 隐藏所有导出按钮
    const allExportButtons = document.querySelectorAll('[id^="export-buttons"]');
    allExportButtons.forEach(btn => {
        if (btn.style.display !== 'none') {
            btn.style.display = 'none';
        }
    });
    
    // 2. 只显示当前激活模块的导出按钮
    if (activeModule) {
        const resultContainer = activeModule.querySelector('[id$="-result-container"]');
        if (resultContainer && resultContainer.style.display !== 'none') {
            const exportButtons = resultContainer.querySelector('[id^="export-buttons"]');
            const hasTable = resultContainer.querySelector('table') !== null;
            
            if (exportButtons && hasTable && exportButtons.style.display !== 'block') {
                exportButtons.style.display = 'block';
            }
        }
    }
}
```

#### 性能优化

1. **防抖机制**：延迟100ms执行更新，避免频繁触发
2. **精确监听**：只监听 `style` 属性和 `childList`，不监听 `subtree`
3. **条件更新**：设置样式前先检查当前值，避免触发新的变化事件
4. **本地化库文件**：所有依赖库本地化，避免CDN加载延迟

#### 文件格式特点

| 格式 | 编码 | 特殊处理 |
|------|------|----------|
| Word | UTF-8 | 保留学术表格样式，Times New Roman字体 |
| Excel | UTF-8 | 自动调整列宽（15字符） |
| TXT | UTF-8 | 固定宽度对齐，添加时间戳 |
| CSV | UTF-8 BOM | 添加BOM头（`\ufeff`）确保中文显示 |

#### 文件命名规则

格式：`表格标题_时间戳.扩展名`

示例：
- `Regression_Results_20260123_153045.docx`
- `描述性统计_20260123_153045.xlsx`

时间戳格式：`YYYYMMDD_HHMMSS`

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