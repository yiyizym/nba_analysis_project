#!/bin/bash
# 调整 VPS 上的 webscraping 配置，增加等待时间和重试次数

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
CONFIG_FILE="$PROJECT_DIR/configs/nba/webscraping_config.yaml"

echo "=========================================="
echo "🔧 调整 VPS 爬虫配置"
echo "=========================================="
echo ""

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

echo "备份原配置文件..."
cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
echo "✅ 备份已创建: $CONFIG_FILE.backup"
echo ""

echo "修改配置参数..."

# 增加超时时间
sed -i 's/^page_load_timeout: 30$/page_load_timeout: 60/' "$CONFIG_FILE"
sed -i 's/^dynamic_content_timeout: 30$/dynamic_content_timeout: 60/' "$CONFIG_FILE"

# 增加重试次数和延迟
sed -i 's/^max_retries: 2$/max_retries: 5/' "$CONFIG_FILE"
sed -i 's/^retry_delay: 2$/retry_delay: 5/' "$CONFIG_FILE"
sed -i 's/^wait_time: 10$/wait_time: 20/' "$CONFIG_FILE"

echo "✅ 配置已更新"
echo ""

echo "新配置值："
echo "  page_load_timeout: $(grep '^page_load_timeout:' "$CONFIG_FILE" | awk '{print $2}')"
echo "  dynamic_content_timeout: $(grep '^dynamic_content_timeout:' "$CONFIG_FILE" | awk '{print $2}')"
echo "  max_retries: $(grep '^max_retries:' "$CONFIG_FILE" | awk '{print $2}')"
echo "  retry_delay: $(grep '^retry_delay:' "$CONFIG_FILE" | awk '{print $2}')"
echo "  wait_time: $(grep '^wait_time:' "$CONFIG_FILE" | awk '{print $2}')"
echo ""

echo "=========================================="
echo "🎉 配置调整完成！"
echo "=========================================="
echo ""
echo "如需恢复原配置："
echo "  cp $CONFIG_FILE.backup $CONFIG_FILE"
