#!/usr/bin/env python3
"""
Telegram Chat ID 获取工具

这个脚本会持续监听你的 Telegram Bot，
当你给机器人发送消息时，自动显示你的 Chat ID
"""

import requests
import time
import sys

def print_banner():
    print("=" * 60)
    print("🔍 Telegram Chat ID 获取工具")
    print("=" * 60)
    print()

def get_chat_id(bot_token):
    """获取并显示所有 Chat ID"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get('ok'):
            print(f"❌ API 错误: {data.get('description', '未知错误')}")
            return None

        results = data.get('result', [])

        if not results:
            return None

        # 获取所有唯一的 chat_id
        chat_ids = set()
        for update in results:
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                chat_type = update['message']['chat']['type']
                from_user = update['message']['from'].get('first_name', 'Unknown')
                text = update['message'].get('text', '(无文本)')

                chat_ids.add(chat_id)

                print(f"\n✅ 找到消息:")
                print(f"   发送人: {from_user}")
                print(f"   Chat ID: {chat_id}")
                print(f"   Chat 类型: {chat_type}")
                print(f"   消息内容: {text}")

        return list(chat_ids)

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return None

def main():
    print_banner()

    # 获取 Bot Token
    if len(sys.argv) > 1:
        bot_token = sys.argv[1]
    else:
        print("请输入你的 Telegram Bot Token:")
        print("(从 @BotFather 获取，格式: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
        print()
        bot_token = input("Bot Token: ").strip()

    if not bot_token:
        print("❌ Token 不能为空")
        return 1

    print()
    print("=" * 60)
    print("📱 请在 Telegram 中给你的机器人发送消息")
    print("=" * 60)
    print()
    print("步骤:")
    print("1. 打开 Telegram")
    print("2. 搜索你的机器人（用户名）")
    print("3. 点击 START 按钮（如果还没点过）")
    print("4. 发送任意消息（如: hello 或 /start）")
    print()
    print("等待消息中... (按 Ctrl+C 退出)")
    print()

    found_ids = set()
    check_count = 0

    try:
        while True:
            check_count += 1
            print(f"\r正在检查... (第 {check_count} 次)", end='', flush=True)

            chat_ids = get_chat_id(bot_token)

            if chat_ids:
                new_ids = set(chat_ids) - found_ids
                if new_ids:
                    found_ids.update(new_ids)
                    print()
                    print()
                    print("=" * 60)
                    print("🎉 成功获取 Chat ID!")
                    print("=" * 60)
                    print()

                    if len(found_ids) == 1:
                        chat_id = list(found_ids)[0]
                        print(f"你的 Chat ID 是: {chat_id}")
                        print()
                        print("📝 请将以下配置添加到 .env 文件:")
                        print()
                        print(f"TELEGRAM_BOT_TOKEN={bot_token}")
                        print(f"TELEGRAM_CHAT_ID={chat_id}")
                        print()
                    else:
                        print(f"找到 {len(found_ids)} 个 Chat ID:")
                        for cid in found_ids:
                            print(f"  - {cid}")
                        print()

                    print("继续监听新消息... (按 Ctrl+C 退出)")
                    print()

            time.sleep(2)  # 每2秒检查一次

    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("👋 已停止监听")
        print("=" * 60)

        if found_ids:
            print()
            print(f"总共找到 {len(found_ids)} 个 Chat ID:")
            for cid in found_ids:
                print(f"  - {cid}")
            print()
            print("请将其中一个添加到 .env 文件中的 TELEGRAM_CHAT_ID")
        else:
            print()
            print("⚠️  未找到任何消息")
            print()
            print("请确认:")
            print("1. Bot Token 是否正确")
            print("2. 是否已在 Telegram 中给机器人发送消息")
            print("3. 网络是否能访问 api.telegram.org")

        return 0

if __name__ == '__main__':
    sys.exit(main())
