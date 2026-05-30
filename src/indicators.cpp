#include "trading/indicators.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>

namespace trading {

namespace {

constexpr double kEpsilon = 1e-9;

double ema_next(double value, double previous, int period)
{
    const double alpha = 2.0 / (static_cast<double>(period) + 1.0);
    return alpha * value + (1.0 - alpha) * previous;
}

double stddev_window(const std::vector<double>& values, std::size_t end_index, std::size_t period)
{
    if (end_index + 1 < period || period == 0) {
        return 0.0;
    }

    const std::size_t begin = end_index + 1 - period;
    const double mean = simple_moving_average(values, end_index, period);
    double sum = 0.0;
    for (std::size_t i = begin; i <= end_index; ++i) {
        const double diff = values[i] - mean;
        sum += diff * diff;
    }
    return std::sqrt(sum / static_cast<double>(period));
}

} // namespace

double simple_moving_average(const std::vector<double>& values,
                             std::size_t end_index,
                             std::size_t period)
{
    if (values.empty() || period == 0) {
        return 0.0;
    }
    const std::size_t count = std::min(period, end_index + 1);
    const std::size_t begin = end_index + 1 - count;
    const double sum = std::accumulate(values.begin() + static_cast<std::ptrdiff_t>(begin),
                                       values.begin() + static_cast<std::ptrdiff_t>(end_index + 1),
                                       0.0);
    return sum / static_cast<double>(count);
}

std::vector<IndicatorSnapshot> compute_indicators(const std::vector<Bar>& bars,
                                                  const StrategyConfig& config)
{
    std::vector<IndicatorSnapshot> snapshots(bars.size());
    if (bars.empty()) {
        return snapshots;
    }

    std::vector<double> closes;
    closes.reserve(bars.size());
    for (const auto& bar : bars) {
        closes.push_back(bar.close);
    }

    double fast_ema = closes.front();
    double slow_ema = closes.front();
    double signal_ema = 0.0;
    double avg_gain = 0.0;
    double avg_loss = 0.0;
    double atr = 0.0;
    double cumulative_pv = 0.0;
    double cumulative_volume = 0.0;
    double k_prev = 50.0;
    double d_prev = 50.0;

    for (std::size_t i = 0; i < bars.size(); ++i) {
        auto& out = snapshots[i];
        const Bar& bar = bars[i];
        const double typical_price = (bar.high + bar.low + bar.close) / 3.0;
        cumulative_pv += typical_price * bar.volume;
        cumulative_volume += bar.volume;
        out.vwap = cumulative_volume > kEpsilon ? cumulative_pv / cumulative_volume : bar.close;

        fast_ema = i == 0 ? bar.close : ema_next(bar.close, fast_ema, config.macd_fast);
        slow_ema = i == 0 ? bar.close : ema_next(bar.close, slow_ema, config.macd_slow);
        out.macd = fast_ema - slow_ema;
        signal_ema = i == 0 ? out.macd : ema_next(out.macd, signal_ema, config.macd_signal);
        out.macd_signal = signal_ema;
        out.macd_histogram = out.macd - out.macd_signal;

        out.bollinger_middle = simple_moving_average(closes, i, static_cast<std::size_t>(config.bollinger_period));
        const double deviation = stddev_window(closes, i, static_cast<std::size_t>(config.bollinger_period));
        out.bollinger_upper = out.bollinger_middle + config.bollinger_stddev * deviation;
        out.bollinger_lower = out.bollinger_middle - config.bollinger_stddev * deviation;

        if (i > 0) {
            const double change = bar.close - bars[i - 1].close;
            const double gain = std::max(change, 0.0);
            const double loss = std::max(-change, 0.0);
            if (i <= static_cast<std::size_t>(config.rsi_period)) {
                avg_gain += gain;
                avg_loss += loss;
                if (i == static_cast<std::size_t>(config.rsi_period)) {
                    avg_gain /= static_cast<double>(config.rsi_period);
                    avg_loss /= static_cast<double>(config.rsi_period);
                }
            } else {
                avg_gain = (avg_gain * (config.rsi_period - 1) + gain) / static_cast<double>(config.rsi_period);
                avg_loss = (avg_loss * (config.rsi_period - 1) + loss) / static_cast<double>(config.rsi_period);
            }

            if (i >= static_cast<std::size_t>(config.rsi_period)) {
                if (avg_loss < kEpsilon) {
                    out.rsi = 100.0;
                } else {
                    const double rs = avg_gain / avg_loss;
                    out.rsi = 100.0 - (100.0 / (1.0 + rs));
                }
            }
        }

        if (i == 0) {
            atr = bar.high - bar.low;
        } else {
            const double tr = std::max({bar.high - bar.low,
                                        std::abs(bar.high - bars[i - 1].close),
                                        std::abs(bar.low - bars[i - 1].close)});
            if (i < static_cast<std::size_t>(config.atr_period)) {
                atr = ((atr * static_cast<double>(i)) + tr) / static_cast<double>(i + 1);
            } else {
                atr = ((atr * static_cast<double>(config.atr_period - 1)) + tr) /
                      static_cast<double>(config.atr_period);
            }
        }
        out.atr = atr;

        const std::size_t kdj_period = static_cast<std::size_t>(config.kdj_period);
        const std::size_t begin = i + 1 > kdj_period ? i + 1 - kdj_period : 0;
        double highest = bars[begin].high;
        double lowest = bars[begin].low;
        for (std::size_t j = begin; j <= i; ++j) {
            highest = std::max(highest, bars[j].high);
            lowest = std::min(lowest, bars[j].low);
        }
        const double rsv = (highest - lowest) > kEpsilon
            ? (bar.close - lowest) / (highest - lowest) * 100.0
            : 50.0;
        out.k = (2.0 * k_prev + rsv) / 3.0;
        out.d = (2.0 * d_prev + out.k) / 3.0;
        out.j = 3.0 * out.k - 2.0 * out.d;
        k_prev = out.k;
        d_prev = out.d;
    }

    return snapshots;
}

} // namespace trading
