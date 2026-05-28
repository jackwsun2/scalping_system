"""
配置文件示例 - Config Example
请复制此文件为 config.py 并填入你的真实参数
"""

# ===== 交易配置 Trading Config =====
TRADING_CONFIG = {
    # 美股ETF 代码，如 GLD, SLV, QQQ 等
    'symbols': ['GLD', 'SLV'],
    
    # 交易数据频率：1m (1分钟), 5m (5分钟), 1h (1小时), 1d (1天)
    'interval': '5m',
    
    # 每笔订单的股数
    'quantity': 10,
    
    # 最大持仓数量，用于风险控制
    'max_position': 100,

    # 模拟/实盘轮询配置
    'live_poll_seconds': 300,
    'live_cycles': 1,  # None 表示持续运行
}

# ===== Alpaca API 配置 (可选，用于实盘交易) =====
ALPACA_CONFIG = {
    # 获取地址: https://app.alpaca.markets/
    'api_key': 'YOUR_ALPACA_API_KEY',
    'secret_key': 'YOUR_ALPACA_SECRET_KEY',
    
    # 基础URL: 
    # 模拟盘: https://paper-api.alpaca.markets
    # 实盘: https://api.alpaca.markets
    'base_url': 'https://paper-api.alpaca.markets',  # 使用模拟盘
}

# ===== Telegram 推送配置 (可选) =====
TELEGRAM_CONFIG = {
    # 获取 token: https://t.me/botfather
    'bot_token': 'YOUR_TELEGRAM_BOT_TOKEN',
    
    # 获取 chat_id: 发送 /start 到你的 bot，然后查看日志
    'chat_id': 'YOUR_TELEGRAM_CHAT_ID',
    
    # 是否启用 Telegram 推送
    'enabled': False,
}

# ===== 策略参数 Strategy Parameters =====
STRATEGY_CONFIG = {
    # RSI 参数
    'rsi_period': 14,
    'rsi_oversold': 30,    # RSI < 30 作为买入信号
    'rsi_overbought': 70,  # RSI > 70 作为卖出信号
    
    # MACD 参数
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    
    # 布林带参数
    'bb_period': 20,
    'bb_std': 2,
    
    # KDJ 参数 (随机指标)
    'kdj_period': 9,        # KDJ 周期，默认 9
    'kdj_k_oversold': 20,   # K < 20 作为超卖信号
    'kdj_k_overbought': 80, # K > 80 作为超买信号
    
    # 止损参数
    'stop_loss_pct': 1.0,  # 止损点数（百分比）
    'take_profit_pct': 2.0,  # 止盈点数（百分比）
}

# ===== 风控参数 Risk Parameters =====
RISK_CONFIG = {
    # yfinance 分钟级数据常有延迟；实盘数据源应调低该值
    'max_data_delay_minutes': 15,

    # 是否允许盘前/盘后交易
    'allow_after_hours': False,

    # 单笔最大名义金额，None 表示不限制
    'max_notional_per_trade': None,
}

# ===== 回测参数 Backtest Parameters =====
BACKTEST_CONFIG = {
    # 初始资金
    'initial_cash': 10000.0,
    
    # 滑点（百分比）
    'slippage': 0.01,
    
    # 交易佣金（美元）
    'commission': 0.0,  # Alpaca 免佣金
    
    # 回测时间段
    'start_date': '2024-01-01',
    'end_date': '2024-12-31',
}

# ===== 日志配置 Logging Config =====
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/trading_system.log',
}
