"""
================================================================================
STATAU 统计模型模块 (core/models.py)
================================================================================
说明：
    - 本模块包含所有统计分析模型的实现
    - 支持：OLS、固定效应、Logit、Probit、描述统计、相关性分析、VIF检验
    - 使用 statsmodels 和 linearmodels 库进行计算

设计理念：
    - StataModel 类封装所有统计计算逻辑
    - 与 Flask 路由完全解耦，只接收纯 Python 数据
    - 输出格式化的系数和统计量，供表格生成器使用

使用方式：
    from core.models import StataModel
    
    model = StataModel(df, y_var='y', x_vars=['x1', 'x2'], method='ols')
    result = model.fit(decimals=3)
    coeffs, stats = model.get_coeffs_dataframe()
================================================================================
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS, RandomEffects, PooledOLS
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
from scipy.stats import pearsonr, f as f_dist, chi2
from typing import Dict, List, Optional, Any, Tuple


# ============================================================================
# 辅助函数
# ============================================================================

def drop_singletons_func(df: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    """
    剔除 Singleton（只出现一次的个体）
    
    参数:
        df: 数据框
        entity_col: 个体标识列名
    
    返回:
        剔除 singleton 后的数据框
    
    说明:
        在固定效应模型中，只出现一次的个体无法估计固定效应，
        需要在回归前剔除
    """
    if not entity_col or entity_col not in df.columns:
        return df
    
    counts = df.groupby(entity_col)[entity_col].transform('count')
    return df[counts > 1].copy()


# ============================================================================
# 主模型类
# ============================================================================

class StataModel:
    """
    统计模型类
    
    封装所有统计分析方法，提供统一的接口
    
    属性:
        data: 原始数据框
        y_var: 因变量名
        x_vars: 自变量列表
        method: 分析方法
        panel_ids: 面板数据标识 {'entity': ..., 'time': ...}
        fe_vars: 固定效应变量列表
        se_options: 标准误选项 {'type': ..., 'cluster_var': ...}
        desc_options: 描述统计选项列表
        result: 模型拟合结果
        model_stats: 模型统计量字典
        custom_html: 自定义 HTML 输出（用于描述统计等）
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        y_var: str,
        x_vars: List[str],
        method: str = 'ols',
        panel_ids: Optional[Dict[str, str]] = None,
        fe_vars: Optional[List[str]] = None,
        se_options: Optional[Dict[str, Any]] = None,
        desc_options: Optional[List[str]] = None,
        merge_freq_tables: bool = False,
        group_var: Optional[str] = None
    ):
        """
        初始化统计模型
        
        参数:
            data: 数据框
            y_var: 因变量名
            x_vars: 自变量列表
            method: 分析方法 ('ols', 'fe', 'logit', 'probit', 'desc', 'corr', 'vif', 'freq', 'grouped_desc')
            panel_ids: 面板数据标识
            fe_vars: 固定效应变量列表
            se_options: 标准误选项
            desc_options: 描述统计选项
            merge_freq_tables: 是否合并频数统计表
            group_var: 分组变量（用于分组描述性统计）
        """
        self.data = data
        self.y_var = y_var
        self.x_vars = x_vars
        self.method = method
        self.panel_ids = panel_ids or {}
        self.fe_vars = fe_vars or []
        self.se_options = se_options or {'type': 'iid'}
        self.desc_options = desc_options or ['mean', 'std', 'min', 'max']
        self.merge_freq_tables = merge_freq_tables
        self.group_var = group_var
        
        # 结果存储
        self.result = None
        self.model_stats = {}
        self.custom_html = None

    # ========================================================================
    # 主拟合方法
    # ========================================================================
    
    def fit(self, decimals: int = 3, table_title: str = "") -> Any:
        """
        执行模型拟合
        
        参数:
            decimals: 小数位数
            table_title: 表格标题
        
        返回:
            模型拟合结果对象（回归模型）或 self（描述统计等）
        """
        # --------------------------------------------------------------------
        # 分支 1: 基础分析 (Desc, Corr, VIF, Freq, Grouped_Desc)
        # --------------------------------------------------------------------
        if self.method in ['desc', 'corr', 'vif', 'freq', 'grouped_desc']:
            return self._fit_basic_analysis(decimals, table_title)
        
        # --------------------------------------------------------------------
        # 分支 2: 回归分析 (OLS, FE, Logit, Probit)
        # --------------------------------------------------------------------
        return self._fit_regression(decimals, table_title)
    
    # ========================================================================
    # 基础分析方法
    # ========================================================================
    
    def _fit_basic_analysis(self, decimals: int, table_title: str) -> 'StataModel':
        """
        执行基础分析（描述统计、相关性、VIF）
        
        参数:
            decimals: 小数位数
            table_title: 表格标题
        
        返回:
            self（包含 custom_html 属性）
        """
        target_cols = self.x_vars
        if not target_cols:
            raise ValueError("未选择任何变量。")
        
        # 频数统计不需要只选择数值列，可以处理所有类型的列
        if self.method == 'freq':
            self._fit_frequency(self.data, decimals, table_title)
            return self
        
        # 分组描述性统计
        if self.method == 'grouped_desc':
            self._fit_grouped_descriptive(self.data, decimals, table_title)
            return self
        
        # 其他分析方法需要筛选数值列并清洗数据
        valid_cols = [c for c in target_cols if c in self.data.columns]
        df_clean = self.data[valid_cols].select_dtypes(include=[np.number]).dropna()
        
        if df_clean.empty:
            raise ValueError("有效数据为空。")
        
        # 根据方法类型执行不同分析
        if self.method == 'desc':
            self._fit_descriptive(df_clean, decimals, table_title)
        elif self.method == 'corr':
            self._fit_correlation(df_clean, decimals, table_title)
        elif self.method == 'vif':
            self._fit_vif(df_clean, decimals, table_title)
        
        return self
    
    def _fit_descriptive(self, df: pd.DataFrame, decimals: int, title: str) -> None:
        """
        执行描述性统计分析
        
        参数:
            df: 清洗后的数据框
            decimals: 小数位数
            title: 表格标题
        """
        desc = df.describe().T
        
        # 列名映射
        col_map = {
            'count': 'N', 'mean': 'Mean', 'std': 'Std.Dev',
            'min': 'Min', 'max': 'Max', 'p50': 'Median'
        }
        
        # 构造最终表格
        final_cols = []
        rename_map = {}
        
        for opt in self.desc_options:
            # 将nobs映射为count
            if opt == 'nobs':
                opt = 'count'
            # Pandas describe 输出的百分位数键名是 '50%'
            pd_key = '50%' if opt == 'p50' else opt
            if pd_key in desc.columns:
                if pd_key not in final_cols:  # 避免重复添加
                    final_cols.append(pd_key)
                    rename_map[pd_key] = col_map.get(opt, opt)
        
        final_df = desc[final_cols].rename(columns=rename_map)
        
        # N 列转为整数
        if 'N' in final_df.columns:
            final_df['N'] = final_df['N'].astype(int)
        
        # 生成 HTML
        title = title if title else "Descriptive Statistics"
        self.custom_html = self._generate_html_table(final_df, title, decimals=decimals)
    
    def _fit_grouped_descriptive(self, df: pd.DataFrame, decimals: int, title: str) -> None:
        """
        执行分组描述性统计分析
        
        参数:
            df: 数据框
            decimals: 小数位数
            title: 表格标题
        """
        if not self.group_var:
            raise ValueError("未指定分组变量。")
        
        if self.group_var not in df.columns:
            raise ValueError(f"分组变量 '{self.group_var}' 不存在于数据中。")
        
        # 检查分析变量
        target_cols = self.x_vars
        if not target_cols:
            raise ValueError("未选择任何分析变量。")
        
        # 筛选数值列
        valid_cols = [c for c in target_cols if c in df.columns]
        numeric_cols = [c for c in valid_cols if df[c].dtype in [np.float64, np.float32, np.int64, np.int32]]
        
        if not numeric_cols:
            raise ValueError("没有可用的数值型变量进行描述性统计。")
        
        # 只删除分组变量的缺失值，保留分析变量的缺失值
        df_clean = df[[self.group_var] + numeric_cols].dropna(subset=[self.group_var])
        
        if df_clean.empty:
            raise ValueError("清洗后的数据为空。")
        
        # 按分组变量分组计算描述性统计
        grouped = df_clean.groupby(self.group_var)
        
        # 为每个分组构建独立的结果表格
        group_tables = []
        
        for group_name, group_data in grouped:
            group_results = []
            
            for var in numeric_cols:
                # 对每个变量单独处理缺失值
                var_data = group_data[var].dropna()
                
                row_dict = {'Variable': var}
                
                # 如果该变量在该分组中全是缺失值，只显示N=0，其他统计量不显示
                if len(var_data) == 0:
                    if 'nobs' in self.desc_options or 'count' in self.desc_options:
                        row_dict['N'] = 0
                    # 其他统计量设置为空字符串（不显示）
                    if 'mean' in self.desc_options:
                        row_dict['Mean'] = ''
                    if 'std' in self.desc_options:
                        row_dict['Std.Dev'] = ''
                    if 'min' in self.desc_options:
                        row_dict['Min'] = ''
                    if 'max' in self.desc_options:
                        row_dict['Max'] = ''
                    if 'p50' in self.desc_options:
                        row_dict['Median'] = ''
                else:
                    # 有有效数据，正常计算统计量
                    if 'nobs' in self.desc_options or 'count' in self.desc_options:
                        row_dict['N'] = len(var_data)
                    if 'mean' in self.desc_options:
                        row_dict['Mean'] = var_data.mean()
                    if 'std' in self.desc_options:
                        row_dict['Std.Dev'] = var_data.std()
                    if 'min' in self.desc_options:
                        row_dict['Min'] = var_data.min()
                    if 'max' in self.desc_options:
                        row_dict['Max'] = var_data.max()
                    if 'p50' in self.desc_options:
                        row_dict['Median'] = var_data.median()
                
                group_results.append(row_dict)
            
            # 如果该分组有有效数据，添加到结果中
            if group_results:
                group_df = pd.DataFrame(group_results)
                group_tables.append({
                    'group_name': str(group_name),
                    'data': group_df
                })
        
        # 生成HTML（竖式布局，每个分组一个表格）
        title = title if title else f"Grouped Descriptive Statistics by {self.group_var}"
        self.custom_html = self._generate_grouped_descriptive_html_vertical(
            group_tables, title, decimals, self.group_var
        )
    
    def _generate_grouped_descriptive_html_vertical(
        self,
        group_tables: list,
        title: str,
        decimals: int,
        group_var: str
    ) -> str:
        """
        生成分组描述性统计的HTML表格（竖式布局）
        
        参数:
            group_tables: 分组表格列表，每个元素包含 {'group_name': ..., 'data': DataFrame}
            title: 表格标题
            decimals: 小数位数
            group_var: 分组变量名
        
        返回:
            HTML字符串
        """
        if not group_tables:
            return '<div class="alert alert-warning">没有可显示的数据</div>'
        
        html_parts = []
        
        for group_info in group_tables:
            group_name = group_info['group_name']
            df = group_info['data']
            
            # 每个分组一个独立的表格
            html = f'<div class="table-editable-container" style="margin-bottom: 30px;">'
            
            # 分组标题
            group_title = f"{group_var} = {group_name}"
            html += f'<h6 style="text-align: center; font-weight: bold; margin-bottom: 10px;">{group_title}</h6>'
            
            html += '<table class="academic-table" style="width: auto; margin: 0 auto; min-width: 50%;">'
            
            # 表头
            html += '<thead><tr>'
            html += '<th style="border-bottom: 1px solid black; text-align: left;">Variable</th>'
            
            # 动态添加统计量列
            stat_cols = [col for col in df.columns if col != 'Variable']
            for col in stat_cols:
                html += f'<th style="border-bottom: 1px solid black; text-align: center;">{col}</th>'
            
            html += '</tr></thead><tbody>'
            
            # 内容
            for idx, row in df.iterrows():
                html += '<tr>'
                html += f'<td style="text-align: left;">{row["Variable"]}</td>'
                
                # 统计量
                for col in stat_cols:
                    val = row[col]
                    if val == '' or val is None or (isinstance(val, float) and np.isnan(val)):
                        # 空值或缺失值，显示为空
                        html += '<td style="text-align: center;">-</td>'
                    elif col == 'N':
                        html += f'<td style="text-align: center;">{int(val)}</td>'
                    else:
                        html += f'<td style="text-align: center;">{val:.{decimals}f}</td>'
                
                html += '</tr>'
            
            html += '</tbody>'
            html += '<tfoot><tr><td colspan="' + str(len(df.columns)) + '" style="border-top: 1px solid black;"></td></tr></tfoot>'
            html += '</table></div>'
            
            html_parts.append(html)
        
        # 添加总标题
        final_html = f'<div class="table-editable-container">'
        final_html += f'<input type="text" class="table-title-input" value="{title}" style="margin-bottom: 20px;" />'
        final_html += '</div>'
        final_html += ''.join(html_parts)
        
        return final_html
    
    def _fit_correlation(self, df: pd.DataFrame, decimals: int, title: str) -> None:
        """
        执行相关性分析（带显著性星号）
        
        参数:
            df: 清洗后的数据框
            decimals: 小数位数
            title: 表格标题
        """
        cols = df.columns
        n = len(cols)
        corr_matrix = df.corr()
        p_matrix = np.zeros((n, n))
        
        # 计算 p-value
        for i in range(n):
            for j in range(n):
                if i == j:
                    p_matrix[i, j] = 1.0
                else:
                    _, p = pearsonr(df[cols[i]], df[cols[j]])
                    p_matrix[i, j] = p
        
        # 格式化带星号的字符串矩阵
        formatted_df = pd.DataFrame(index=cols, columns=cols)
        for i in range(n):
            for j in range(n):
                val = corr_matrix.iloc[i, j]
                p_val = p_matrix[i, j]
                
                stars = ""
                if i != j:  # 对角线不加星
                    if p_val < 0.01:
                        stars = "***"
                    elif p_val < 0.05:
                        stars = "**"
                    elif p_val < 0.1:
                        stars = "*"
                
                formatted_df.iloc[i, j] = f"{val:.{decimals}f}{stars}"
        
        title = title if title else "Correlation Matrix"
        note = "*** p<0.01, ** p<0.05, * p<0.1"
        self.custom_html = self._generate_html_table(
            formatted_df, title, index_name="Variables", bottom_note=note
        )
    
    def _fit_vif(self, df: pd.DataFrame, decimals: int, title: str) -> None:
        """
        执行 VIF 共线性检验
        
        参数:
            df: 清洗后的数据框
            decimals: 小数位数
            title: 表格标题
        """
        X = df.copy()
        X['const'] = 1
        vif_data = []
        vif_values = []  # 用于计算 Mean VIF
        
        for i in range(len(X.columns)):
            col_name = X.columns[i]
            if col_name == 'const':
                continue
            try:
                val = variance_inflation_factor(X.values, i)
                if np.isinf(val):
                    vif_str = "Inf"
                    tol_str = "0.000"
                else:
                    vif_str = f"{val:.{decimals}f}"
                    tol_str = f"{1/val:.{decimals}f}"  # 容忍度 1/VIF
                    vif_values.append(val)
                
                vif_data.append({
                    'Variable': col_name,
                    'VIF': vif_str,
                    '1/VIF': tol_str
                })
            except Exception:
                vif_data.append({
                    'Variable': col_name,
                    'VIF': 'Error',
                    '1/VIF': '-'
                })
        
        # 计算 Mean VIF
        if vif_values:
            mean_vif = np.mean(vif_values)
            vif_data.append({
                'Variable': 'Mean VIF',
                'VIF': f"{mean_vif:.{decimals}f}",
                '1/VIF': '.'
            })
        
        vif_df = pd.DataFrame(vif_data)
        title = title if title else "Variance Inflation Factor"
        self.custom_html = self._generate_html_table(vif_df, title, index_name=None)
    
    def _fit_frequency(self, df: pd.DataFrame, decimals: int, title: str) -> None:
        """
        执行频数统计分析（类似Stata的tab命令）
        
        参数:
            df: 清洗后的数据框
            decimals: 小数位数
            title: 表格标题
        """
        # 对于频数统计，我们不需要只选择数值列，可以处理分类变量
        # 重新从原始数据中获取选中的列（包括非数值列）
        target_cols = self.x_vars
        valid_cols = [c for c in target_cols if c in self.data.columns]
        
        if not valid_cols:
            raise ValueError("未选择任何有效变量。")
        
        # 如果只选择了一个变量，生成单变量频数表
        if len(valid_cols) == 1:
            self._fit_frequency_single(valid_cols[0], decimals, title)
        else:
            # 如果选择了多个变量，根据merge_freq_tables参数决定是否合并
            if self.merge_freq_tables:
                self._fit_frequency_merged(valid_cols, decimals, title)
            else:
                self._fit_frequency_multiple(valid_cols, decimals, title)
    
    def _fit_frequency_single(self, var: str, decimals: int, title: str) -> None:
        """
        生成单变量频数统计表
        
        参数:
            var: 变量名
            decimals: 小数位数
            title: 表格标题
        """
        # 获取变量数据（删除缺失值）
        data_series = self.data[var].dropna()
        
        if len(data_series) == 0:
            raise ValueError(f"变量 {var} 没有有效数据。")
        
        # 计算频数
        freq_counts = data_series.value_counts().sort_index()
        total = len(data_series)
        
        # 构建频数表
        freq_data = []
        cumulative_freq = 0
        cumulative_pct = 0.0
        
        for value, count in freq_counts.items():
            freq = int(count)
            percent = (count / total) * 100
            cumulative_freq += freq
            cumulative_pct += percent
            
            freq_data.append({
                'Value': str(value),
                'Freq.': freq,
                'Percent': f"{percent:.{decimals}f}",
                'Cum.': f"{cumulative_pct:.{decimals}f}"
            })
        
        # 添加总计行
        freq_data.append({
            'Value': 'Total',
            'Freq.': total,
            'Percent': f"{100.0:.{decimals}f}",
            'Cum.': f"{100.0:.{decimals}f}"
        })
        
        freq_df = pd.DataFrame(freq_data)
        title = title if title else f"Frequency Table: {var}"
        
        # 生成HTML（使用自定义样式，Total行加粗边框）
        self.custom_html = self._generate_frequency_html(freq_df, title, var)
    
    def _fit_frequency_multiple(self, vars: List[str], decimals: int, title: str) -> None:
        """
        生成多变量频数统计表（每个变量一个表格）
        
        参数:
            vars: 变量列表
            decimals: 小数位数
            title: 表格标题
        """
        html_parts = []
        
        for var in vars:
            try:
                # 获取变量数据（删除缺失值）
                data_series = self.data[var].dropna()
                
                if len(data_series) == 0:
                    continue
                
                # 计算频数
                freq_counts = data_series.value_counts().sort_index()
                total = len(data_series)
                
                # 构建频数表
                freq_data = []
                cumulative_freq = 0
                cumulative_pct = 0.0
                
                for value, count in freq_counts.items():
                    freq = int(count)
                    percent = (count / total) * 100
                    cumulative_freq += freq
                    cumulative_pct += percent
                    
                    freq_data.append({
                        'Value': str(value),
                        'Freq.': freq,
                        'Percent': f"{percent:.{decimals}f}",
                        'Cum.': f"{cumulative_pct:.{decimals}f}"
                    })
                
                # 添加总计行
                freq_data.append({
                    'Value': 'Total',
                    'Freq.': total,
                    'Percent': f"{100.0:.{decimals}f}",
                    'Cum.': f"{100.0:.{decimals}f}"
                })
                
                freq_df = pd.DataFrame(freq_data)
                var_title = f"Frequency Table: {var}"
                
                # 生成单个表格的HTML
                html_parts.append(self._generate_frequency_html(freq_df, var_title, var))
            
            except Exception as e:
                # 如果某个变量出错，跳过并继续
                continue
        
        # 合并所有表格
        if html_parts:
            self.custom_html = '<div style="margin-bottom: 30px;">' + '</div><div style="margin-bottom: 30px;">'.join(html_parts) + '</div>'
        else:
            raise ValueError("没有生成任何有效的频数表。")
    
    def _fit_frequency_merged(self, vars: List[str], decimals: int, title: str) -> None:
        """
        生成合并的多变量频数统计表
        
        参数:
            vars: 变量列表
            decimals: 小数位数
            title: 表格标题
        """
        # 收集所有变量的频数数据
        merged_data = []
        
        for var in vars:
            try:
                # 获取变量数据（删除缺失值）
                data_series = self.data[var].dropna()
                
                if len(data_series) == 0:
                    continue
                
                # 计算频数
                freq_counts = data_series.value_counts().sort_index()
                total = len(data_series)
                
                # 构建频数数据
                cumulative_pct = 0.0
                
                for value, count in freq_counts.items():
                    freq = int(count)
                    percent = (count / total) * 100
                    cumulative_pct += percent
                    
                    merged_data.append({
                        'Variable': var,
                        'Value': str(value),
                        'Freq.': freq,
                        'Percent': f"{percent:.{decimals}f}",
                        'Cum.': f"{cumulative_pct:.{decimals}f}"
                    })
                
                # 添加每个变量的小计行
                merged_data.append({
                    'Variable': var,
                    'Value': 'Subtotal',
                    'Freq.': total,
                    'Percent': f"{100.0:.{decimals}f}",
                    'Cum.': f"{100.0:.{decimals}f}"
                })
            
            except Exception as e:
                # 如果某个变量出错，跳过并继续
                continue
        
        if not merged_data:
            raise ValueError("没有生成任何有效的频数表。")
        
        # 生成合并的HTML表格
        merged_df = pd.DataFrame(merged_data)
        title = title if title else "Merged Frequency Table"
        self.custom_html = self._generate_merged_frequency_html(merged_df, title, decimals)
    
    def _generate_merged_frequency_html(self, df: pd.DataFrame, title: str, decimals: int) -> str:
        """
        生成合并频数表的HTML
        
        参数:
            df: 合并的频数数据框
            title: 表格标题
            decimals: 小数位数
        
        返回:
            HTML字符串
        """
        html = f'<div class="table-editable-container">'
        html += f'<input type="text" class="table-title-input" value="{title}" />'
        html += '<table class="academic-table" style="width: auto; margin: 0 auto; min-width: 60%;">'
        
        # 表头
        html += '<thead><tr>'
        html += '<th style="border-bottom: 1px solid black; text-align: left;">Variable</th>'
        html += '<th style="border-bottom: 1px solid black; text-align: left;">Value</th>'
        html += '<th style="border-bottom: 1px solid black; text-align: center;">Freq.</th>'
        html += '<th style="border-bottom: 1px solid black; text-align: center;">Percent</th>'
        html += '<th style="border-bottom: 1px solid black; text-align: center;">Cum.</th>'
        html += '</tr></thead><tbody>'
        
        # 内容
        current_var = None
        for idx, row in df.iterrows():
            var_name = row['Variable']
            value = row['Value']
            
            # Subtotal 行加粗边框区分
            if value == 'Subtotal':
                row_style = "border-top: 1px solid black; font-weight: bold;"
            else:
                row_style = ""
            
            html += f'<tr style="{row_style}">'
            
            # 变量名只在第一次出现时显示，或者在Subtotal行显示
            if value == 'Subtotal' or var_name != current_var:
                html += f'<td style="text-align: left;">{var_name}</td>'
                current_var = var_name
            else:
                html += '<td style="text-align: left;"></td>'
            
            html += f'<td style="text-align: left;">{value}</td>'
            html += f'<td style="text-align: center;">{row["Freq."]}</td>'
            html += f'<td style="text-align: center;">{row["Percent"]}</td>'
            html += f'<td style="text-align: center;">{row["Cum."]}</td>'
            html += '</tr>'
        
        html += '</tbody>'
        html += '<tfoot><tr><td colspan="5" style="border-top: 1px solid black;"></td></tr></tfoot>'
        html += '</table></div>'
        
        return html
    
    def _generate_frequency_html(self, df: pd.DataFrame, title: str, var_name: str) -> str:
        """
        生成频数表的HTML
        
        参数:
            df: 频数数据框
            title: 表格标题
            var_name: 变量名
        
        返回:
            HTML字符串
        """
        html = f'<div class="table-editable-container">'
        html += f'<input type="text" class="table-title-input" value="{title}" />'
        html += '<table class="academic-table" style="width: auto; margin: 0 auto; min-width: 50%;">'
        
        # 表头
        html += '<thead><tr>'
        html += f'<th style="border-bottom: 1px solid black; text-align: left;">{var_name}</th>'
        html += '<th style="border-bottom: 1px solid black; text-align: center;">Freq.</th>'
        html += '<th style="border-bottom: 1px solid black; text-align: center;">Percent</th>'
        html += '<th style="border-bottom: 1px solid black; text-align: center;">Cum.</th>'
        html += '</tr></thead><tbody>'
        
        # 内容
        for idx, row in df.iterrows():
            # Total 行加粗边框区分
            row_style = "border-top: 1px solid black; font-weight: bold;" if row['Value'] == 'Total' else ""
            
            html += f'<tr style="{row_style}">'
            html += f'<td style="text-align: left;">{row["Value"]}</td>'
            html += f'<td style="text-align: center;">{row["Freq."]}</td>'
            html += f'<td style="text-align: center;">{row["Percent"]}</td>'
            html += f'<td style="text-align: center;">{row["Cum."]}</td>'
            html += '</tr>'
        
        html += '</tbody>'
        html += '<tfoot><tr><td colspan="4" style="border-top: 1px solid black;"></td></tr></tfoot>'
        html += '</table></div>'
        
        return html
    
    # ========================================================================
    # 回归分析方法
    # ========================================================================
    
    def _fit_regression(self, decimals: int, table_title: str) -> Any:
        """
        执行回归分析
        
        参数:
            decimals: 小数位数
            table_title: 表格标题
        
        返回:
            模型拟合结果对象
        """
        # 准备数据列
        cols = [self.y_var] + self.x_vars + self.fe_vars
        cluster_var = self.se_options.get('cluster_var')
        if cluster_var and cluster_var not in cols:
            cols.append(cluster_var)
        
        entity_col = self.panel_ids.get('entity')
        time_col = self.panel_ids.get('time')
        if entity_col and entity_col not in cols:
            cols.append(entity_col)
        if time_col and time_col not in cols:
            cols.append(time_col)
        
        cols = list(set([c for c in cols if c]))
        df_clean = self.data[cols].dropna()
        
        # 根据方法类型执行不同回归
        if self.method == 'fe':
            return self._fit_fixed_effects(df_clean, entity_col, time_col)
        elif self.method == 're':
            return self._fit_random_effects(df_clean, entity_col, time_col)
        elif self.method == 'pooled':
            return self._fit_pooled_ols(df_clean, entity_col, time_col)
        else:
            return self._fit_standard_regression(df_clean)
    
    def _fit_fixed_effects(
        self,
        df: pd.DataFrame,
        entity_col: str,
        time_col: str
    ) -> Any:
        """
        执行固定效应回归
        
        参数:
            df: 清洗后的数据框
            entity_col: 个体标识列
            time_col: 时间标识列
        
        返回:
            PanelOLS 拟合结果
        """
        if not entity_col or not time_col:
            raise ValueError("FE Model needs Entity and Time ID")
        
        # 剔除 singleton
        df = drop_singletons_func(df, entity_col)
        
        # 设置面板索引
        df_panel = df.set_index([entity_col, time_col])
        y = df_panel[self.y_var]
        
        # 准备自变量
        exog_cols = [v for v in self.x_vars if v != self.y_var]
        if not exog_cols:
            df_panel['const'] = 1
            x = df_panel[['const']]
        else:
            x = df_panel[exog_cols]
        
        # 配置固定效应
        entity_effects = False
        time_effects = False
        other_effects = {}
        
        for fe in self.fe_vars:
            if fe == entity_col:
                entity_effects = True
            elif fe == time_col:
                time_effects = True
            else:
                other_effects[fe] = df_panel[fe].astype('category')
        
        if not other_effects:
            other_effects = None
        
        # 创建模型
        mod = PanelOLS(
            y, x,
            entity_effects=entity_effects,
            time_effects=time_effects,
            other_effects=other_effects,
            drop_absorbed=True
        )
        
        # 配置标准误
        se_type = self.se_options.get('type')
        fit_kwargs = {}
        
        if se_type == 'robust':
            fit_kwargs['cov_type'] = 'robust'
        elif se_type == 'cluster':
            fit_kwargs['cov_type'] = 'clustered'
            c_var = self.se_options.get('cluster_var')
            if c_var == entity_col:
                fit_kwargs['cluster_entity'] = True
            elif c_var == time_col:
                fit_kwargs['cluster_time'] = True
            else:
                fit_kwargs['clusters'] = df_panel[c_var]
        else:
            fit_kwargs['cov_type'] = 'unadjusted'
        
        # 拟合模型
        self.result = mod.fit(**fit_kwargs)
        
        # 计算统计量
        r2_inclusive = self.result.rsquared_inclusive
        nobs = self.result.nobs
        df_resid = self.result.df_resid
        adj_r2 = 1 - (1 - r2_inclusive) * (nobs - 1) / df_resid if df_resid > 0 else np.nan
        
        self.model_stats = {
            'N': int(nobs),
            'R2': r2_inclusive,
            'Adj-R2': adj_r2,
            'F': self.result.f_statistic.stat
        }
        
        return self.result
    
    def _fit_random_effects(
        self,
        df: pd.DataFrame,
        entity_col: str,
        time_col: str
    ) -> Any:
        """
        执行随机效应回归
        
        参数:
            df: 清洗后的数据框
            entity_col: 个体标识列
            time_col: 时间标识列
        
        返回:
            RandomEffects 拟合结果
        """
        if not entity_col or not time_col:
            raise ValueError("RE Model needs Entity and Time ID")
        
        # 剔除 singleton
        df = drop_singletons_func(df, entity_col)
        
        # 设置面板索引
        df_panel = df.set_index([entity_col, time_col])
        y = df_panel[self.y_var]
        
        # 准备自变量（随机效应模型需要常数项）
        exog_cols = [v for v in self.x_vars if v != self.y_var]
        if not exog_cols:
            df_panel['const'] = 1
            x = df_panel[['const']]
        else:
            x = add_constant(df_panel[exog_cols])
        
        # 创建随机效应模型
        mod = RandomEffects(y, x)
        
        # 配置标准误
        se_type = self.se_options.get('type')
        fit_kwargs = {}
        
        if se_type == 'robust':
            fit_kwargs['cov_type'] = 'robust'
        elif se_type == 'cluster':
            fit_kwargs['cov_type'] = 'clustered'
            c_var = self.se_options.get('cluster_var')
            if c_var == entity_col:
                fit_kwargs['cluster_entity'] = True
            elif c_var == time_col:
                fit_kwargs['cluster_time'] = True
            else:
                fit_kwargs['clusters'] = df_panel[c_var]
        else:
            fit_kwargs['cov_type'] = 'unadjusted'
        
        # 拟合模型
        self.result = mod.fit(**fit_kwargs)
        
        # 计算统计量
        r2_overall = self.result.rsquared_overall
        nobs = self.result.nobs
        df_resid = self.result.df_resid
        adj_r2 = 1 - (1 - r2_overall) * (nobs - 1) / df_resid if df_resid > 0 else np.nan
        
        self.model_stats = {
            'N': int(nobs),
            'R2': r2_overall,
            'Adj-R2': adj_r2,
            'F': self.result.f_statistic.stat
        }
        
        return self.result
    
    def _fit_pooled_ols(
        self,
        df: pd.DataFrame,
        entity_col: str,
        time_col: str
    ) -> Any:
        """
        执行混合OLS回归（面板数据的混合估计）
        
        参数:
            df: 清洗后的数据框
            entity_col: 个体标识列
            time_col: 时间标识列
        
        返回:
            PooledOLS 拟合结果
        """
        if not entity_col or not time_col:
            raise ValueError("Pooled OLS Model needs Entity and Time ID")
        
        # 剔除 singleton
        df = drop_singletons_func(df, entity_col)
        
        # 设置面板索引
        df_panel = df.set_index([entity_col, time_col])
        y = df_panel[self.y_var]
        
        # 准备自变量（混合OLS需要常数项）
        exog_cols = [v for v in self.x_vars if v != self.y_var]
        if not exog_cols:
            df_panel['const'] = 1
            x = df_panel[['const']]
        else:
            x = add_constant(df_panel[exog_cols])
        
        # 创建混合OLS模型
        mod = PooledOLS(y, x)
        
        # 配置标准误
        se_type = self.se_options.get('type')
        fit_kwargs = {}
        
        if se_type == 'robust':
            fit_kwargs['cov_type'] = 'robust'
        elif se_type == 'cluster':
            fit_kwargs['cov_type'] = 'clustered'
            c_var = self.se_options.get('cluster_var')
            if c_var == entity_col:
                fit_kwargs['cluster_entity'] = True
            elif c_var == time_col:
                fit_kwargs['cluster_time'] = True
            else:
                fit_kwargs['clusters'] = df_panel[c_var]
        else:
            fit_kwargs['cov_type'] = 'unadjusted'
        
        # 拟合模型
        self.result = mod.fit(**fit_kwargs)
        
        # 计算统计量
        r2 = self.result.rsquared
        nobs = self.result.nobs
        df_resid = self.result.df_resid
        adj_r2 = 1 - (1 - r2) * (nobs - 1) / df_resid if df_resid > 0 else np.nan
        
        self.model_stats = {
            'N': int(nobs),
            'R2': r2,
            'Adj-R2': adj_r2,
            'F': self.result.f_statistic.stat
        }
        
        return self.result
    
    def _fit_standard_regression(self, df: pd.DataFrame) -> Any:
        """
        执行标准回归（OLS、Logit、Probit）
        
        参数:
            df: 清洗后的数据框
        
        返回:
            statsmodels 拟合结果
        """
        formula = f"{self.y_var} ~ {' + '.join(self.x_vars)}"
        
        if self.method == 'ols':
            model = smf.ols(formula, data=df)
            
            # 配置标准误
            if self.se_options.get('type') == 'robust':
                self.result = model.fit(cov_type='HC1')
            elif self.se_options.get('type') == 'cluster':
                c_var = self.se_options.get('cluster_var')
                self.result = model.fit(
                    cov_type='cluster',
                    cov_kwds={'groups': df[c_var]}
                )
            else:
                self.result = model.fit()
            
            self.model_stats = {
                'N': int(self.result.nobs),
                'R2': self.result.rsquared,
                'Adj-R2': self.result.rsquared_adj,
                'F': self.result.fvalue,
                'AIC': self.result.aic
            }
        
        elif self.method == 'logit':
            model = smf.logit(formula, data=df)
            self.result = model.fit()
            self.model_stats = {
                'N': int(self.result.nobs),
                'Pseudo-R2': self.result.prsquared,
                'AIC': self.result.aic,
                'LL': self.result.llf
            }
        
        elif self.method == 'probit':
            model = smf.probit(formula, data=df)
            self.result = model.fit()
            self.model_stats = {
                'N': int(self.result.nobs),
                'Pseudo-R2': self.result.prsquared,
                'AIC': self.result.aic,
                'LL': self.result.llf
            }
        
        return self.result
    
    # ========================================================================
    # HTML 表格生成方法
    # ========================================================================
    
    def _generate_html_table(
        self,
        df: pd.DataFrame,
        title: str,
        index_name: str = "Variable",
        decimals: int = 3,
        bottom_note: str = ""
    ) -> str:
        """
        生成通用 HTML 表格
        
        参数:
            df: 数据框
            title: 表格标题
            index_name: 索引列名称（None 则不显示索引）
            decimals: 小数位数
            bottom_note: 底部注释
        
        返回:
            HTML 字符串
        """
        html = f'<div class="table-editable-container">'
        html += f'<input type="text" class="table-title-input" value="{title}" />'
        html += '<table class="academic-table" style="width: auto; margin: 0 auto; min-width: 50%;">'
        
        # 表头
        html += '<thead><tr>'
        if index_name:
            html += f'<th style="border-bottom: 1px solid black; text-align: left;">{index_name}</th>'
        
        for col in df.columns:
            html += f'<th style="border-bottom: 1px solid black; text-align: center;">{col}</th>'
        html += '</tr></thead><tbody>'
        
        # 内容
        for idx, row in df.iterrows():
            # Mean VIF 行加粗边框区分
            row_style = "border-top: 1px solid black;" if idx == 'Mean VIF' else ""
            
            html += f'<tr style="{row_style}">'
            if index_name:
                html += f'<td style="text-align: left;">{idx}</td>'
            
            for col in df.columns:
                val = row[col]
                # 如果已经是字符串，直接显示
                if isinstance(val, str):
                    disp = val
                # 如果是数字，应用 decimals
                elif isinstance(val, (int, float)):
                    if col == 'N':
                        disp = f"{int(val)}"
                    else:
                        disp = f"{val:.{decimals}f}"
                else:
                    disp = str(val)
                
                html += f'<td style="text-align: center;">{disp}</td>'
            html += '</tr>'
        
        html += '</tbody>'
        
        # 底部 Note
        if bottom_note:
            colspan = len(df.columns) + (1 if index_name else 0)
            html += f'<tfoot><tr><td colspan="{colspan}" style="border-top: 1px solid black; font-size: 0.8em; text-align: left;">{bottom_note}</td></tr></tfoot>'
        else:
            colspan = len(df.columns) + (1 if index_name else 0)
            html += f'<tfoot><tr><td colspan="{colspan}" style="border-top: 1px solid black;"></td></tr></tfoot>'
        
        html += '</table></div>'
        return html
    
    # ========================================================================
    # 系数提取方法
    # ========================================================================
    
    def get_coeffs_dataframe(
        self,
        decimals: int = 3,
        show_se: bool = True
    ) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, Any]]:
        """
        获取格式化的系数数据框
        
        参数:
            decimals: 小数位数
            show_se: 是否显示标准误（False 则显示 t/z 值）
        
        返回:
            元组 (系数字典, 统计量字典)
            系数字典格式: {变量名: (系数字符串, 标准误/t值字符串)}
        """
        if self.custom_html:
            return {}, {}
        
        if self.method in ['fe', 're', 'pooled']:
            return self._get_panel_coeffs(decimals, show_se)
        else:
            return self._get_standard_coeffs(decimals, show_se)
    
    def _get_panel_coeffs(
        self,
        decimals: int,
        show_se: bool
    ) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, Any]]:
        """
        获取面板数据模型的系数（FE/RE/Pooled）
        """
        params = self.result.params
        std_errors = self.result.std_errors
        pvalues = self.result.pvalues
        
        formatted_series = {}
        for var in params.index:
            if var in ('const', 'Intercept'):
                continue
            
            coef = params[var]
            p_val = pvalues[var]
            
            # 显著性星号
            if p_val < 0.01:
                stars = "***"
            elif p_val < 0.05:
                stars = "**"
            elif p_val < 0.1:
                stars = "*"
            else:
                stars = ""
            
            coef_str = f"{coef:.{decimals}f}{stars}"
            val = std_errors[var] if show_se else self.result.tstats[var]
            formatted_series[var] = (coef_str, f"({val:.{decimals}f})")
        
        return formatted_series, self.model_stats
    
    def _get_standard_coeffs(
        self,
        decimals: int,
        show_se: bool
    ) -> Tuple[Dict[str, Tuple[str, str]], Dict[str, Any]]:
        """
        获取标准回归模型的系数
        """
        summary = self.result.summary2()
        df = summary.tables[1].copy()
        
        if 'Intercept' in df.index:
            df = df.rename(index={'Intercept': 'Constant'})
        
        formatted_series = {}
        for idx, row in df.iterrows():
            p = row.get('P>|t|', row.get('P>|z|', 1))
            
            # 显著性星号
            if p < 0.01:
                stars = "***"
            elif p < 0.05:
                stars = "**"
            elif p < 0.1:
                stars = "*"
            else:
                stars = ""
            
            coef_str = f"{row['Coef.']:.{decimals}f}{stars}"
            val = row['Std.Err.'] if show_se else row.get('t', row.get('z'))
            formatted_series[idx] = (coef_str, f"({val:.{decimals}f})")
        
        return formatted_series, self.model_stats


