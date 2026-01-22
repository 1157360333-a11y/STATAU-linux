# -*- coding: utf-8 -*-
"""
================================================================================
管理员账户初始化脚本
================================================================================
说明：
    此脚本用于创建或重置管理员账户
    
使用方式：
    python init_admin.py
    
注意：
    - 如果管理员账户已存在，将重置密码
    - 管理员用户名: admin
    - 管理员密码: Qbt030523...
================================================================================
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from core.auth import User

def init_admin():
    """
    初始化管理员账户
    """
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        # 管理员信息
        admin_username = 'admin'
        admin_password = 'Qbt030523...'
        admin_email = 'admin@statau.com'
        
        # 检查管理员是否已存在
        admin = User.query.filter_by(username=admin_username).first()
        
        if admin:
            print(f"[INFO] 管理员账户已存在: {admin_username}")
            print(f"[INFO] 正在重置密码...")
            
            # 重置密码
            admin.set_password(admin_password)
            admin.role = 'admin'
            admin.is_active = True
            admin.email_verified = True
            
            db.session.commit()
            print(f"[SUCCESS] 管理员密码已重置")
        else:
            print(f"[INFO] 正在创建管理员账户...")
            
            # 创建新管理员
            admin = User(
                username=admin_username,
                email=admin_email,
                role='admin',
                is_active=True,
                email_verified=True
            )
            admin.set_password(admin_password)
            
            db.session.add(admin)
            db.session.commit()
            print(f"[SUCCESS] 管理员账户创建成功")
        
        print()
        print("=" * 70)
        print("管理员账户信息")
        print("=" * 70)
        print(f"用户名: {admin_username}")
        print(f"密码:   {admin_password}")
        print(f"邮箱:   {admin_email}")
        print(f"角色:   管理员")
        print("=" * 70)
        print()
        print("[提示] 请访问 http://localhost:5000/admin 登录管理后台")
        print("[提示] 建议登录后立即修改密码")
        print()


if __name__ == '__main__':
    print("=" * 70)
    print("STATAU 管理员账户初始化")
    print("=" * 70)
    print()
    
    try:
        init_admin()
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
