#include "trading/application/trading_service.hpp"

#include <chrono>
#include <iomanip>
#include <sstream>

namespace trading {

namespace {

std::string compact_timestamp()
{
    const auto now = std::chrono::system_clock::now();
    const auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()).count();
    return std::to_string(millis);
}

} // namespace

TradingService::TradingService(std::shared_ptr<IMarketDataSource> data_source,
                               std::shared_ptr<ITradingStore> store,
                               std::shared_ptr<ILogger> logger,
                               StrategyConfig strategy_config,
                               RiskConfig risk_config)
    : data_source_(std::move(data_source)),
      store_(std::move(store)),
      logger_(std::move(logger)),
      strategy_config_(strategy_config),
      risk_config_(risk_config)
{
    store_->initialize();
}

ServiceRunResult TradingService::run_backtest(const std::vector<std::string>& symbols)
{
    return run_backtest(symbols, strategy_config_, risk_config_);
}

ServiceRunResult TradingService::run_backtest(const std::vector<std::string>& symbols,
                                              const StrategyConfig& strategy_config,
                                              const RiskConfig& risk_config)
{
    logger_->info("TradingService", "backtest requested");
    store_->save_runtime_event(RuntimeEvent{"", "INFO", "TradingService", "Backtest requested"});

    strategy_config_ = strategy_config;
    risk_config_ = risk_config;

    ServiceRunResult output;
    output.markets = load_market_data(symbols);

    Backtester backtester{ScalpingStrategy(strategy_config_), RiskManager(risk_config_)};
    for (const auto& market : output.markets) {
        const BacktestResult result = backtester.run(market);
        const std::string run_id = next_run_id() + "_" + market.symbol;
        store_->save_backtest_result(run_id, market.symbol, result);
        output.results.push_back(result);

        std::ostringstream message;
        message << "Backtest completed symbol=" << market.symbol
                << " return=" << std::fixed << std::setprecision(2)
                << result.total_return_pct << "% trades=" << result.total_trades;
        logger_->info("TradingService", message.str());
        store_->save_runtime_event(RuntimeEvent{"", "INFO", "Backtest", message.str()});
    }

    return output;
}

std::vector<MarketSeries> TradingService::load_market_data(const std::vector<std::string>& symbols)
{
    auto markets = data_source_->load(symbols);
    for (const auto& market : markets) {
        store_->save_market_series(market);
        logger_->info("MarketData", "stored bars for " + market.symbol);
    }
    return markets;
}

std::vector<RuntimeEvent> TradingService::recent_events(int limit)
{
    return store_->recent_events(limit);
}

const StrategyConfig& TradingService::strategy_config() const
{
    return strategy_config_;
}

const RiskConfig& TradingService::risk_config() const
{
    return risk_config_;
}

std::string TradingService::next_run_id() const
{
    return "run_" + compact_timestamp();
}

} // namespace trading
