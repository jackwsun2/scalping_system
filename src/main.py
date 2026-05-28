"""
主程序 - Main Entry Point
超短线量化交易系统的主程序
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from time import sleep

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    TRADING_CONFIG,
    ALPACA_CONFIG,
    STRATEGY_CONFIG,
    BACKTEST_CONFIG,
    TELEGRAM_CONFIG,
    RISK_CONFIG,
    LOG_CONFIG,
)
from data_fetcher import DataFetcher
from indicators import TechnicalIndicators
from strategy import ScalpingStrategy
from backtest import BacktestEngine
from executor import OrderExecutor
from alerts import AlertManager
from risk import RiskManager
from storage import TradingStore


def setup_logging():
    """配置日志"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG['level']),
        format=LOG_CONFIG['format'],
        handlers=[
            logging.FileHandler(LOG_CONFIG['file']),
            logging.StreamHandler(),
        ],
    )
    
    return logging.getLogger(__name__)


def run_backtest():
    """运行回测"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Starting Backtest Mode")
    logger.info("=" * 60)
    
    # 1. 获取数据
    logger.info(f"Fetching data for {TRADING_CONFIG['symbols']}...")
    data_fetcher = DataFetcher(
        symbols=TRADING_CONFIG['symbols'],
        interval=TRADING_CONFIG['interval'],
    )
    
    all_results = {}
    
    for symbol in TRADING_CONFIG['symbols']:
        logger.info(f"\n--- Processing {symbol} ---")
        
        # 获取历史数据
        df = data_fetcher.fetch_historical(
            symbol=symbol,
            start_date=BACKTEST_CONFIG['start_date'],
            end_date=BACKTEST_CONFIG['end_date'],
        )
        
        if df.empty or not data_fetcher.validate_data(df):
            logger.warning(f"Invalid data for {symbol}, skipping...")
            continue
        
        # 2. 计算技术指标
        logger.info("Calculating indicators...")
        df = TechnicalIndicators.calculate_all_indicators(df, STRATEGY_CONFIG)
        
        # 3. 生成信号
        logger.info("Generating signals...")
        strategy = ScalpingStrategy(STRATEGY_CONFIG)
        signals = strategy.generate_signals(df, symbol=symbol)
        logger.info(f"Generated {len(signals)} signals")
        
        # 4. 运行回测
        logger.info("Running backtest...")
        backtest_engine = BacktestEngine(BACKTEST_CONFIG)
        results = backtest_engine.run(
            df=df,
            signals=signals,
            quantity=TRADING_CONFIG['quantity'],
        )
        
        # 5. 输出结果
        logger.info("\n" + "=" * 60)
        logger.info(f"Backtest Results for {symbol}")
        logger.info("=" * 60)
        logger.info(f"Total Return: {results.total_return:+.2f}%")
        logger.info(f"Win Rate: {results.win_rate:.2f}%")
        logger.info(f"Total Trades: {results.total_trades}")
        logger.info(f"Winning Trades: {results.winning_trades}")
        logger.info(f"Losing Trades: {results.losing_trades}")
        logger.info(f"Avg Win: ${results.avg_win:.2f}")
        logger.info(f"Avg Loss: ${results.avg_loss:.2f}")
        logger.info(f"Profit Factor: {results.profit_factor:.2f}")
        logger.info(f"Max Drawdown: {results.max_drawdown:.2f}%")
        logger.info(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        logger.info(f"Sortino Ratio: {results.sortino_ratio:.2f}")
        
        # 输出前5个交易详情
        if results.trades:
            logger.info("\nFirst 5 Trades:")
            for i, trade in enumerate(results.trades[:5], 1):
                logger.info(
                    f"  Trade {i}: "
                    f"Entry: ${trade['entry_price']:.2f}, "
                    f"Exit: ${trade['exit_price']:.2f}, "
                    f"Profit: ${trade['profit']:+.2f} ({trade['profit_pct']:+.2f}%)"
                )
        
        all_results[symbol] = results
    
    logger.info("\n" + "=" * 60)
    logger.info("Backtest Complete")
    logger.info("=" * 60)
    
    return all_results


def run_live_trading():
    """运行实盘交易（模拟盘）"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Starting Live Trading Mode (Paper Trading)")
    logger.info("=" * 60)
    
    # 初始化组件
    data_fetcher = DataFetcher(
        symbols=TRADING_CONFIG['symbols'],
        interval=TRADING_CONFIG['interval'],
    )
    
    strategy = ScalpingStrategy(STRATEGY_CONFIG)
    executor = OrderExecutor(ALPACA_CONFIG, paper_trading=True)
    alert_manager = AlertManager(TELEGRAM_CONFIG)
    risk_manager = RiskManager(TRADING_CONFIG, RISK_CONFIG)
    store = TradingStore()
    
    logger.info("System initialized. Ready for live trading.")
    logger.info("Note: This is paper trading mode. No real money is at risk.")
    logger.info("\nMonitoring symbols: " + ", ".join(TRADING_CONFIG['symbols']))
    
    # 获取账户信息
    account_info = executor.get_account_info()
    if account_info:
        logger.info(f"Account Cash: ${account_info['cash']:.2f}")
        logger.info(f"Portfolio Value: ${account_info['portfolio_value']:.2f}")
    
    alert_manager.send_alert(
        "Trading System Started",
        f"System started in paper trading mode.\n"
        f"Monitoring: {', '.join(TRADING_CONFIG['symbols'])}"
    )

    poll_seconds = TRADING_CONFIG.get('live_poll_seconds', 300)
    max_cycles = TRADING_CONFIG.get('live_cycles', 1)
    cycle = 0

    while max_cycles is None or cycle < max_cycles:
        cycle += 1
        logger.info(f"Live scan cycle {cycle}")
        positions = executor.get_positions()
        account_info = executor.get_account_info()

        for symbol in TRADING_CONFIG['symbols']:
            df = data_fetcher.fetch_historical_data(symbol, interval=TRADING_CONFIG['interval'], days=5)
            if df.empty or not data_fetcher.validate_data(df):
                msg = f"Invalid or insufficient data for {symbol}"
                logger.warning(msg)
                alert_manager.send_error_alert(msg)
                continue

            df = TechnicalIndicators.calculate_all_indicators(df, STRATEGY_CONFIG)
            latest_signals = strategy.generate_latest_signals(df, symbol=symbol)

            for signal in latest_signals:
                store.record_signal(signal)
                alert_manager.send_trade_alert(signal)

                decision = risk_manager.evaluate(
                    signal=signal,
                    positions=positions,
                    account_info=account_info,
                    latest_bar_time=df.iloc[-1]['datetime'],
                )
                if not decision.approved:
                    logger.info(f"Signal blocked by risk manager: {symbol} {decision.reason}")
                    continue

                side = 'buy' if signal.signal_type.name == 'BUY' else 'sell'
                client_order_id = f"{symbol}-{side}-{int(pd_timestamp(signal.timestamp).timestamp())}"
                order = executor.submit_order(
                    symbol=symbol,
                    qty=decision.quantity,
                    side=side,
                    order_type='market',
                    client_order_id=client_order_id,
                )
                if order:
                    store.record_order(order, signal_timestamp=signal.timestamp)
                    logger.info(f"Recorded order {order.order_id} for {symbol}")

        if max_cycles is None or cycle < max_cycles:
            sleep(poll_seconds)
    
    return


def pd_timestamp(value):
    """Local helper to avoid importing pandas at module import time for CLI startup."""
    import pandas as pd
    return pd.to_datetime(value)


def main():
    """主程序"""
    logger = setup_logging()
    
    logger.info(f"\nScalping Trading System Started at {datetime.now()}")
    logger.info(f"Python Version: {sys.version}")
    
    # 选择运行模式
    mode = input("\nSelect mode:\n1. Backtest (历史回测)\n2. Live Trading (实盘/模拟盘)\nChoice (1 or 2): ").strip()
    
    if mode == '1':
        run_backtest()
    elif mode == '2':
        run_live_trading()
    else:
        logger.error("Invalid choice. Exiting.")
        sys.exit(1)
    
    logger.info(f"\nSystem stopped at {datetime.now()}")


if __name__ == '__main__':
    main()
