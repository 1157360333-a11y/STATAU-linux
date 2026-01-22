"""
================================================================================
STATAU 数据分析蓝图 (blueprints/analysis.py)
================================================================================
说明：
    - 本蓝图负责所有数据分析相关的 API 接口
    - 包括：文件上传、数据分析、数据预览、清空表格
    - 这是应用的核心功能模块

包含路由：
    - POST /upload        文件上传
    - POST /analyze       执行分析
    - GET  /preview       数据预览
    - POST /clear_table   清空结果表格

设计理念：
    - 分析逻辑与认证逻辑完全分离
    - 文件操作委托给 FileService
    - 统计计算委托给 core/models.py
    - 表格生成委托给 core/table_generator.py

注意：
    - RESULT_CACHE 是本地版的结果缓存（基于 IP 地址）
    - 服务器版应使用 session 存储（已注释保留）
================================================================================
"""

from flask import Blueprint, request, jsonify, current_app, session

# 导入服务层
from services.file_service import FileService
from flask_session import Session

# 导入核心分析模块
from core.models import StataModel,ModelTests
from core.table_generator import generate_merged_html

# ------------------------------------------------------------------------
# 创建蓝图实例
# ------------------------------------------------------------------------
analysis_bp = Blueprint(
    'analysis',        # 蓝图名称
    __name__
)

# ------------------------------------------------------------------------
# 结果缓存（本地版）
# ------------------------------------------------------------------------
# 说明：
#   - 使用客户端 IP 作为 key 存储分析结果
#   - 这是本地开发版的实现方式
#   - 服务器部署时应改用 session 存储（见注释代码）
# ------------------------------------------------------------------------
# RESULT_CACHE = {}


# ============================================================================
# 辅助函数
# ============================================================================

def get_file_service() -> FileService:
    """
    获取文件服务实例
    
    返回:
        FileService 实例，使用应用配置的上传目录
    
    说明:
        每次请求时创建新实例，确保使用最新的配置
    """
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return FileService(upload_folder)


def get_client_id() -> str:
    """
    获取客户端标识
    
    返回:
        客户端 IP 地址作为标识
    
    说明:
        本地版使用 IP 地址区分不同用户
        服务器版应使用 session ID
    """
    return request.remote_addr


# ============================================================================
# 文件上传接口
# ============================================================================

