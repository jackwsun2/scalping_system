"""
Configuration settings for the scalping trading system
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Trading Parameters
SYMBOLS = ['GLD', 'SLV']  # ETFs to trade
TIMEFRAME = '1min'  # 1min, 5min
LOOKBACK_PERIODS = 100  # Historical data points to fetch

# Strategy Parameters
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# Risk Management
POSITION_SIZE = 100  # Number of shares per trade
STOP_LOSS_PERCENT = 2.0  # Stop loss percentage
TAKE_PROFIT_PERCENT = 1.5  # Take profit percentage
MAX_TRADES_PER_DAY = 5
MAX_DRAWDOWN_PERCENT = 5.0

# API Keys (from environment variables)
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'  # Paper trading URL

# Telegram Bot (for alerts)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Data Source
DATA_CACHE_DIR = './data_cache'
YFINANCE_INTERVAL = '1m'  # 1m, 5m, 1h, 1d

# Backtest Parameters
BACKTEST_START_DATE = '2023-01-01'
BACKTEST_END_DATE = '2024-01-01'
BACKTEST_INITIAL_CAPITAL = 10000

# System Parameters
LOG_LEVEL = 'INFO'
ENABLE_PAPER_TRADING = True  # Set to False for real trading
SIMULATION_MODE = True  # Simulate trading without executing
