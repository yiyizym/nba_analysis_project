#!/bin/bash
# VPS 环境配置脚本
# 在 VPS 上运行此脚本

set -e

echo "=========================================="
echo "🖥️  VPS 环境配置"
echo "=========================================="
echo ""

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
else
    echo "❌ 无法检测操作系统"
    exit 1
fi

echo "检测到系统: $OS $OS_VERSION"
echo ""

# ============================================================================
# 1. 安装系统依赖
# ============================================================================

echo "=========================================="
echo "📦 安装系统依赖"
echo "=========================================="
echo ""

if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    echo "更新软件包列表..."
    sudo apt update

    echo ""
    echo "安装必要工具..."
    sudo apt install -y \
        python3 \
        python3-pip \
        wget \
        curl \
        git \
        unzip

    echo ""
    echo "安装 Chrome 浏览器..."
    if ! command -v google-chrome &> /dev/null; then
        wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
        sudo apt install -y ./google-chrome-stable_current_amd64.deb
        rm google-chrome-stable_current_amd64.deb
        echo "✅ Chrome 已安装: $(google-chrome --version)"
    else
        echo "✅ Chrome 已安装: $(google-chrome --version)"
    fi

elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]]; then
    echo "更新软件包..."
    sudo yum update -y

    echo ""
    echo "安装必要工具..."
    sudo yum install -y \
        python3 \
        python3-pip \
        wget \
        curl \
        git \
        unzip

    echo ""
    echo "安装 Chrome 浏览器..."
    if ! command -v google-chrome &> /dev/null; then
        wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
        sudo yum install -y ./google-chrome-stable_current_x86_64.rpm
        rm google-chrome-stable_current_x86_64.rpm
        echo "✅ Chrome 已安装: $(google-chrome --version)"
    else
        echo "✅ Chrome 已安装: $(google-chrome --version)"
    fi
else
    echo "⚠️  未识别的操作系统，请手动安装依赖"
fi

# ============================================================================
# 2. 安装 ChromeDriver
# ============================================================================

echo ""
echo "=========================================="
echo "🚗 安装 ChromeDriver"
echo "=========================================="
echo ""

# 获取 Chrome 版本
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+' | cut -d'.' -f1)
echo "Chrome 主版本: $CHROME_VERSION"

# 从 Chrome for Testing API 获取匹配的 ChromeDriver 版本
echo "查询匹配的 ChromeDriver 版本..."
CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json" | \
    python3 -c "import sys, json; data=json.load(sys.stdin); print(data['milestones']['$CHROME_VERSION']['version'])" 2>/dev/null)

if [ -z "$CHROMEDRIVER_VERSION" ]; then
    echo "⚠️  无法找到 Chrome $CHROME_VERSION 对应的 ChromeDriver 版本"
    echo "尝试使用最新稳定版本..."
    CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json" | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['channels']['Stable']['version'])")
fi

echo "ChromeDriver 版本: $CHROMEDRIVER_VERSION"

# 下载 ChromeDriver
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"

echo "下载 ChromeDriver..."
if wget -q "$CHROMEDRIVER_URL" -O chromedriver.zip; then
    unzip -q chromedriver.zip
    sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    rm -rf chromedriver.zip chromedriver-linux64
    echo "✅ ChromeDriver 已安装: $(chromedriver --version)"
else
    echo "❌ ChromeDriver 下载失败"
    echo "URL: $CHROMEDRIVER_URL"
    exit 1
fi

# ============================================================================
# 3. 安装 uv (Python 包管理器)
# ============================================================================

echo ""
echo "=========================================="
echo "📦 安装 uv"
echo "=========================================="
echo ""

if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    echo "✅ uv 已安装: $(uv --version)"
else
    echo "✅ uv 已安装: $(uv --version)"
fi

# ============================================================================
# 4. 安装项目依赖
# ============================================================================

echo ""
echo "=========================================="
echo "🐍 安装项目依赖"
echo "=========================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "项目路径: $PROJECT_DIR"
echo ""

# 使用 uv 同步依赖
echo "同步 Python 依赖..."
# 尝试多个可能的 uv 路径
if command -v uv &> /dev/null; then
    uv sync
elif [ -f "$HOME/.local/bin/uv" ]; then
    $HOME/.local/bin/uv sync
elif [ -f "$HOME/.cargo/bin/uv" ]; then
    $HOME/.cargo/bin/uv sync
else
    echo "❌ 找不到 uv，请手动安装依赖"
    exit 1
fi

echo ""
echo "✅ 依赖安装完成"

# ============================================================================
# 5. 创建必要目录
# ============================================================================

echo ""
echo "=========================================="
echo "📁 创建目录结构"
echo "=========================================="
echo ""

mkdir -p logs
mkdir -p data/newly_scraped/tracking_monthly
mkdir -p data/newly_scraped/player_monthly

echo "✅ 目录创建完成"

# ============================================================================
# 6. 配置检查
# ============================================================================

echo ""
echo "=========================================="
echo "🔍 配置检查"
echo "=========================================="
echo ""

if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件"
    echo ""
    echo "请创建 .env 文件并配置 Telegram Bot:"
    echo "  cp .env.example .env"
    echo "  vim .env"
    echo ""
else
    echo "✅ .env 文件已存在"

    # 检查关键配置
    if grep -q "TELEGRAM_BOT_TOKEN=.*[^[:space:]]" .env && \
       ! grep -q "TELEGRAM_BOT_TOKEN=123456789:" .env; then
        echo "✅ TELEGRAM_BOT_TOKEN 已配置"
    else
        echo "⚠️  TELEGRAM_BOT_TOKEN 未配置或使用默认值"
    fi

    if grep -q "TELEGRAM_CHAT_ID=.*[^[:space:]]" .env && \
       ! grep -q "TELEGRAM_CHAT_ID=987654321" .env; then
        echo "✅ TELEGRAM_CHAT_ID 已配置"
    else
        echo "⚠️  TELEGRAM_CHAT_ID 未配置或使用默认值"
    fi
fi

# ============================================================================
# 完成
# ============================================================================

echo ""
echo "=========================================="
echo "🎉 VPS 环境配置完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo ""
echo "1. 测试 Telegram 通知:"
echo "   ./scripts/test_telegram.sh"
echo ""
echo "2. 测试数据抓取:"
echo "   python scripts/scrape_latest.py --team-only"
echo ""
echo "3. 设置定时任务:"
echo "   ./scripts/deploy/03_setup_cron.sh"
echo ""
