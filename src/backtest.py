"""
回测模块 - Backtest Engine
执行策略的历史回测，计算收益率、夏普比等指标
"""

import logging
from typing import Dict, List
import pandas as pd
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """回测结果数据类"""
    total_return: float  # 总收益率 %
    win_rate: float  # 胜率 %
    total_trades: int  # 总交易数
    winning_trades: int  # 赢的交易数
    losing_trades: int  # 输的交易数
    avg_win: float  # 平均赢利
    avg_loss: float  # 平均亏损
    profit_factor: float  # 利润因子 (总赢利/总亏损)
    max_drawdown: float  # 最大回撤 %
    sharpe_ratio: float  # 夏普比率
    sortino_ratio: float  # 索提诺比率
    trades: List[Dict]  # 详细交易列表


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: Dict):
        """
        初始化回测引擎
        
        Args:
            config: 回测配置
        """
        self.initial_cash = config.get('initial_cash', 10000)
        self.slippage = config.get('slippage', 0.01) / 100  # 转换为小数
        self.commission = config.get('commission', 0.0)
        self.stop_loss_pct = config.get('stop_loss_pct', config.get('stop_loss', 1.0)) / 100
        self.take_profit_pct = config.get('take_profit_pct', config.get('take_profit', 2.0)) / 100
    
    def run(
        self,
        df: pd.DataFrame,
        signals: List,
        quantity: int = 10,
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            df: 包含价格数据的 DataFrame
            signals: 交易信号列表
            quantity: 每笔交易的股数
            
        Returns:
            BacktestResult 对象
        """
        trades = []
        portfolio_values = [self.initial_cash]
        position = 0  # 当前持仓
        entry_price = 0
        entry_time = None
        cash = self.initial_cash
        
        try:
            working_df = df.copy()
            if 'datetime' not in working_df.columns:
                working_df = working_df.reset_index().rename(columns={working_df.index.name or 'index': 'datetime'})
            working_df['datetime'] = pd.to_datetime(working_df['datetime'])

            signals = sorted(signals, key=lambda item: pd.to_datetime(item.timestamp))

            for signal in signals:
                # 从 DataFrame 中获取当前行的数据
                signal_time = pd.to_datetime(signal.timestamp)
                matching_rows = working_df[working_df['datetime'] == signal_time]
                
                if matching_rows.empty:
                    # 尝试找最接近的时间
                    matching_rows = working_df.loc[(working_df['datetime'] - signal_time).abs().argsort()[:1]]
                
                if matching_rows.empty:
                    continue
                
                current_price = matching_rows.iloc[0]['close']
                signal_value = signal.signal_type.value
                
                # 应用滑点
                actual_price = current_price * (1 + self.slippage * (1 if signal_value > 0 else -1))
                
                # 买入
                if signal_value > 0 and position == 0:
                    cost = actual_price * quantity + self.commission
                    
                    if cash >= cost:
                        cash -= cost
                        position = quantity
                        entry_price = actual_price
                        entry_time = signal_time
                        logger.info(f"BUY {quantity} @ {actual_price:.2f}")
                
                # 卖出
                elif signal_value < 0 and position > 0:
                    revenue = actual_price * position - self.commission
                    profit = revenue - (entry_price * position)
                    profit_pct = (profit / (entry_price * position)) * 100
                    
                    cash += revenue
                    
                    trade = {
                        'entry_time': entry_time,
                        'exit_time': signal_time,
                        'entry_price': entry_price,
                        'exit_price': actual_price,
                        'quantity': position,
                        'profit': profit,
                        'profit_pct': profit_pct,
                    }
                    trades.append(trade)
                    
                    logger.info(
                        f"SELL {position} @ {actual_price:.2f}, "
                        f"Profit: ${profit:.2f} ({profit_pct:.2f}%)"
                    )
                    
                    position = 0
                    entry_price = 0
                
                # 更新投资组合价值
                portfolio_value = cash + (position * current_price if position > 0 else 0)
                portfolio_values.append(portfolio_value)

                if position > 0 and entry_price > 0:
                    pnl_pct = (current_price - entry_price) / entry_price
                    if pnl_pct <= -self.stop_loss_pct or pnl_pct >= self.take_profit_pct:
                        exit_price = current_price * (1 - self.slippage)
                        revenue = exit_price * position - self.commission
                        profit = revenue - (entry_price * position)
                        profit_pct = (profit / (entry_price * position)) * 100
                        cash += revenue
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': signal_time,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'quantity': position,
                            'profit': profit,
                            'profit_pct': profit_pct,
                            'exit_reason': 'stop_loss' if pnl_pct <= -self.stop_loss_pct else 'take_profit',
                        })
                        position = 0
                        entry_price = 0
            
            # 计算指标
            results = self._calculate_metrics(
                trades=trades,
                portfolio_values=portfolio_values,
                initial_cash=self.initial_cash,
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            return BacktestResult(
                total_return=0,
                win_rate=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0,
                avg_loss=0,
                profit_factor=0,
                max_drawdown=0,
                sharpe_ratio=0,
                sortino_ratio=0,
                trades=[],
            )
    
    def _calculate_metrics(
        self,
        trades: List[Dict],
        portfolio_values: List[float],
        initial_cash: float,
    ) -> BacktestResult:
        """
        计算回测指标
        """
        if not trades:
            return BacktestResult(
                total_return=0,
                win_rate=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0,
                avg_loss=0,
                profit_factor=0,
                max_drawdown=0,
                sharpe_ratio=0,
                sortino_ratio=0,
                trades=[],
            )
        
        # 总收益率
        final_value = portfolio_values[-1]
        total_return = ((final_value - initial_cash) / initial_cash) * 100
        
        # 交易统计
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['profit'] > 0)
        losing_trades = sum(1 for t in trades if t['profit'] <= 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 平均赢利和亏损
        winning_profits = [t['profit'] for t in trades if t['profit'] > 0]
        losing_profits = [t['profit'] for t in trades if t['profit'] <= 0]
        
        avg_win = np.mean(winning_profits) if winning_profits else 0
        avg_loss = abs(np.mean(losing_profits)) if losing_profits else 0
        
        # 利润因子
        total_wins = sum(winning_profits) if winning_profits else 0
        total_losses = abs(sum(losing_profits)) if losing_profits else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        # 最大回撤
        portfolio_array = np.array(portfolio_values)
        running_max = np.maximum.accumulate(portfolio_array)
        drawdown = (portfolio_array - running_max) / running_max
        max_drawdown = np.min(drawdown) * 100
        
        # 夏普比率和索提诺比率
        returns = np.diff(portfolio_array) / portfolio_array[:-1]
        
        if len(returns) > 0:
            daily_return = np.mean(returns)
            daily_std = np.std(returns)
            sharpe_ratio = (daily_return / daily_std * np.sqrt(252)) if daily_std > 0 else 0
            
            negative_returns = returns[returns < 0]
            downside_std = np.std(negative_returns) if len(negative_returns) > 0 else daily_std
            sortino_ratio = (daily_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
        
        return BacktestResult(
            total_return=total_return,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            trades=trades,
        )
