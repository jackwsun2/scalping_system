"""Technical indicator calculations."""

import pandas as pd
import logging
from typing import Dict, Optional, Tuple

try:
    import pandas_ta as ta
except Exception:  # pragma: no cover - fallback keeps tests usable without pandas-ta
    ta = None

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Calculate and manage technical indicators"""
    
    @staticmethod
    def calculate_rsi(
        df: pd.DataFrame, 
        period: int = 14, 
        column: str = 'close'
    ) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            df: DataFrame with price data
            period: RSI period (default 14)
            column: Column to calculate RSI on
            
        Returns:
            Series with RSI values
        """
        if df.empty or column not in df.columns:
            return pd.Series()
        
        if ta is not None:
            rsi = ta.rsi(df[column], length=period)
            if rsi is not None:
                return rsi

        delta = df[column].diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
        rs = gain / loss.replace(0, pd.NA)
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        column: str = 'close'
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            df: DataFrame with price data
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            column: Column to calculate on
            
        Returns:
            Tuple of (MACD, Signal, Histogram)
        """
        if df.empty or column not in df.columns:
            return pd.Series(), pd.Series(), pd.Series()
        
        if ta is not None:
            macd = ta.macd(df[column], fast=fast, slow=slow, signal=signal)
            if macd is not None and not macd.empty:
                macd_line = macd.iloc[:, 0] if macd.shape[1] > 0 else pd.Series(index=df.index)
                histogram = macd.iloc[:, 1] if macd.shape[1] > 1 else pd.Series(index=df.index)
                signal_line = macd.iloc[:, 2] if macd.shape[1] > 2 else pd.Series(index=df.index)
                return macd_line, signal_line, histogram

        ema_fast = df[column].ewm(span=fast, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = 'close'
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Args:
            df: DataFrame with price data
            period: Moving average period
            std_dev: Standard deviation multiplier
            column: Column to calculate on
            
        Returns:
            Tuple of (Upper Band, Middle Band, Lower Band)
        """
        if df.empty or column not in df.columns:
            return pd.Series(), pd.Series(), pd.Series()
        
        if ta is not None:
            bb = ta.bbands(df[column], length=period, std=std_dev)
            if bb is not None and not bb.empty:
                upper = bb.iloc[:, 2] if bb.shape[1] > 2 else pd.Series(index=df.index)
                middle = bb.iloc[:, 1] if bb.shape[1] > 1 else pd.Series(index=df.index)
                lower = bb.iloc[:, 0] if bb.shape[1] > 0 else pd.Series(index=df.index)
                return upper, middle, lower

        middle = df[column].rolling(period).mean()
        std = df[column].rolling(period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper, middle, lower
    
    @staticmethod
    def calculate_volume_weighted_average_price(
        df: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate VWAP (Volume Weighted Average Price)
        
        Args:
            df: DataFrame with price and volume data
            
        Returns:
            Series with VWAP values
        """
        if df.empty or 'close' not in df.columns or 'volume' not in df.columns:
            return pd.Series()
        
        high = df['high'] if 'high' in df.columns else df['close']
        low = df['low'] if 'low' in df.columns else df['close']
        typical_price = (high + low + df['close']) / 3

        if ta is not None:
            try:
                vwap = ta.vwap(high=high, low=low, close=df['close'], volume=df['volume'])
                if vwap is not None:
                    return vwap
            except Exception as e:
                logger.debug(f"pandas-ta VWAP failed, using fallback: {e}")

        volume = df['volume'].replace(0, pd.NA)
        return (typical_price * volume).cumsum() / volume.cumsum()

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        required = {'high', 'low', 'close'}
        if df.empty or not required.issubset(df.columns):
            return pd.Series()

        if ta is not None:
            atr = ta.atr(df['high'], df['low'], df['close'], length=period)
            if atr is not None:
                return atr

        previous_close = df['close'].shift(1)
        tr = pd.concat(
            [
                df['high'] - df['low'],
                (df['high'] - previous_close).abs(),
                (df['low'] - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return tr.rolling(period).mean()
    
    @staticmethod
    def calculate_kdj(
        df: pd.DataFrame,
        period: int = 9,
        k_smooth: int = 3,
        d_smooth: int = 3,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate KDJ (Stochastic Oscillator)
        
        Args:
            df: DataFrame with OHLCV data
            period: Lookback period (default 9)
            k_smooth: K line smoothing period (default 3)
            d_smooth: D line smoothing period (default 3)
            
        Returns:
            Tuple of (K, D, J) series
        """
        try:
            if df.empty or 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
                return pd.Series(), pd.Series(), pd.Series()
            
            if ta is not None:
                stoch = ta.stoch(
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    k=period,
                    d=d_smooth,
                    smooth_k=k_smooth,
                )
                if stoch is not None and not stoch.empty:
                    k_line = stoch.iloc[:, 0] if stoch.shape[1] > 0 else pd.Series(index=df.index)
                    d_line = stoch.iloc[:, 1] if stoch.shape[1] > 1 else pd.Series(index=df.index)
                    j_line = 3 * k_line - 2 * d_line
                    return k_line, d_line, j_line

            lowest_low = df['low'].rolling(period).min()
            highest_high = df['high'].rolling(period).max()
            rsv = (df['close'] - lowest_low) / (highest_high - lowest_low).replace(0, pd.NA) * 100
            k_line = rsv.rolling(k_smooth).mean()
            d_line = k_line.rolling(d_smooth).mean()
            j_line = 3 * k_line - 2 * d_line
            return k_line, d_line, j_line
            
        except Exception as e:
            logger.error(f"Error calculating KDJ: {str(e)}")
            return pd.Series(), pd.Series(), pd.Series()
    
    @staticmethod
    def add_all_indicators(
        df: pd.DataFrame,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        kdj_period: int = 9,
        atr_period: int = 14,
    ) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame
        
        Args:
            df: DataFrame with OHLCV data
            rsi_period: RSI period
            macd_fast: MACD fast period
            macd_slow: MACD slow period
            macd_signal: MACD signal period
            bb_period: Bollinger Band period
            bb_std: Bollinger Band standard deviation
            
        Returns:
            DataFrame with indicators added
        """
        if df.empty:
            return df
        
        df_copy = df.copy()
        
        # Normalize column names
        df_copy.columns = [col.lower() for col in df_copy.columns]
        
        # Calculate RSI
        df_copy['rsi'] = TechnicalIndicators.calculate_rsi(
            df_copy, period=rsi_period
        )
        
        # Calculate MACD
        macd, signal, histogram = TechnicalIndicators.calculate_macd(
            df_copy, fast=macd_fast, slow=macd_slow, signal=macd_signal
        )
        df_copy['macd'] = macd
        df_copy['macd_signal'] = signal
        df_copy['macd_histogram'] = histogram
        
        # Calculate Bollinger Bands
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
            df_copy, period=bb_period, std_dev=bb_std
        )
        df_copy['bb_upper'] = upper
        df_copy['bb_middle'] = middle
        df_copy['bb_lower'] = lower
        
        # Calculate KDJ
        k_line, d_line, j_line = TechnicalIndicators.calculate_kdj(
            df_copy, period=kdj_period
        )
        df_copy['kdj_k'] = k_line
        df_copy['kdj_d'] = d_line
        df_copy['kdj_j'] = j_line
        
        # Calculate VWAP
        df_copy['vwap'] = TechnicalIndicators.calculate_volume_weighted_average_price(
            df_copy
        )

        # Calculate ATR
        df_copy['atr'] = TechnicalIndicators.calculate_atr(df_copy, period=atr_period)
        
        return df_copy

    @staticmethod
    def calculate_all_indicators(
        df: pd.DataFrame,
        config: Optional[Dict] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Compatibility wrapper used by main/tests."""
        params = {}
        if config:
            params.update(config)
        params.update(kwargs)

        return TechnicalIndicators.add_all_indicators(
            df,
            rsi_period=params.get('rsi_period', 14),
            macd_fast=params.get('macd_fast', 12),
            macd_slow=params.get('macd_slow', 26),
            macd_signal=params.get('macd_signal', 9),
            bb_period=params.get('bb_period', 20),
            bb_std=params.get('bb_std', 2.0),
            kdj_period=params.get('kdj_period', 9),
            atr_period=params.get('atr_period', 14),
        )
