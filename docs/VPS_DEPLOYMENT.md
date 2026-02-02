# 🖥️ VPS 部署完整指南

本指南将帮你在 VPS 上部署 NBA 数据自动抓取系统。

---

## 📋 准备工作

### VPS 要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| **CPU** | 1核 | 2核+ |
| **内存** | 1GB | 2GB+ |
| **硬盘** | 10GB | 20GB+ |
| **系统** | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| **网络** | 能访问 nba.com 和 telegram.org | - |

### 本地准备

1. ✅ 已完成 Telegram Bot 配置（`.env` 文件已填写）
2. ✅ VPS SSH 访问已配置
3. ✅ 本地测试已通过

---

## 🚀 快速部署（三步走）

### 第一步：上传项目到 VPS

在**本地机器**运行：

```bash
cd /Users/zhu/works/nba_analysis_project
./scripts/deploy/01_upload_to_vps.sh
```

按提示输入：
- VPS 用户名（如 `root` 或 `ubuntu`）
- VPS IP 地址
- 目标路径（默认 `/home/用户名/nba_analysis_project`）

**预计时间：** 2-5 分钟（取决于网络速度）

---

### 第二步：配置 VPS 环境

SSH 登录到 VPS：

```bash
ssh 用户名@VPS_IP
```

运行安装脚本：

```bash
cd nba_analysis_project
chmod +x scripts/deploy/*.sh
./scripts/deploy/02_setup_vps.sh
```

脚本会自动：
- ✅ 安装 Python、Chrome、ChromeDriver
- ✅ 安装 uv 和项目依赖
- ✅ 创建必要目录
- ✅ 检查配置文件

**预计时间：** 5-10 分钟

---

### 第三步：设置定时任务

在 VPS 上运行：

```bash
./scripts/deploy/03_setup_cron.sh
```

选择定时方案：
1. **每月1日凌晨3点**（推荐） - 抓取上个月数据
2. **每月1日 + 每周日** - 月度 + 周度更新
3. **仅每周日** - 仅周度更新
4. **自定义** - 自定义时间

**预计时间：** 1 分钟

---

## ✅ 测试验证

### 1. 测试 Telegram 通知

```bash
./scripts/test_telegram.sh
```

检查 Telegram 是否收到测试消息。

---

### 2. 测试数据抓取

```bash
# 测试球队数据抓取（较快）
python scripts/scrape_latest.py --team-only

# 测试完整抓取
./scripts/scrape_and_notify.sh
```

---

### 3. 查看定时任务

```bash
# 查看当前定时任务
crontab -l

# 查看日志
tail -f logs/scrape_monthly.log
```

---

## 📝 详细部署步骤

如果自动脚本遇到问题，可以手动执行以下步骤：

### 1. 上传项目

```bash
# 方法 A: 使用 rsync (推荐)
rsync -avz --exclude='.git' --exclude='.venv' \
    /Users/zhu/works/nba_analysis_project/ \
    user@vps-ip:/home/user/nba_analysis_project/

# 方法 B: 使用 scp
scp -r /Users/zhu/works/nba_analysis_project user@vps-ip:/home/user/

# 方法 C: 使用 Git
ssh user@vps-ip
cd ~
git clone https://github.com/your-repo/nba_analysis_project.git
# 然后手动上传 .env 文件
```

---

### 2. VPS 环境配置

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y python3 python3-pip wget curl git unzip

# 安装 Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# 安装 ChromeDriver
# 查看 Chrome 版本
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+' | head -1)
# 下载对应版本 ChromeDriver
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE -O /tmp/chromedriver_version
DRIVER_VERSION=$(cat /tmp/chromedriver_version)
wget https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip
```

#### CentOS/RHEL

```bash
# 更新系统
sudo yum update -y

# 安装基础工具
sudo yum install -y python3 python3-pip wget curl git unzip

# 安装 Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm
rm google-chrome-stable_current_x86_64.rpm

# ChromeDriver 安装同上
```

---

### 3. 安装项目依赖

```bash
cd /home/user/nba_analysis_project

# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 同步依赖
uv sync

