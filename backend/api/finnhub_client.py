"""
Finnhub API Client (Free Tier)
Free tier: 60 API calls/minute
Provides: Real-time quotes, company financials, earnings
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from backend.config import get_config

config = get_config()


class FinnhubClient:
    """Finnhub API client for stock market data"""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self):
        self.api_key = config.FINNHUB_API_KEY
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not set in environment variables")

        self.session = requests.Session()
        self.session.params = {'token': self.api_key}

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            return {'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            {
                'c': current price,
                'h': high price of the day,
                'l': low price of the day,
                'o': open price of the day,
                'pc': previous close price,
                't': timestamp
            }
        """
        return self._make_request('quote', {'symbol': symbol})

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Get company profile

        Returns:
            Company info including name, industry, market cap, etc.
        """
        return self._make_request('stock/profile2', {'symbol': symbol})

    def get_company_financials(self, symbol: str, statement_type: str = 'ic',
                              frequency: str = 'quarterly') -> Dict[str, Any]:
        """
        Get company financial statements

        Args:
            symbol: Stock symbol
            statement_type: 'bs' (balance sheet), 'ic' (income statement), 'cf' (cash flow)
            frequency: 'annual' or 'quarterly'

        Returns:
            Financial data
        """
        params = {
            'symbol': symbol,
            'statement': statement_type,
            'freq': frequency
        }
        return self._make_request('stock/financials-reported', params)

    def get_earnings(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get earnings data

        Returns:
            List of earnings surprises
        """
        result = self._make_request('stock/earnings', {'symbol': symbol})
        return result if isinstance(result, list) else []

    def get_recommendation_trends(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get analyst recommendations

        Returns:
            List of recommendation trends
        """
        result = self._make_request('stock/recommendation', {'symbol': symbol})
        return result if isinstance(result, list) else []

    def get_news(self, symbol: str, from_date: Optional[str] = None,
                to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get company news

        Args:
            symbol: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of news articles
        """
        if not from_date:
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')

        params = {
            'symbol': symbol,
            'from': from_date,
            'to': to_date
        }
        result = self._make_request('company-news', params)
        return result if isinstance(result, list) else []

    def get_market_news(self, category: str = 'general') -> List[Dict[str, Any]]:
        """
        Get general market news

        Args:
            category: 'general', 'forex', 'crypto', 'merger'

        Returns:
            List of news articles
        """
        result = self._make_request('news', {'category': category})
        return result if isinstance(result, list) else []

    def get_candles(self, symbol: str, resolution: str = 'D',
                   from_timestamp: Optional[int] = None,
                   to_timestamp: Optional[int] = None) -> Dict[str, Any]:
        """
        Get historical candlestick data

        Args:
            symbol: Stock symbol
            resolution: '1', '5', '15', '30', '60', 'D', 'W', 'M'
            from_timestamp: Unix timestamp
            to_timestamp: Unix timestamp

        Returns:
            OHLC data: {
                'o': open prices,
                'h': high prices,
                'l': low prices,
                'c': close prices,
                'v': volumes,
                't': timestamps
            }
        """
        if not from_timestamp:
            from_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())
        if not to_timestamp:
            to_timestamp = int(datetime.now().timestamp())

        params = {
            'symbol': symbol,
            'resolution': resolution,
            'from': from_timestamp,
            'to': to_timestamp
        }
        return self._make_request('stock/candle', params)

    def search_symbol(self, query: str) -> Dict[str, Any]:
        """
        Search for stock symbols

        Args:
            query: Search term

        Returns:
            Matching symbols
        """
        return self._make_request('search', {'q': query})

    def get_market_status(self, exchange: str = 'US') -> Dict[str, Any]:
        """
        Get market status (open/closed)

        Args:
            exchange: Exchange code

        Returns:
            Market status info
        """
        return self._make_request('stock/market-status', {'exchange': exchange})


# Singleton instance
_finnhub_client = None


def get_finnhub_client() -> FinnhubClient:
    """Get Finnhub client singleton"""
    global _finnhub_client
    if _finnhub_client is None:
        _finnhub_client = FinnhubClient()
    return _finnhub_client
