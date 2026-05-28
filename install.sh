#!/bin/bash
# macOS 安装脚本 - Install Script for macOS
# 用于安装依赖和设置环境

set -e

echo "=========================================="
echo "超短线量化交易系统 - 安装脚本"
echo "Scalping Trading System - Setup Script"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "请先安装 Python 3.8+ (使用 Homebrew 或官网)"
    echo "brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ 找到 Python $PYTHON_VERSION"

# 创建虚拟环境
echo ""
echo "创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 虚拟环境已创建"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate
echo "✓ 虚拟环境已激活"

# 升级 pip
echo ""
echo "升级 pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "✓ pip 已升级"

# 安装依赖
echo ""
echo "安装依赖包..."
echo "(这可能需要几分钟...)"

# 先安装基础依赖
pip install numpy pandas > /dev/null 2>&1

# 安装其他依赖
pip install -r requirements.txt

echo "✓ 依赖安装完成"

# 创建必要的目录
echo ""
echo "创建目录结构..."
mkdir -p logs data_cache config

# 生成 .env 模板
if [ ! -f ".env.example" ]; then
    cat > .env.example << 'EOF'
# Alpaca API 配置
ALPACA_API_KEY=YOUR_API_KEY
ALPACA_SECRET_KEY=YOUR_SECRET_KEY

# Telegram Bot 配置 (可选)
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
EOF
    echo "✓ .env.example 已创建"
fi

# 复制配置文件
if [ ! -f "config/config.py" ]; then
    cp config/example_config.py config/config.py
    echo "✓ 配置文件已复制到 config/config.py"
    echo "  请编辑 config/config.py 填入你的配置"
fi

echo ""
echo "=========================================="
echo "安装完成! ✓"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 编辑 config/config.py 配置参数"
echo "2. 编辑 .env 文件 (如需 Alpaca 或 Telegram)"
echo "3. 运行: python src/main.py"
echo ""
