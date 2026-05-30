#include "trading/live_simulator.hpp"
#include "trading/indicators.hpp"

#include <chrono>
#include <iomanip>
#include <iostream>
#include <thread>

namespace trading {

void run_live_simulation(const MarketSeries& series,
                         const ScalpingStrategy& strategy,
                         const RiskManager& risk_manager,
                         int delay_ms)
{
    std::cout << "\n=== Live Simulation: " << series.symbol << " ===\n";
    std::cout << "mode=paper timeframe=5m broker=simulated data=replay\n";

    const auto indicators = compute_indicators(series.bars, strategy.config());
    Position position;
    position.symbol = series.symbol;
    double cash = risk_manager.config().initial_cash;
    int trades = 0;

    for (std::size_t i = 0; i < series.bars.size(); ++i) {
        const auto& bar = series.bars[i];
        Signal signal = strategy.evaluate(series.bars, indicators, i, position);

        std::cout << std::fixed << std::setprecision(2)
                  << bar.timestamp << ' '
                  << bar.symbol
                  << " close=" << bar.close
                  << " rsi=" << signal.indicators.rsi
                  << " macd_hist=" << signal.indicators.macd_histogram
                  << " signal=" << to_string(signal.side)
                  << " confidence=" << signal.confidence
                  << " reason=" << signal.reason << "\n";

        if (signal.side == Side::Buy && position.side == PositionSide::Flat &&
            risk_manager.can_enter(series.symbol, cash, 0.0, trades) &&
            risk_manager.within_total_drawdown(cash)) {
            const double fill = risk_manager.apply_buy_slippage(bar.close);
            const std::size_t qty = risk_manager.position_size(cash, fill, signal.stop_loss);
            if (qty > 0) {
                cash -= fill * static_cast<double>(qty) + risk_manager.commission(qty);
                position.side = PositionSide::Long;
                position.quantity = qty;
                position.average_price = fill;
                position.stop_loss = signal.stop_loss;
                position.take_profit = signal.take_profit;
                position.entry_time = bar.timestamp;
                ++trades;
                std::cout << "  PAPER_ORDER BUY qty=" << qty
                          << " fill=" << fill
                          << " stop=" << position.stop_loss
                          << " target=" << position.take_profit << "\n";
            }
        } else if (signal.side == Side::Sell && position.side == PositionSide::Long) {
            const double fill = risk_manager.apply_sell_slippage(bar.close);
            cash += fill * static_cast<double>(position.quantity) -
                    risk_manager.commission(position.quantity);
            std::cout << "  PAPER_ORDER SELL qty=" << position.quantity
                      << " fill=" << fill
                      << " cash=" << cash << "\n";
            position = Position{};
            position.symbol = series.symbol;
        }

        if (delay_ms > 0) {
            std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
        }
    }
}

} // namespace trading
