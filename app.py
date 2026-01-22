"""
================================================================================
STATAU 应用入口 (app.py)
================================================================================
说明：
    - 本文件是 Flask 应用的主入口
    - 使用应用工厂模式 (Application Factory Pattern)
    - 负责创建和配置 Flask 应用实例

架构概览：
    app.py                  # 本文件 - 应用入口和工厂函数
    ├── config.py           # 配置模块
    ├── extensions.py       # Flask 扩展初始化
    ├── blueprints/         # 蓝图模块（路由层）
    │   ├── pages.py        # 页面路由
    │   ├── auth.py         # 认证路由
    │   └── analysis.py     # 分析路由
    ├── services/           # 服务层（业务逻辑）
    │   ├── file_service.py
    │   └── captcha_service.py
    └── core/               # 核心模块（数据模型和算法）
        ├── auth.py         # 用户模型
        ├── models.py       # 统计模型
        └── table_generator.py

设计理念（解耦优于复用）：
    - 每个模块职责单一，相互独立
    - 蓝图之间不共享路由处理函数
    - 服务层封装可复用的业务逻辑
    - 核心层提供数据模型和算法

使用方式：
    # 开发环境
    python app.py
    
    # 生产环境
    gunicorn "app:create_app()"
================================================================================
"""

import os
from flask import Flask

# 导入配置
from config import get_config, DevelopmentConfig

# 导入扩展初始化函数
from extensions import init_extensions

# 导入蓝图注册函数
from blueprints import register_blueprints


def create_app(config_class=None):
    """
    应用工厂函数
    
    参数:
        config_class: 配置类，如果为 None 则根据环境变量自动选择
    
    返回:
        配置完成的 Flask 应用实例
    
    说明:
        此函数创建并配置 Flask 应用，包括：
        1. 加载配置
        2. 初始化扩展
        3. 注册蓝图
        4. 创建必要的目录
    """
    # ------------------------------------------------------------------------
    # 1. 创建 Flask 应用实例
    # ------------------------------------------------------------------------
    app = Flask(__name__)
    
    # ------------------------------------------------------------------------
    # 2. 加载配置
    # ------------------------------------------------------------------------
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    print(f"[app.py] 已加载配置: {config_class.__name__}")
    
    # ------------------------------------------------------------------------
    # 3. 确保上传目录存在
    # ------------------------------------------------------------------------
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        print(f"[app.py] 创建上传目录: {upload_folder}")
    
    # ------------------------------------------------------------------------
    # 4. 初始化 Flask 扩展
    # ------------------------------------------------------------------------
    init_extensions(app)
    
    # ------------------------------------------------------------------------
    # 5. 注册蓝图
    # ------------------------------------------------------------------------
    register_blueprints(app)
    
    # ------------------------------------------------------------------------
    # 6. 配置 Flask-Login 的 Remember Me
    # ------------------------------------------------------------------------
    from extensions import login_manager
    from datetime import timedelta
    
    login_manager.remember_cookie_duration = app.config.get(
        'REMEMBER_COOKIE_DURATION', 
        timedelta(days=7)
    )
    login_manager.session_protection = app.config.get(
        'SESSION_PROTECTION', 
        'basic'
    )
    
    print("[app.py] Flask 应用创建完成")
    return app


# ============================================================================
# 服务器版 Session 配置（勿删）
# ============================================================================
# 说明：
#   以下代码用于服务器部署时启用文件系统 Session
#   本地开发时保持注释状态

from flask_session import Session

def configure_server_session(app):
    """配置服务器版 Session"""
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = './flask_session'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    Session(app)
    print("[app.py] 服务器版 Session 已配置")
# ============================================================================


# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    # ------------------------------------------------------------------------
    # 创建应用实例
    # ------------------------------------------------------------------------
    app = create_app(ProductionConfig)
    
    # ------------------------------------------------------------------------
    # 本地开发服务器启动
    # ------------------------------------------------------------------------
    # 开发环境：启用调试模式，监听 5000 端口
    # app.run(debug=True, port=5000)
    
    # ------------------------------------------------------------------------
    # 服务器版启动（勿删）
    # ------------------------------------------------------------------------
    # 生产环境：禁用调试模式
    app.run(debug=False)
    
    # 或者使用 Gunicorn（推荐）：
    # gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
