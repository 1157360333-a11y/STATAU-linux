"""
================================================================================
STATAU 验证码服务模块 (services/captcha_service.py)
================================================================================
说明：
    - 本模块负责图形验证码的生成
    - 使用 captcha 库生成验证码图片
    - 不依赖 Flask session，验证码存储由调用方处理

职责：
    1. 生成随机验证码字符串
    2. 生成验证码图片（返回字节流）
    3. 验证用户输入的验证码

使用方式：
    from services.captcha_service import CaptchaService
    
    captcha_service = CaptchaService()
    code, image_bytes = captcha_service.generate()
    is_valid = captcha_service.verify(user_input, stored_code)
================================================================================
"""

import io
import random
import string
from typing import Tuple

# 验证码图片生成库
from captcha.image import ImageCaptcha


class CaptchaService:
    """
    验证码服务类
    
    负责生成和验证图形验证码
    """
    
    # ------------------------------------------------------------------------
    # 默认配置
    # ------------------------------------------------------------------------
    DEFAULT_WIDTH = 120
    DEFAULT_HEIGHT = 40
    DEFAULT_LENGTH = 4
    DEFAULT_FONT_SIZES = (28, 30, 32)
    
    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        length: int = DEFAULT_LENGTH,
        font_sizes: Tuple[int, ...] = DEFAULT_FONT_SIZES
    ):
        """
        初始化验证码服务
        
        参数:
            width: 验证码图片宽度（像素）
            height: 验证码图片高度（像素）
            length: 验证码字符长度
            font_sizes: 字体大小元组
        """
        self.width = width
        self.height = height
        self.length = length
        self.font_sizes = font_sizes
        
        # 创建 ImageCaptcha 实例
        self._image_captcha = ImageCaptcha(
            width=self.width,
            height=self.height,
            font_sizes=list(self.font_sizes)
        )
    
    # ------------------------------------------------------------------------
    # 验证码生成方法
    # ------------------------------------------------------------------------
    def generate_code(self) -> str:
        """
        生成随机验证码字符串
        
        返回:
            随机生成的验证码字符串（大写字母和数字组合）
        """
        # 使用大写字母和数字的组合
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choices(characters, k=self.length))
        return code
    
    def generate_image(self, code: str) -> bytes:
        """
        根据验证码字符串生成图片
        
        参数:
            code: 验证码字符串
        
        返回:
            PNG 格式的图片字节数据
        """
        # 生成图片数据流
        data = self._image_captcha.generate(code)
        
        # 读取为字节
        img_bytes = io.BytesIO(data.read())
        return img_bytes
    
    def generate(self) -> Tuple[str, io.BytesIO]:
        """
        生成验证码（字符串 + 图片）
        
        返回:
            元组 (验证码字符串, 图片字节流)
            
        说明:
            - 验证码字符串应存储在 session 中用于后续验证
            - 图片字节流可直接作为 HTTP 响应返回
        """
        code = self.generate_code()
        image_bytes = self.generate_image(code)
        
        return code, image_bytes
    
    # ------------------------------------------------------------------------
    # 验证码验证方法
    # ------------------------------------------------------------------------
    @staticmethod
    def verify(user_input: str, stored_code: str, case_sensitive: bool = False) -> bool:
        """
        验证用户输入的验证码是否正确
        
        参数:
            user_input: 用户输入的验证码
            stored_code: 存储在 session 中的正确验证码
            case_sensitive: 是否区分大小写，默认不区分
        
        返回:
            True 如果验证码正确，否则 False
        """
        if not user_input or not stored_code:
            return False
        
        if case_sensitive:
            return user_input == stored_code
        else:
            return user_input.lower() == stored_code.lower()
    
    @staticmethod
    def normalize_code(code: str) -> str:
        """
        标准化验证码（转为小写）
        
        参数:
            code: 原始验证码
        
        返回:
            标准化后的验证码（小写）
            
        说明:
            存储验证码时建议使用此方法标准化，
            以便后续验证时不区分大小写
        """
        if not code:
            return ''
        return code.lower()