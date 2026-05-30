#pragma once

#include "trading/domain/config.hpp"
#include "trading/domain/types.hpp"

#include <vector>

namespace trading {

class ScalpingStrategy {
public:
    explicit ScalpingStrategy(StrategyConfig config = {});

    Signal evaluate(const std::vector<Bar>& bars,
                    const std::vector<IndicatorSnapshot>& indicators,
                    std::size_t index,
                    const Position& position) const;

    const StrategyConfig& config() const;

private:
    StrategyConfig config_;
};

} // namespace trading
