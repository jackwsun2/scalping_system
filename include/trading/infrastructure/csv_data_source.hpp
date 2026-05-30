#pragma once

#include "trading/application/interfaces.hpp"

#include <string>
#include <vector>

namespace trading {

class CsvDataSource final : public IMarketDataSource {
public:
    explicit CsvDataSource(std::string path);
    std::vector<MarketSeries> load(const std::vector<std::string>& symbols) override;

private:
    std::string path_;
};

class SampleDataSource final : public IMarketDataSource {
public:
    explicit SampleDataSource(int bars_per_symbol = 240);
    std::vector<MarketSeries> load(const std::vector<std::string>& symbols) override;

private:
    int bars_per_symbol_ = 240;
};

std::vector<MarketSeries> generate_sample_market_data(
    const std::vector<std::string>& symbols,
    int bars_per_symbol);

void write_sample_csv(const std::string& path,
                      const std::vector<MarketSeries>& data);

} // namespace trading
