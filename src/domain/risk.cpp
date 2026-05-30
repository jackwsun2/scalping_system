#include "trading/domain/risk.hpp"

#include <algorithm>
#include <cmath>

namespace trading {

RiskManager::RiskManager(RiskConfig config)
    : config_(config)
{
}

const RiskConfig& RiskManager::config() const
{
    return config_;
}

bool RiskManager::can_enter(const std::string&,
                            double equity,
                            double realized_pnl,
                            int trades_for_symbol) const
{
    if (equity <= 0.0) {
        return false;
    }
    if (trades_for_symbol >= config_.max_trades_per_symbol) {
        return false;
    }
    const double daily_loss_limit = -config_.initial_cash * config_.max_daily_loss_pct;
    return realized_pnl > daily_loss_limit;
}

bool RiskManager::within_total_drawdown(double equity) const
{
    if (config_.initial_cash <= 0.0 || config_.max_total_drawdown_pct <= 0.0) {
        return true;
    }
    const double drawdown = (config_.initial_cash - equity) / config_.initial_cash;
    return drawdown < config_.max_total_drawdown_pct;
}

std::size_t RiskManager::position_size(double equity,
                                       double entry_price,
                                       double stop_loss) const
{
    const double risk_per_share = std::abs(entry_price - stop_loss);
    if (entry_price <= 0.0 || risk_per_share <= 0.0) {
        return 0;
    }
    const double risk_budget = equity * config_.risk_per_trade_pct;
    const double max_notional = equity * config_.max_position_pct;
    const auto by_risk = static_cast<std::size_t>(std::floor(risk_budget / risk_per_share));
    const auto by_notional = static_cast<std::size_t>(std::floor(max_notional / entry_price));
    return std::min(by_risk, by_notional);
}

double RiskManager::apply_buy_slippage(double price) const
{
    return price * (1.0 + config_.slippage_bps / 10000.0);
}

double RiskManager::apply_sell_slippage(double price) const
{
    return price * (1.0 - config_.slippage_bps / 10000.0);
}

double RiskManager::commission(std::size_t quantity) const
{
    return static_cast<double>(quantity) * config_.commission_per_share;
}

} // namespace trading
