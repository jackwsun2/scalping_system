#include "trading/domain/backtester.hpp"
#include "trading/infrastructure/csv_data_source.hpp"
#include "trading/presentation/app_factory.hpp"

#include <exception>
#include <iostream>
#include <string>
#include <vector>

namespace {

void print_usage()
{
    std::cout
        << "ScalpingSystem - C++ ETF day trading research runner\n\n"
        << "Usage:\n"
        << "  scalper_cli --backtest [--csv path] [--symbols GLD,SLV] [--db path] [--logs dir]\n"
        << "  scalper --write-sample path\n\n"
        << "CSV columns: timestamp,symbol,open,high,low,close,volume\n";
}

std::vector<std::string> split_symbols(const std::string& input)
{
    std::vector<std::string> result;
    std::string current;
    for (char ch : input) {
        if (ch == ',') {
            if (!current.empty()) {
                result.push_back(current);
            }
            current.clear();
        } else {
            current.push_back(ch);
        }
    }
    if (!current.empty()) {
        result.push_back(current);
    }
    return result;
}

} // namespace

int main(int argc, char** argv)
{
    using namespace trading;

    DesktopAppConfig app;
    std::string write_sample_path;
    bool run_backtest = false;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--help" || arg == "-h") {
            print_usage();
            return 0;
        }
        if (arg == "--backtest") {
            run_backtest = true;
        } else if (arg == "--csv" && i + 1 < argc) {
            app.csv_path = argv[++i];
        } else if (arg == "--symbols" && i + 1 < argc) {
            app.symbols = split_symbols(argv[++i]);
        } else if (arg == "--db" && i + 1 < argc) {
            app.db_path = argv[++i];
        } else if (arg == "--logs" && i + 1 < argc) {
            app.log_dir = argv[++i];
        } else if (arg == "--log-retention-days" && i + 1 < argc) {
            app.log_retention_days = std::stoi(argv[++i]);
        } else if (arg == "--write-sample" && i + 1 < argc) {
            write_sample_path = argv[++i];
        } else {
            std::cerr << "Unknown or incomplete argument: " << arg << "\n";
            print_usage();
            return 2;
        }
    }

    try {
        if (!write_sample_path.empty()) {
            const auto data = generate_sample_market_data(app.symbols, 240);
            write_sample_csv(write_sample_path, data);
            std::cout << "Sample CSV written to " << write_sample_path << "\n";
            return 0;
        }

        if (!run_backtest) {
            run_backtest = true;
        }

        const auto context = create_desktop_app_context(app);

        if (run_backtest) {
            const auto output = context.service->run_backtest(app.symbols);
            for (std::size_t i = 0; i < output.results.size(); ++i) {
                const std::string symbol = i < output.markets.size() ? output.markets[i].symbol : "";
                print_result_summary(output.results[i], symbol);
            }
            std::cout << "\nPersisted to SQLite: " << app.db_path
                      << "\nLogs: " << app.log_dir << "\n";
        }
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << "\n";
        return 1;
    }

    return 0;
}