@analysis_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    文件上传接口
    
    URL: POST /upload
    
    请求:
        multipart/form-data 格式，包含 'file' 字段
    
    返回:
        成功: {"message": "Success", "filename": "xxx", "columns": [...]}
        失败: {"error": "错误信息"}, HTTP 状态码 400/500
    
    说明:
        - 支持 CSV、Excel、Stata DTA 格式
        - 上传新文件时会清空之前的分析结果缓存
    """
    # ------------------------------------------------------------------------
    # 1. 检查文件是否存在
    # ------------------------------------------------------------------------
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # ------------------------------------------------------------------------
    # 2. 保存文件
    # ------------------------------------------------------------------------
    file_service = get_file_service()
    
    try:
        filepath = file_service.save_file(file, file.filename)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # ------------------------------------------------------------------------
    # 3. 读取列名
    # ------------------------------------------------------------------------
    try:
        df = file_service.read_datafile(filepath)
        columns = df.columns.tolist()
    except Exception as e:
        return jsonify({'error': f'文件读取失败: {str(e)}'}), 500
    
    # ------------------------------------------------------------------------
    # 4. 清空之前的结果缓存
    # ------------------------------------------------------------------------
    # client_id = get_client_id()
    # RESULT_CACHE[client_id] = []
    
    # 服务器版（勿删）：
    session['analysis_results'] = []
    session.modified = True
    
    return jsonify({
        'message': 'Success',
        'filename': file.filename,
        'columns': columns
    })


# ============================================================================
# 数据分析接口
# ============================================================================

@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    执行数据分析接口
    
    URL: POST /analyze
    
    请求体 (JSON):
        {
            "filename": "数据文件名",
            "method": "分析方法 (ols/fe/logit/probit/desc/corr/vif)",
            "action": "操作类型 (new/append)",
            "y_var": "因变量",
            "x_vars": ["自变量列表"],
            "manual_controls": "手动输入的控制变量",
            "decimals": 小数位数,
            "show_se": 是否显示标准误,
            "table_title": "表格标题",
            "panel_entity": "面板个体变量",
            "panel_time": "面板时间变量",
            "fe_vars": ["固定效应变量列表"],
            "se_type": "标准误类型 (iid/robust/cluster)",
            "cluster_var": "聚类变量",
            "custom_rows": [{"label": "xxx", "value": "xxx"}],
            "export_options": ["导出选项列表"]
        }
    
    返回:
        成功: {"html_table": "HTML表格", "raw_output": "原始输出", "model_count": 数量}
        失败: {"error": "错误信息"}, HTTP 状态码 500
    """
    # ------------------------------------------------------------------------
    # 1. 解析请求参数
    # ------------------------------------------------------------------------
    data = request.json
    client_id = get_client_id()
    
    # 基础参数
    action = data.get('action', 'new')
    filename = data.get('filename')
    method = data.get('method', 'ols')
    
    # 变量参数
    y_var = data.get('y_var')
    x_vars = data.get('x_vars', [])
    manual_controls = data.get('manual_controls', '')
    
    # 格式参数
    decimals = int(data.get('decimals', 3))
    show_se = data.get('show_se', True)
    user_title = data.get('table_title', 'Regression Results')
    
    # 面板数据参数
    panel_entity = data.get('panel_entity')
    panel_time = data.get('panel_time')
    fe_vars = data.get('fe_vars', [])
    
    # 标准误参数
    se_options = {
        'type': data.get('se_type', 'iid'),
        'cluster_var': data.get('cluster_var')
    }
    
    # 自定义行
    custom_rows = data.get('custom_rows', [])
    
    # 导出选项
    export_options = data.get('export_options', [])
    
    # ------------------------------------------------------------------------
    # 2. 读取数据文件
    # ------------------------------------------------------------------------
    file_service = get_file_service()
    
    try:
        df = file_service.read_datafile_by_name(filename)
    except Exception as e:
        return jsonify({'error': f'文件读取失败: {str(e)}'}), 500
    
    # ------------------------------------------------------------------------
    # 3. 处理手动输入的控制变量
    # ------------------------------------------------------------------------
    if manual_controls:
        extras = [c.strip() for c in manual_controls.replace(',', ' ').split() if c.strip()]
        valid_extras = [c for c in extras if c in df.columns]
        x_vars.extend(valid_extras)
    
    # ------------------------------------------------------------------------
    # 4. 执行分析
    # ------------------------------------------------------------------------
    try:
        model_runner = StataModel(
            df, y_var, x_vars, method,
            panel_ids={'entity': panel_entity, 'time': panel_time},
            fe_vars=fe_vars,
            se_options=se_options,
            desc_options=export_options
        )
        result_obj = model_runner.fit(decimals=decimals, table_title=user_title)
        
        # --------------------------------------------------------------------
        # 4.1 特殊分析分支 (Desc, Corr, VIF)
        # --------------------------------------------------------------------
        if model_runner.custom_html:
            return jsonify({
                'html_table': model_runner.custom_html,
                'raw_output': 'Descriptive/Correlation/VIF Analysis Completed.',
                'model_count': 0
            })
        
        # --------------------------------------------------------------------
        # 4.2 回归分析分支
        # --------------------------------------------------------------------
        if result_obj is None:
            return jsonify({'error': '模型计算失败，未生成结果。'}), 500
        
        # 获取系数和统计量
        coeffs, stats = model_runner.get_coeffs_dataframe(decimals=decimals, show_se=show_se)
        
        # 构建模型数据
        model_data = {
            'coeffs': coeffs,
            'stats': stats,
            'y_name': y_var,
            'method': method,
            'se_type': se_options['type'],
            'custom_rows': custom_rows
        }
        
        # --------------------------------------------------------------------
        # 4.3 更新结果缓存
        # --------------------------------------------------------------------
        # 本地版
        # if action == 'new':
        #     RESULT_CACHE[client_id] = [model_data]
        # elif action == 'append':
        #     if client_id not in RESULT_CACHE:
        #         RESULT_CACHE[client_id] = []
        #     RESULT_CACHE[client_id].append(model_data)
        
        # current_models = RESULT_CACHE[client_id]
        
        # 服务器版（勿删）：
        if 'analysis_results' not in session:
            session['analysis_results'] = []
        if action == 'new':
            session['analysis_results'] = [model_data]
        elif action == 'append':
            current_list = session['analysis_results']
            current_list.append(model_data)
            session['analysis_results'] = current_list
        session.modified = True
        current_models = session['analysis_results']
        
        # --------------------------------------------------------------------
        # 4.4 生成 HTML 表格
        # --------------------------------------------------------------------
        html_table = generate_merged_html(
            current_models,
            title=user_title,
            decimals=decimals,
            show_se=show_se,
            export_options=export_options
        )
        
        # --------------------------------------------------------------------
        # 4.5 生成原始输出
        # --------------------------------------------------------------------
        if method == 'fe':
            # linearmodels 库：summary 是属性
            raw_output = str(result_obj.summary)
        else:
            # statsmodels 库：summary() 是方法
            raw_output = result_obj.summary().as_text()
        
        return jsonify({
            'html_table': html_table,
            'raw_output': raw_output,
            'model_count': len(current_models)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 清空表格接口
# ============================================================================

@analysis_bp.route('/clear_table', methods=['POST'])
def clear_table():
    """
    清空结果表格接口
    
    URL: POST /clear_table
    
    返回:
        {"status": "cleared"}
    
    说明:
        清空当前用户的所有分析结果缓存
    """
    # client_id = get_client_id()
    # RESULT_CACHE[client_id] = []
    
    # 服务器版（勿删）：
    session['analysis_results'] = []
    session.modified = True
    
    return jsonify({'status': 'cleared'})


# ============================================================================
# 数据预览接口
# ============================================================================

@analysis_bp.route('/preview')
def preview():
    """
    数据预览接口
    
    URL: GET /preview?filename=xxx
    
    参数:
        filename: 要预览的文件名
    
    返回:
        成功: {"columns": [...], "dtypes": {...}, "preview": [...]}
        失败: {"error": "错误信息"}, HTTP 状态码 400/404/500
    
    说明:
        返回数据文件的前 10 行预览
    """
    # ------------------------------------------------------------------------
    # 1. 参数验证
    # ------------------------------------------------------------------------
    filename = request.args.get('filename')
    
    if not filename:
        return jsonify({'error': 'Missing filename'}), 400
    
    # ------------------------------------------------------------------------
    # 2. 检查文件是否存在
    # ------------------------------------------------------------------------
    file_service = get_file_service()
    
    if not file_service.file_exists(filename):
        return jsonify({'error': 'File not found'}), 404
    
    # ------------------------------------------------------------------------
    # 3. 获取预览数据
    # ------------------------------------------------------------------------
    try:
        preview_data = file_service.get_preview_data(filename, nrows=10)
        return jsonify(preview_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# F检验接口（固定效应 vs 混合OLS）
# ============================================================================

@analysis_bp.route('/f_test', methods=['POST'])
def f_test():
    """
    F检验接口：固定效应模型 vs 混合OLS模型
    
    URL: POST /f_test
    
    请求体 (JSON):
        {
            "filename": "数据文件名",
            "y_var": "因变量",
            "x_vars": ["自变量列表"],
            "panel_entity": "面板个体变量",
            "panel_time": "面板时间变量",
            "decimals": 小数位数
        }
    
    返回:
        成功: {"result": {...检验结果...}}
        失败: {"error": "错误信息"}, HTTP 状态码 500
    
    说明:
        用于检验是否应该使用固定效应模型而非混合OLS模型
    """
    # ------------------------------------------------------------------------
    # 1. 解析请求参数
    # ------------------------------------------------------------------------
    data = request.json
    filename = data.get('filename')
    y_var = data.get('y_var')
    x_vars = data.get('x_vars', [])
    panel_entity = data.get('panel_entity')
    panel_time = data.get('panel_time')
    decimals = int(data.get('decimals', 4))
    
    # ------------------------------------------------------------------------
    # 2. 参数验证
    # ------------------------------------------------------------------------
    if not all([filename, y_var, x_vars, panel_entity, panel_time]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    # ------------------------------------------------------------------------
    # 3. 读取数据文件
    # ------------------------------------------------------------------------
    file_service = get_file_service()
    
    try:
        df = file_service.read_datafile_by_name(filename)
    except Exception as e:
        return jsonify({'error': f'文件读取失败: {str(e)}'}), 500
    
    # ------------------------------------------------------------------------
    # 4. 执行F检验
    # ------------------------------------------------------------------------
    try:
        result = ModelTests.f_test_fe_vs_pooled(
            df=df,
            y_var=y_var,
            x_vars=x_vars,
            entity_col=panel_entity,
            time_col=panel_time,
            decimals=decimals
        )
        
        return jsonify({'result': result})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Hausman检验接口（固定效应 vs 随机效应）
# ============================================================================

@analysis_bp.route('/hausman_test', methods=['POST'])
def hausman_test():
    """
    Hausman检验接口：固定效应模型 vs 随机效应模型
    
    URL: POST /hausman_test
    
    请求体 (JSON):
        {
            "filename": "数据文件名",
            "y_var": "因变量",
            "x_vars": ["自变量列表"],
            "panel_entity": "面板个体变量",
            "panel_time": "面板时间变量",
            "decimals": 小数位数,
            "sigmamore": 是否使用sigmamore选项（可选，默认false）
        }
    
    返回:
        成功: {"result": {...检验结果...}}
        失败: {"error": "错误信息"}, HTTP 状态码 500
    
    说明:
        用于检验是否应该使用固定效应模型而非随机效应模型
        sigmamore选项：使用基于随机效应的统一方差估计，可以解决协方差矩阵不正定的问题
    """
    # ------------------------------------------------------------------------
    # 1. 解析请求参数
    # ------------------------------------------------------------------------
    data = request.json
    filename = data.get('filename')
    y_var = data.get('y_var')
    x_vars = data.get('x_vars', [])
    panel_entity = data.get('panel_entity')
    panel_time = data.get('panel_time')
    decimals = int(data.get('decimals', 4))
    sigmamore = data.get('sigmamore', False)
    
    # ------------------------------------------------------------------------
    # 2. 参数验证
    # ------------------------------------------------------------------------
    if not all([filename, y_var, x_vars, panel_entity, panel_time]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    # ------------------------------------------------------------------------
    # 3. 读取数据文件
    # ------------------------------------------------------------------------
    file_service = get_file_service()
    
    try:
        df = file_service.read_datafile_by_name(filename)
    except Exception as e:
        return jsonify({'error': f'文件读取失败: {str(e)}'}), 500
    
    # ------------------------------------------------------------------------
    # 4. 执行Hausman检验
    # ------------------------------------------------------------------------
    try:
        result = ModelTests.hausman_test(
            df=df,
            y_var=y_var,
            x_vars=x_vars,
            entity_col=panel_entity,
            time_col=panel_time,
            decimals=decimals,
            sigmamore=sigmamore
        )
        
        return jsonify({'result': result})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500        
