# STATAU-linux 项目配置

## Git 仓库信息

### 远程仓库地址
- **SSH**: `git@github.com:1157360333-a11y/STATAU-linux.git`
- **HTTPS**: `https://github.com/1157360333-a11y/STATAU-linux.git`
- **GitHub用户**: 1157360333-a11y
- **仓库名**: STATAU-linux

### 分支信息
- **主分支**: master
- **开发分支**: main（如果存在）

## 自动化Git操作指南

### 拉取最新代码
当需要更新本地代码时，执行：
```bash
git fetch origin
git pull origin master
```

### 提交并推送代码
当完成代码修改后，执行：
```bash
git add .
git commit -m "描述性的提交信息"
git push origin master
```

### 查看状态
```bash
git status
git log --oneline -5
```

## 项目信息

### 项目类型
Flask Web应用 - 统计分析工具

### 主要功能
- 豪斯曼检验
- F检验
- 控制变量选取
- 邮箱验证登录功能

### 技术栈
- Python Flask
- 数据库（见config.py）
- 前端模板（templates目录）

### 重要文件
- `app.py` - 主应用入口
- `config.py` - 配置文件
- `requirements.txt` - Python依赖
- `blueprints/` - 蓝图模块
- `core/` - 核心功能
- `services/` - 服务层

### 文档
- `README.md` - 项目说明
- `ARCHITECTURE.md` - 架构文档
- `部署.md` - 部署指南
- `管理后台使用说明.md` - 管理后台文档
- `邮箱验证功能说明.md` - 邮箱功能文档

## Claude助手工作流程

### 代码修改后的标准流程
1. 确认修改内容符合要求
2. 运行测试（如果有）
3. 使用 `git status` 查看修改的文件
4. 使用 `git add` 添加修改的文件
5. 使用 `git commit` 提交，附带清晰的提交信息
6. 使用 `git push origin master` 推送到远程仓库

### 开始工作前
1. 使用 `git pull origin master` 拉取最新代码
2. 检查是否有冲突
3. 确认当前分支是 master

### 注意事项
- 提交信息应该清晰描述修改内容
- 推送前确认代码可以正常运行
- 重要修改前建议先拉取最新代码
- SSH密钥已配置在 `~/.ssh/id_ed25519`

## 环境配置

### SSH配置
- SSH密钥类型: ed25519
- 公钥位置: `~/.ssh/id_ed25519.pub`
- 私钥位置: `~/.ssh/id_ed25519`
- 已添加到GitHub账户

### 本地路径
- 项目路径: `c:\Users\86132\Desktop\STATAU-linux`
- 虚拟环境: `venv/`

## 快速命令参考

```bash
# 查看远程仓库
git remote -v

# 查看当前分支
git branch

# 切换分支
git checkout master

# 查看提交历史
git log --oneline --graph --all

# 撤销未提交的修改
git checkout -- <file>

# 查看差异
git diff
```
