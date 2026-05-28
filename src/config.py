"""Configuration loading with environment variable overrides."""

import importlib.util
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def _load_module_from_path(path: Path):
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("trading_user_config", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_module = _load_module_from_path(CONFIG_DIR / "config.py") or _load_module_from_path(CONFIG_DIR / "example_config.py")


TRADING_CONFIG = getattr(_module, "TRADING_CONFIG", {
    'symbols': ['GLD'],
    'interval': '5m',
    'quantity': 10,
    'max_position': 100,
    'live_poll_seconds': 300,
    'live_cycles': 1,
})

ALPACA_CONFIG = getattr(_module, "ALPACA_CONFIG", {
    'api_key': os.getenv('ALPACA_API_KEY', 'YOUR_API_KEY'),
    'secret_key': os.getenv('ALPACA_SECRET_KEY', 'YOUR_SECRET_KEY'),
    'base_url': 'https://paper-api.alpaca.markets',
})
ALPACA_CONFIG = {
    **ALPACA_CONFIG,
    'api_key': os.getenv('ALPACA_API_KEY', ALPACA_CONFIG.get('api_key', 'YOUR_API_KEY')),
    'secret_key': os.getenv('ALPACA_SECRET_KEY', ALPACA_CONFIG.get('secret_key', 'YOUR_SECRET_KEY')),
}

TELEGRAM_CONFIG = getattr(_module, "TELEGRAM_CONFIG", {
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
    'enabled': False,
})
TELEGRAM_CONFIG = {
    **TELEGRAM_CONFIG,
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', TELEGRAM_CONFIG.get('bot_token', '')),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID', TELEGRAM_CONFIG.get('chat_id', '')),
}

STRATEGY_CONFIG = getattr(_module, "STRATEGY_CONFIG", {
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bb_period': 20,
    'bb_std': 2,
    'kdj_period': 9,
    'kdj_k_oversold': 20,
    'kdj_k_overbought': 80,
    'stop_loss_pct': 1.0,
    'take_profit_pct': 2.0,
})

BACKTEST_CONFIG = getattr(_module, "BACKTEST_CONFIG", {
    'initial_cash': 10000.0,
    'slippage': 0.01,
    'commission': 0.0,
    'start_date': '2024-01-01',
    'end_date': '2024-12-31',
})

RISK_CONFIG = getattr(_module, "RISK_CONFIG", {
    'max_data_delay_minutes': 15,
    'allow_after_hours': False,
    'max_notional_per_trade': None,
})

LOG_CONFIG = getattr(_module, "LOG_CONFIG", {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/trading_system.log',
})
