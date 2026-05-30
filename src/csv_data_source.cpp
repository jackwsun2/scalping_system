#include "trading/data_source.hpp"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

namespace trading {

namespace {

std::vector<std::string> split_csv_line(const std::string& line)
{
    std::vector<std::string> fields;
    std::string field;
    bool in_quotes = false;
    for (char ch : line) {
        if (ch == '"') {
            in_quotes = !in_quotes;
        } else if (ch == ',' && !in_quotes) {
            fields.push_back(field);
            field.clear();
        } else {
            field.push_back(ch);
        }
    }
    fields.push_back(field);
    return fields;
}

double parse_double(const std::string& value)
{
    return value.empty() ? 0.0 : std::stod(value);
}

} // namespace

CsvDataSource::CsvDataSource(std::string path)
    : path_(std::move(path))
{
}

std::vector<MarketSeries> CsvDataSource::load(const std::vector<std::string>& symbols)
{
    std::ifstream input(path_);
    if (!input) {
        throw std::runtime_error("Cannot open CSV file: " + path_);
    }

    std::unordered_set<std::string> filter(symbols.begin(), symbols.end());
    std::unordered_map<std::string, std::vector<Bar>> grouped;

    std::string line;
    if (!std::getline(input, line)) {
        return {};
    }

    while (std::getline(input, line)) {
        if (line.empty()) {
            continue;
        }
        const auto fields = split_csv_line(line);
        if (fields.size() < 7) {
            continue;
        }
        Bar bar;
        bar.timestamp = fields[0];
        bar.symbol = fields[1];
        if (!filter.empty() && filter.find(bar.symbol) == filter.end()) {
            continue;
        }
        bar.open = parse_double(fields[2]);
        bar.high = parse_double(fields[3]);
        bar.low = parse_double(fields[4]);
        bar.close = parse_double(fields[5]);
        bar.volume = parse_double(fields[6]);
        grouped[bar.symbol].push_back(bar);
    }

    std::vector<MarketSeries> output;
    output.reserve(grouped.size());
    for (auto& item : grouped) {
        auto& bars = item.second;
        std::sort(bars.begin(), bars.end(), [](const Bar& a, const Bar& b) {
            return a.timestamp < b.timestamp;
        });
        output.push_back(MarketSeries{item.first, bars});
    }
    std::sort(output.begin(), output.end(), [](const MarketSeries& a, const MarketSeries& b) {
        return a.symbol < b.symbol;
    });
    return output;
}

std::string to_string(Side side)
{
    switch (side) {
    case Side::Buy:
        return "BUY";
    case Side::Sell:
        return "SELL";
    case Side::Hold:
        return "HOLD";
    }
    return "HOLD";
}

std::string to_string(TimeFrame timeframe)
{
    switch (timeframe) {
    case TimeFrame::Min1:
        return "1m";
    case TimeFrame::Min5:
        return "5m";
    case TimeFrame::Hour1:
        return "1h";
    case TimeFrame::Day1:
        return "1d";
    }
    return "5m";
}

} // namespace trading
