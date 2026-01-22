"""
================================================================================
STATAU 文件服务模块 (services/file_service.py)
================================================================================
说明：
    - 本模块负责所有文件相关的业务逻辑
    - 包括：文件上传、文件读取、数据预览、文件格式验证
    - 不依赖 Flask 的 request 对象，接收纯 Python 参数

职责：
    1. 验证上传文件的格式
    2. 保存上传文件到指定目录
    3. 读取数据文件为 DataFrame
    4. 生成数据预览（前 N 行）

使用方式：
    from services.file_service import FileService
    
    file_service = FileService(upload_folder='/path/to/uploads')
    filepath = file_service.save_file(file_storage, filename)
    df = file_service.read_datafile(filepath)
================================================================================
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any, Tuple


class FileService:
    """
    文件服务类
    
    负责处理所有与数据文件相关的操作
    """
    
    # ------------------------------------------------------------------------
    # 支持的文件扩展名
    # ------------------------------------------------------------------------
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'dta'}
    
    def __init__(self, upload_folder: str):
        """
        初始化文件服务
        
        参数:
            upload_folder: 文件上传目录的绝对路径
        """
        self.upload_folder = upload_folder
        
        # 确保上传目录存在
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
            print(f"[FileService] 创建上传目录: {self.upload_folder}")
    
    # ------------------------------------------------------------------------
    # 文件验证方法
    # ------------------------------------------------------------------------
    def is_allowed_file(self, filename: str) -> bool:
        """
        检查文件扩展名是否在允许列表中
        
        参数:
            filename: 文件名（包含扩展名）
        
        返回:
            True 如果文件格式允许，否则 False
        """
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS
    
    def get_file_extension(self, filename: str) -> str:
        """
        获取文件扩展名（小写）
        
        参数:
            filename: 文件名
        
        返回:
            扩展名字符串（不含点号），如 'csv', 'xlsx'
        """
        if '.' not in filename:
            return ''
        return filename.rsplit('.', 1)[1].lower()
    
    # ------------------------------------------------------------------------
    # 文件保存方法
    # ------------------------------------------------------------------------
    def save_file(self, file_storage, filename: str) -> str:
        """
        保存上传的文件到上传目录
        
        参数:
            file_storage: Flask 的 FileStorage 对象
            filename: 保存的文件名
        
        返回:
            保存后的文件完整路径
        
        异常:
            ValueError: 如果文件格式不允许
        """
        if not self.is_allowed_file(filename):
            raise ValueError(f"不支持的文件格式: {filename}")
        
        filepath = os.path.join(self.upload_folder, filename)
        file_storage.save(filepath)
        print(f"[FileService] 文件已保存: {filepath}")
        
        return filepath
    
    def get_filepath(self, filename: str) -> str:
        """
        获取文件的完整路径
        
        参数:
            filename: 文件名
        
        返回:
            文件的完整路径
        """
        return os.path.join(self.upload_folder, filename)
    
    def file_exists(self, filename: str) -> bool:
        """
        检查文件是否存在
        
        参数:
            filename: 文件名
        
        返回:
            True 如果文件存在，否则 False
        """
        filepath = self.get_filepath(filename)
        return os.path.exists(filepath)
    
    # ------------------------------------------------------------------------
    # 数据读取方法
    # ------------------------------------------------------------------------
    def read_datafile(self, filepath: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """
        读取数据文件为 Pandas DataFrame
        
        参数:
            filepath: 文件完整路径
            nrows: 可选，只读取前 N 行（用于预览）
        
        返回:
            Pandas DataFrame
        
        异常:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件格式不支持
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        ext = self.get_file_extension(filepath)
        
        # 根据扩展名选择读取方法
        if ext == 'csv':
            if nrows:
                df = pd.read_csv(filepath, nrows=nrows)
            else:
                df = pd.read_csv(filepath)
        
        elif ext == 'dta':
            # Stata 文件不支持 nrows 参数，需要先全部读取再截取
            df = pd.read_stata(filepath)
            if nrows:
                df = df.head(nrows)
        
        elif ext in ('xlsx', 'xls'):
            if nrows:
                df = pd.read_excel(filepath, nrows=nrows)
            else:
                df = pd.read_excel(filepath)
        
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        return df
    
    def read_datafile_by_name(self, filename: str, nrows: Optional[int] = None) -> pd.DataFrame:
        """
        根据文件名读取数据文件
        
        参数:
            filename: 文件名（不含路径）
            nrows: 可选，只读取前 N 行
        
        返回:
            Pandas DataFrame
        """
        filepath = self.get_filepath(filename)
        return self.read_datafile(filepath, nrows)
    
    # ------------------------------------------------------------------------
    # 数据预览方法
    # ------------------------------------------------------------------------
    def get_preview_data(self, filename: str, nrows: int = 10) -> Dict[str, Any]:
        """
        获取数据文件的预览信息
        
        参数:
            filename: 文件名
            nrows: 预览行数，默认 10 行
        
        返回:
            字典，包含:
            - columns: 列名列表
            - dtypes: 各列数据类型
            - preview: 预览数据（字典列表）
        
        异常:
            FileNotFoundError: 如果文件不存在
        """
        df = self.read_datafile_by_name(filename, nrows=nrows)
        
        # 获取数据类型
        dtypes = {col: str(df[col].dtype) for col in df.columns}
        
        # 将 NaN 转换为 None 以便 JSON 序列化
        preview_data = df.replace({np.nan: None}).to_dict(orient='records')
        
        return {
            'columns': df.columns.tolist(),
            'dtypes': dtypes,
            'preview': preview_data
        }
    
    def get_columns(self, filename: str) -> List[str]:
        """
        获取数据文件的列名列表
        
        参数:
            filename: 文件名
        
        返回:
            列名列表
        """
        # 只读取第一行以获取列名，提高效率
        df = self.read_datafile_by_name(filename, nrows=1)
        return df.columns.tolist()