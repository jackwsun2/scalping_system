"""
技术指标单元测试 - Unit Tests for Indicators
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from indicators import TechnicalIndicators


def test_rsi_calculation():
    """测试 RSI 计算"""
    # 创建简单的测试数据
    prices = pd.Series([100, 101, 102, 103, 104, 105, 104, 103, 102, 101,
                       100, 99, 98, 99, 100, 101, 102, 103, 104, 105])
    df = pd.DataFrame({'close': prices})
    
    rsi = TechnicalIndicators.calculate_rsi(df, period=14)
    
    # RSI 应该返回 Series
    assert isinstance(rsi, pd.Series), "RSI should return a pandas Series"
    
    # RSI 值应该在 0-100 之间
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all(), "RSI values should be between 0 and 100"
    
    print("✓ RSI calculation test passed")


def test_macd_calculation():
    """测试 MACD 计算"""
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    df = pd.DataFrame({'close': prices})
    
    macd_line, signal_line, histogram = TechnicalIndicators.calculate_macd(
        df, fast=12, slow=26, signal=9
    )
    
    # 检查返回类型
    assert isinstance(macd_line, pd.Series), "MACD line should be a Series"
    assert isinstance(signal_line, pd.Series), "Signal line should be a Series"
    assert isinstance(histogram, pd.Series), "Histogram should be a Series"
    
    print("✓ MACD calculation test passed")


def test_bollinger_bands_calculation():
    """测试布林带计算"""
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    df = pd.DataFrame({'close': prices})
    
    upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
        df, period=20, std_dev=2
    )
    
    # 检查返回类型
    assert isinstance(upper, pd.Series), "Upper band should be a Series"
    assert isinstance(middle, pd.Series), "Middle band should be a Series"
    assert isinstance(lower, pd.Series), "Lower band should be a Series"
    
    # 布林带上 > 中 > 下
    valid_indices = ~(upper.isna() | middle.isna() | lower.isna())
    assert (upper[valid_indices] > middle[valid_indices]).all(), "Upper band should be > middle band"
    assert (middle[valid_indices] > lower[valid_indices]).all(), "Middle band should be > lower band"
    
    print("✓ Bollinger Bands calculation test passed")


def test_atr_calculation():
    """测试 ATR 计算"""
    df = pd.DataFrame({
        'high': np.random.rand(100) * 10 + 100,
        'low': np.random.rand(100) * 10 + 90,
        'close': np.random.rand(100) * 10 + 95,
    })
    
    atr = TechnicalIndicators.calculate_atr(df, period=14)
    
    # ATR 应该返回 Series
    assert isinstance(atr, pd.Series), "ATR should return a pandas Series"
    
    # ATR 值应该为正
    valid_atr = atr.dropna()
    assert (valid_atr > 0).all(), "ATR values should be positive"
    
    print("✓ ATR calculation test passed")


def test_all_indicators():
    """测试所有指标的综合计算"""
    # 创建完整的 OHLCV 数据
    n = 100
    df = pd.DataFrame({
        'open': np.random.rand(n) * 10 + 100,
        'high': np.random.rand(n) * 10 + 102,
        'low': np.random.rand(n) * 10 + 98,
        'close': np.random.rand(n) * 10 + 100,
        'volume': np.random.randint(1000000, 5000000, n),
    })
    
    config = {
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bb_period': 20,
        'bb_std': 2,
    }
    
    result = TechnicalIndicators.calculate_all_indicators(df, config)
    
    # 检查所有指标列是否存在
    required_columns = ['rsi', 'macd', 'macd_signal', 'macd_histogram',
                       'bb_upper', 'bb_middle', 'bb_lower', 'atr']
    
    for col in required_columns:
        assert col in result.columns, f"Column {col} not found in result"
    
    print("✓ All indicators calculation test passed")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Running Indicator Tests")
    print("=" * 60 + "\n")
    
    test_rsi_calculation()
    test_macd_calculation()
    test_bollinger_bands_calculation()
    test_atr_calculation()
    test_all_indicators()
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
