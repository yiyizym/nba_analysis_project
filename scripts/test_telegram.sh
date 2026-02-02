#!/bin/bash
# Telegram Bot 配置测试脚本

echo "🏀 NBA 数据抓取 - Telegram Bot 配置测试"
echo "=========================================="
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件"
    echo ""
    echo "请按以下步骤操作："
    echo "1. 复制 .env.example 为 .env"
    echo "   cp .env.example .env"
    echo ""
    echo "2. 编辑 .env 文件，填入你的 Telegram Bot 配置"
    echo "   vim .env  # 或使用其他编辑器"
    echo ""
    exit 1
fi

echo "✅ 找到 .env 文件"
echo ""

# 检查配置
echo "📋 当前配置："
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "  TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:0:10}... (从环境变量)"
else
    TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env 2>/dev/null | cut -d'=' -f2)
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "123456789:ABCdefGHIjklMNOpqrsTUVwxyz" ]; then
        echo "  TELEGRAM_BOT_TOKEN: ${TOKEN:0:10}... (从 .env)"
    else
        echo "  ❌ TELEGRAM_BOT_TOKEN 未配置或使用默认值"
        exit 1
    fi
fi

if [ -n "$TELEGRAM_CHAT_ID" ]; then
    echo "  TELEGRAM_CHAT_ID: $TELEGRAM_CHAT_ID (从环境变量)"
else
    CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" .env 2>/dev/null | cut -d'=' -f2)
    if [ -n "$CHAT_ID" ] && [ "$CHAT_ID" != "987654321" ]; then
        echo "  TELEGRAM_CHAT_ID: $CHAT_ID (从 .env)"
    else
        echo "  ❌ TELEGRAM_CHAT_ID 未配置或使用默认值"
        exit 1
    fi
fi

echo ""
echo "🚀 发送测试消息..."
uv run python scripts/send_telegram_notification.py test

echo ""
echo "📱 请检查你的 Telegram 是否收到测试消息"
