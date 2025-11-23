"""
Alpha Vantage API Client (Free Tier)
Free tier: 5 API calls/minute, 500 calls/day
Provides: Technical indicators, time series data
"""
import requests
from typing import Dict, List, Optional, Any
from backend.config import get_config

config = get_config()


class AlphaVantageClient:
    """Alpha Vantage API client for technical indicators and time series"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self.api_key = config.ALPHA_VANTAGE_API_KEY
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not set in environment variables")

    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            params['apikey'] = self.api_key
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Check for API error messages
            if 'Error Message' in data:
                return {'error': data['Error Message']}
            if 'Note' in data:
                return {'error': 'API call frequency limit reached'}

            return data

        except requests.exceptions.Timeout:
            return {'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def get_intraday(self, symbol: str, interval: str = '5min') -> Dict[str, Any]:
        """
        Get intraday time series data

        Args:
            symbol: Stock symbol
            interval: '1min', '5min', '15min', '30min', '60min'

        Returns:
            Intraday price data
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval
        }
        return self._make_request(params)

    def get_daily(self, symbol: str, outputsize: str = 'compact') -> Dict[str, Any]:
        """
        Get daily time series data

        Args:
            symbol: Stock symbol
            outputsize: 'compact' (100 days) or 'full' (20 years)

        Returns:
            Daily price data
        """
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize
        }
        return self._make_request(params)

    def get_sma(self, symbol: str, interval: str = 'daily',
               time_period: int = 20, series_type: str = 'close') -> Dict[str, Any]:
        """
        Get Simple Moving Average (SMA)

        Args:
            symbol: Stock symbol
            interval: '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'
            time_period: Number of data points
            series_type: 'close', 'open', 'high', 'low'

        Returns:
            SMA data
        """
        params = {
            'function': 'SMA',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period),
            'series_type': series_type
        }
        return self._make_request(params)

    def get_ema(self, symbol: str, interval: str = 'daily',
               time_period: int = 20, series_type: str = 'close') -> Dict[str, Any]:
        """Get Exponential Moving Average (EMA)"""
        params = {
            'function': 'EMA',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period),
            'series_type': series_type
        }
        return self._make_request(params)

    def get_rsi(self, symbol: str, interval: str = 'daily',
               time_period: int = 14, series_type: str = 'close') -> Dict[str, Any]:
        """
        Get Relative Strength Index (RSI)

        Args:
            symbol: Stock symbol
            interval: Time interval
            time_period: Number of data points (typically 14)
            series_type: Price type

        Returns:
            RSI data
        """
        params = {
            'function': 'RSI',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period),
            'series_type': series_type
        }
        return self._make_request(params)

    def get_macd(self, symbol: str, interval: str = 'daily',
                series_type: str = 'close') -> Dict[str, Any]:
        """
        Get Moving Average Convergence Divergence (MACD)

        Returns:
            MACD data with MACD, signal, and histogram
        """
        params = {
            'function': 'MACD',
            'symbol': symbol,
            'interval': interval,
            'series_type': series_type
        }
        return self._make_request(params)

    def get_bbands(self, symbol: str, interval: str = 'daily',
                  time_period: int = 20, series_type: str = 'close') -> Dict[str, Any]:
        """
        Get Bollinger Bands (BBANDS)

        Returns:
            Upper, middle, and lower bands
        """
        params = {
            'function': 'BBANDS',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period),
            'series_type': series_type
        }
        return self._make_request(params)

    def get_stoch(self, symbol: str, interval: str = 'daily') -> Dict[str, Any]:
        """
        Get Stochastic Oscillator (STOCH)

        Returns:
            SlowK and SlowD values
        """
        params = {
            'function': 'STOCH',
            'symbol': symbol,
            'interval': interval
        }
        return self._make_request(params)

    def get_adx(self, symbol: str, interval: str = 'daily',
               time_period: int = 14) -> Dict[str, Any]:
        """
        Get Average Directional Index (ADX)

        Returns:
            ADX trend strength indicator
        """
        params = {
            'function': 'ADX',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period)
        }
        return self._make_request(params)

    def get_cci(self, symbol: str, interval: str = 'daily',
               time_period: int = 20) -> Dict[str, Any]:
        """Get Commodity Channel Index (CCI)"""
        params = {
            'function': 'CCI',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period)
        }
        return self._make_request(params)

    def get_aroon(self, symbol: str, interval: str = 'daily',
                 time_period: int = 25) -> Dict[str, Any]:
        """Get Aroon Indicator"""
        params = {
            'function': 'AROON',
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period)
        }
        return self._make_request(params)

    def get_obv(self, symbol: str, interval: str = 'daily') -> Dict[str, Any]:
        """Get On Balance Volume (OBV)"""
        params = {
            'function': 'OBV',
            'symbol': symbol,
            'interval': interval
        }
        return self._make_request(params)

    def search_symbol(self, keywords: str) -> Dict[str, Any]:
        """
        Search for symbols matching keywords

        Args:
            keywords: Search term

        Returns:
            Matching symbols with basic info
        """
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        return self._make_request(params)

    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Get company fundamental data

        Returns:
            Company overview including P/E ratio, market cap, etc.
        """
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        return self._make_request(params)


# Singleton instance
_alphavantage_client = None


def get_alphavantage_client() -> AlphaVantageClient:
    """Get Alpha Vantage client singleton"""
    global _alphavantage_client
    if _alphavantage_client is None:
        _alphavantage_client = AlphaVantageClient()
    return _alphavantage_client
