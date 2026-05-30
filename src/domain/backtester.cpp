#include "trading/domain/backtester.hpp"
#include "trading/domain/indicators.hpp"
#include "trading/domain/risk.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <unordered_map>

namespace trading {

namespace {

double mark_to_market(double cash, const Position& position, double close)
{
    if (position.side == PositionSide::Long) {
        return cash + static_cast<double>(position.quantity) * close;
    }
    return cash;
}

double compute_max_drawdown(const std::vector<double>& equity_curve)
{
    if (equity_curve.empty()) {
        return 0.0;
    }
    double peak = equity_curve.front();
    double max_drawdown = 0.0;
    for (double equity : equity_curve) {
        peak = std::max(peak, equity);
        if (peak > 0.0) {
            max_drawdown = std::max(max_drawdown, (peak - equity) / peak);
        }
    }
    return max_drawdown * 100.0;
}

double compute_sharpe(const std::vector<double>& equity_curve)
{
    if (equity_curve.size() < 3) {
        return 0.0;
    }

    std::vector<double> returns;
    returns.reserve(equity_curve.size() - 1);
    for (std::size_t i = 1; i < equity_curve.size(); ++i) {
        if (equity_curve[i - 1] > 0.0) {
            returns.push_back((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]);
        }
    }
    if (returns.size() < 2) {
        return 0.0;
    }
    const double mean = std::accumulate(returns.begin(), returns.end(), 0.0) /
                        static_cast<double>(returns.size());
    double variance = 0.0;
    for (double value : returns) {
        const double diff = value - mean;
        variance += diff * diff;
    }
    variance /= static_cast<double>(returns.size() - 1);
    const double stdev = std::sqrt(variance);
    if (stdev <= 1e-12) {
        return 0.0;
    }
    return (mean / stdev) * std::sqrt(252.0 * 78.0);
}

} // namespace

Backtester::Backtester(ScalpingStrategy strategy, RiskManager risk_manager)
    : strategy_(strategy),
      risk_manager_(risk_manager)
{
}

BacktestResult Backtester::run(const MarketSeries& series) const
{
    BacktestResult result;
    result.initial_cash = risk_manager_.config().initial_cash;
    double cash = result.initial_cash;
    double realized_pnl = 0.0;
    double total_fees = 0.0;
    int trades_for_symbol = 0;
    Position position;
    position.symbol = series.symbol;

    const auto indicators = compute_indicators(series.bars, strategy_.config());
    result.equity_curve.reserve(series.bars.size());

    for (std::size_t i = 0; i < series.bars.size(); ++i) {
        const Bar& bar = series.bars[i];
        if (position.side == PositionSide::Long) {
            ++position.bars_held;
        }

        Signal signal = strategy_.evaluate(series.bars, indicators, i, position);

        if (position.side == PositionSide::Long &&
            signal.side != Side::Sell &&
            position.bars_held >= risk_manager_.config().max_bars_in_trade) {
            signal.side = Side::Sell;
            signal.reason = "MAX_HOLD_TIME";
        }

        if (signal.side == Side::Buy && position.side == PositionSide::Flat &&
            risk_manager_.can_enter(series.symbol, mark_to_market(cash, position, bar.close), realized_pnl, trades_for_symbol) &&
            risk_manager_.within_total_drawdown(mark_to_market(cash, position, bar.close))) {
            const double fill = risk_manager_.apply_buy_slippage(bar.close);
            const std::size_t quantity = risk_manager_.position_size(
                mark_to_market(cash, position, bar.close), fill, signal.stop_loss);
            const double cost = fill * static_cast<double>(quantity);
            const double fee = risk_manager_.commission(quantity);
            if (quantity > 0 && cost + fee <= cash) {
                cash -= cost + fee;
                total_fees += fee;
                position.side = PositionSide::Long;
                position.quantity = quantity;
                position.average_price = fill;
                position.stop_loss = signal.stop_loss;
                position.take_profit = signal.take_profit;
                position.entry_time = bar.timestamp;
                position.bars_held = 0;
                ++trades_for_symbol;
            }
        } else if (signal.side == Side::Sell && position.side == PositionSide::Long) {
            double exit_price = bar.close;
            if (signal.reason == "STOP_LOSS") {
                exit_price = position.stop_loss;
            } else if (signal.reason == "TAKE_PROFIT") {
                exit_price = position.take_profit;
            }
            const double fill = risk_manager_.apply_sell_slippage(exit_price);
            const double proceeds = fill * static_cast<double>(position.quantity);
            const double fee = risk_manager_.commission(position.quantity);
            total_fees += fee;
            cash += proceeds - fee;
            const double pnl = (fill - position.average_price) * static_cast<double>(position.quantity) -
                               fee - risk_manager_.commission(position.quantity);
            realized_pnl += pnl;

            Trade trade;
            trade.symbol = series.symbol;
            trade.entry_time = position.entry_time;
            trade.exit_time = bar.timestamp;
            trade.quantity = position.quantity;
            trade.entry_price = position.average_price;
            trade.exit_price = fill;
            trade.pnl = pnl;
            trade.exit_reason = signal.reason;
            result.trades.push_back(trade);

            position = Position{};
            position.symbol = series.symbol;
        }

        result.equity_curve.push_back(mark_to_market(cash, position, bar.close));
    }

    if (position.side == PositionSide::Long && !series.bars.empty()) {
        const Bar& bar = series.bars.back();
        const double fill = risk_manager_.apply_sell_slippage(bar.close);
        const double proceeds = fill * static_cast<double>(position.quantity);
        const double fee = risk_manager_.commission(position.quantity);
        total_fees += fee;
        cash += proceeds - fee;
        const double pnl = (fill - position.average_price) * static_cast<double>(position.quantity) -
                           fee - risk_manager_.commission(position.quantity);
        result.trades.push_back(Trade{series.symbol, position.entry_time, bar.timestamp,
                                      position.quantity, position.average_price, fill, pnl,
                                      "END_OF_DATA"});
        result.equity_curve.push_back(cash);
    }

    result.final_equity = result.equity_curve.empty() ? cash : result.equity_curve.back();
    result.net_profit = result.final_equity - result.initial_cash;
    result.total_return_pct = result.initial_cash > 0.0
        ? (result.final_equity - result.initial_cash) / result.initial_cash * 100.0
        : 0.0;
    result.max_drawdown_pct = compute_max_drawdown(result.equity_curve);
    result.sharpe_ratio = compute_sharpe(result.equity_curve);
    result.total_trades = result.trades.size();
    double gross_profit = 0.0;
    double gross_loss = 0.0;
    for (const auto& trade : result.trades) {
        if (trade.pnl > 0.0) {
            ++result.winning_trades;
            gross_profit += trade.pnl;
            result.largest_win = std::max(result.largest_win, trade.pnl);
        } else {
            ++result.losing_trades;
            gross_loss += -trade.pnl;
            result.largest_loss = std::min(result.largest_loss, trade.pnl);
        }
    }
    result.win_rate_pct = result.total_trades > 0
        ? static_cast<double>(result.winning_trades) / static_cast<double>(result.total_trades) * 100.0
        : 0.0;
    result.profit_factor = gross_loss > 1e-12 ? gross_profit / gross_loss : (gross_profit > 0.0 ? gross_profit : 0.0);
    result.average_trade_pnl = result.total_trades > 0
        ? result.net_profit / static_cast<double>(result.total_trades)
        : 0.0;
    result.average_win = result.winning_trades > 0
        ? gross_profit / static_cast<double>(result.winning_trades)
        : 0.0;
    result.average_loss = result.losing_trades > 0
        ? -gross_loss / static_cast<double>(result.losing_trades)
        : 0.0;
    result.total_fees = total_fees;
    return result;
}

void print_result_summary(const BacktestResult& result, const std::string& symbol)
{
    std::cout << "\n=== Backtest: " << symbol << " ===\n"
              << std::fixed << std::setprecision(2)
              << "Initial Cash : $" << result.initial_cash << "\n"
              << "Final Equity : $" << result.final_equity << "\n"
              << "Net Profit   : $" << result.net_profit << "\n"
              << "Return       : " << result.total_return_pct << "%\n"
              << "Max Drawdown : " << result.max_drawdown_pct << "%\n"
              << "Sharpe       : " << result.sharpe_ratio << "\n"
              << "ProfitFactor : " << result.profit_factor << "\n"
              << "Total Fees   : $" << result.total_fees << "\n"
              << "Trades       : " << result.total_trades << "\n"
              << "Win Rate     : " << result.win_rate_pct << "%\n";

    const std::size_t show = std::min<std::size_t>(result.trades.size(), 5);
    if (show > 0) {
        std::cout << "Recent Trades:\n";
        for (std::size_t i = result.trades.size() - show; i < result.trades.size(); ++i) {
            const auto& trade = result.trades[i];
            std::cout << "  " << trade.entry_time << " -> " << trade.exit_time
                      << " qty=" << trade.quantity
                      << " entry=" << trade.entry_price
                      << " exit=" << trade.exit_price
                      << " pnl=" << trade.pnl
                      << " reason=" << trade.exit_reason << "\n";
        }
    }
}

} // namespace trading
