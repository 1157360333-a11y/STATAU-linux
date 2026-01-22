"""
================================================================================
STATAU 用户认证蓝图 (blueprints/auth.py)
================================================================================
说明：
    - 本蓝图负责所有用户认证相关的 API 接口
    - 包括：登录、注册、登出、验证码生成
    - 所有接口都以 /api 为前缀（在蓝图注册时配置）

包含路由：
    - POST /api/login      用户登录
    - POST /api/register   用户注册
    - GET  /api/logout     用户登出
    - GET  /api/captcha    获取验证码图片

设计理念：
    - 认证逻辑与其他业务逻辑完全分离
    - 每个接口独立处理，不共享处理函数
    - 验证码服务通过服务层调用
================================================================================
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user

# 导入服务层
from services.captcha_service import CaptchaService
from services.email_service import EmailService

# 导入数据库和用户模型
from extensions import db
from core.auth import User

# ------------------------------------------------------------------------
# 创建蓝图实例
# ------------------------------------------------------------------------
auth_bp = Blueprint(
    'auth',            # 蓝图名称
    __name__
)

# ------------------------------------------------------------------------
# 创建服务实例
# ------------------------------------------------------------------------
captcha_service = CaptchaService()
email_service = EmailService()


# ============================================================================
# 验证码接口
# ============================================================================

@auth_bp.route('/captcha')
def get_captcha():
    """
    获取图形验证码
    
    URL: GET /api/captcha
    
    返回:
        PNG 格式的验证码图片
    
    说明:
        - 验证码字符串存储在 session['captcha_code'] 中
        - 存储时转为小写，验证时不区分大小写
        - 每次请求都会生成新的验证码
    """
    # 生成验证码
    code, image_bytes = captcha_service.generate()
    
    # 存入 session（转为小写，便于后续验证）
    session['captcha_code'] = captcha_service.normalize_code(code)
    
    # 返回图片
    return send_file(image_bytes, mimetype='image/png')


# ============================================================================
# 邮箱验证码接口
# ============================================================================

@auth_bp.route('/send_email_code', methods=['POST'])
def send_email_code():
    """
    发送邮箱验证码
    
    URL: POST /api/send_email_code
    
    请求体 (JSON):
        {
            "email": "user@example.com"
        }
    
    返回:
        成功: {"status": "success", "message": "验证码已发送"}
        失败: {"error": "错误信息"}, HTTP 状态码 400/500
    """
    data = request.json
    
    # ------------------------------------------------------------------------
    # 1. 参数验证
    # ------------------------------------------------------------------------
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'error': '邮箱地址不能为空'}), 400
    
    # 简单的邮箱格式验证
    import re
    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_pattern, email):
        return jsonify({'error': '邮箱格式不正确'}), 400
    
    # ------------------------------------------------------------------------
    # 2. 检查邮箱是否已被注册
    # ------------------------------------------------------------------------
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '该邮箱已被注册'}), 409
    
    # ------------------------------------------------------------------------
    # 3. 发送验证码
    # ------------------------------------------------------------------------
    try:
        success, result = email_service.send_verification_code(
            email=email,
            smtp_server=current_app.config['MAIL_SERVER'],
            smtp_port=current_app.config['MAIL_PORT'],
            smtp_user=current_app.config['MAIL_USERNAME'],
            smtp_password=current_app.config['MAIL_PASSWORD'],
            sender_name=current_app.config['MAIL_SENDER_NAME']
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'验证码已发送至 {email}，请查收邮件（有效期5分钟）'
            })
        else:
            return jsonify({'error': result}), 500
            
    except Exception as e:
        return jsonify({'error': f'发送邮件失败：{str(e)}'}), 500


# ============================================================================
# 发送登录验证码接口
# ============================================================================

@auth_bp.route('/send_login_code', methods=['POST'])
def send_login_code():
    """
    发送登录验证码
    
    URL: POST /api/send_login_code
    
    请求体 (JSON):
        {
            "email": "user@example.com"
        }
    
    返回:
        成功: {"status": "success", "message": "验证码已发送"}
        失败: {"error": "错误信息"}, HTTP 状态码 400/404/500
    """
    data = request.json
    
    # ------------------------------------------------------------------------
    # 1. 参数验证
    # ------------------------------------------------------------------------
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'error': '邮箱地址不能为空'}), 400
    
    # 简单的邮箱格式验证
    import re
    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_pattern, email):
        return jsonify({'error': '邮箱格式不正确'}), 400
    
    # ------------------------------------------------------------------------
    # 2. 检查邮箱是否已注册
    # ------------------------------------------------------------------------
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': '该邮箱未注册'}), 404
    
    # ------------------------------------------------------------------------
    # 3. 发送验证码
    # ------------------------------------------------------------------------
    try:
        success, result = email_service.send_verification_code(
            email=email,
            smtp_server=current_app.config['MAIL_SERVER'],
            smtp_port=current_app.config['MAIL_PORT'],
            smtp_user=current_app.config['MAIL_USERNAME'],
            smtp_password=current_app.config['MAIL_PASSWORD'],
            sender_name=current_app.config['MAIL_SENDER_NAME']
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'验证码已发送至 {email}，请查收邮件（有效期5分钟）'
            })
        else:
            return jsonify({'error': result}), 500
            
    except Exception as e:
        return jsonify({'error': f'发送邮件失败：{str(e)}'}), 500


# ============================================================================
# 邮箱验证码登录接口
# ============================================================================

@auth_bp.route('/login_with_code', methods=['POST'])
def login_with_code():
    """
    邮箱验证码登录接口
    
    URL: POST /api/login_with_code
    
    请求体 (JSON):
        {
            "email": "user@example.com",
            "code": "123456"
        }
    
    返回:
        成功: {"status": "success", "user": {"username": "xxx", "role": "xxx"}}
        失败: {"error": "错误信息"}, HTTP 状态码 400/401
    """
    data = request.json
    
    # ------------------------------------------------------------------------
    # 1. 参数验证
    # ------------------------------------------------------------------------
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    
    if not email or not code:
        return jsonify({'error': '邮箱和验证码不能为空'}), 400
    
    # ------------------------------------------------------------------------
    # 2. 查询用户
    # ------------------------------------------------------------------------
    user = User.query.filter_by(email=email).first()
    
    if user is None:
        return jsonify({'error': '用户不存在'}), 401
    
    # ------------------------------------------------------------------------
    # 3. 验证邮箱验证码
    # ------------------------------------------------------------------------
    if not email_service.verify_code(email, code):
        return jsonify({'error': '验证码错误或已过期'}), 401
    
    # 验证成功后清除验证码
    email_service.clear_code(email)
    
    # ------------------------------------------------------------------------
    # 4. 登录用户（使用 Flask-Login）
    # ------------------------------------------------------------------------
    login_user(user, remember=True)
    
    return jsonify({
        'status': 'success',
        'user': {
            'username': user.username,
            'role': user.role
        }
    })


# ============================================================================
# 密码登录接口
# ============================================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    
    URL: POST /api/login
    
    请求体 (JSON):
        {
            "username": "用户名或邮箱",
            "password": "密码"
        }
    
    返回:
        成功: {"status": "success", "user": {"username": "xxx", "role": "xxx"}}
        失败: {"error": "错误信息"}, HTTP 状态码 400/401
    """
    data = request.json
    
    # ------------------------------------------------------------------------
    # 1. 参数验证
    # ------------------------------------------------------------------------
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # ------------------------------------------------------------------------
    # 2. 查询用户（支持用户名或邮箱登录）
    # ------------------------------------------------------------------------
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if user is None:
        return jsonify({'error': '用户不存在'}), 401
    
    # ------------------------------------------------------------------------
    # 3. 验证密码
    # ------------------------------------------------------------------------
    if not user.check_password(password):
        return jsonify({'error': '密码错误'}), 401
    
    # ------------------------------------------------------------------------
    # 4. 登录用户（使用 Flask-Login）
    # ------------------------------------------------------------------------
    login_user(user, remember=True)
    
    return jsonify({
        'status': 'success',
        'user': {
            'username': user.username,
            'role': user.role
        }
    })


