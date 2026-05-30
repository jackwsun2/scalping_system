#include "trading/strategy.hpp"

#include <algorithm>
#include <sstream>

namespace trading {

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
        if (ind.rsi > config_.rsi_overbought && ind.macd_histogram < 0.0) {
            signal.side = Side::Sell;
            signal.reason = "RSI_OVERBOUGHT_MACD_FADE";
            signal.confidence = 0.82;
            return signal;
        }
        signal.reason = "MANAGE_LONG";
        return signal;
    }

    const bool enough_history = index > static_cast<std::size_t>(
        std::max({config_.macd_slow, config_.bollinger_period, config_.atr_period, config_.kdj_period}));
    if (!enough_history || ind.atr <= 0.0) {
        signal.reason = "WARMUP";
        return signal;
    }

    double score = 0.0;
    std::ostringstream reason;

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
    if (bar.volume > 0.0 && index >= 20) {
        double avg_volume = 0.0;
        for (std::size_t i = index - 20; i < index; ++i) {
            avg_volume += bars[i].volume;
        }
        avg_volume /= 20.0;
        if (bar.volume > avg_volume * 1.15) {
            score += 0.08;
            reason << "VOLUME_CONFIRM ";
        }
    }

    signal.confidence = std::min(score, 1.0);
    if (signal.confidence >= config_.minimum_confidence) {
        const double stop_distance = std::max(ind.atr * config_.atr_stop_multiplier, bar.close * 0.002);
        signal.side = Side::Buy;
        signal.stop_loss = bar.close - stop_distance;
        signal.take_profit = bar.close + stop_distance * config_.risk_reward;
        signal.reason = reason.str().empty() ? "MULTI_FACTOR_LONG" : reason.str();
    } else {
        signal.reason = "WAIT";
    }

    return signal;
}

} // namespace trading
