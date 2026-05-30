#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace trading {

enum class TimeFrame {
    Min1,
    Min5,
    Hour1,
    Day1
};

enum class Side {
    Buy,
    Sell,
    Hold
};

enum class OrderType {
    Market,
    Limit
};

enum class PositionSide {
    Flat,
    Long
};

struct Bar {
    std::string timestamp;
    std::string symbol;
    double open = 0.0;
    double high = 0.0;
    double low = 0.0;
    double close = 0.0;
    double volume = 0.0;
};

struct IndicatorSnapshot {
    double rsi = 50.0;
    double short_ma = 0.0;
    double long_ma = 0.0;
    double macd = 0.0;
    double macd_signal = 0.0;
    double macd_histogram = 0.0;
    double bollinger_upper = 0.0;
    double bollinger_middle = 0.0;
    double bollinger_lower = 0.0;
    double atr = 0.0;
    double k = 50.0;
    double d = 50.0;
    double j = 50.0;
    double vwap = 0.0;
};

struct Signal {
    Side side = Side::Hold;
    std::string reason = "WAIT";
    double confidence = 0.0;
    double stop_loss = 0.0;
    double take_profit = 0.0;
    IndicatorSnapshot indicators;
};

struct Order {
    std::string id;
    std::string timestamp;
    std::string symbol;
    Side side = Side::Hold;
    OrderType type = OrderType::Market;
    std::size_t quantity = 0;
    double requested_price = 0.0;
    double fill_price = 0.0;
    double commission = 0.0;
    std::string status = "new";
};

struct Trade {
    std::string symbol;
    std::string entry_time;
    std::string exit_time;
    std::size_t quantity = 0;
    double entry_price = 0.0;
    double exit_price = 0.0;
    double pnl = 0.0;
    std::string exit_reason;
};

struct Position {
    std::string symbol;
    PositionSide side = PositionSide::Flat;
    std::size_t quantity = 0;
    double average_price = 0.0;
    double stop_loss = 0.0;
    double take_profit = 0.0;
    std::string entry_time;
    int bars_held = 0;
};

struct BacktestResult {
    double initial_cash = 0.0;
    double final_equity = 0.0;
    double net_profit = 0.0;
    double total_return_pct = 0.0;
    double max_drawdown_pct = 0.0;
    double sharpe_ratio = 0.0;
    double win_rate_pct = 0.0;
    double profit_factor = 0.0;
    double average_trade_pnl = 0.0;
    double average_win = 0.0;
    double average_loss = 0.0;
    double largest_win = 0.0;
    double largest_loss = 0.0;
    double total_fees = 0.0;
    std::size_t total_trades = 0;
    std::size_t winning_trades = 0;
    std::size_t losing_trades = 0;
    std::vector<Trade> trades;
    std::vector<double> equity_curve;
};

struct MarketSeries {
    std::string symbol;
    std::vector<Bar> bars;
};

std::string to_string(Side side);
std::string to_string(TimeFrame timeframe);

} // namespace trading
