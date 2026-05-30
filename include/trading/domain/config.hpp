#pragma once

#include "trading/types.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace trading {

struct StrategyConfig {
    std::string name = "RSI_MULTI_FACTOR";
    int rsi_period = 14;
    int macd_fast = 12;
    int macd_slow = 26;
    int macd_signal = 9;
    int bollinger_period = 20;
    double bollinger_stddev = 2.0;
    int atr_period = 14;
    int kdj_period = 9;
    int short_ma_period = 5;
    int long_ma_period = 20;
    double rsi_oversold = 32.0;
    double rsi_overbought = 68.0;
    double risk_reward = 1.8;
    double atr_stop_multiplier = 1.4;
    double fixed_stop_loss_pct = 0.0;
    double fixed_take_profit_pct = 0.0;
    double minimum_confidence = 0.58;
    double minimum_volume_ratio = 0.70;
    double min_atr_pct = 0.0005;
    double max_atr_pct = 0.045;
    bool require_trend_confirmation = true;
};

struct RiskConfig {
    double initial_cash = 100000.0;
    double risk_per_trade_pct = 0.005;
    double max_position_pct = 0.25;
    double max_daily_loss_pct = 0.03;
    double max_total_drawdown_pct = 0.15;
    int max_trades_per_symbol = 8;
    int max_bars_in_trade = 18;
    double commission_per_share = 0.0035;
    double slippage_bps = 1.5;
};

struct AppConfig {
    std::vector<std::string> symbols = {"GLD", "SLV"};
    TimeFrame timeframe = TimeFrame::Min5;
    std::string csv_path;
    std::string db_path = "scalping_system/runtime/trading.db";
    std::string log_dir = "scalping_system/logs";
    int log_retention_days = 7;
    bool live_simulation = false;
};

} // namespace trading
