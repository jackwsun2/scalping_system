"""
实盘执行模块 - Order Executor
对接 Alpaca API 进行实盘交易 (或模拟盘)
"""

import logging
from typing import Optional, Dict
from dataclasses import dataclass
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Order:
    """订单数据类"""
    symbol: str
    qty: int
    side: str  # 'buy' or 'sell'
    type: str  # 'market' or 'limit'
    limit_price: Optional[float] = None
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: str = 'pending'


class OrderExecutor:
    """
    订单执行器
    支持 Alpaca API 和模拟模式
    """
    
    def __init__(self, config: dict, paper_trading: bool = True):
        """
        初始化执行器
        
        Args:
            config: Alpaca 配置 (api_key, secret_key, base_url)
            paper_trading: 是否使用模拟盘
        """
        self.config = config
        self.paper_trading = paper_trading
        self.client = None
        
        api_key = config.get('api_key')
        secret_key = config.get('secret_key')
        has_real_keys = (
            api_key and secret_key
            and not str(api_key).startswith('YOUR_')
            and not str(secret_key).startswith('YOUR_')
        )

        # Use the current alpaca-py SDK when credentials are available.
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
            from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

            self.OrderSide = OrderSide
            self.OrderType = OrderType
            self.TimeInForce = TimeInForce
            self.LimitOrderRequest = LimitOrderRequest
            self.MarketOrderRequest = MarketOrderRequest

            if has_real_keys:
                self.client = TradingClient(api_key, secret_key, paper=paper_trading)
                logger.info("Alpaca trading client initialized")
            else:
                logger.warning("Alpaca credentials are not configured. Using mock mode.")
        except ImportError:
            logger.warning("alpaca-py is not installed. Using mock mode.")
            self.client = None
    
    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str = 'market',
        limit_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[Order]:
        """
        提交订单
        
        Args:
            symbol: 股票代码
            qty: 数量
            side: 'buy' 或 'sell'
            order_type: 'market' 或 'limit'
            limit_price: 限价 (仅当 order_type='limit')
            
        Returns:
            Order 对象，或 None 如果失败
        """
        try:
            client_order_id = client_order_id or f"{symbol}-{side}-{uuid4().hex[:12]}"

            if not self.client:
                logger.warning("No Alpaca client configured. Using mock order.")
                return self._create_mock_order(symbol, qty, side, order_type, limit_price, client_order_id)

            side_enum = self.OrderSide.BUY if side.lower() == 'buy' else self.OrderSide.SELL
            order_type = order_type.lower()

            if order_type == 'limit':
                if limit_price is None:
                    raise ValueError("limit_price is required for limit orders")
                order_request = self.LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    time_in_force=self.TimeInForce.DAY,
                    limit_price=limit_price,
                    client_order_id=client_order_id,
                )
            else:
                order_request = self.MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    time_in_force=self.TimeInForce.DAY,
                    client_order_id=client_order_id,
                )

            order = self.client.submit_order(order_data=order_request)
            
            logger.info(f"Order submitted: {symbol} {qty} {side.upper()} @ {limit_price or 'market'}")
            
            return Order(
                symbol=symbol,
                qty=qty,
                side=side.lower(),
                type=order_type.lower(),
                limit_price=limit_price,
                order_id=str(order.id),
                client_order_id=client_order_id,
                status=str(order.status),
            )
            
        except Exception as e:
            logger.error(f"Error submitting order: {str(e)}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单 ID
            
        Returns:
            是否取消成功
        """
        try:
            if not self.client:
                logger.info(f"Mock: Cancel order {order_id}")
                return True
            
            self.client.cancel_order_by_id(order_id)
            logger.info(f"Order {order_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    def get_positions(self) -> Dict[str, float]:
        """
        获取当前持仓
        
        Returns:
            {symbol: quantity} 的字典
        """
        try:
            if not self.client:
                logger.info("Mock: Get positions")
                return {}
            
            positions = self.client.get_all_positions()
            
            result = {}
            for position in positions:
                result[position.symbol] = int(position.qty)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return {}
    
    def get_account_info(self) -> Optional[Dict]:
        """
        获取账户信息
        
        Returns:
            包含 cash, portfolio_value 等的字典
        """
        try:
            if not self.client:
                logger.info("Mock: Get account info")
                return {
                    'cash': 10000.0,
                    'portfolio_value': 10000.0,
                    'multiplier': 1.0,
                }
            
            account = self.client.get_account()
            
            return {
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'multiplier': float(account.multiplier),
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None
    
    def _create_mock_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str,
        limit_price: Optional[float],
        client_order_id: Optional[str] = None,
    ) -> Order:
        """
        创建模拟订单 (用于测试)
        """
        order = Order(
            symbol=symbol,
            qty=qty,
            side=side.lower(),
            type=order_type.lower(),
            limit_price=limit_price,
            order_id=client_order_id or str(uuid4())[:8],
            client_order_id=client_order_id,
            status='mock_submitted',
        )
        
        logger.info(
            f"Mock order created: {symbol} {qty} {side.upper()} "
            f"@ {limit_price or 'market'} (ID: {order.order_id})"
        )
        
        return order
