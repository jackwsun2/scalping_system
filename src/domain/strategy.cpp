#include "trading/domain/strategy.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

namespace trading {

namespace {

bool is_valid_bar(const Bar& bar)
{
    return std::isfinite(bar.open) &&
           std::isfinite(bar.high) &&
           std::isfinite(bar.low) &&
           std::isfinite(bar.close) &&
           std::isfinite(bar.volume) &&
           bar.open > 0.0 &&
           bar.high > 0.0 &&
           bar.low > 0.0 &&
           bar.close > 0.0 &&
           bar.high >= bar.low &&
           bar.high >= std::max(bar.open, bar.close) &&
           bar.low <= std::min(bar.open, bar.close) &&
           bar.volume >= 0.0;
}

double average_volume(const std::vector<Bar>& bars, std::size_t index, std::size_t period)
{
    if (index == 0 || period == 0) {
        return 0.0;
    }

    const std::size_t begin = index > period ? index - period : 0;
    double sum = 0.0;
    std::size_t count = 0;
    for (std::size_t i = begin; i < index; ++i) {
        sum += bars[i].volume;
        ++count;
    }
    return count > 0 ? sum / static_cast<double>(count) : 0.0;
}

} // namespace

ScalpingStrategy::ScalpingStrategy(StrategyConfig config)
    : config_(config)
{
}

const StrategyConfig& ScalpingStrategy::config() const
{
    return config_;
}

Signal ScalpingStrategy::evaluate(const std::vector<Bar>& bars,
                                  const std::vector<IndicatorSnapshot>& indicators,
                                  std::size_t index,
                                  const Position& position) const
{
    Signal signal;
    if (index >= bars.size() || index >= indicators.size()) {
        return signal;
    }

    const Bar& bar = bars[index];
    const auto& ind = indicators[index];
    signal.indicators = ind;

    if (!is_valid_bar(bar)) {
        signal.reason = "INVALID_BAR";
        return signal;
    }

    if (position.side == PositionSide::Long) {
        if (bar.low <= position.stop_loss) {
            signal.side = Side::Sell;
            signal.reason = "STOP_LOSS";
            signal.confidence = 1.0;
            return signal;
        }
        if (bar.high >= position.take_profit) {
            signal.side = Side::Sell;
            signal.reason = "TAKE_PROFIT";
            signal.confidence = 1.0;
            return signal;
        }
        if (ind.rsi > config_.rsi_overbought &&
            (config_.name == "RSI_ONLY" || ind.macd_histogram < 0.0)) {
            signal.side = Side::Sell;
            signal.reason = "RSI_OVERBOUGHT_MACD_FADE";
            signal.confidence = 0.82;
            return signal;
        }
        signal.reason = "MANAGE_LONG";
        return signal;
    }

    const bool enough_history = index > static_cast<std::size_t>(
        std::max({config_.macd_slow,
                  config_.bollinger_period,
                  config_.atr_period,
                  config_.kdj_period,
                  config_.long_ma_period}));
    if (!enough_history || ind.atr <= 0.0) {
        signal.reason = "WARMUP";
        return signal;
    }

    double score = 0.0;
    std::ostringstream reason;

    if (config_.name == "RSI_ONLY" && ind.rsi < config_.rsi_oversold) {
        score = 0.72;
        reason << "RSI_OVERSOLD ";
    } else if (config_.name == "RSI_ONLY") {
        signal.confidence = 0.0;
        signal.reason = "WAIT";
        return signal;
    }

    if (config_.name != "RSI_ONLY") {
        const double atr_pct = bar.close > 0.0 ? ind.atr / bar.close : 0.0;
        if (atr_pct < config_.min_atr_pct) {
            signal.reason = "VOLATILITY_TOO_LOW";
            return signal;
        }
        if (atr_pct > config_.max_atr_pct) {
            signal.reason = "VOLATILITY_TOO_HIGH";
            return signal;
        }

        const double avg_volume = average_volume(bars, index, 20);
        if (avg_volume > 0.0 && bar.volume < avg_volume * config_.minimum_volume_ratio) {
            signal.reason = "VOLUME_TOO_LOW";
            return signal;
        }

        const bool trend_confirmed = !config_.require_trend_confirmation ||
                                     bar.close >= ind.long_ma ||
                                     ind.short_ma >= ind.long_ma ||
                                     ind.macd_histogram > 0.0;
        if (!trend_confirmed) {
            signal.reason = "TREND_FILTER";
            return signal;
        }

        if (bar.close <= ind.bollinger_lower && ind.rsi <= config_.rsi_oversold + 3.0) {
            score += 0.28;
            reason << "BOLLINGER_REVERSION ";
        }
        if (ind.rsi < config_.rsi_oversold) {
            score += 0.22;
            reason << "RSI_OVERSOLD ";
        }
        if (index > 0 && ind.macd > ind.macd_signal && indicators[index - 1].macd <= indicators[index - 1].macd_signal) {
            score += 0.22;
            reason << "MACD_CROSS_UP ";
        } else if (ind.macd_histogram > 0.0) {
            score += 0.10;
            reason << "MACD_POSITIVE ";
        }
        if (ind.k < 25.0 && ind.k > ind.d) {
            score += 0.16;
            reason << "KDJ_RECOVERY ";
        }
        if (bar.close > ind.vwap) {
            score += 0.10;
            reason << "ABOVE_VWAP ";
        }
        if (avg_volume > 0.0 && bar.volume > avg_volume * 1.15) {
            score += 0.08;
            reason << "VOLUME_CONFIRM ";
        }
        if (ind.short_ma > ind.long_ma) {
            score += 0.08;
            reason << "MA_TREND_CONFIRM ";
        }
    }

    signal.confidence = std::min(score, 1.0);
    if (signal.confidence >= config_.minimum_confidence) {
        const double configured_stop_distance = config_.fixed_stop_loss_pct > 0.0
            ? bar.close * config_.fixed_stop_loss_pct / 100.0
            : 0.0;
        const double stop_distance = configured_stop_distance > 0.0
            ? configured_stop_distance
            : std::max(ind.atr * config_.atr_stop_multiplier, bar.close * 0.002);
        const double configured_take_distance = config_.fixed_take_profit_pct > 0.0
            ? bar.close * config_.fixed_take_profit_pct / 100.0
            : 0.0;
        const double take_distance = configured_take_distance > 0.0
            ? configured_take_distance
            : stop_distance * config_.risk_reward;
        signal.side = Side::Buy;
        signal.stop_loss = bar.close - stop_distance;
        signal.take_profit = bar.close + take_distance;
        signal.reason = reason.str().empty() ? "MULTI_FACTOR_LONG" : reason.str();
    } else {
        signal.reason = "WAIT";
    }

    return signal;
}

} // namespace trading
