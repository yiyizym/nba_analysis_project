#!/bin/bash
# NBA 数据抓取 + Telegram 通知集成脚本
# 适合在 VPS 的 crontab 中使用

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR" || exit 1

# 确保日志目录存在
mkdir -p logs
LOG_FILE="logs/scrape_monthly.log"

# 定义一个函数来同时输出到终端和日志
log() {
    echo "$@" | tee -a "$LOG_FILE"
}

log "=========================================="
log "🏀 NBA 数据月度抓取"
log "=========================================="
log "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
log ""

# 运行数据抓取脚本，同时输出到终端和日志
log "📊 开始抓取数据..."
set +e  # 暂时关闭 errexit，以便捕获退出码
uv run python scripts/scrape_latest.py "$@" 2>&1 | tee -a "$LOG_FILE"
SCRAPE_EXIT_CODE=${PIPESTATUS[0]}
set -e

if [ "$SCRAPE_EXIT_CODE" -eq 0 ]; then
    log "✅ 数据抓取完成"
    SCRAPE_SUCCESS=true
else
    log "❌ 数据抓取失败 (退出码: $SCRAPE_EXIT_CODE)"
    SCRAPE_SUCCESS=false
fi

log ""
log "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
log "=========================================="

echo ""

# 发送 Telegram 通知
echo "📱 发送 Telegram 通知..."
uv run python scripts/send_telegram_notification.py

# 返回抓取结果状态码
if [ "$SCRAPE_SUCCESS" = true ]; then
    exit 0
else
    exit 1
fi
