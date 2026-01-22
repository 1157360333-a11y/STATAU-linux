"""
================================================================================
STATAU 配置模块 (config.py)
================================================================================
说明：
    - 本模块包含所有应用配置
    - 分为开发环境、生产环境、测试环境三套配置
    - 每个配置类都是独立的，不依赖其他模块

使用方式：
    from config import DevelopmentConfig, ProductionConfig
    app.config.from_object(DevelopmentConfig)
================================================================================
"""

import os
from datetime import timedelta

# 获取项目根目录的绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    """
    基础配置类
    包含所有环境共用的配置项
    """
    # ------------------------------------------------------------------------
    # Flask 核心配置
    # ------------------------------------------------------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'statau_secret_key_dev'
    
    # ------------------------------------------------------------------------
    # 数据库配置 (SQLAlchemy)
    # ------------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'statau.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ------------------------------------------------------------------------
    # 文件上传配置
    # ------------------------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 最大上传文件大小：50MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'dta'}
    
    # ------------------------------------------------------------------------
    # Flask-Login 配置
    # ------------------------------------------------------------------------
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_PROTECTION = 'basic'
    
    # ------------------------------------------------------------------------
    # 模板配置
    # ------------------------------------------------------------------------
    TEMPLATES_AUTO_RELOAD = True
    
    # ------------------------------------------------------------------------
    # 邮件服务器配置 (用于发送邮箱验证码)
    # ------------------------------------------------------------------------
    # SMTP 服务器配置（请根据实际情况修改）
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'  # QQ邮箱示例
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'statu_official@qq.com'  # 发件邮箱
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'fhooorwxfqnccfeb'  # 邮箱授权码（不是登录密码）
    MAIL_SENDER_NAME = 'STATAU'  # 发件人名称
    
    # 注意：
    # 1. QQ邮箱需要开启SMTP服务并获取授权码
    # 2. 163邮箱: smtp.163.com, 端口 25 或 465
    # 3. Gmail: smtp.gmail.com, 端口 587
    # 4. 建议使用环境变量配置敏感信息


class DevelopmentConfig(BaseConfig):
    """
    开发环境配置
    用于本地开发调试
    """
    DEBUG = True
    TESTING = False
    
    # 开发环境下的特殊配置
    SEND_FILE_MAX_AGE_DEFAULT = 0  # 禁用静态文件缓存


class ProductionConfig(BaseConfig):
    """
    生产环境配置
    用于服务器部署
    """
    DEBUG = False
    TESTING = False
    
    # ------------------------------------------------------------------------
    # 服务器 URL 配置（重要：防止生成 localhost URL）
    # ------------------------------------------------------------------------
    # 方式1：如果使用域名，设置 SERVER_NAME（推荐）
    # SERVER_NAME = 'your-domain.com'  # 替换为你的实际域名
    
    # 方式2：如果使用 IP 或反向代理，设置 PREFERRED_URL_SCHEME
    PREFERRED_URL_SCHEME = 'http'  # 如果使用 HTTPS，改为 'https'
    
    # 方式3：强制使用相对 URL（最通用的方案）
    APPLICATION_ROOT = '/'
    
    
    # ------------------------------------------------------------------------
    # 生产环境 Session 配置 (服务器版，使用文件系统存储)
    # 注意：在服务器上运行时取消下面的注释
    # ------------------------------------------------------------------------
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = './flask_session'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    



class TestingConfig(BaseConfig):
    """
    测试环境配置
    用于单元测试
    """
    DEBUG = True
    TESTING = True
    
    # 测试环境使用内存数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 禁用 CSRF 保护以便于测试
    WTF_CSRF_ENABLED = False


# ------------------------------------------------------------------------
# 配置映射字典
# 方便通过字符串名称获取配置类
# ------------------------------------------------------------------------
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    获取配置类的工厂函数
    
    参数:
        config_name: 配置名称 ('development', 'production', 'testing')
                     如果为 None，则从环境变量 FLASK_ENV 读取
    
    返回:
        对应的配置类
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_map.get(config_name, DevelopmentConfig)