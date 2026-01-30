# Gunicorn 日志配置指南

## 📋 概述

本指南帮助你配置 Gunicorn 的日志功能，让服务器的访问日志和错误日志持久化保存到文件中，方便随时查看服务器状态和排查问题。

---

## 🎯 解决的问题

- ✅ 服务器报错无法及时看到
- ✅ 不用每次都重启 gunicorn 加 `--log-level debug` 来查看报错
- ✅ 日志持久化保存，可以追溯历史问题
- ✅ 访问日志和错误日志分离，便于分析

---

## 📁 文件说明

项目中已创建 [`gunicorn_config.py`](gunicorn_config.py:1) 配置文件，包含以下配置：

### 核心配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `bind` | 服务器绑定地址 | `0.0.0.0:8000` |
| `workers` | Worker 进程数 | CPU核心数 * 2 + 1 |
| `timeout` | 请求超时时间 | 120秒 |
| `accesslog` | 访问日志路径 | `logs/gunicorn_access.log` |
| `errorlog` | 错误日志路径 | `logs/gunicorn_error.log` |
| `loglevel` | 日志级别 | `info` |

### 日志级别说明

| 级别 | 说明 | 适用场景 |
|------|------|----------|
| `debug` | 最详细的日志 | 开发调试 |
| `info` | 一般信息 | 生产环境（推荐） |
| `warning` | 警告信息 | 只关注警告和错误 |
| `error` | 错误信息 | 只记录错误 |
| `critical` | 严重错误 | 只记录严重问题 |

---

## 🚀 部署步骤

### 步骤 1：在服务器上创建日志目录

```bash
# 进入项目目录
cd /var/www/STATAU

# 创建日志目录
mkdir -p logs

# 设置权限（确保 gunicorn 可以写入）
chmod 755 logs
```

### 步骤 2：上传配置文件

将 [`gunicorn_config.py`](gunicorn_config.py:1) 上传到服务器的项目根目录：

```bash
# 方式一：使用 Git（推荐）
git pull

# 方式二：使用 SFTP/SCP
# 使用 FileZilla 或其他工具上传 gunicorn_config.py 到 /var/www/STATAU/
```

### 步骤 3：更新 Systemd 服务配置

编辑服务文件：

```bash
sudo nano /etc/systemd/system/statau.service
```

修改 `ExecStart` 行，使用配置文件启动：

```ini
[Unit]
Description=Gunicorn instance to serve STATAU
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/STATAU
Environment="PATH=/var/www/STATAU/venv/bin"
Environment="FLASK_ENV=production"

# 使用配置文件启动（新方式）
ExecStart=/var/www/STATAU/venv/bin/gunicorn -c gunicorn_config.py "app:create_app()"

# 或者使用命令行参数（旧方式，二选一）
# ExecStart=/var/www/STATAU/venv/bin/gunicorn --workers 4 --timeout 120 --bind 0.0.0.0:8000 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info "app:create_app()"

[Install]
WantedBy=multi-user.target
```

### 步骤 4：重新加载并重启服务

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 重启服务
sudo systemctl restart statau

# 查看服务状态
sudo systemctl status statau
```

---

## 📊 查看日志

### 实时查看错误日志

```bash
# 实时查看最新的错误日志（推荐）
tail -f /var/www/STATAU/logs/gunicorn_error.log

# 查看最后 50 行
tail -n 50 /var/www/STATAU/logs/gunicorn_error.log

# 查看完整日志
cat /var/www/STATAU/logs/gunicorn_error.log
```

### 实时查看访问日志

```bash
# 实时查看访问日志
tail -f /var/www/STATAU/logs/gunicorn_access.log

# 查看最后 100 行
tail -n 100 /var/www/STATAU/logs/gunicorn_access.log
```

### 使用 systemd 查看日志

```bash
# 查看服务日志（包含启动信息）
sudo journalctl -u statau

# 实时查看服务日志
sudo journalctl -u statau -f

# 查看最近 100 行
sudo journalctl -u statau -n 100

# 查看今天的日志
sudo journalctl -u statau --since today
```

### 搜索特定错误

```bash
# 搜索包含 "error" 的日志
grep -i "error" /var/www/STATAU/logs/gunicorn_error.log

# 搜索包含 "traceback" 的日志（Python 错误堆栈）
grep -i "traceback" /var/www/STATAU/logs/gunicorn_error.log

# 搜索 500 错误
grep "500" /var/www/STATAU/logs/gunicorn_access.log
```

---

## 🔧 日志格式说明

### 访问日志格式

```
客户端IP - - [时间] "请求方法 路径 协议" 状态码 响应大小 "Referer" "User-Agent" 处理时间(微秒)
```

示例：
```
192.168.1.100 - - [21/Jan/2026:13:45:23 +0800] "POST /analyze HTTP/1.1" 200 1234 "http://example.com/analysis" "Mozilla/5.0..." 125000
```

### 错误日志格式

```
[时间] [日志级别] [进程ID] 错误信息
```

示例：
```
[2026-01-21 13:45:23 +0800] [ERROR] [12345] Exception on /analyze [POST]
Traceback (most recent call last):
  File "/var/www/STATAU/venv/lib/python3.8/site-packages/flask/app.py", line 2525, in wsgi_app
    response = self.full_dispatch_request()
...
```

---

## 🛠️ 常见问题

### 1. 日志文件不存在或无法写入

**问题**：启动服务后没有生成日志文件

**解决方案**：
```bash
# 检查日志目录是否存在
ls -la /var/www/STATAU/logs

