#!/bin/bash
# 上传项目到 VPS

set -e

echo "=========================================="
echo "📤 上传项目到 VPS"
echo "=========================================="
echo ""

# 配置（请根据实际情况修改）
read -p "VPS 用户名 (如 root 或 ubuntu): " VPS_USER
read -p "VPS IP 地址: " VPS_IP
read -p "VPS 目标路径 (默认 /home/$VPS_USER/nba_analysis_project): " VPS_PATH
VPS_PATH=${VPS_PATH:-/home/$VPS_USER/nba_analysis_project}

echo ""
echo "配置信息:"
echo "  用户: $VPS_USER"
echo "  地址: $VPS_IP"
echo "  路径: $VPS_PATH"
echo ""

read -p "确认上传? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "🔄 开始同步..."
echo ""

# 使用 rsync 上传项目
rsync -avz --progress \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='logs/*.log' \
    --exclude='data/newly_scraped/scrape_latest_progress_*.json' \
    /Users/zhu/works/nba_analysis_project/ \
    $VPS_USER@$VPS_IP:$VPS_PATH/

echo ""
echo "✅ 上传完成！"
echo ""
echo "下一步："
echo "1. SSH 登录到 VPS:"
echo "   ssh $VPS_USER@$VPS_IP"
echo ""
echo "2. 运行安装脚本:"
echo "   cd $VPS_PATH"
echo "   ./scripts/deploy/02_setup_vps.sh"
