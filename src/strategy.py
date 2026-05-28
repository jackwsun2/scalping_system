"""
Trading strategy implementation for scalping
"""
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Signal types"""
    BUY = 1
    SELL = -1
    HOLD = 0

@dataclass
class TradeSignal:
    """Represents a trading signal"""
    symbol: str
    signal_type: SignalType
    price: float
    timestamp: pd.Timestamp
    confidence: float  # 0.0 to 1.0
    reason: str
    indicators: dict  # Supporting indicator values

class ScalpingStrategy:
    """
    Scalping strategy using RSI, MACD, and Bollinger Bands
    Entry: RSI < 30 (oversold) and price breaks below lower Bollinger Band
    Exit: RSI > 70 (overbought) or price touches upper Bollinger Band
    """
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        min_confidence: float = 0.6
    ):
        """
        Initialize strategy
        
        Args:
            rsi_oversold: RSI oversold threshold for buy signals
            rsi_overbought: RSI overbought threshold for sell signals
            min_confidence: Minimum confidence level for signals
        """
        if isinstance(config, dict):
            self.rsi_oversold = config.get('rsi_oversold', rsi_oversold)
            self.rsi_overbought = config.get('rsi_overbought', rsi_overbought)
            self.min_confidence = config.get('min_confidence', min_confidence)
            self.kdj_oversold = config.get('kdj_k_oversold', 20)
            self.kdj_overbought = config.get('kdj_k_overbought', 80)
        else:
            self.rsi_oversold = config if isinstance(config, (int, float)) else rsi_oversold
            self.rsi_overbought = rsi_overbought
            self.min_confidence = min_confidence
            self.kdj_oversold = 20
            self.kdj_overbought = 80
    
    def generate_signals(
        self, 
        df: pd.DataFrame,
        symbol: str
    ) -> List[TradeSignal]:
        """
        Generate trading signals based on indicators
        
        Args:
            df: DataFrame with technical indicators
            symbol: Symbol being analyzed
            
        Returns:
            List of TradeSignal objects
        """
        signals = []
        
        if df.empty or len(df) < 2:
            return signals
        
        # Ensure all required indicators are present
        required_cols = ['rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_middle', 'bb_lower', 'close', 'kdj_k', 'kdj_d', 'kdj_j']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing indicators: {missing_cols}")
            return signals
        
        for i in range(1, len(df)):
            current = df.iloc[i]
            previous = df.iloc[i - 1]
            row_signals = self._generate_row_signals(current, previous, symbol)
            signals.extend(row_signals)
        
        return signals

    def generate_latest_signals(self, df: pd.DataFrame, symbol: str) -> List[TradeSignal]:
        """Generate signals only for the latest completed bar."""
        if df.empty or len(df) < 2:
            return []
        return self._generate_row_signals(df.iloc[-1], df.iloc[-2], symbol)

    def _generate_row_signals(self, current, previous, symbol: str) -> List[TradeSignal]:
        """Generate buy/sell signals for one row."""
        numeric_fields = ['close', 'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_middle', 'bb_lower']
        if any(pd.isna(current.get(field)) for field in numeric_fields):
            return []

        current_price = current['close']
        current_rsi = current['rsi']
        current_macd = current['macd']
        current_macd_signal = current['macd_signal']
        bb_upper = current['bb_upper']
        bb_middle = current['bb_middle']
        bb_lower = current['bb_lower']
        kdj_k = current.get('kdj_k', 0)
        kdj_d = current.get('kdj_d', 0)
        kdj_j = current.get('kdj_j', 0)

        signals = []
        buy_signal = self._check_buy_signal(
            current, previous, symbol, current_price,
            current_rsi, current_macd, current_macd_signal,
            bb_upper, bb_middle, bb_lower,
            kdj_k, kdj_d, kdj_j
        )
        if buy_signal:
            signals.append(buy_signal)

        sell_signal = self._check_sell_signal(
            current, previous, symbol, current_price,
            current_rsi, current_macd, current_macd_signal,
            bb_upper, bb_middle, bb_lower,
            kdj_k, kdj_d, kdj_j
        )
        if sell_signal:
            signals.append(sell_signal)

        return signals
    
    def _check_buy_signal(
        self, current, previous, symbol, price,
        rsi, macd, macd_signal, bb_upper, bb_middle, bb_lower,
        kdj_k, kdj_d, kdj_j
    ) -> Optional[TradeSignal]:
        """Check if buy conditions are met"""
        
        conditions = []
        confidence = 0.0
        
        # Condition 1: RSI oversold
        if rsi < self.rsi_oversold and rsi > 0:
            conditions.append(f"RSI={rsi:.2f} < {self.rsi_oversold}")
            confidence += 0.25
        
        # Condition 2: Price near lower Bollinger Band
        if bb_lower > 0 and price <= bb_lower * 1.01:  # Within 1% of lower band
            conditions.append(f"Price at lower BB (distance: {((price-bb_lower)/bb_lower*100):.2f}%)")
            confidence += 0.25
        
        # Condition 3: MACD positive crossover
        if previous is not None:
            prev_macd = previous['macd']
            prev_signal = previous['macd_signal']
            
            if prev_macd < prev_signal and macd > macd_signal:
                conditions.append("MACD crossed above signal")
                confidence += 0.15
        
        # Condition 4: Price below middle band (trend down before reversal)
        if price < bb_middle:
            conditions.append("Price below middle BB")
            confidence += 0.15
        
        # Condition 5: KDJ buy signal (K < 20 = oversold or K and J in low zone)
        if not pd.isna(kdj_k) and not pd.isna(kdj_d):
            if kdj_k < self.kdj_oversold and kdj_j < self.kdj_oversold:
                conditions.append(f"KDJ oversold (K={kdj_k:.2f}, J={kdj_j:.2f})")
                confidence += 0.2
            elif kdj_k > kdj_d and previous is not None:
                # KDJ bullish crossover (K crosses above D)
                prev_k = previous.get('kdj_k', 0)
                prev_d = previous.get('kdj_d', 0)
                if prev_k <= prev_d and not pd.isna(prev_k) and not pd.isna(prev_d):
                    conditions.append(f"KDJ K crossed above D (K={kdj_k:.2f}, D={kdj_d:.2f})")
                    confidence += 0.15
        
        if confidence >= self.min_confidence and len(conditions) > 0:
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=price,
                timestamp=self._extract_timestamp(current),
                confidence=min(confidence, 1.0),
                reason=" + ".join(conditions),
                indicators={
                    'rsi': float(rsi) if pd.notna(rsi) else 0,
                    'macd': float(macd) if pd.notna(macd) else 0,
                    'price': float(price),
                    'bb_lower': float(bb_lower) if pd.notna(bb_lower) else 0,
                    'vwap': float(current.get('vwap', 0)) if pd.notna(current.get('vwap', 0)) else 0,
                    'atr': float(current.get('atr', 0)) if pd.notna(current.get('atr', 0)) else 0,
                    'kdj_k': float(kdj_k) if pd.notna(kdj_k) else 0,
                    'kdj_d': float(kdj_d) if pd.notna(kdj_d) else 0,
                    'kdj_j': float(kdj_j) if pd.notna(kdj_j) else 0
                }
            )
        
        return None
    
    def _check_sell_signal(
        self, current, previous, symbol, price,
        rsi, macd, macd_signal, bb_upper, bb_middle, bb_lower,
        kdj_k, kdj_d, kdj_j
    ) -> Optional[TradeSignal]:
        """Check if sell conditions are met"""
        
        conditions = []
        confidence = 0.0
        
        # Condition 1: RSI overbought
        if rsi > self.rsi_overbought and rsi < 100:
            conditions.append(f"RSI={rsi:.2f} > {self.rsi_overbought}")
            confidence += 0.25
        
        # Condition 2: Price near upper Bollinger Band
        if bb_upper > 0 and price >= bb_upper * 0.99:  # Within 1% of upper band
            conditions.append(f"Price at upper BB (distance: {((bb_upper-price)/bb_upper*100):.2f}%)")
            confidence += 0.25
        
        # Condition 3: MACD negative crossover
        if previous is not None:
            prev_macd = previous['macd']
            prev_signal = previous['macd_signal']
            
            if prev_macd > prev_signal and macd < macd_signal:
                conditions.append("MACD crossed below signal")
                confidence += 0.15
        
        # Condition 4: Price above middle band (trend up)
        if price > bb_middle:
            conditions.append("Price above middle BB")
            confidence += 0.15
        
        # Condition 5: KDJ sell signal (K > 80 = overbought or K and J in high zone)
        if not pd.isna(kdj_k) and not pd.isna(kdj_d):
            if kdj_k > self.kdj_overbought and kdj_j > self.kdj_overbought:
                conditions.append(f"KDJ overbought (K={kdj_k:.2f}, J={kdj_j:.2f})")
                confidence += 0.2
            elif kdj_k < kdj_d and previous is not None:
                # KDJ bearish crossover (K crosses below D)
                prev_k = previous.get('kdj_k', 0)
                prev_d = previous.get('kdj_d', 0)
                if prev_k >= prev_d and not pd.isna(prev_k) and not pd.isna(prev_d):
                    conditions.append(f"KDJ K crossed below D (K={kdj_k:.2f}, D={kdj_d:.2f})")
                    confidence += 0.15
        
        if confidence >= self.min_confidence and len(conditions) > 0:
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                price=price,
                timestamp=self._extract_timestamp(current),
                confidence=min(confidence, 1.0),
                reason=" + ".join(conditions),
                indicators={
                    'rsi': float(rsi) if pd.notna(rsi) else 0,
                    'macd': float(macd) if pd.notna(macd) else 0,
                    'price': float(price),
                    'bb_upper': float(bb_upper) if pd.notna(bb_upper) else 0,
                    'vwap': float(current.get('vwap', 0)) if pd.notna(current.get('vwap', 0)) else 0,
                    'atr': float(current.get('atr', 0)) if pd.notna(current.get('atr', 0)) else 0,
                    'kdj_k': float(kdj_k) if pd.notna(kdj_k) else 0,
                    'kdj_d': float(kdj_d) if pd.notna(kdj_d) else 0,
                    'kdj_j': float(kdj_j) if pd.notna(kdj_j) else 0
                }
            )
        
        return None

    @staticmethod
    def _extract_timestamp(row) -> pd.Timestamp:
        if 'datetime' in row.index and pd.notna(row.get('datetime')):
            return pd.to_datetime(row.get('datetime'))
        if hasattr(row, 'name') and row.name is not None:
            return pd.to_datetime(row.name)
        return pd.Timestamp.now()
