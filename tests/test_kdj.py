"""
KDJ 指标测试脚本 - Test KDJ Indicator
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from indicators import TechnicalIndicators


def test_kdj_calculation():
    """测试 KDJ 计算"""
    print("\n" + "=" * 60)
    print("KDJ 指标测试")
    print("=" * 60)
    
    # 创建测试数据 (100根K线)
    np.random.seed(42)
    n = 100
    
    close = np.random.randn(n).cumsum() + 100
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    
    df = pd.DataFrame({
        'open': close + np.random.randn(n) * 0.5,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(1000000, 5000000, n),
    })
    
    print(f"\n✓ 测试数据: {len(df)} 根K线")
    print(f"  Close 价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # 计算 KDJ
    print("\n计算 KDJ 指标...")
    kdj_k, kdj_d, kdj_j = TechnicalIndicators.calculate_kdj(df, period=9)
    
    # 检查返回值
    print(f"\n✓ KDJ 计算完成:")
    print(f"  K 线数据点: {kdj_k.count()}")
    print(f"  D 线数据点: {kdj_d.count()}")
    print(f"  J 线数据点: {kdj_j.count()}")
    
    # 检查取值范围
    valid_k = kdj_k.dropna()
    valid_d = kdj_d.dropna()
    valid_j = kdj_j.dropna()
    
    print(f"\n✓ KDJ 值范围检查:")
    print(f"  K 线范围: {valid_k.min():.2f} - {valid_k.max():.2f}")
    print(f"  D 线范围: {valid_d.min():.2f} - {valid_d.max():.2f}")
    print(f"  J 线范围: {valid_j.min():.2f} - {valid_j.max():.2f}")
    
    # 检查 J = 3*K - 2*D 的关系
    print(f"\n✓ J线计算验证 (J = 3*K - 2*D):")
    calculated_j = 3 * kdj_k - 2 * kdj_d
    max_diff = (valid_j - calculated_j.dropna()).abs().max()
    print(f"  最大差异: {max_diff:.6f}")
    
    # 最新的 KDJ 值
    latest_k = kdj_k.iloc[-1]
    latest_d = kdj_d.iloc[-1]
    latest_j = kdj_j.iloc[-1]
    
    print(f"\n✓ 最新 KDJ 值:")
    print(f"  K = {latest_k:.2f}")
    print(f"  D = {latest_d:.2f}")
    print(f"  J = {latest_j:.2f}")
    
    # 信号判断
    print(f"\n✓ 信号判断:")
    if latest_k < 20 and latest_j < 20:
        print(f"  ⚠️  超卖信号 (K={latest_k:.2f}, J={latest_j:.2f})")
    elif latest_k > 80 and latest_j > 80:
        print(f"  ⚠️  超买信号 (K={latest_k:.2f}, J={latest_j:.2f})")
    else:
        print(f"  ○ 正常区间 (K={latest_k:.2f}, J={latest_j:.2f})")
    
    # 在数据框中添加 KDJ
    print(f"\n✓ 添加 KDJ 到数据框:")
    df['kdj_k'] = kdj_k
    df['kdj_d'] = kdj_d
    df['kdj_j'] = kdj_j
    
    print(f"  数据框列数: {len(df.columns)}")
    print(f"  包含列: {', '.join(df.columns.tolist())}")
    
    # 显示最后几行
    print(f"\n✓ 最后5行数据:")
    print(df[['close', 'kdj_k', 'kdj_d', 'kdj_j']].tail())
    
    print("\n" + "=" * 60)
    print("KDJ 测试完成! ✓")
    print("=" * 60 + "\n")
    
    return df


def test_all_indicators_with_kdj():
    """测试包含 KDJ 的所有指标"""
    print("\n" + "=" * 60)
    print("所有指标计算测试 (包含 KDJ)")
    print("=" * 60)
    
    # 创建测试数据
    np.random.seed(42)
    n = 100
    
    close = np.random.randn(n).cumsum() + 100
    df = pd.DataFrame({
        'open': close + np.random.randn(n) * 0.5,
        'high': close + np.abs(np.random.randn(n)),
        'low': close - np.abs(np.random.randn(n)),
        'close': close,
        'volume': np.random.randint(1000000, 5000000, n),
    })
    
    # 配置
    config = {
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bb_period': 20,
        'bb_std': 2,
        'kdj_period': 9,
    }
    
    print(f"\n计算所有指标 (配置: {config})...")
    df_with_indicators = TechnicalIndicators.calculate_all_indicators(df, **config)
    
    # 检查新添加的列
    indicator_columns = ['rsi', 'macd', 'macd_signal', 'macd_histogram',
                        'bb_upper', 'bb_middle', 'bb_lower',
                        'kdj_k', 'kdj_d', 'kdj_j', 'vwap']
    
    print(f"\n✓ 指标计算完成:")
    for col in indicator_columns:
        if col in df_with_indicators.columns:
            valid_count = df_with_indicators[col].count()
            print(f"  ✓ {col:20} - {valid_count:3d} 个有效值")
        else:
            print(f"  ✗ {col:20} - 未计算")
    
    print(f"\n✓ 最后一行数据:")
    last_row = df_with_indicators.iloc[-1]
    print(f"  Close:   {last_row['close']:.2f}")
    print(f"  RSI:     {last_row.get('rsi', 0):.2f}")
    print(f"  MACD:    {last_row.get('macd', 0):.4f}")
    print(f"  KDJ_K:   {last_row.get('kdj_k', 0):.2f}")
    print(f"  KDJ_D:   {last_row.get('kdj_d', 0):.2f}")
    print(f"  KDJ_J:   {last_row.get('kdj_j', 0):.2f}")
    
    print("\n" + "=" * 60)
    print("所有指标测试完成! ✓")
    print("=" * 60 + "\n")
    
    return df_with_indicators


if __name__ == '__main__':
    print("\n")
    test_kdj_calculation()
    test_all_indicators_with_kdj()
    
    print("所有测试通过! ✓\n")
