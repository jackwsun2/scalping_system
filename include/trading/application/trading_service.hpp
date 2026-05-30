#pragma once

#include "trading/application/interfaces.hpp"
#include "trading/domain/backtester.hpp"
#include "trading/domain/config.hpp"
#include "trading/domain/risk.hpp"
#include "trading/domain/strategy.hpp"

#include <memory>
#include <string>
#include <vector>

namespace trading {

struct ServiceRunResult {
    std::vector<MarketSeries> markets;
    std::vector<BacktestResult> results;
};

class TradingService {
public:
    TradingService(std::shared_ptr<IMarketDataSource> data_source,
                   std::shared_ptr<ITradingStore> store,
                   std::shared_ptr<ILogger> logger,
                   StrategyConfig strategy_config = {},
                   RiskConfig risk_config = {});

    ServiceRunResult run_backtest(const std::vector<std::string>& symbols);
    ServiceRunResult run_backtest(const std::vector<std::string>& symbols,
                                  const StrategyConfig& strategy_config,
                                  const RiskConfig& risk_config);
    std::vector<MarketSeries> load_market_data(const std::vector<std::string>& symbols);
    std::vector<RuntimeEvent> recent_events(int limit);

    const StrategyConfig& strategy_config() const;
    const RiskConfig& risk_config() const;

private:
    std::string next_run_id() const;

    std::shared_ptr<IMarketDataSource> data_source_;
    std::shared_ptr<ITradingStore> store_;
    std::shared_ptr<ILogger> logger_;
    StrategyConfig strategy_config_;
    RiskConfig risk_config_;
};

} // namespace trading