# ============================================================================
# 注册接口
# ============================================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口（支持邮箱验证码）
    
    URL: POST /api/register
    
    请求体 (JSON):
        {
            "username": "用户名",
            "email": "邮箱",
            "password": "密码",
            "captcha": "图形验证码",
            "email_code": "邮箱验证码"
        }
    
    返回:
        成功: {"status": "success", "message": "注册成功，请登录", "user": {...}}
        失败: {"error": "错误信息"}, HTTP 状态码 400/409
    """
    data = request.json
    
    # ------------------------------------------------------------------------
    # 1. 参数提取
    # ------------------------------------------------------------------------
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    captcha = data.get('captcha')
    email_code = data.get('email_code')
    
    # ------------------------------------------------------------------------
    # 2. 基础参数验证
    # ------------------------------------------------------------------------
    if not username or not password or not email:
        return jsonify({'error': '用户名、邮箱和密码均为必填项'}), 400
    
    if not email_code:
        return jsonify({'error': '请输入邮箱验证码'}), 400
    
    # ------------------------------------------------------------------------
    # 3. 图形验证码验证
    # ------------------------------------------------------------------------
    session_code = session.get('captcha_code')
    
    if not captcha_service.verify(captcha, session_code):
        return jsonify({'error': '图形验证码错误或已过期'}), 400
    
    # 验证成功后清除 session 中的验证码，防止重复使用
    session.pop('captcha_code', None)
    
    # ------------------------------------------------------------------------
    # 4. 邮箱验证码验证
    # ------------------------------------------------------------------------
    if not email_service.verify_code(email, email_code):
        return jsonify({'error': '邮箱验证码错误或已过期'}), 400
    
    # 验证成功后清除邮箱验证码
    email_service.clear_code(email)
    
    # ------------------------------------------------------------------------
    # 5. 数据库唯一性验证
    # ------------------------------------------------------------------------
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已被使用'}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 409
    
    # ------------------------------------------------------------------------
    # 6. 创建新用户
    # ------------------------------------------------------------------------
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    new_user.email_verified = True  # 邮箱已验证
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '注册成功，请登录',
        'user': {
            'username': new_user.username,
            'role': new_user.role
        }
    })


# ============================================================================
# 登出接口
# ============================================================================

@auth_bp.route('/logout')
@login_required
def logout():
    """
    用户登出接口
    
    URL: GET /api/logout
    权限: 需要登录
    
    返回:
        重定向到首页
    """
    logout_user()
    return redirect(url_for('pages.home'))