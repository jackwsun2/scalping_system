"""
项目结构生成脚本 - Project Structure Generator
显示完整的项目目录结构
"""

import os
from pathlib import Path

def print_tree(path, prefix="", is_last=True):
    """递归打印目录树"""
    
    # 跳过某些文件和目录
    skip_names = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', '.venv',
                  '.DS_Store', '*.pyc', 'node_modules', '.idea', '.vscode'}
    
    path_obj = Path(path)
    
    # 获取所有子项
    try:
        items = sorted(path_obj.iterdir(), key=lambda x: (x.is_file(), x.name))
    except PermissionError:
        return
    
    # 过滤
    items = [
        item for item in items 
        if item.name not in skip_names and not item.name.startswith('.')
    ]
    
    for i, item in enumerate(items):
        is_last_item = i == len(items) - 1
        
        # 打印当前项
        current_prefix = "└── " if is_last_item else "├── "
        print(prefix + current_prefix + item.name)
        
        # 如果是目录，递归处理
        if item.is_dir():
            next_prefix = prefix + ("    " if is_last_item else "│   ")
            print_tree(item, next_prefix, is_last_item)


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("超短线量化交易系统 - 项目结构")
    print("Scalping Trading System - Project Structure")
    print("=" * 70 + "\n")
    
    print("scalping_system/\n")
    print_tree(".")
    
    print("\n" + "=" * 70)
    print("项目统计")
    print("=" * 70)
    
    # 统计文件
    py_files = list(Path('.').rglob('*.py'))
    md_files = list(Path('.').rglob('*.md'))
    config_files = list(Path('config').glob('*.py')) if Path('config').exists() else []
    
    print(f"\n代码文件统计:")
    print(f"  - Python 源文件: {len(py_files)} 个")
    print(f"  - Markdown 文档: {len(md_files)} 个")
    print(f"  - 配置文件: {len(config_files)} 个")
    
    print(f"\n主要模块:")
    print(f"  ✓ src/data_fetcher.py   - 数据获取")
    print(f"  ✓ src/indicators.py     - 技术指标")
    print(f"  ✓ src/strategy.py       - 交易策略")
    print(f"  ✓ src/backtest.py       - 回测引擎")
    print(f"  ✓ src/executor.py       - 订单执行")
    print(f"  ✓ src/alerts.py         - 告警推送")
    print(f"  ✓ src/main.py           - 主程序入口")
    
    print(f"\n文档:")
    print(f"  ✓ README.md             - 完整文档")
    print(f"  ✓ QUICKSTART.md         - 快速开始")
    print(f"  ✓ CHANGELOG.md          - 版本日志")
    
    print("\n" + "=" * 70 + "\n")
