#include "trading/data_source.hpp"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <random>
#include <sstream>
#include <stdexcept>

namespace trading {

std::vector<MarketSeries> generate_sample_market_data(
    const std::vector<std::string>& symbols,
    int bars_per_symbol)
{
    std::vector<MarketSeries> output;
    output.reserve(symbols.size());
    std::mt19937 rng(42);
    std::normal_distribution<double> noise(0.0, 0.18);

    for (std::size_t s = 0; s < symbols.size(); ++s) {
        MarketSeries series;
        series.symbol = symbols[s];
        series.bars.reserve(static_cast<std::size_t>(bars_per_symbol));
        double price = symbols[s] == "SLV" ? 28.0 : 220.0;

        for (int i = 0; i < bars_per_symbol; ++i) {
            const double wave = std::sin(static_cast<double>(i) / 11.0) * 0.22;
            const double regime = (i / 90) % 2 == 0 ? 0.035 : -0.018;
            const double shock = noise(rng);
            const double open = price;
            price = std::max(1.0, price + wave + regime + shock);
            const double close = price;
            const double spread = 0.18 + std::abs(noise(rng)) * 0.6;

            Bar bar;
            const int day = 1 + i / 78;
            const int slot = i % 78;
            const int minute = 30 + slot * 5;
            const int hour = 9 + minute / 60;
            const int min = minute % 60;
            std::ostringstream timestamp;
            timestamp << "2026-05-" << std::setw(2) << std::setfill('0') << day
                      << " " << std::setw(2) << std::setfill('0') << hour
                      << ":" << std::setw(2) << std::setfill('0') << min << ":00";
            bar.timestamp = timestamp.str();
            bar.symbol = series.symbol;
            bar.open = open;
            bar.close = close;
            bar.high = std::max(open, close) + spread;
            bar.low = std::min(open, close) - spread;
            bar.volume = 450000.0 + 80000.0 * std::sin(static_cast<double>(i) / 7.0) +
                         static_cast<double>((i % 13) * 11000);
            if (i % 37 == 0) {
                bar.volume *= 1.8;
            }
            series.bars.push_back(bar);
        }
        output.push_back(series);
    }

    return output;
}

void write_sample_csv(const std::string& path,
                      const std::vector<MarketSeries>& data)
{
    const std::filesystem::path file_path(path);
    if (file_path.has_parent_path()) {
        std::filesystem::create_directories(file_path.parent_path());
    }

    std::ofstream output(path);
    if (!output) {
        throw std::runtime_error("Cannot write sample CSV: " + path);
    }
    output << "timestamp,symbol,open,high,low,close,volume\n";
    output << std::fixed << std::setprecision(4);
    for (const auto& series : data) {
        for (const auto& bar : series.bars) {
            output << bar.timestamp << ','
                   << bar.symbol << ','
                   << bar.open << ','
                   << bar.high << ','
                   << bar.low << ','
                   << bar.close << ','
                   << std::setprecision(0) << bar.volume << std::setprecision(4)
                   << '\n';
        }
    }
}

} // namespace trading
