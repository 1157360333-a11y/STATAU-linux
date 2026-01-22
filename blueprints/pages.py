"""
================================================================================
STATAU 页面路由蓝图 (blueprints/pages.py)
================================================================================
说明：
    - 本蓝图负责所有页面的渲染路由
    - 只处理 GET 请求，返回 HTML 页面
    - 不包含任何 API 接口或数据处理逻辑

包含路由：
    - GET /           首页
    - GET /analysis   数据分析页（需登录）
    - GET /database   数据库页
    - GET /help       帮助手册页

设计理念：
    - 页面路由与 API 路由分离
    - 每个页面路由独立，不共享处理逻辑
    - 页面渲染逻辑简单明了
================================================================================
"""

from flask import Blueprint, render_template
from flask_login import login_required

# ------------------------------------------------------------------------
# 创建蓝图实例
# ------------------------------------------------------------------------
pages_bp = Blueprint(
    'pages',           # 蓝图名称，用于 url_for('pages.home')
    __name__,          # 模块名称
    template_folder='../templates'  # 模板目录（相对于本文件）
)


# ============================================================================
# 页面路由
# ============================================================================

@pages_bp.route('/')
def home():
    """
    首页路由
    
    URL: GET /
    模板: home.html
    权限: 公开访问
    """
    return render_template('home.html', active_page='home')


@pages_bp.route('/analysis')
@login_required
def analysis():
    """
    数据分析页路由
    
    URL: GET /analysis
    模板: analysis.html
    权限: 需要登录
    
    说明:
        - 使用 @login_required 装饰器保护
        - 未登录用户会被重定向到首页（由 Flask-Login 配置）
    """
    return render_template('analysis.html', active_page='analysis')


@pages_bp.route('/database')
def database():
    """
    数据库页路由
    
    URL: GET /database
    模板: database.html
    权限: 公开访问
    """
    return render_template('database.html', active_page='database')


@pages_bp.route('/help')
def help_page():
    """
    帮助手册页路由
    
    URL: GET /help
    模板: help.html
    权限: 公开访问
    
    注意:
        函数名为 help_page 而非 help，避免与 Python 内置函数冲突
    """
    return render_template('help.html', active_page='help')


# ============================================================================
# 调试路由（仅开发环境使用）
# ============================================================================

@pages_bp.route('/debug/user')
def debug_user():
    """
    调试用户认证状态
    
    URL: GET /debug/user
    权限: 公开访问（仅用于开发调试）
    
    返回:
        JSON 格式的用户认证状态信息
    
    注意:
        生产环境应禁用此路由
    """
    from flask import jsonify, session
    from flask_login import current_user
    
    user_info = {
        'is_authenticated': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None,
        'session_keys': list(session.keys()),
        'session_user': session.get('user'),
        'remember_me': session.get('remember'),
        'session_id': session.get('_id'),
    }
    return jsonify(user_info)