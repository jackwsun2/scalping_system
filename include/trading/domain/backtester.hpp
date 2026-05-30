#pragma once

#include "trading/domain/config.hpp"
#include "trading/domain/risk.hpp"
#include "trading/domain/strategy.hpp"
#include "trading/domain/types.hpp"

namespace trading {

class Backtester {
public:
    Backtester(ScalpingStrategy strategy, RiskManager risk_manager);

    BacktestResult run(const MarketSeries& series) const;

private:
    ScalpingStrategy strategy_;
    RiskManager risk_manager_;
};

void print_result_summary(const BacktestResult& result, const std::string& symbol);

} // namespace trading
