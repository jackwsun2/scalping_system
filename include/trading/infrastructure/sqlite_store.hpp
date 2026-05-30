#pragma once

#include "trading/application/interfaces.hpp"

#include <sqlite3.h>

#include <string>
#include <vector>

namespace trading {

class SqliteTradingStore final : public ITradingStore {
public:
    explicit SqliteTradingStore(std::string db_path);
    ~SqliteTradingStore() override;

    SqliteTradingStore(const SqliteTradingStore&) = delete;
    SqliteTradingStore& operator=(const SqliteTradingStore&) = delete;

    void initialize() override;
    void save_market_series(const MarketSeries& series) override;
    void save_backtest_result(const std::string& run_id,
                              const std::string& symbol,
                              const BacktestResult& result) override;
    void save_runtime_event(const RuntimeEvent& event) override;
    std::vector<RuntimeEvent> recent_events(int limit) override;

private:
    void open();
    void exec(const std::string& sql);

    std::string db_path_;
    sqlite3* db_ = nullptr;
};

} // namespace trading
