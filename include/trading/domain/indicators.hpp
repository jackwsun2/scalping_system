#pragma once

#include "trading/domain/config.hpp"
#include "trading/domain/types.hpp"

#include <vector>

namespace trading {

std::vector<IndicatorSnapshot> compute_indicators(const std::vector<Bar>& bars,
                                                  const StrategyConfig& config);

double simple_moving_average(const std::vector<double>& values,
                             std::size_t end_index,
                             std::size_t period);

} // namespace trading
