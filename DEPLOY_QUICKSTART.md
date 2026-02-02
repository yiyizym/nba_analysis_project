# 🚀 VPS 部署快速开始

3步完成 NBA 数据自动抓取系统的 VPS 部署！

---

## ⚡ 超快速部署（5分钟）

### 前提条件

- ✅ 已有 VPS（Ubuntu/Debian/CentOS）
- ✅ 本地已配置好 `.env` 文件（Telegram Bot）
- ✅ 可以 SSH 登录 VPS

---

## 第一步：上传项目（本地运行）

```bash
cd /Users/zhu/works/nba_analysis_project
./scripts/deploy/01_upload_to_vps.sh
```

按提示输入 VPS 信息即可。

---

## 第二步：安装环境（VPS 上运行）

SSH 登录到 VPS：

```bash
ssh 用户名@VPS_IP
cd nba_analysis_project
./scripts/deploy/02_setup_vps.sh
```

等待安装完成（约5-10分钟）。

---

## 第三步：设置定时任务（VPS 上运行）

```bash
./scripts/deploy/03_setup_cron.sh
```

选择 `1`（每月1日凌晨3点抓取数据）。

---

## ✅ 验证

### 测试通知

```bash
./scripts/test_telegram.sh
```

检查 Telegram 是否收到消息。

### 测试抓取

```bash
./scripts/scrape_and_notify.sh --team-only
```

等待几分钟，检查是否收到通知。

### 查看定时任务

```bash
crontab -l
```

---

## 🎯 完成！

现在你的 VPS 会：
- 📅 每月1日凌晨3点自动抓取上个月数据
- 📱 抓取完成后发送 Telegram 通知
- 📊 数据保存在 `data/newly_scraped/` 目录

---

## 📖 更多文档

- 详细部署指南：`docs/VPS_DEPLOYMENT.md`
- Telegram 配置：`docs/TELEGRAM_SETUP.md`
- 脚本使用说明：`SCRIPTS.md`

---

## 🔧 常用命令

```bash
# 查看日志
tail -f logs/scrape_monthly.log

# 手动运行抓取
python scripts/scrape_latest.py

# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e
```

---

## ❓ 遇到问题？

查看详细部署指南：
```bash
cat docs/VPS_DEPLOYMENT.md | less
```

或手动执行单个步骤（见文档）。
