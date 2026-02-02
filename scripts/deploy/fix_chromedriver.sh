#!/bin/bash
# 快速修复 ChromeDriver 版本不匹配问题

set -e

echo "=========================================="
echo "🔧 修复 ChromeDriver 版本"
echo "=========================================="
echo ""

# 获取 Chrome 版本
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+' | cut -d'.' -f1)
echo "当前 Chrome 主版本: $CHROME_VERSION"

# 检查当前 ChromeDriver 版本
if command -v chromedriver &> /dev/null; then
    CURRENT_CHROMEDRIVER=$(chromedriver --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1 || echo "unknown")
    echo "当前 ChromeDriver 版本: $CURRENT_CHROMEDRIVER"
else
    echo "未找到 ChromeDriver"
fi

echo ""

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

echo "目标 ChromeDriver 版本: $CHROMEDRIVER_VERSION"
echo ""

# 下载 ChromeDriver
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"

echo "下载 ChromeDriver..."
if wget -q "$CHROMEDRIVER_URL" -O /tmp/chromedriver.zip; then
    echo "解压..."
    unzip -q -o /tmp/chromedriver.zip -d /tmp/

    echo "安装到 /usr/local/bin/..."
    sudo mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver

    echo "清理临时文件..."
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

    echo ""
    echo "✅ ChromeDriver 已更新!"
    echo "新版本: $(chromedriver --version)"
else
    echo "❌ ChromeDriver 下载失败"
    echo "URL: $CHROMEDRIVER_URL"
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 修复完成！"
echo "=========================================="
