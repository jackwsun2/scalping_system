#!/usr/bin/env python3
"""
KDJ 指标快速示例 - Quick Example of KDJ Integration
"""

import sys
from pathlib import Path
import pandas as pd

# 添加 src 目录
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_fetcher import DataFetcher
from indicators import TechnicalIndicators
from strategy import ScalpingStrategy


def example_1_kdj_values():
    """示例 1: 获取最新 KDJ 值"""
    print("\n" + "=" * 70)
    print("示例 1: 获取最新 KDJ 值")
    print("=" * 70)
    
    print("\n1. 获取 GLD 最近 5 天的数据...")
    fetcher = DataFetcher(['GLD'], '5m')
    df = fetcher.fetch_historical('GLD', days=5)
    
    print(f"   ✓ 获取 {len(df)} 根 K线")
    
    print("\n2. 添加 KDJ 指标...")
    df = TechnicalIndicators.calculate_all_indicators(df)
    print(f"   ✓ KDJ 计算完成")
    
    print("\n3. 显示最新 5 根 K线的 KDJ 值:")
    print("\n" + df[['close', 'kdj_k', 'kdj_d', 'kdj_j']].tail().to_string())
    
    print("\n4. 分析最新 KDJ 信号:")
    last_k = df['kdj_k'].iloc[-1]
    last_d = df['kdj_d'].iloc[-1]
    last_j = df['kdj_j'].iloc[-1]
    
    print(f"   K = {last_k:.2f}, D = {last_d:.2f}, J = {last_j:.2f}")
    
    if last_k < 20:
        print(f"   ⚠️  KDJ 处于超卖区 (K={last_k:.2f} < 20)")
    elif last_k > 80:
        print(f"   ⚠️  KDJ 处于超买区 (K={last_k:.2f} > 80)")
    else:
        print(f"   ○  KDJ 处于正常区间 (20 < K={last_k:.2f} < 80)")
    
    if last_k > last_d:
        print(f"   📈 K 线在 D 线上方 (K > D) - 看涨")
    else:
        print(f"   📉 K 线在 D 线下方 (K < D) - 看跌")


def example_2_kdj_signals():
    """示例 2: 生成包含 KDJ 的交易信号"""
    print("\n" + "=" * 70)
    print("示例 2: 生成包含 KDJ 的交易信号")
    print("=" * 70)
    
    print("\n1. 获取数据并计算指标...")
    fetcher = DataFetcher(['SLV'], '1h')
    df = fetcher.fetch_historical('SLV', days=10)
    
    if df.empty:
        print("   ✗ 无法获取数据，跳过...")
        return
    
    df = TechnicalIndicators.calculate_all_indicators(df)
    print(f"   ✓ 获取 {len(df)} 根 K线，计算指标完成")
    
    print("\n2. 生成交易信号...")
    strategy = ScalpingStrategy(rsi_oversold=30, rsi_overbought=70)
    signals = strategy.generate_signals(df, symbol='SLV')
    
    print(f"   ✓ 生成 {len(signals)} 个信号\n")
    
    if not signals:
        print("   (没有生成信号)")
        return
    
    print("3. 信号详情:")
    for i, signal in enumerate(signals[-5:], 1):  # 显示最后 5 个信号
        print(f"\n   信号 {i}:")
        print(f"   ├─ 类型: {signal.signal_type.name}")
        print(f"   ├─ 价格: ${signal.price:.2f}")
        print(f"   ├─ 置信度: {signal.confidence*100:.1f}%")
        print(f"   ├─ 原因: {signal.reason}")
        print(f"   └─ KDJ: K={signal.indicators['kdj_k']:.2f}, "
              f"D={signal.indicators['kdj_d']:.2f}, "
              f"J={signal.indicators['kdj_j']:.2f}")


