"""Market data fetching and normalization."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetch historical and intraday market data from yfinance."""
    
    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        interval: str = '5m',
        cache_dir: str = './data_cache',
    ):
        self.symbols = symbols or []
        self.interval = interval
        self.cache_dir = cache_dir
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

    def fetch_historical_data(
        self, 
        symbol: str, 
        interval: Optional[str] = None,
        days: int = 30,
    ) -> pd.DataFrame:
        """
        Fetch historical data from yfinance
        
        Args:
            symbol: Stock/ETF symbol (e.g., 'GLD', 'SLV')
            interval: Data interval ('1m', '5m', '1h', '1d')
            days: Number of days of historical data to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            interval = interval or self.interval
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            return self.fetch_historical(symbol, start_date, end_date, interval)
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_historical(
        self,
        symbol: str,
        start_date,
        end_date=None,
        interval: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch historical bars and return a normalized OHLCV DataFrame."""
        interval = interval or self.interval
        logger.info(f"Fetching {symbol} {interval} data from {start_date} to {end_date}")

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            if df.empty:
                logger.warning(f"No data fetched for {symbol}")
                return pd.DataFrame()

            df = self.normalize_data(df)
            logger.info(f"Fetched {len(df)} normalized bars for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_intraday_data(
        self, 
        symbol: str, 
        interval: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch intraday data (current trading day)
        
        Args:
            symbol: Stock/ETF symbol
            interval: Data interval ('1m', '5m', etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        return self.fetch_historical_data(symbol, interval or self.interval, days=1)
    
    def fetch_multiple_symbols(
        self, 
        symbols: Optional[List[str]] = None,
        interval: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols
        
        Args:
            symbols: List of symbols to fetch
            interval: Data interval
            days: Number of days
            
        Returns:
            Dictionary with symbol as key and DataFrame as value
        """
        data = {}
        for symbol in symbols or self.symbols:
            df = self.fetch_historical_data(symbol, interval or self.interval, days)
            data[symbol] = df
        return data

    @staticmethod
    def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize yfinance-style data to lowercase OHLCV plus datetime column."""
        if df.empty:
            return df

        normalized = df.copy()
        normalized.columns = [str(col).strip().lower().replace(' ', '_') for col in normalized.columns]

        if 'datetime' not in normalized.columns:
            normalized = normalized.reset_index()
            first_col = normalized.columns[0]
            if first_col != 'datetime':
                normalized = normalized.rename(columns={first_col: 'datetime'})

        normalized['datetime'] = pd.to_datetime(normalized['datetime'], errors='coerce')
        normalized = normalized.dropna(subset=['datetime'])
        normalized = normalized.sort_values('datetime').drop_duplicates(subset=['datetime'])

        keep_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        optional_columns = [col for col in normalized.columns if col not in keep_columns]
        return normalized[[col for col in keep_columns if col in normalized.columns] + optional_columns]

    @staticmethod
    def validate_data(df: pd.DataFrame, min_rows: int = 30) -> bool:
        """Validate the minimum OHLCV schema needed by indicators and strategies."""
        if df is None or df.empty:
            return False

        required = {'datetime', 'open', 'high', 'low', 'close', 'volume'}
        missing = required - set(df.columns)
        if missing:
            logger.warning(f"Market data missing columns: {sorted(missing)}")
            return False

        if len(df) < min_rows:
            logger.warning(f"Market data has only {len(df)} rows, expected at least {min_rows}")
            return False

        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        invalid = df[numeric_cols].isna().any().any()
        non_positive_price = (df[['open', 'high', 'low', 'close']] <= 0).any().any()
        negative_volume = (df['volume'] < 0).any()
        return not (invalid or non_positive_price or negative_volume)


def get_latest_price(symbol: str) -> Optional[float]:
    """
    Get the latest price for a symbol
    
    Args:
        symbol: Stock/ETF symbol
        
    Returns:
        Latest close price or None if error
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        logger.error(f"Error fetching latest price for {symbol}: {str(e)}")
    
    return None
