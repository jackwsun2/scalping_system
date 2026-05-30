#pragma once

#include "trading/application/trading_service.hpp"

#include <memory>
#include <string>
#include <vector>

namespace trading {

struct DesktopAppConfig {
    std::vector<std::string> symbols = {"GLD", "SLV"};
    std::string csv_path;
    std::string db_path = "scalping_system/runtime/trading.db";
    std::string log_dir = "scalping_system/logs";
    int log_retention_days = 7;
    StrategyConfig strategy;
    RiskConfig risk;
};

struct DesktopAppContext {
    DesktopAppConfig config;
    std::shared_ptr<ILogger> logger;
    std::shared_ptr<ITradingStore> store;
    std::shared_ptr<IMarketDataSource> data_source;
    std::shared_ptr<TradingService> service;
};

DesktopAppContext create_desktop_app_context(const DesktopAppConfig& config);

} // namespace trading
