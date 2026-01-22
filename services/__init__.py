"""
================================================================================
STATAU 服务层模块 (services/)
================================================================================
说明：
    - 本目录包含业务逻辑服务
    - 每个服务模块负责一个独立的业务领域
    - 服务层位于蓝图（路由层）和核心模块（数据层）之间

目录结构：
    services/
    ├── __init__.py          # 本文件，服务层入口
    ├── file_service.py      # 文件上传、读取、预览服务
    └── captcha_service.py   # 验证码生成服务

设计理念：
    - 服务层封装可复用的业务逻辑
    - 蓝图只负责 HTTP 请求/响应处理
    - 服务层不依赖 Flask 的 request/response 对象
================================================================================
"""

# 导出服务模块，方便外部导入
from services.file_service import FileService
from services.captcha_service import CaptchaService

__all__ = ['FileService', 'CaptchaService']