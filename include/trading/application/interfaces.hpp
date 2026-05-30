#pragma once

#include "trading/domain/types.hpp"

#include <string>
#include <vector>

namespace trading {

struct RuntimeEvent {
    std::string timestamp;
    std::string level;
    std::string component;
    std::string message;
};

class IMarketDataSource {
public:
    virtual ~IMarketDataSource() = default;
    virtual std::vector<MarketSeries> load(const std::vector<std::string>& symbols) = 0;
};

class ITradingStore {
public:
    virtual ~ITradingStore() = default;

    virtual void initialize() = 0;
    virtual void save_market_series(const MarketSeries& series) = 0;
    virtual void save_backtest_result(const std::string& run_id,
                                      const std::string& symbol,
                                      const BacktestResult& result) = 0;
    virtual void save_runtime_event(const RuntimeEvent& event) = 0;
    virtual std::vector<RuntimeEvent> recent_events(int limit) = 0;
};

class ILogger {
public:
    virtual ~ILogger() = default;

    virtual void info(const std::string& component, const std::string& message) = 0;
    virtual void warn(const std::string& component, const std::string& message) = 0;
    virtual void error(const std::string& component, const std::string& message) = 0;
};

} // namespace trading
