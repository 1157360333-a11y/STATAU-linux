"""
================================================================================
STATAU 表格生成模块 (core/table_generator.py)
================================================================================
说明：
    - 本模块负责生成学术标准的 HTML 回归结果表格
    - 支持多列结果合并、显著性星号、自定义行
    - 输出格式参考 Stata 的 esttab 命令

设计理念：
    - 与统计模型完全解耦，只接收格式化后的数据
    - 专注于表格渲染，不涉及统计计算
    - 支持灵活的导出选项配置

使用方式：
    from core.table_generator import generate_merged_html
    
    html = generate_merged_html(
        models_data,
        title="Regression Results",
        decimals=3,
        show_se=True,
        export_options=['nobs', 'r2', 'adj_r2']
    )
================================================================================
"""

import pandas as pd
from typing import List, Dict, Any, Optional


def generate_merged_html(
    models_data: List[Dict[str, Any]],
    title: str = "Regression Analysis",
    decimals: int = 3,
    show_se: bool = True,
    export_options: Optional[List[str]] = None
) -> str:
    """
    生成合并的回归结果 HTML 表格
    
    参数:
        models_data: 模型数据列表，每个元素包含:
            - coeffs: 系数字典 {变量名: (系数字符串, 标准误字符串)}
            - stats: 统计量字典 {统计量名: 值}
            - y_name: 因变量名
            - method: 回归方法
            - se_type: 标准误类型
            - custom_rows: 自定义行列表 [{'label': ..., 'value': ...}]
        title: 表格标题
        decimals: 小数位数
        show_se: 是否显示标准误（False 则显示 t/z 值）
        export_options: 导出的统计量选项列表
    
    返回:
        HTML 字符串
    
    说明:
        生成的表格遵循学术论文标准格式：
        - 顶部单线
        - 系数带显著性星号
        - 标准误/t值在括号内
        - 底部双线
        - 注释说明显著性水平
    """
    # ------------------------------------------------------------------------
    # 空数据检查
    # ------------------------------------------------------------------------
    if not models_data:
        return ""
    
    # 默认导出选项
    if export_options is None:
        export_options = ['nobs', 'r2', 'adj_r2', 'f_stat']
    
    # ------------------------------------------------------------------------
    # 1. 收集所有变量名
    # ------------------------------------------------------------------------
    all_vars = []
    has_constant = False
    
    for m in models_data:
        for var in m['coeffs'].keys():
            if var == 'Constant':
                has_constant = True
                continue
            if var not in all_vars:
                all_vars.append(var)
    
    # 常数项放在最后
    if has_constant:
        all_vars.append('Constant')
    
    # ------------------------------------------------------------------------
    # 2. 生成表头
    # ------------------------------------------------------------------------
    html = f"""
    <div class="table-editable-container">
        <input type="text" class="table-title-input" value="{title}" />
        <table class="academic-table" style="line-height: 1.1;">
            <thead>
                <tr>
                    <th style="border-bottom: 1px solid black; text-align: left;">Variables</th>
    """
    
    # 每列的标题：(列号) + 因变量名 + 方法
    for i, m in enumerate(models_data):
        model_type = m.get('method', 'OLS').upper()
        col_name = (
            f"({i+1})<br>{m['y_name']}<br>"
            f"<span style='font-size:0.8em; font-weight:normal'>({model_type})</span>"
        )
        html += f"<th style='border-bottom: 1px solid black;'>{col_name}</th>"
    
    html += "</tr></thead><tbody>"
    
    # ------------------------------------------------------------------------
    # 3. 填充系数行
    # ------------------------------------------------------------------------
    for var in all_vars:
        # 系数行
        html += f"<tr><td style='text-align:left;'>{var}</td>"
        for m in models_data:
            val = m['coeffs'].get(var, ("", ""))[0]
            html += f"<td>{val}</td>"
        html += "</tr>"
        
        # 标准误/t值行
        html += "<tr><td></td>"
        for m in models_data:
            val = m['coeffs'].get(var, ("", ""))[1]
            html += f"<td style='color: #666; font-size: 0.85em; padding-bottom: 4px;'>{val}</td>"
        html += "</tr>"
    
    html += "</tbody><tfoot>"
    
    # ------------------------------------------------------------------------
    # 4. 填充统计量行
    # ------------------------------------------------------------------------
    stats_map = {
        'nobs': ('Observations', 'N'),
        'r2': ('R-squared', 'R2'),
        'adj_r2': ('Adj. R-squared', 'Adj-R2'),
        'f_stat': ('F-statistic', 'F'),
        'pseudo_r2': ('Pseudo R2', 'Pseudo-R2'),
        'aic': ('AIC', 'AIC'),
        'bic': ('BIC', 'BIC'),
        'll': ('Log Likelihood', 'LL')
    }
    
    # 确保 nobs 在最前面
    if 'nobs' in export_options:
        export_options.remove('nobs')
        export_options.insert(0, 'nobs')
    
    first_stat = True
    for opt in export_options:
        if opt not in stats_map:
            continue
        
        label, data_key = stats_map[opt]
        row_values = []
        has_value = False
        
        for m in models_data:
            val = m['stats'].get(data_key, "")
            if val != "":
                has_value = True
                if isinstance(val, (int, float)):
                    if data_key == 'N':
                        val = int(val)
                    else:
                        val = f"{val:.{decimals}f}"
            row_values.append(val)
        
        # 如果所有模型都没有这个统计量，跳过
        if not has_value:
            continue
        
        # 第一个统计量行添加顶部边框
        border_style = "border-top: 1px solid black;" if first_stat else ""
        html += f"<tr><td style='text-align:left; {border_style}'>{label}</td>"
        for val in row_values:
            html += f"<td style='{border_style}'>{val}</td>"
        html += "</tr>"
        first_stat = False
    
    # ------------------------------------------------------------------------
    # 5. 填充自定义行（如 Fixed Effects 标记）
    # ------------------------------------------------------------------------
    # 收集所有模型中出现过的自定义行 Label
    all_custom_labels = []
    for m in models_data:
        for row in m.get('custom_rows', []):
            if row['label'] not in all_custom_labels:
                all_custom_labels.append(row['label'])
    
    # 渲染每一行自定义内容
    for label in all_custom_labels:
        html += f"<tr><td style='text-align:left;'>{label}</td>"
        for m in models_data:
            # 查找当前模型是否有这个 label 的值
            val = "No"  # 默认为 No
            for r in m.get('custom_rows', []):
                if r['label'] == label:
                    val = r['value']
                    break
            html += f"<td>{val}</td>"
        html += "</tr>"
    
    # ------------------------------------------------------------------------
    # 6. 生成底部注释
    # ------------------------------------------------------------------------
    note_lines = []
    
    if show_se:
        note_lines.append("Standard errors in parentheses")
    else:
        note_lines.append("t-statistics in parentheses")
    
    # 检查是否有聚类标准误
    has_cluster = any(m.get('se_type') == 'cluster' for m in models_data)
    if has_cluster:
        note_lines.append("Standard errors are clustered.")
    
    note_text = "<br>".join(note_lines)
    
    html += f"""
            <tr>
                <td colspan="100%" style="border-bottom: 3px double black; border-top: 1px solid black; font-size: 0.8em; text-align: left; padding-top: 5px;">
                    {note_text}<br>*** p<0.01, ** p<0.05, * p<0.1
                </td>
            </tr>
        </tfoot>
    </table>
    </div>
    """
    
    return html