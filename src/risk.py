"""Risk checks for paper/live trading."""

from dataclasses import dataclass
from datetime import time
from typing import Dict, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from strategy import SignalType


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    quantity: int = 0


class RiskManager:
    """Pre-trade guard rails for a small scalping system."""

    def __init__(self, trading_config: Dict, risk_config: Optional[Dict] = None):
        self.trading_config = trading_config or {}
        self.risk_config = risk_config or {}
        self.max_position = self.trading_config.get('max_position', 100)
        self.default_quantity = self.trading_config.get('quantity', 1)
        self.max_data_delay_minutes = self.risk_config.get('max_data_delay_minutes', 15)
        self.allow_after_hours = self.risk_config.get('allow_after_hours', False)
        self.max_notional_per_trade = self.risk_config.get('max_notional_per_trade', None)

    def evaluate(
        self,
        signal,
        positions: Dict[str, int],
        account_info: Optional[Dict],
        latest_bar_time,
    ) -> RiskDecision:
        """Return whether a signal is allowed to become an order."""
        if signal.signal_type == SignalType.HOLD:
            return RiskDecision(False, "hold signal")

        if not self.allow_after_hours and not self.is_regular_market_hours(latest_bar_time):
            return RiskDecision(False, "outside regular market hours")

        if not self.is_data_fresh(latest_bar_time):
            return RiskDecision(False, "market data is stale")

        quantity = int(self.default_quantity)
        current_position = int(positions.get(signal.symbol, 0))

        if signal.signal_type == SignalType.BUY:
            if current_position + quantity > self.max_position:
                return RiskDecision(False, "max position would be exceeded")

            cash = float((account_info or {}).get('cash', 0))
            notional = signal.price * quantity
            if self.max_notional_per_trade and notional > self.max_notional_per_trade:
                return RiskDecision(False, "max notional per trade would be exceeded")
            if cash and notional > cash:
                return RiskDecision(False, "insufficient cash")

        if signal.signal_type == SignalType.SELL and current_position <= 0:
            return RiskDecision(False, "no long position to sell")

        return RiskDecision(True, "approved", quantity)

    def is_data_fresh(self, latest_bar_time) -> bool:
        latest = pd.to_datetime(latest_bar_time)
        if latest.tzinfo is None:
            latest = latest.tz_localize('UTC')
        now = pd.Timestamp.now(tz=latest.tzinfo)
        delay_minutes = (now - latest).total_seconds() / 60
        return delay_minutes <= self.max_data_delay_minutes

    @staticmethod
    def is_regular_market_hours(dt_value) -> bool:
        dt = pd.to_datetime(dt_value)
        if dt.tzinfo is None:
            dt = dt.tz_localize('UTC')
        eastern = dt.tz_convert(ZoneInfo("America/New_York"))
        if eastern.weekday() >= 5:
            return False
        return time(9, 30) <= eastern.to_pydatetime().time() <= time(16, 0)