def example_3_kdj_crossover():
    """示例 3: 检测 KDJ K/D 交叉"""
    print("\n" + "=" * 70)
    print("示例 3: 检测 KDJ K/D 交叉信号")
    print("=" * 70)
    
    print("\n1. 获取最近 20 天的日线数据...")
    fetcher = DataFetcher(['GLD'], '1d')
    df = fetcher.fetch_historical('GLD', days=20)
    
    if df.empty:
        print("   ✗ 无法获取数据，跳过...")
        return
    
    df = TechnicalIndicators.calculate_all_indicators(df)
    print(f"   ✓ 获取 {len(df)} 根 K线")
    
    print("\n2. 查找 K/D 交叉点:")
    
    kdj_k = df['kdj_k'].values
    kdj_d = df['kdj_d'].values
    
    crossovers = []
    for i in range(1, len(kdj_k)):
        prev_k, curr_k = kdj_k[i-1], kdj_k[i]
        prev_d, curr_d = kdj_d[i-1], kdj_d[i]
        
        # K 从下向上穿过 D (金叉 - 买入信号)
        if prev_k < prev_d and curr_k >= curr_d:
            crossovers.append({
                'type': '金叉 (买入)',
                'index': i,
                'k': curr_k,
                'd': curr_d,
                'price': df['close'].iloc[i],
            })
        
        # K 从上向下穿过 D (死叉 - 卖出信号)
        elif prev_k > prev_d and curr_k <= curr_d:
            crossovers.append({
                'type': '死叉 (卖出)',
                'index': i,
                'k': curr_k,
                'd': curr_d,
                'price': df['close'].iloc[i],
            })
    
    if crossovers:
        print(f"   ✓ 发现 {len(crossovers)} 个交叉点:\n")
        for co in crossovers:
            print(f"   └─ {co['type']}")
            print(f"      ├─ K={co['k']:.2f}, D={co['d']:.2f}")
            print(f"      └─ 价格: ${co['price']:.2f}\n")
    else:
        print("   (未发现交叉点)")


def example_4_kdj_zones():
    """示例 4: 分析 KDJ 区域分布"""
    print("\n" + "=" * 70)
    print("示例 4: 分析 KDJ 区域分布")
    print("=" * 70)
    
    print("\n1. 获取最近 30 天的数据...")
    fetcher = DataFetcher(['GLD'], '1h')
    df = fetcher.fetch_historical('GLD', days=30)
    
    if df.empty:
        print("   ✗ 无法获取数据，跳过...")
        return
    
    df = TechnicalIndicators.calculate_all_indicators(df)
    print(f"   ✓ 获取 {len(df)} 根 K线")
    
    kdj_k = df['kdj_k'].dropna()
    
    print(f"\n2. KDJ K 线统计:")
    print(f"   ├─ 最小值: {kdj_k.min():.2f}")
    print(f"   ├─ 最大值: {kdj_k.max():.2f}")
    print(f"   ├─ 平均值: {kdj_k.mean():.2f}")
    print(f"   └─ 当前值: {kdj_k.iloc[-1]:.2f}")
    
    print(f"\n3. KDJ 分布统计:")
    oversold = (kdj_k < 20).sum()
    overbought = (kdj_k > 80).sum()
    normal = ((kdj_k >= 20) & (kdj_k <= 80)).sum()
    
    total = len(kdj_k)
    
    print(f"   ├─ 超卖区 (K < 20): {oversold:3d} 根 ({oversold/total*100:5.1f}%)")
    print(f"   ├─ 正常区 (20 ≤ K ≤ 80): {normal:3d} 根 ({normal/total*100:5.1f}%)")
    print(f"   └─ 超买区 (K > 80): {overbought:3d} 根 ({overbought/total*100:5.1f}%)")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("KDJ 指标快速示例")
    print("Scalping Trading System - KDJ Examples")
    print("=" * 70)
    
    try:
        # 运行各个示例
        example_1_kdj_values()
        
        example_2_kdj_signals()
        
        example_3_kdj_crossover()
        
        example_4_kdj_zones()
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        print("\n提示: 请确保:")
        print("  1. 网络连接正常")
        print("  2. 所有依赖包已安装 (pip install -r requirements.txt)")
        print("  3. 数据可以正常下载")
    
    print("\n" + "=" * 70)
    print("示例完成!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
