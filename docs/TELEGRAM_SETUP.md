# 🤖 Telegram Bot 通知设置指南

本指南将帮你设置 Telegram Bot 来接收 NBA 数据抓取的自动通知。

---

## 📱 第一步：创建 Telegram Bot

### 1. 打开 Telegram，搜索 `@BotFather`

BotFather 是 Telegram 官方的机器人管理员。

### 2. 创建新机器人

发送以下命令：
```
/newbot
```

### 3. 按提示操作

```
BotFather: Alright, a new bot. How are we going to call it?
           Please choose a name for your bot.

你: NBA Data Scraper Bot

BotFather: Good. Now let's choose a username for your bot.
           It must end in `bot`. Like this, for example: TetrisBot or tetris_bot.

你: nba_data_scraper_bot
```

**注意：**
- Bot 名称可以随意（如"NBA Data Scraper Bot"）
- 用户名必须以 `_bot` 或 `Bot` 结尾
- 用户名必须全局唯一，如果被占用就换一个

### 4. 保存 Bot Token

创建成功后，BotFather 会返回：

```
Done! Congratulations on your new bot. You will find it at t.me/nba_data_scraper_bot.

Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz

Keep your token secure and store it safely, it can be used by anyone to control your bot.
```

⚠️ **重要：保存这个 Token**，这就是你的 `TELEGRAM_BOT_TOKEN`

---

## 🔍 第二步：获取 Chat ID

### 1. 激活你的机器人

- 在 Telegram 中搜索你的机器人（用户名，如 `@nba_data_scraper_bot`）
- 点击 **START** 按钮
- 发送任意消息（如 `Hello`）

### 2. 获取 Chat ID

在浏览器中访问以下 URL（替换成你的 Token）：

```
https://api.telegram.org/bot<你的TOKEN>/getUpdates
```

完整示例：
```
https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
```

### 3. 找到你的 Chat ID

返回的 JSON 中找到：

```json
{
  "ok": true,
  "result": [
    {
      "update_id": 123456789,
      "message": {
        "message_id": 1,
        "from": {
          "id": 987654321,
          "is_bot": false,
          "first_name": "Your Name"
        },
        "chat": {
          "id": 987654321,    ← 这就是你的 CHAT_ID
          "first_name": "Your Name",
          "type": "private"
        },
        "date": 1234567890,
        "text": "Hello"
      }
    }
  ]
}
```

⚠️ **保存这个数字**（如 `987654321`），这就是你的 `TELEGRAM_CHAT_ID`

---

## ⚙️ 第三步：配置项目

### 方式 1：使用 .env 文件（推荐）

1. **复制示例文件**
   ```bash
   cd /Users/zhu/works/nba_analysis_project
   cp .env.example .env
   ```

2. **编辑 .env 文件**
   ```bash
   vim .env  # 或使用其他编辑器
   ```

3. **填入你的配置**
   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=987654321
   ```

### 方式 2：使用环境变量

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="987654321"
```

然后执行：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

---

## 🧪 第四步：测试

### 快速测试脚本

```bash
cd /Users/zhu/works/nba_analysis_project
./scripts/test_telegram.sh
```

### 手动测试

```bash
python scripts/send_telegram_notification.py test
```

如果配置正确，你会在 Telegram 中收到测试消息：

```
🏀 NBA 数据抓取系统测试

这是一条测试消息

📅 2026-02-02 10:30:45
```

---

## 🖥️ 第五步：VPS 部署

### 1. 上传项目到 VPS

```bash
# 从本地同步到 VPS
rsync -avz --exclude '.venv' --exclude '.git' \
    /Users/zhu/works/nba_analysis_project/ \
    user@your-vps:/home/user/nba_analysis_project/
```

### 2. VPS 上安装依赖

```bash
ssh user@your-vps

cd /home/user/nba_analysis_project

# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 同步依赖
uv sync

# 安装 Chrome (用于数据抓取)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

### 3. 配置 .env 文件

```bash
cd /home/user/nba_analysis_project
cp .env.example .env
vim .env  # 填入你的 Telegram 配置
```

### 4. 测试

```bash
./scripts/test_telegram.sh
```

### 5. 设置 Crontab 定时任务

```bash
crontab -e
```

添加以下内容：

```bash
# 每月1日凌晨3点抓取上个月数据并发送通知
0 3 1 * * cd /home/user/nba_analysis_project && ./scripts/scrape_and_notify.sh >> logs/scrape_monthly.log 2>&1

# 可选：每周日凌晨2点更新当月数据
0 2 * * 0 cd /home/user/nba_analysis_project && ./scripts/scrape_and_notify.sh >> logs/scrape_weekly.log 2>&1
```

---

## 📊 使用示例

### 手动抓取并通知

```bash
# 抓取上个月数据并发送通知
./scripts/scrape_and_notify.sh

# 只抓取球队数据
./scripts/scrape_and_notify.sh --team-only

# 抓取指定月份
./scripts/scrape_and_notify.sh --month december
```

### 只发送通知（不抓取）

```bash
# 测试通知
python scripts/send_telegram_notification.py test

# 发送上次抓取结果
python scripts/send_telegram_notification.py
```

---

## ❓ 常见问题

### Q1: 收不到消息？

检查：
1. Bot Token 是否正确
2. Chat ID 是否正确
3. 是否给机器人发送过消息（必须先 START）
4. 检查网络是否能访问 `api.telegram.org`

### Q2: 报错 "Unauthorized"

Token 错误，请重新检查 `TELEGRAM_BOT_TOKEN`

### Q3: 报错 "Bad Request: chat not found"

Chat ID 错误，请重新获取 `TELEGRAM_CHAT_ID`

### Q4: VPS 无法访问 Telegram？

使用代理：

```python
# 在脚本中添加
proxies = {
    'http': 'http://your-proxy:port',
    'https': 'http://your-proxy:port',
}
response = requests.post(url, json=data, proxies=proxies)
```

---

## 📝 通知消息示例

### 成功通知

```
🏀 NBA 数据抓取完成

✅ 成功: 40
❌ 失败: 0

📅 时间: 2026-02-02 03:05
```

### 失败通知

```
⚠️ NBA 数据抓取可能失败

请检查日志文件

📅 时间: 2026-02-02 03:05
```

---

## 🔒 安全提示

⚠️ **重要：保护你的 Token**

- ✅ 使用 `.env` 文件（已在 `.gitignore` 中）
- ✅ 不要将 Token 提交到 Git
- ✅ 不要在公开场合分享 Token
- ❌ 如果泄露，立即在 BotFather 中重新生成：`/revoke`

---

## 🎯 总结

1. ✅ 在 @BotFather 创建机器人，获取 Token
2. ✅ 给机器人发消息，获取 Chat ID
3. ✅ 配置 .env 文件
4. ✅ 运行 `./scripts/test_telegram.sh` 测试
5. ✅ VPS 上设置 crontab 定时任务

完成！现在你会在每月1日自动收到数据抓取通知 🎉
