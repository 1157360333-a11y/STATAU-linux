"""
================================================================================
STATAU 管理后台蓝图 (blueprints/admin.py)
================================================================================
说明：
    - 本蓝图负责管理后台相关功能
    - 包括：用户管理、数据查看、系统设置等
    - 所有接口都需要管理员权限

包含路由：
    - GET  /admin              管理后台首页
    - GET  /admin/users        获取用户列表
    - POST /admin/users/delete 删除用户
    - POST /admin/users/toggle 切换用户状态

设计理念：
    - 严格的权限控制
    - 完整的操作日志
    - 安全的数据操作
================================================================================
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

# 导入数据库和用户模型
from extensions import db
from core.auth import User

# ------------------------------------------------------------------------
# 创建蓝图实例
# ------------------------------------------------------------------------
admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin'
)


# ============================================================================
# 权限验证装饰器
# ============================================================================

def admin_required(f):
    """
    管理员权限验证装饰器
    
    说明:
        - 必须登录且角色为 admin
        - 否则重定向到首页或返回错误
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否登录
        if not current_user.is_authenticated:
            # 如果是页面请求，重定向到首页
            if request.path.startswith('/admin') and not request.path.startswith('/admin/api'):
                from flask import flash
                flash('请先登录以访问管理后台', 'warning')
                return redirect(url_for('pages.home', next=request.path))
            # 如果是 API 请求，返回 JSON 错误
            return jsonify({'error': '请先登录'}), 401
        
        # 检查是否有管理员权限
        if current_user.role != 'admin':
            # 如果是页面请求，重定向到首页
            if request.path.startswith('/admin') and not request.path.startswith('/admin/api'):
                from flask import flash
                flash('权限不足，需要管理员权限', 'danger')
                return redirect(url_for('pages.home'))
            # 如果是 API 请求，返回 JSON 错误
            return jsonify({'error': '权限不足，需要管理员权限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# 管理后台首页
# ============================================================================

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """
    管理后台首页
    
    URL: GET /admin
    权限: 管理员
    
    返回:
        管理后台页面
    """
    return render_template('admin.html', active_page='admin')


# ============================================================================
# 用户管理 API
# ============================================================================

@admin_bp.route('/users')
@login_required
@admin_required
def get_users():
    """
    获取用户列表
    
    URL: GET /admin/users
    权限: 管理员
    
    查询参数:
        page: 页码（默认 1）
        per_page: 每页数量（默认 20）
        search: 搜索关键词（用户名或邮箱）
    
    返回:
        {
            "users": [...],
            "total": 总数,
            "page": 当前页,
            "per_page": 每页数量,
            "pages": 总页数
        }
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    
    # 构建查询
    query = User.query
    
    # 搜索过滤
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            (User.username.like(search_pattern)) | 
            (User.email.like(search_pattern))
        )
    
    # 分页
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 构建用户列表
    users = []
    for user in pagination.items:
        users.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
        })
    
    return jsonify({
        'users': users,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    })


@admin_bp.route('/users/delete', methods=['POST'])
@login_required
@admin_required
def delete_user():
    """
    删除用户
    
    URL: POST /admin/users/delete
    权限: 管理员
    
    请求体 (JSON):
        {
            "user_id": 用户ID
        }
    
    返回:
        成功: {"status": "success", "message": "用户已删除"}
        失败: {"error": "错误信息"}, HTTP 状态码 400/404
    """
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': '缺少用户ID'}), 400
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 不能删除自己
    if user.id == current_user.id:
        return jsonify({'error': '不能删除自己的账户'}), 400
    
    # 不能删除其他管理员
    if user.role == 'admin':
        return jsonify({'error': '不能删除管理员账户'}), 400
    
    # 删除用户
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'用户 {username} 已删除'
    })


@admin_bp.route('/users/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user_status():
    """
    切换用户状态（启用/禁用）
    
    URL: POST /admin/users/toggle
    权限: 管理员
    
    请求体 (JSON):
        {
            "user_id": 用户ID
        }
    
    返回:
        成功: {"status": "success", "is_active": true/false}
        失败: {"error": "错误信息"}, HTTP 状态码 400/404
    """
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': '缺少用户ID'}), 400
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 不能禁用自己
    if user.id == current_user.id:
        return jsonify({'error': '不能禁用自己的账户'}), 400
    
    # 不能禁用其他管理员
    if user.role == 'admin':
        return jsonify({'error': '不能禁用管理员账户'}), 400
    
    # 切换状态
    user.is_active = not user.is_active
    db.session.commit()
    
    status_text = '启用' if user.is_active else '禁用'
    
    return jsonify({
        'status': 'success',
        'message': f'用户 {user.username} 已{status_text}',
        'is_active': user.is_active
    })


@admin_bp.route('/stats')
@login_required
@admin_required
def get_stats():
    """
    获取统计信息
    
    URL: GET /admin/stats
    权限: 管理员
    
    返回:
        {
            "total_users": 总用户数,
            "active_users": 活跃用户数,
            "verified_users": 已验证邮箱用户数,
            "admin_users": 管理员数
        }
    """
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    verified_users = User.query.filter_by(email_verified=True).count()
    admin_users = User.query.filter_by(role='admin').count()
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'admin_users': admin_users
    })