# 创建目录
mkdir -p logs
mkdir -p data/newly_scraped
```

---

### 4. 配置 .env 文件

```bash
# 如果没有上传 .env，手动创建
cp .env.example .env
vim .env  # 填入 Telegram 配置
```

---

### 5. 设置 Crontab

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（每月1日凌晨3点）
0 3 1 * * cd /home/user/nba_analysis_project && ./scripts/scrape_and_notify.sh >> logs/scrape_monthly.log 2>&1
```

**Cron 时间表达式说明：**
```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日期 (1 - 31)
│ │ │ ┌───────────── 月份 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 7) (0或7表示周日)
│ │ │ │ │
│ │ │ │ │
* * * * *

示例：
0 3 1 * *     每月1日凌晨3点
0 2 * * 0     每周日凌晨2点
0 0 * * *     每天凌晨0点
*/30 * * * *  每30分钟
```

---

## 🔧 常见问题

### Q1: Chrome 或 ChromeDriver 版本不匹配

**错误：**
```
session not created: This version of ChromeDriver only supports Chrome version XX
```

**解决：**
```bash
# 查看 Chrome 版本
google-chrome --version

# 查看 ChromeDriver 版本
chromedriver --version

# 下载匹配版本
# 访问 https://chromedriver.chromium.org/downloads
```

---

### Q2: 无法访问 Telegram API

**错误：**
```
Failed to connect to api.telegram.org
```

**解决：**

方法 A：配置代理
```bash
export HTTP_PROXY=http://proxy-server:port
export HTTPS_PROXY=http://proxy-server:port
```

方法 B：修改脚本使用代理（在 `send_telegram_notification.py` 中）
```python
proxies = {
    'http': 'http://your-proxy:port',
    'https': 'http://your-proxy:port',
}
response = requests.post(url, json=data, proxies=proxies)
```

---

### Q3: 权限不足

**错误：**
```
Permission denied
```

**解决：**
```bash
# 给脚本添加执行权限
chmod +x scripts/*.sh
chmod +x scripts/deploy/*.sh

# 或使用 sudo 运行
sudo ./scripts/deploy/02_setup_vps.sh
```

---

### Q4: 磁盘空间不足

**检查：**
```bash
df -h
du -sh data/newly_scraped/*
```

**清理：**
```bash
# 清理旧日志
find logs -name "*.log" -mtime +30 -delete

# 清理旧进度文件
rm data/newly_scraped/scrape_latest_progress_*.json

# 压缩旧数据
tar -czf data_backup_$(date +%Y%m).tar.gz data/newly_scraped/
```

---

## 📊 监控和维护

### 查看日志

```bash
# 实时查看最新日志
tail -f logs/scrape_monthly.log

# 查看最近100行
tail -100 logs/scrape_monthly.log

# 搜索错误
grep "错误\|失败\|Error" logs/scrape_monthly.log
```

---

### 手动运行

```bash
# 测试抓取（不启动 Chrome）
python scripts/scrape_latest.py --help

# 抓取上个月数据
python scripts/scrape_latest.py

# 抓取指定月份
python scripts/scrape_latest.py --month january

# 只抓取球队数据
python scripts/scrape_latest.py --team-only
```

---

### 数据备份

```bash
# 定期备份数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# 上传到云存储（示例：rclone）
rclone copy data/ remote:nba_backup/

# 或同步回本地
rsync -avz user@vps-ip:/home/user/nba_analysis_project/data/ \
    /Users/zhu/works/nba_analysis_project/data_backup/
```

---

### 更新项目

```bash
# 在本地更新代码后，重新上传
./scripts/deploy/01_upload_to_vps.sh

# 在 VPS 上重新安装依赖（如果有新依赖）
cd /home/user/nba_analysis_project
uv sync
```

---

## 🎯 部署检查清单

部署完成后，请确认：

- [ ] VPS 环境已配置（Chrome、ChromeDriver、Python、uv）
- [ ] 项目已上传且 .env 文件正确
- [ ] Telegram 通知测试成功
- [ ] 数据抓取测试成功
- [ ] Crontab 定时任务已设置
- [ ] 日志目录可写且日志正常生成
- [ ] 收到第一次自动抓取的 Telegram 通知

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件：`tail -f logs/scrape_monthly.log`
2. 检查 Telegram 通知是否收到
3. 手动运行测试脚本
4. 查看本文档的常见问题部分

---

## 🎉 完成！

现在你的 VPS 会在每月1日自动抓取上个月的 NBA 数据，并通过 Telegram 通知你！
