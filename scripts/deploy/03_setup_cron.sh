#!/bin/bash
# 设置 Crontab 定时任务

set -e

echo "=========================================="
echo "⏰ 设置定时任务"
echo "=========================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"

echo "项目路径: $PROJECT_DIR"
echo "Python 路径: $PYTHON_PATH"
echo ""

# 检查 Python 是否存在
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ 未找到 Python 虚拟环境"
    echo "请先运行 02_setup_vps.sh 安装依赖"
    exit 1
fi

# ============================================================================
# 定时任务配置
# ============================================================================

echo "请选择定时任务配置:"
echo ""
echo "1) 每月1日凌晨3点抓取上个月数据（推荐）"
echo "2) 每月1日凌晨3点 + 每周日凌晨2点更新当月数据"
echo "3) 仅每周日凌晨2点抓取数据"
echo "4) 自定义"
echo "5) 取消"
echo ""

read -p "选择 (1-5): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 3 1 * *"
        CRON_COMMAND="cd $PROJECT_DIR && ./scripts/scrape_and_notify.sh >> logs/scrape_monthly.log 2>&1"
        DESCRIPTION="每月1日凌晨3点抓取数据"
        ;;
    2)
        CRON_MONTHLY="0 3 1 * * cd $PROJECT_DIR && ./scripts/scrape_and_notify.sh >> logs/scrape_monthly.log 2>&1"
        CRON_WEEKLY="0 2 * * 0 cd $PROJECT_DIR && ./scripts/scrape_and_notify.sh >> logs/scrape_weekly.log 2>&1"
        DESCRIPTION="每月1日 + 每周日抓取数据"
        ;;
    3)
        CRON_SCHEDULE="0 2 * * 0"
        CRON_COMMAND="cd $PROJECT_DIR && ./scripts/scrape_and_notify.sh >> logs/scrape_weekly.log 2>&1"
        DESCRIPTION="每周日凌晨2点抓取数据"
        ;;
    4)
        echo ""
        echo "输入 cron 时间表达式 (如 '0 3 1 * *' 表示每月1日凌晨3点):"
        read -p "Cron 表达式: " CRON_SCHEDULE
        CRON_COMMAND="cd $PROJECT_DIR && ./scripts/scrape_and_notify.sh >> logs/scrape_custom.log 2>&1"
        DESCRIPTION="自定义定时任务"
        ;;
    5)
        echo "已取消"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# ============================================================================
# 添加到 Crontab
# ============================================================================

echo ""
echo "准备添加定时任务:"
echo ""
if [ -n "$CRON_MONTHLY" ]; then
    echo "  月度: $CRON_MONTHLY"
    echo "  周度: $CRON_WEEKLY"
else
    echo "  $CRON_SCHEDULE $CRON_COMMAND"
fi
echo ""

read -p "确认添加? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 备份当前 crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# 添加新任务
(
    crontab -l 2>/dev/null || true
    echo ""
    echo "# NBA 数据抓取定时任务 - 添加于 $(date)"
    if [ -n "$CRON_MONTHLY" ]; then
        echo "$CRON_MONTHLY"
        echo "$CRON_WEEKLY"
    else
        echo "$CRON_SCHEDULE $CRON_COMMAND"
    fi
) | crontab -

echo ""
echo "✅ 定时任务已添加"
echo ""

# ============================================================================
# 显示当前 Crontab
# ============================================================================

echo "=========================================="
echo "📋 当前定时任务"
echo "=========================================="
echo ""
crontab -l
echo ""

# ============================================================================
# 测试运行
# ============================================================================

echo "=========================================="
echo "🧪 测试任务"
echo "=========================================="
echo ""

read -p "是否立即测试运行? (y/N): " test_confirm
if [[ "$test_confirm" =~ ^[Yy]$ ]]; then
    echo ""
    echo "运行测试..."
    cd "$PROJECT_DIR"
    ./scripts/scrape_and_notify.sh --team-only
    echo ""
    echo "✅ 测试完成，请检查 Telegram 是否收到通知"
fi

echo ""
echo "=========================================="
echo "🎉 定时任务设置完成！"
echo "=========================================="
echo ""
echo "管理命令:"
echo "  查看定时任务: crontab -l"
echo "  编辑定时任务: crontab -e"
echo "  删除定时任务: crontab -r"
echo ""
echo "日志文件:"
echo "  月度日志: $PROJECT_DIR/logs/scrape_monthly.log"
echo "  周度日志: $PROJECT_DIR/logs/scrape_weekly.log"
echo ""
echo "查看日志:"
echo "  tail -f $PROJECT_DIR/logs/scrape_monthly.log"
echo ""
