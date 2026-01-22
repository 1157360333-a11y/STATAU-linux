"""
Gunicorn 配置文件
用于生产环境的日志和性能配置
"""
import os
import multiprocessing

# 服务器绑定
bind = "0.0.0.0:8000"

# Worker 进程数（推荐：CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# Worker 类型（sync 适合 CPU 密集型任务，如数据分析）
worker_class = "sync"

# 超时时间（秒）- 数据分析可能需要较长时间
timeout = 120

# 保持连接时间（秒）
keepalive = 5

# 日志配置
# 访问日志文件路径
accesslog = "logs/gunicorn_access.log"

# 错误日志文件路径
errorlog = "logs/gunicorn_error.log"

# 日志级别：debug, info, warning, error, critical
loglevel = "info"

# 访问日志格式
# %(h)s - 客户端IP
# %(l)s - 远程日志名
# %(u)s - 用户名
# %(t)s - 请求时间
# %(r)s - 请求行（方法 路径 协议）
# %(s)s - 状态码
# %(b)s - 响应大小
# %(f)s - Referer
# %(a)s - User-Agent
# %(D)s - 请求处理时间（微秒）
# %(L)s - 请求处理时间（秒，小数）
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "statau"

# Daemon 模式（后台运行）- 使用 systemd 时设为 False
daemon = False

# PID 文件
pidfile = "logs/gunicorn.pid"

# 临时文件目录
worker_tmp_dir = "/dev/shm"

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 优雅重启超时
graceful_timeout = 30

# 预加载应用（可以减少内存占用，但调试时建议关闭）
preload_app = False

# 捕获输出到日志
capture_output = True

# 启用访问日志
accesslog = "logs/gunicorn_access.log"

# 错误日志
errorlog = "logs/gunicorn_error.log"

# 日志文件权限
umask = 0o007

# 回调函数：服务器启动时
def on_starting(server):
    """服务器启动时的回调"""
    print("=" * 60)
    print("STATAU Gunicorn 服务器正在启动...")
    print(f"绑定地址: {bind}")
    print(f"Worker 数量: {workers}")
    print(f"超时时间: {timeout}秒")
    print(f"访问日志: {accesslog}")
    print(f"错误日志: {errorlog}")
    print(f"日志级别: {loglevel}")
    print("=" * 60)

# 回调函数：Worker 启动时
def on_reload(server):
    """配置重载时的回调"""
    print("配置已重载")

# 回调函数：Worker 退出时
def worker_exit(server, worker):
    """Worker 退出时的回调"""
    print(f"Worker {worker.pid} 已退出")
