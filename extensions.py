"""
================================================================================
STATAU 扩展初始化模块 (extensions.py)
================================================================================
说明：
    - 本模块集中管理所有 Flask 扩展的实例化
    - 扩展在此处创建，但不绑定到具体的 app 实例
    - 绑定操作在 app.py 的 create_app() 工厂函数中完成

设计理念：
    - 将扩展实例化与应用初始化分离
    - 避免循环导入问题
    - 便于在测试中替换扩展实例

使用方式：
    from extensions import db, login_manager
    
    # 在 create_app() 中：
    db.init_app(app)
    login_manager.init_app(app)
================================================================================
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# ------------------------------------------------------------------------
# SQLAlchemy 数据库扩展
# ------------------------------------------------------------------------
# 用于 ORM 数据库操作
# 在 core/auth.py 中的 User 模型会使用此实例
db = SQLAlchemy()

# ------------------------------------------------------------------------
# Flask-Login 登录管理扩展
# ------------------------------------------------------------------------
# 用于用户会话管理、登录状态维护
login_manager = LoginManager()

# 配置 Flask-Login
login_manager.login_view = 'pages.home'  # 未登录时重定向到首页 (使用蓝图名.视图函数名)
login_manager.login_message = '请先登录以访问该页面。'
login_manager.login_message_category = 'warning'

# 关键修复：禁用绝对 URL 生成，避免服务器上生成 localhost URL
# 这样重定向时会使用相对路径，而不是绝对路径
login_manager.refresh_view = None
login_manager.needs_refresh_message = None

# ------------------------------------------------------------------------
# 用户加载回调函数
# ------------------------------------------------------------------------
# Flask-Login 需要此函数来从 session 中恢复用户对象
# 注意：此函数需要在 User 模型定义之后才能正常工作
@login_manager.user_loader
def load_user(user_id):
    """
    根据用户 ID 加载用户对象
    
    参数:
        user_id: 存储在 session 中的用户 ID (字符串)
    
    返回:
        User 对象，如果用户不存在则返回 None
    """
    # 延迟导入，避免循环依赖
    from core.auth import User
    return User.query.get(int(user_id))


# ------------------------------------------------------------------------
# 扩展初始化函数
# ------------------------------------------------------------------------
def init_extensions(app):
    """
    初始化所有扩展并绑定到 Flask 应用实例
    
    参数:
        app: Flask 应用实例
    
    说明:
        此函数应在 create_app() 工厂函数中调用
    """
    # 初始化数据库
    db.init_app(app)
    
    # 初始化登录管理器
    login_manager.init_app(app)
    
    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()
        print("[extensions.py] 数据库表已创建/更新")