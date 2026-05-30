#pragma once

#include "trading/backtester.hpp"
#include "trading/types.hpp"

namespace trading {

void run_live_simulation(const MarketSeries& series,
                         const ScalpingStrategy& strategy,
                         const RiskManager& risk_manager,
                         int delay_ms);

} // namespace trading
