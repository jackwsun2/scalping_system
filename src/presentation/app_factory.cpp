#include "trading/presentation/app_factory.hpp"

#include "trading/infrastructure/csv_data_source.hpp"
#include "trading/infrastructure/file_logger.hpp"
#include "trading/infrastructure/sqlite_store.hpp"

namespace trading {

DesktopAppContext create_desktop_app_context(const DesktopAppConfig& config)
{
    DesktopAppContext context;
    context.config = config;
    context.logger = std::make_shared<SpdlogFileLogger>(
        config.log_dir, config.log_retention_days);
    context.store = std::make_shared<SqliteTradingStore>(config.db_path);
    if (config.csv_path.empty()) {
        context.data_source = std::make_shared<SampleDataSource>(240);
    } else {
        context.data_source = std::make_shared<CsvDataSource>(config.csv_path);
    }
    context.service = std::make_shared<TradingService>(
        context.data_source, context.store, context.logger, config.strategy, config.risk);
    context.logger->info("DesktopApp", "application context created");
    context.store->save_runtime_event(RuntimeEvent{"", "INFO", "DesktopApp", "Application context created"});
    return context;
}

} // namespace trading
