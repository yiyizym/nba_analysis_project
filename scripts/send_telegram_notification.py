#!/usr/bin/env python3
"""
通过 Telegram Bot 发送通知

优点：
- 免费
- 无需配置 SMTP
- 实时推送到手机
- 不会被当作垃圾邮件

设置步骤：
1. 在 Telegram 中找 @BotFather
2. 发送 /newbot 创建机器人，获取 TOKEN
3. 发送 /start 给你的机器人
4. 访问 https://api.telegram.org/bot<TOKEN>/getUpdates 获取 CHAT_ID
"""

import os
import requests
import sys
from datetime import datetime
from pathlib import Path

# 尝试从 .env 文件加载配置
def load_env_file():
    """从 .env 文件加载环境变量"""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env_file()

# 从环境变量读取配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


def check_config():
    """检查配置是否完整"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN':
        print("❌ 错误：TELEGRAM_BOT_TOKEN 未配置")
        print("请在 .env 文件中设置或通过环境变量设置")
        return False

    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == 'YOUR_CHAT_ID':
        print("❌ 错误：TELEGRAM_CHAT_ID 未配置")
        print("请在 .env 文件中设置或通过环境变量设置")
        return False

    return True


def send_telegram_message(message):
    """
    发送 Telegram 消息

    Args:
        message: 消息内容（支持 Markdown 格式）

    Returns:
        bool: 是否发送成功
    """
    if not check_config():
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'  # 支持 Markdown 格式
    }

    try:
        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            print("✅ Telegram 通知发送成功")
            return True
        else:
            print(f"❌ Telegram 发送失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Telegram 发送失败: {e}")
        return False


def read_scrape_log(log_file='logs/scrape_monthly.log', lines=30):
    """读取抓取日志"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except FileNotFoundError:
        return "日志文件不存在"


def notify_scrape_result():
    """发送抓取结果通知到 Telegram"""
    log_content = read_scrape_log(lines=20)

    # 检查是否成功
    if '抓取完成' in log_content:
        # 提取统计
        success_line = [line for line in log_content.split('\n') if '成功:' in line]
        failed_line = [line for line in log_content.split('\n') if '失败:' in line]

        success_count = success_line[-1].split(':')[-1].strip() if success_line else 'N/A'
        failed_count = failed_line[-1].split(':')[-1].strip() if failed_line else 'N/A'

        message = f"""🏀 *NBA 数据抓取完成*

✅ 成功: {success_count}
❌ 失败: {failed_count}

📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        emoji = "✅"
    else:
        message = f"""⚠️ *NBA 数据抓取可能失败*

请检查日志文件

📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        emoji = "❌"

    send_telegram_message(message)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        send_telegram_message(
            "🏀 *NBA 数据抓取系统测试*\n\n"
            f"这是一条测试消息\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        notify_scrape_result()
