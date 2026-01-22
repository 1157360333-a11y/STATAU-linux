"""
================================================================================
STATAU 用户认证模型模块 (core/auth.py)
================================================================================
说明：
    - 本模块定义用户数据模型 (User)
    - 包含密码哈希和验证方法
    - 使用 Flask-Login 的 UserMixin 提供登录支持

设计理念：
    - 模型定义与路由处理分离
    - 数据库实例从 extensions.py 导入，避免循环依赖
    - 密码使用 werkzeug 的安全哈希函数

使用方式：
    from core.auth import User
    
    # 创建用户
    user = User(username='test', email='test@example.com')
    user.set_password('password123')
    
    # 验证密码
    if user.check_password('password123'):
        print('密码正确')
================================================================================
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ------------------------------------------------------------------------
# 从 extensions 导入数据库实例
# 注意：这里导入的是已经实例化但未绑定 app 的 db 对象
# ------------------------------------------------------------------------
from extensions import db


class User(db.Model, UserMixin):
    """
    用户模型
    
    继承:
        db.Model: SQLAlchemy 模型基类
        UserMixin: Flask-Login 用户混入类，提供 is_authenticated 等属性
    
    字段:
        id: 主键
        username: 用户名（唯一）
        email: 邮箱（唯一）
        password_hash: 密码哈希值
        created_at: 创建时间
        is_active: 是否激活
        role: 用户角色 ('user' 或 'admin')
    """
    __tablename__ = 'users'
    
    # ------------------------------------------------------------------------
    # 数据库字段定义
    # ------------------------------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin'
    email_verified = db.Column(db.Boolean, default=False)  # 邮箱是否已验证
    
    # ------------------------------------------------------------------------
    # 用户的分析历史（未来扩展）
    # ------------------------------------------------------------------------
    # analyses = db.relationship('Analysis', backref='user', lazy=True)
    
    # ------------------------------------------------------------------------
    # 密码处理方法
    # ------------------------------------------------------------------------
    def set_password(self, password: str) -> None:
        """
        设置密码（存储哈希值）
        
        参数:
            password: 明文密码
        
        说明:
            使用 werkzeug 的 generate_password_hash 函数
            默认使用 pbkdf2:sha256 算法
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        验证密码
        
        参数:
            password: 待验证的明文密码
        
        返回:
            True 如果密码正确，否则 False
        """
        return check_password_hash(self.password_hash, password)
    
    # ------------------------------------------------------------------------
    # Flask-Login 要求的方法
    # ------------------------------------------------------------------------
    def get_id(self) -> str:
        """
        获取用户 ID（字符串形式）
        
        返回:
            用户 ID 的字符串表示
        
        说明:
            Flask-Login 要求此方法返回字符串类型的用户标识
        """
        return str(self.id)
    
    # ------------------------------------------------------------------------
    # 对象表示
    # ------------------------------------------------------------------------
    def __repr__(self) -> str:
        """返回用户对象的字符串表示"""
        return f'<User {self.username}>'


# ============================================================================
# 兼容性函数（保留原有接口）
# ============================================================================
# 注意：以下函数在新架构中已不再需要，但为了兼容性保留
# 新代码应直接使用 extensions.py 中的 init_extensions() 函数

def init_auth(app):
    """
    初始化认证扩展（兼容性函数）
    
    参数:
        app: Flask 应用实例
    
    说明:
        此函数保留是为了兼容旧代码
        新代码应使用 extensions.init_extensions(app)
    
    警告:
        此函数已废弃，将在未来版本中移除
    """
    # 配置数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///statau.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化 db
    db.init_app(app)
    
    # 创建表（如果不存在）
    with app.app_context():
        db.create_all()
        print("[core/auth.py] 数据库表已创建/更新 (兼容模式)")
