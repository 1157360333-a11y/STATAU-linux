# -*- coding: utf-8 -*-
"""
================================================================================
数据库迁移脚本 - 添加 email_verified 字段
================================================================================
说明：
    此脚本用于为现有的 users 表添加 email_verified 字段
    
使用方式：
    python migrate_db.py
    
注意：
    - 运行前请备份数据库
    - 此脚本会为所有现有用户设置 email_verified = False
================================================================================
"""

import sqlite3
import os
import sys

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate_database():
    """
    为 users 表添加 email_verified 字段
    """
    # 数据库文件路径
    db_path = os.path.join('instance', 'statau.db')
    
    if not os.path.exists(db_path):
        print(f"[ERROR] 数据库文件不存在: {db_path}")
        print("        请先运行应用创建数据库")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email_verified' in columns:
            print("[OK] email_verified 字段已存在，无需迁移")
            conn.close()
            return True
        
        # 添加新字段
        print("[INFO] 正在添加 email_verified 字段...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN email_verified BOOLEAN DEFAULT 0
        """)
        
        # 提交更改
        conn.commit()
        print("[OK] 成功添加 email_verified 字段")
        
        # 验证字段已添加
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email_verified' in columns:
            print("[SUCCESS] 数据库迁移成功！")
            print(f"          数据库路径: {db_path}")
            print(f"          新增字段: email_verified (BOOLEAN, 默认值: False)")
            success = True
        else:
            print("[ERROR] 字段添加失败")
            success = False
        
        # 关闭连接
        conn.close()
        return success
        
    except sqlite3.Error as e:
        print(f"[ERROR] 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("STATAU 数据库迁移工具")
    print("=" * 70)
    print()
    
    # 执行迁移
    success = migrate_database()
    
    print()
    if success:
        print("[DONE] 迁移完成！现在可以运行 python app.py 启动应用")
    else:
        print("[WARN] 迁移失败，请检查错误信息")
    
    print("=" * 70)