# ============================================================================
# 模型检验类
# ============================================================================

class ModelTests:
    """
    面板数据模型检验类
    
    提供F检验和Hausman检验功能，用于选择合适的面板数据模型
    """
    
    @staticmethod
    def f_test_fe_vs_pooled(
        df: pd.DataFrame,
        y_var: str,
        x_vars: List[str],
        entity_col: str,
        time_col: str,
        decimals: int = 4
    ) -> Dict[str, Any]:
        """
        F检验：固定效应模型 vs 混合OLS模型
        
        参数:
            df: 数据框
            y_var: 因变量名
            x_vars: 自变量列表
            entity_col: 个体标识列
            time_col: 时间标识列
            decimals: 小数位数
        
        返回:
            包含检验结果的字典
        """
        # 准备数据
        cols = [y_var] + x_vars + [entity_col, time_col]
        df_clean = df[cols].dropna()
        df_clean = drop_singletons_func(df_clean, entity_col)
        
        # 1. 估计混合OLS模型
        formula = f"{y_var} ~ {' + '.join(x_vars)}"
        pooled_model = smf.ols(formula, data=df_clean)
        pooled_result = pooled_model.fit()
        rss_pooled = pooled_result.ssr  # 残差平方和
        
        # 2. 估计固定效应模型
        df_panel = df_clean.set_index([entity_col, time_col])
        y = df_panel[y_var]
        x = df_panel[x_vars]
        
        fe_model = PanelOLS(y, x, entity_effects=True, drop_absorbed=True)
        fe_result = fe_model.fit()
        rss_fe = fe_result.resid_ss  # 残差平方和
        
        # 3. 计算F统计量
        # F = [(RSS_pooled - RSS_fe) / (N-1)] / [RSS_fe / (NT - N - K)]
        n_entities = df_clean[entity_col].nunique()
        n_obs = len(df_clean)
        k_vars = len(x_vars)
        
        df1 = n_entities - 1  # 分子自由度
        df2 = n_obs - n_entities - k_vars  # 分母自由度
        
        f_stat = ((rss_pooled - rss_fe) / df1) / (rss_fe / df2)
        p_value = 1 - f_dist.cdf(f_stat, df1, df2)
        
        # 4. 判断结果
        if p_value < 0.01:
            conclusion = "强烈拒绝原假设，应使用固定效应模型"
            stars = "***"
        elif p_value < 0.05:
            conclusion = "拒绝原假设，应使用固定效应模型"
            stars = "**"
        elif p_value < 0.1:
            conclusion = "弱拒绝原假设，倾向使用固定效应模型"
            stars = "*"
        else:
            conclusion = "不能拒绝原假设，可使用混合OLS模型"
            stars = ""
        
        return {
            'test_name': 'F Test (Fixed Effects vs Pooled OLS)',
            'null_hypothesis': '所有个体效应为0（混合OLS模型合适）',
            'alternative_hypothesis': '至少存在一个个体效应不为0（固定效应模型合适）',
            'f_statistic': round(f_stat, decimals),
            'df1': df1,
            'df2': df2,
            'p_value': round(p_value, decimals),
            'significance': stars,
            'conclusion': conclusion,
            'rss_pooled': round(rss_pooled, decimals),
            'rss_fe': round(rss_fe, decimals),
            'n_entities': n_entities,
            'n_obs': n_obs
        }
    
    @staticmethod
    def hausman_test(
        df: pd.DataFrame,
        y_var: str,
        x_vars: List[str],
        entity_col: str,
        time_col: str,
        decimals: int = 4,
        sigmamore: bool = False
    ) -> Dict[str, Any]:
        """
        Hausman检验：固定效应模型 vs 随机效应模型
        
        参数:
            df: 数据框
            y_var: 因变量名
            x_vars: 自变量列表
            entity_col: 个体标识列
            time_col: 时间标识列
            decimals: 小数位数
            sigmamore: 是否使用sigmamore选项（基于随机效应统一方差估计）
        
        返回:
            包含检验结果的字典
        """
        # 准备数据
        cols = [y_var] + x_vars + [entity_col, time_col]
        df_clean = df[cols].dropna()
        df_clean = drop_singletons_func(df_clean, entity_col)
        
        df_panel = df_clean.set_index([entity_col, time_col])
        y = df_panel[y_var]
        x = df_panel[x_vars]
        
        # 1. 估计固定效应模型（添加常数项）
        # 注意：Stata的hausman检验使用constant选项时会包含常数项
        x_with_const_fe = add_constant(x)
        fe_model = PanelOLS(y, x_with_const_fe, entity_effects=True, drop_absorbed=True)
        fe_result = fe_model.fit(cov_type='unadjusted')
        
        # 2. 估计随机效应模型（添加常数项）
        x_with_const = add_constant(x)
        re_model = RandomEffects(y, x_with_const)
        re_result = re_model.fit(cov_type='unadjusted')
        
        # 提取系数
        beta_fe = fe_result.params
        beta_re = re_result.params
        
        # 确保两个模型的变量顺序一致
        common_vars = [v for v in beta_fe.index if v in beta_re.index]
        beta_fe = beta_fe[common_vars]
        beta_re = beta_re[common_vars]
        
        # 3. 应用sigmamore选项（如果启用）
        if sigmamore:
            # 根据Stata官方hausman.ado源代码（第157-169行）：
            # if "`sigmamore'" != "" {
            #     matrix `V1' = ((`s2_2'/`s2_1')^2) * `V1'
            # }
            # 其中：
            # - V1 是固定效应模型的协方差矩阵
            # - s2_1 是FE模型的sigma_e
            # - s2_2 是RE模型的rmse
            
            # 计算FE模型的sigma_e
            s2_fe = np.sqrt(fe_result.resid_ss / fe_result.df_resid)
            
            # 计算RE模型的rmse（使用Pooled OLS，因为sigma_u可能为0）
            pooled_model = PooledOLS(y, x_with_const)
            pooled_result = pooled_model.fit(cov_type='unadjusted')
            s2_re = np.sqrt(pooled_result.resid_ss / pooled_result.df_resid)
            
            # 计算缩放因子
            scaling_factor = (s2_re / s2_fe) ** 2
            
            # 应用缩放到FE的协方差矩阵
            cov_fe = scaling_factor * fe_result.cov.loc[common_vars, common_vars]
            
            # RE使用pooled结果的协方差矩阵
            cov_re = pooled_result.cov.loc[common_vars, common_vars]
        else:
            # 不使用sigmamore，直接使用原始协方差矩阵
            cov_fe = fe_result.cov.loc[common_vars, common_vars]
            cov_re = re_result.cov.loc[common_vars, common_vars]
        
        # 3. 计算Hausman统计量
        # H = (beta_fe - beta_re)' * [Var(beta_fe) - Var(beta_re)]^(-1) * (beta_fe - beta_re)
        beta_diff = beta_fe - beta_re
        cov_diff = cov_fe - cov_re
        
        try:
            # 计算协方差矩阵差的逆（使用Moore-Penrose伪逆处理奇异矩阵）
            cov_diff_inv = np.linalg.pinv(cov_diff)
            
            # 计算Hausman统计量
            h_stat = float(beta_diff.T @ cov_diff_inv @ beta_diff)
            
            # 如果统计量为负数，说明协方差矩阵差不是正定的
            if h_stat < 0:
                # 计算标准误差异的标准误（用于显示）
                std_err_diff = {}
                for var in beta_diff.index:
                    var_diff = cov_diff.loc[var, var]
                    if var_diff > 0:
                        std_err_diff[var] = round(np.sqrt(var_diff), decimals)
                    else:
                        std_err_diff[var] = 'negative'
                
                return {
                    'test_name': 'Hausman Test (Fixed Effects vs Random Effects)',
                    'warning': '协方差矩阵差不是正定的（V_b-V_B is not positive definite）',
                    'note': 'Stata也会显示此警告。这通常表明固定效应和随机效应模型的估计非常接近。',
                    'chi2_statistic': round(abs(h_stat), decimals),
                    'df': len(beta_diff),
                    'p_value': 'N/A',
                    'significance': '',
                    'conclusion': '由于协方差矩阵差不是正定的，无法进行标准的Hausman检验。建议：1) 两种模型估计结果非常接近，可能都适用；2) 检查数据质量和模型设定；3) 考虑使用其他模型选择方法。',
                    'fe_coeffs': {k: round(v, decimals) for k, v in beta_fe.items()},
                    're_coeffs': {k: round(v, decimals) for k, v in beta_re.items()},
                    'coeff_diff': {k: round(beta_diff[k], decimals) for k in beta_diff.index},
                    'fe_std_err': {k: round(np.sqrt(cov_fe.loc[k, k]), decimals) for k in beta_fe.index},
                    're_std_err': {k: round(np.sqrt(cov_re.loc[k, k]), decimals) for k in beta_re.index},
                    'std_err_diff': std_err_diff
                }
            
            # 自由度等于参数个数
            df = len(beta_fe)
            
            # 计算p值（卡方分布）
            p_value = 1 - chi2.cdf(h_stat, df)
            
            # 判断结果
            if p_value < 0.01:
                conclusion = "强烈拒绝原假设，应使用固定效应模型"
                stars = "***"
            elif p_value < 0.05:
                conclusion = "拒绝原假设，应使用固定效应模型"
                stars = "**"
            elif p_value < 0.1:
                conclusion = "弱拒绝原假设，倾向使用固定效应模型"
                stars = "*"
            else:
                conclusion = "不能拒绝原假设，可使用随机效应模型"
                stars = ""
            
            # 计算标准误差异的标准误（用于显示）
            std_err_diff = {}
            for var in beta_diff.index:
                var_diff = cov_diff.loc[var, var]
                if var_diff > 0:
                    std_err_diff[var] = round(np.sqrt(var_diff), decimals)
                else:
                    std_err_diff[var] = 'negative'
            
            return {
                'test_name': 'Hausman Test (Fixed Effects vs Random Effects)',
                'null_hypothesis': '随机效应模型合适（个体效应与解释变量不相关）',
                'alternative_hypothesis': '固定效应模型合适（个体效应与解释变量相关）',
                'chi2_statistic': round(h_stat, decimals),
                'df': df,
                'p_value': round(p_value, decimals),
                'significance': stars,
                'conclusion': conclusion,
                'fe_coeffs': {k: round(v, decimals) for k, v in beta_fe.items()},
                're_coeffs': {k: round(v, decimals) for k, v in beta_re.items()},
                'coeff_diff': {k: round(beta_diff[k], decimals) for k in beta_diff.index},
                'fe_std_err': {k: round(np.sqrt(cov_fe.loc[k, k]), decimals) for k in beta_fe.index},
                're_std_err': {k: round(np.sqrt(cov_re.loc[k, k]), decimals) for k in beta_re.index},
                'std_err_diff': std_err_diff
            }
        
        except Exception as e:
            # 其他错误
            return {
                'test_name': 'Hausman Test (Fixed Effects vs Random Effects)',
                'error': f'计算Hausman统计量时出错: {str(e)}',
                'suggestion': '可能是因为模型设定问题或数据共线性，建议检查数据质量',
                'fe_coeffs': {k: round(v, decimals) for k, v in beta_fe.items()},
                're_coeffs': {k: round(v, decimals) for k, v in beta_re.items()}
            }