# 如果不存在，创建目录
mkdir -p /var/www/STATAU/logs

# 设置权限
chmod 755 /var/www/STATAU/logs

# 重启服务
sudo systemctl restart statau
```

### 2. 日志文件过大

**问题**：日志文件占用太多磁盘空间

**解决方案**：配置日志轮转（logrotate）

创建配置文件：
```bash
sudo nano /etc/logrotate.d/statau
```

添加以下内容：
```
/var/www/STATAU/logs/*.log {
    daily                   # 每天轮转
    rotate 7                # 保留 7 天
    compress                # 压缩旧日志
    delaycompress           # 延迟压缩（保留最近一天的未压缩）
    missingok               # 文件不存在不报错
    notifempty              # 空文件不轮转
    create 0644 root root   # 创建新文件的权限
    sharedscripts           # 所有日志轮转后只执行一次脚本
    postrotate
        systemctl reload statau > /dev/null 2>&1 || true
    endscript
}
```

测试配置：
```bash
sudo logrotate -d /etc/logrotate.d/statau
```

### 3. 看不到 Python 应用的 print 输出

**问题**：代码中的 `print()` 语句没有出现在日志中

**解决方案**：

在 [`gunicorn_config.py`](gunicorn_config.py:1) 中已配置 `capture_output = True`，这会捕获所有标准输出到错误日志。

如果还是看不到，可以在代码中使用 Python 的 logging 模块：

```python
import logging

# 在 app.py 中配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# 使用
logging.info("这是一条信息日志")
logging.error("这是一条错误日志")
```

### 4. 调试时需要更详细的日志

**临时方案**：修改日志级别为 debug

```bash
# 编辑配置文件
nano /var/www/STATAU/gunicorn_config.py

# 修改这一行：
loglevel = "debug"  # 改为 debug

# 重启服务
sudo systemctl restart statau

# 查看详细日志
tail -f /var/www/STATAU/logs/gunicorn_error.log
```

**注意**：调试完成后记得改回 `info`，否则日志会非常多。

---

## 📈 日志分析技巧

### 统计访问量

```bash
# 统计总访问次数
wc -l /var/www/STATAU/logs/gunicorn_access.log

# 统计今天的访问次数
grep "$(date +%d/%b/%Y)" /var/www/STATAU/logs/gunicorn_access.log | wc -l

# 统计各状态码数量
awk '{print $9}' /var/www/STATAU/logs/gunicorn_access.log | sort | uniq -c | sort -rn
```

### 查找慢请求

```bash
# 查找处理时间超过 5 秒（5000000 微秒）的请求
awk '$NF > 5000000' /var/www/STATAU/logs/gunicorn_access.log
```

### 查找最常访问的页面

```bash
# 统计访问最多的 URL
awk '{print $7}' /var/www/STATAU/logs/gunicorn_access.log | sort | uniq -c | sort -rn | head -10
```

---

## 🎨 推荐的日志查看工具

### 1. 命令行工具

- **tail**：实时查看日志
- **less**：分页查看日志（支持搜索）
- **grep**：搜索特定内容
- **awk**：日志分析

### 2. 图形化工具

- **GoAccess**：实时 Web 日志分析工具
  ```bash
  sudo apt install goaccess
  goaccess /var/www/STATAU/logs/gunicorn_access.log -o report.html --log-format=COMBINED
  ```

- **Logwatch**：自动生成日志摘要邮件
  ```bash
  sudo apt install logwatch
  ```

### 3. 在线日志管理平台

- **ELK Stack**（Elasticsearch + Logstash + Kibana）
- **Grafana Loki**
- **Graylog**

---

## 📝 快速参考

### 常用命令速查

```bash
# 查看实时错误日志
tail -f logs/gunicorn_error.log

# 查看实时访问日志
tail -f logs/gunicorn_access.log

# 查看服务状态
sudo systemctl status statau

# 重启服务
sudo systemctl restart statau

# 查看最近的错误
tail -n 50 logs/gunicorn_error.log | grep -i error

# 搜索特定时间的日志
grep "21/Jan/2026:13:" logs/gunicorn_access.log
```

### 日志文件位置

| 日志类型 | 文件路径 |
|---------|---------|
| 访问日志 | `/var/www/STATAU/logs/gunicorn_access.log` |
| 错误日志 | `/var/www/STATAU/logs/gunicorn_error.log` |
| PID 文件 | `/var/www/STATAU/logs/gunicorn.pid` |
| Systemd 日志 | `journalctl -u statau` |

---

## ✅ 验证配置

部署完成后，执行以下步骤验证：

1. **检查日志文件是否生成**
   ```bash
   ls -lh /var/www/STATAU/logs/
   ```

2. **查看服务状态**
   ```bash
   sudo systemctl status statau
   ```

3. **访问网站并检查访问日志**
   ```bash
   tail -f /var/www/STATAU/logs/gunicorn_access.log
   ```

4. **触发一个错误并检查错误日志**
   ```bash
   tail -f /var/www/STATAU/logs/gunicorn_error.log
   ```

---

## 🎉 完成

现在你的 Gunicorn 服务已经配置了完整的日志功能！

- ✅ 所有访问记录都会保存在 `logs/gunicorn_access.log`
- ✅ 所有错误信息都会保存在 `logs/gunicorn_error.log`
- ✅ 可以随时使用 `tail -f` 实时查看日志
- ✅ 不需要每次都重启服务来查看报错

如有问题，请查看日志文件或联系技术支持。
