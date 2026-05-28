"""
系统诊断脚本 - System Diagnostic Script
检查依赖和系统配置
"""

import sys
from pathlib import Path

print("\n" + "=" * 60)
print("系统诊断 - System Diagnostic")
print("=" * 60 + "\n")

# 1. Python 版本
print("✓ Python 版本:")
print(f"  {sys.version}")

# 2. 检查关键依赖
print("\n✓ 依赖检查:")

dependencies = {
    'pandas': '数据处理',
    'numpy': '数值计算',
    'yfinance': '数据获取',
    'pandas_ta': '技术指标',
    'requests': '网络请求',
}

missing = []
for pkg, desc in dependencies.items():
    try:
        __import__(pkg)
        print(f"  ✓ {pkg:20} - {desc}")
    except ImportError:
        print(f"  ✗ {pkg:20} - {desc} (未安装)")
        missing.append(pkg)

# 3. 可选依赖
print("\n✓ 可选依赖:")

optional = {
    'alpaca_trade_api': 'Alpaca 实盘交易',
    'telegram': 'Telegram 推送',
}

for pkg, desc in optional.items():
    try:
        __import__(pkg)
        print(f"  ✓ {pkg:20} - {desc}")
    except ImportError:
        print(f"  ○ {pkg:20} - {desc} (可选,未安装)")

# 4. 目录检查
print("\n✓ 目录结构:")

required_dirs = ['src', 'config', 'tests']
for d in required_dirs:
    path = Path(d)
    if path.exists():
        print(f"  ✓ {d}/")
    else:
        print(f"  ✗ {d}/ (缺失)")

# 5. 文件检查
print("\n✓ 关键文件:")

required_files = {
    'src/main.py': '主程序',
    'src/config.py': '配置管理',
    'requirements.txt': '依赖列表',
    'README.md': '文档',
}

for f, desc in required_files.items():
    path = Path(f)
    if path.exists():
        print(f"  ✓ {f:30} - {desc}")
    else:
        print(f"  ✗ {f:30} - {desc} (缺失)")

# 总结
print("\n" + "=" * 60)
if missing:
    print(f"⚠️  缺失 {len(missing)} 个依赖: {', '.join(missing)}")
    print("运行: pip install -r requirements.txt")
else:
    print("✓ 所有依赖已安装!")

print("=" * 60 + "\n")
