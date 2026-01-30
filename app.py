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

# 尝试加载 .env 文件（如果安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[app.py] 已加载 .env 文件")
except ImportError:
    print("[app.py] 提示: 安装 python-dotenv 可自动加载 .env 文件")
    print("[app.py] 运行: pip install python-dotenv")

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
        1. 加载配置（根据 RUN_MODE 环境变量自动选择）
        2. 初始化扩展
        3. 注册蓝图
        4. 创建必要的目录
        5. 配置 Session（服务器版自动启用文件系统 Session）
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

    # ------------------------------------------------------------------------
    # 7. 服务器版 Session 配置（自动检测）
    # ------------------------------------------------------------------------
    if app.config.get('SESSION_TYPE') == 'filesystem':
        try:
            from flask_session import Session
            Session(app)
            print("[app.py] 服务器版 Session 已启用（文件系统存储）")
        except ImportError:
            print("[app.py] 警告: flask-session 未安装，使用默认 Session（内存存储）")
            print("[app.py] 提示: 运行 'pip install flask-session' 以启用文件系统 Session")

    print("[app.py] Flask 应用创建完成")
    return app


# ============================================================================
# 服务器版 Session 配置说明（已废弃）
# ============================================================================
# 说明：
#   以下代码已不再需要，Session 配置已集成到 config.py 的 ServerConfig 中
#   现在只需设置环境变量 RUN_MODE=server 即可自动启用文件系统 Session
#
# 旧代码（保留作为参考）：
#   from flask_session import Session
#
#   def configure_server_session(app):
#       """配置服务器版 Session"""
#       app.config['SESSION_TYPE'] = 'filesystem'
#       app.config['SESSION_FILE_DIR'] = './flask_session'
#       app.config['SESSION_PERMANENT'] = False
#       app.config['SESSION_USE_SIGNER'] = True
#       Session(app)
#       print("[app.py] 服务器版 Session 已配置")
# ============================================================================


# ============================================================================
# 主入口
# ============================================================================

if __name__ == '__main__':
    # ------------------------------------------------------------------------
    # 创建应用实例（自动根据环境变量选择配置）
    # ------------------------------------------------------------------------
    app = create_app()

    # ------------------------------------------------------------------------
    # 启动开发服务器
    # ------------------------------------------------------------------------
    # 注意：
    #   - 本地版（RUN_MODE=local）：自动启用 debug 模式，绑定 127.0.0.1
    #   - 服务器版（RUN_MODE=server）：自动禁用 debug 模式，绑定 0.0.0.0
    #   - 生产环境建议使用 Gunicorn：gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

    # 根据运行模式选择绑定地址
    run_mode = os.environ.get('RUN_MODE', 'local').lower()
    host = '0.0.0.0' if run_mode == 'server' else '127.0.0.1'

    print(f"[app.py] 运行模式: {run_mode}")
    print(f"[app.py] 绑定地址: {host}:5000")

    app.run(
        host=host,
        debug=app.config.get('DEBUG', False),
        port=5000
    )
