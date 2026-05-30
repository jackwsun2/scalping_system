#include "trading/backtester.hpp"
#include "trading/data_source.hpp"
#include "trading/indicators.hpp"
#include "trading/risk.hpp"
#include "trading/strategy.hpp"

#include <cassert>
#include <iostream>

int main()
{
    using namespace trading;

    const auto data = generate_sample_market_data({"GLD"}, 160);
    assert(data.size() == 1);
    assert(data.front().bars.size() == 160);

    StrategyConfig strategy_config;
    const auto indicators = compute_indicators(data.front().bars, strategy_config);
    assert(indicators.size() == data.front().bars.size());
    assert(indicators.back().atr > 0.0);
    assert(indicators.back().vwap > 0.0);
    assert(indicators.back().short_ma > 0.0);
    assert(indicators.back().long_ma > 0.0);

    ScalpingStrategy strategy(strategy_config);
    RiskManager risk_manager;
    Backtester backtester(strategy, risk_manager);
    const BacktestResult result = backtester.run(data.front());
    assert(result.initial_cash > 0.0);
    assert(result.final_equity > 0.0);
    assert(result.net_profit == result.final_equity - result.initial_cash);
    assert(result.total_fees >= 0.0);
    assert(!result.equity_curve.empty());

    StrategyConfig fixed_strategy_config;
    fixed_strategy_config.name = "RSI_ONLY";
    fixed_strategy_config.rsi_oversold = 101.0;
    fixed_strategy_config.fixed_stop_loss_pct = 0.5;
    fixed_strategy_config.fixed_take_profit_pct = 1.5;
    fixed_strategy_config.minimum_confidence = 0.5;
    ScalpingStrategy fixed_strategy(fixed_strategy_config);
    const auto fixed_indicators = compute_indicators(data.front().bars, fixed_strategy_config);
    const Signal fixed_signal = fixed_strategy.evaluate(
        data.front().bars, fixed_indicators, 40, Position{});
    assert(fixed_signal.side == Side::Buy);
    assert(fixed_signal.stop_loss < data.front().bars[40].close);
    assert(fixed_signal.take_profit > data.front().bars[40].close);

    auto invalid_bars = data.front().bars;
    invalid_bars[40].high = invalid_bars[40].low - 1.0;
    const Signal invalid_signal = fixed_strategy.evaluate(
        invalid_bars, fixed_indicators, 40, Position{});
    assert(invalid_signal.side == Side::Hold);
    assert(invalid_signal.reason == "INVALID_BAR");

    RiskConfig tight_risk_config;
    tight_risk_config.max_total_drawdown_pct = 0.01;
    RiskManager tight_risk(tight_risk_config);
    assert(tight_risk.within_total_drawdown(tight_risk_config.initial_cash));
    assert(!tight_risk.within_total_drawdown(tight_risk_config.initial_cash * 0.98));

    std::cout << "trading_tests passed\n";
    return 0;
}
