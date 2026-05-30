#pragma once

#include "trading/domain/config.hpp"
#include "trading/domain/types.hpp"

#include <cstddef>

namespace trading {

class RiskManager {
public:
    explicit RiskManager(RiskConfig config = {});

    bool can_enter(const std::string& symbol,
                   double equity,
                   double realized_pnl,
                   int trades_for_symbol) const;

    bool within_total_drawdown(double equity) const;

    std::size_t position_size(double equity,
                              double entry_price,
                              double stop_loss) const;

    double apply_buy_slippage(double price) const;
    double apply_sell_slippage(double price) const;
    double commission(std::size_t quantity) const;

    const RiskConfig& config() const;

private:
    RiskConfig config_;
};

} // namespace trading
