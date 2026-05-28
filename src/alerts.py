"""
Alert system for sending notifications via Telegram
"""
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramAlert:
    """Send alerts via Telegram Bot"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram alert
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    def send_trade_alert(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        confidence: float,
        reason: str,
        indicators: dict
    ) -> bool:
        """
        Send trade signal alert
        
        Args:
            symbol: Trading symbol
            signal_type: 'BUY' or 'SELL'
            price: Current price
            confidence: Signal confidence (0-1)
            reason: Signal reason
            indicators: Dictionary of indicator values
            
        Returns:
            True if message sent successfully
        """
        
        emoji = "🟢 BUY" if signal_type == "BUY" else "🔴 SELL"
        rsi = indicators.get('rsi')
        macd = indicators.get('macd')
        rsi_text = f"{rsi:.2f}" if isinstance(rsi, (int, float)) else "N/A"
        macd_text = f"{macd:.4f}" if isinstance(macd, (int, float)) else "N/A"
        
        message = f"""
{emoji} Signal Alert

Symbol: {symbol}
Price: ${price:.2f}
Confidence: {confidence*100:.1f}%
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Indicators:
RSI: {rsi_text}
MACD: {macd_text}

💡 Reason:
{reason}
"""
        
        return self._send_message(message)
    
    def send_error_alert(self, error_msg: str) -> bool:
        """
        Send error alert
        
        Args:
            error_msg: Error message
            
        Returns:
            True if message sent successfully
        """
        message = f"""
⚠️ System Error

{error_msg}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(message)
    
    def send_status_update(self, status_msg: str) -> bool:
        """
        Send system status update
        
        Args:
            status_msg: Status message
            
        Returns:
            True if message sent successfully
        """
        message = f"""
ℹ️ Status Update

{status_msg}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(message)
    
    def _send_message(self, message: str) -> bool:
        """
        Send message to Telegram
        
        Args:
            message: Message text
            
        Returns:
            True if sent successfully
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False
        
        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(self.api_url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False


class AlertManager:
    """Manage multiple alert channels"""
    
    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        enabled: bool = True,
    ):
        """
        Initialize alert manager
        
        Args:
            telegram_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
        """
        self.telegram = None

        if isinstance(telegram_token, dict):
            config: Dict = telegram_token
            telegram_token = config.get('bot_token')
            telegram_chat_id = config.get('chat_id')
            enabled = config.get('enabled', False)

        if telegram_token and telegram_chat_id:
            self.telegram = TelegramAlert(telegram_token, telegram_chat_id) if enabled else None

    def send_alert(self, title: str, message: str, level: str = 'INFO') -> bool:
        """Send a generic alert."""
        full_message = f"[{level}] {title}\n\n{message}"
        if self.telegram:
            return self.telegram._send_message(full_message)

        log_method = logger.error if level in {'ERROR', 'CRITICAL'} else logger.info
        log_method(full_message)
        return True
    
    def send_trade_alert(self, signal) -> bool:
        """
        Send trade alert through available channels
        
        Args:
            signal: TradeSignal object
            
        Returns:
            True if at least one alert was sent
        """
        success = False
        
        if self.telegram:
            success |= self.telegram.send_trade_alert(
                symbol=signal.symbol,
                signal_type=signal.signal_type.name,
                price=signal.price,
                confidence=signal.confidence,
                reason=signal.reason,
                indicators=signal.indicators
            )
        
        # Local logging
        logger.info(f"Trade Signal: {signal.symbol} {signal.signal_type.name} at ${signal.price:.2f}")
        success = True
        
        return success
    
    def send_error_alert(self, error_msg: str) -> bool:
        """Send error alert"""
        if self.telegram:
            return self.telegram.send_error_alert(error_msg)
        
        logger.error(error_msg)
        return True
    
    def send_status_update(self, status_msg: str) -> bool:
        """Send status update"""
        if self.telegram:
            return self.telegram.send_status_update(status_msg)
        
        logger.info(status_msg)
        return True
