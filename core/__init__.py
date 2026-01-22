"""
================================================================================
STATAU 核心模块 (core/)
================================================================================
说明：
    - 本目录包含应用的核心业务逻辑
    - 与 Flask 框架解耦，可独立测试
    - 提供数据模型和统计算法

目录结构：
    core/
    ├── __init__.py          # 本文件，核心模块入口
    ├── auth.py              # 用户认证模型 (User)
    ├── models.py            # 统计模型 (StataModel)
    └── table_generator.py   # 表格生成器

模块职责：
    - auth.py: 定义 User 数据模型，处理密码哈希
    - models.py: 封装所有统计分析算法（OLS、FE、Logit 等）
    - table_generator.py: 生成学术标准的 HTML 表格

设计理念：
    - 核心模块不依赖 Flask 的 request/response
    - 只接收纯 Python 数据，返回纯 Python 结果
    - 便于单元测试和代码复用
================================================================================
"""

# 导出核心类，方便外部导入
from core.auth import User
from core.models import StataModel
from core.table_generator import generate_merged_html

__all__ = ['User', 'StataModel', 'generate_merged_html']