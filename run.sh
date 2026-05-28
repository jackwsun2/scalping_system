#!/bin/bash
# 快速运行脚本 - Quick Run Script

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 创建日志目录
mkdir -p logs

# 运行主程序
python src/main.py
