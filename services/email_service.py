"""
================================================================================
STATAU 邮件服务模块 (services/email_service.py)
================================================================================
说明：
    - 本模块负责邮件发送功能
    - 包括：发送邮箱验证码、生成验证码、验证验证码
    - 使用 Flask-Mail 发送邮件

设计理念：
    - 服务层独立于路由层，可复用
    - 验证码存储在内存中（可扩展为 Redis）
    - 验证码有效期为 5 分钟

使用方式：
    from services.email_service import EmailService
    
    email_service = EmailService()
    code = email_service.send_verification_code('user@example.com')
    is_valid = email_service.verify_code('user@example.com', '123456')
================================================================================
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    """
    邮件服务类
    
    职责：
        - 生成邮箱验证码
        - 发送验证码邮件
        - 验证邮箱验证码
    """
    
    def __init__(self):
        """
        初始化邮件服务
        
        说明：
            - 验证码存储在内存字典中
            - 格式：{email: {'code': '123456', 'expire_time': datetime}}
        """
        self._verification_codes = {}
        self._code_length = 6
        self._expire_minutes = 5
    
    def generate_code(self) -> str:
        """
        生成6位数字验证码
        
        返回:
            6位数字字符串
        """
        return ''.join(random.choices(string.digits, k=self._code_length))
    
    def send_verification_code(
        self, 
        email: str,
        smtp_server: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        sender_name: str = 'STATAU'
    ) -> Tuple[bool, str]:
        """
        发送邮箱验证码
        
        参数:
            email: 接收邮箱地址
            smtp_server: SMTP 服务器地址
            smtp_port: SMTP 服务器端口
            smtp_user: SMTP 用户名（发件邮箱）
            smtp_password: SMTP 密码或授权码
            sender_name: 发件人名称
        
        返回:
            (成功标志, 验证码或错误信息)
        """
        # 生成验证码
        code = self.generate_code()
        
        # 存储验证码和过期时间
        expire_time = datetime.now() + timedelta(minutes=self._expire_minutes)
        self._verification_codes[email] = {
            'code': code,
            'expire_time': expire_time
        }
        
        # 构建邮件内容
        subject = f'【STATAU】邮箱验证码'
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .code-box {{ background: white; border: 2px dashed #6a11cb; 
                            padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
                .code {{ font-size: 32px; font-weight: bold; color: #6a11cb; letter-spacing: 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 12px; }}
                .warning {{ color: #ff4757; font-size: 14px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>STATAU 云端计量经济学平台</h1>
                    <p>邮箱验证码</p>
                </div>
                <div class="content">
                    <p>您好！</p>
                    <p>您正在注册 STATAU 账户，您的邮箱验证码为：</p>
                    <div class="code-box">
                        <div class="code">{code}</div>
                    </div>
                    <p>验证码有效期为 <strong>{self._expire_minutes} 分钟</strong>，请尽快完成验证。</p>
                    <p class="warning">⚠️ 如果这不是您本人的操作，请忽略此邮件。</p>
                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿直接回复。</p>
                        <p>© 2024 STATAU. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'{sender_name} <{smtp_user}>'
            msg['To'] = email
            
            # 添加 HTML 内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 连接 SMTP 服务器并发送
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # 启用 TLS 加密
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            return True, code
            
        except smtplib.SMTPAuthenticationError:
            return False, '邮箱认证失败，请检查 SMTP 配置'
        except smtplib.SMTPException as e:
            return False, f'邮件发送失败：{str(e)}'
        except Exception as e:
            return False, f'发送邮件时发生错误：{str(e)}'
    
    def verify_code(self, email: str, code: str) -> bool:
        """
        验证邮箱验证码
        
        参数:
            email: 邮箱地址
            code: 用户输入的验证码
        
        返回:
            True 如果验证码正确且未过期，否则 False
        """
        if email not in self._verification_codes:
            return False
        
        stored_data = self._verification_codes[email]
        stored_code = stored_data['code']
        expire_time = stored_data['expire_time']
        
        # 检查是否过期
        if datetime.now() > expire_time:
            # 删除过期验证码
            del self._verification_codes[email]
            return False
        
        # 验证码比对（不区分大小写）
        return code.strip().lower() == stored_code.lower()
    
    def clear_code(self, email: str) -> None:
        """
        清除指定邮箱的验证码
        
        参数:
            email: 邮箱地址
        
        说明:
            验证成功后应调用此方法清除验证码，防止重复使用
        """
        if email in self._verification_codes:
            del self._verification_codes[email]
    
    def get_remaining_time(self, email: str) -> Optional[int]:
        """
        获取验证码剩余有效时间（秒）
        
        参数:
            email: 邮箱地址
        
        返回:
            剩余秒数，如果不存在或已过期则返回 None
        """
        if email not in self._verification_codes:
            return None
        
        expire_time = self._verification_codes[email]['expire_time']
        remaining = (expire_time - datetime.now()).total_seconds()
        
        return int(remaining) if remaining > 0 else None
