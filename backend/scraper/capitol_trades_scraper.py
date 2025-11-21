"""
Capitol Trades Scraper
Scrapes politician stock trading data from capitoltrades.com
"""
from .base_scraper import BaseScraper
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CapitolTradesScraper(BaseScraper):
    """Scraper for Capitol Trades website"""

    BASE_URL = "https://www.capitoltrades.com"

    def __init__(self):
        super().__init__()

    def get_recent_trades(self, politician: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get recent politician stock trades

        Args:
            politician: Filter by politician name (optional)
            limit: Maximum number of trades to return

        Returns:
            List of trade dictionaries
        """
        try:
            url = f"{self.BASE_URL}/trades"

            soup = self.get_page(url)
            if not soup:
                return []

            trades = []

            # Find trade table or cards
            trade_elements = soup.find_all(['tr', 'div'], class_=['trade-row', 'trade-card', 'tx-row'])

            for element in trade_elements[:limit]:
                try:
                    trade = self._parse_trade_element(element)
                    if trade:
                        # Filter by politician if specified
                        if politician and politician.lower() not in trade.get('politician', '').lower():
                            continue
                        trades.append(trade)
                except Exception as e:
                    logger.error(f"Error parsing trade element: {e}")
                    continue

            logger.info(f"Scraped {len(trades)} trades from Capitol Trades")
            return trades

        except Exception as e:
            logger.error(f"Error scraping Capitol Trades: {e}")
            return []

    def _parse_trade_element(self, element) -> Optional[Dict]:
        """Parse a single trade element"""
        try:
            trade = {}

            # Try to extract politician name
            politician_elem = element.find(['a', 'span', 'div'], class_=['politician', 'name', 'politician-name'])
            if politician_elem:
                trade['politician'] = politician_elem.get_text(strip=True)

            # Try to extract ticker
            ticker_elem = element.find(['a', 'span'], class_=['ticker', 'q-ticker'])
            if ticker_elem:
                trade['ticker'] = ticker_elem.get_text(strip=True)

            # Try to extract asset name
            asset_elem = element.find(['a', 'span', 'div'], class_=['asset', 'issuer', 'asset-name'])
            if asset_elem:
                trade['asset'] = asset_elem.get_text(strip=True)

            # Try to extract date
            date_elem = element.find(['span', 'time', 'div'], class_=['date', 'tx-date', 'disclosed-date'])
            if date_elem:
                trade['date'] = date_elem.get_text(strip=True)

            # Try to extract trade type
            type_elem = element.find(['span', 'div'], class_=['type', 'tx-type', 'trade-type'])
            if type_elem:
                type_text = type_elem.get_text(strip=True).lower()
                trade['type'] = 'purchase' if 'purchase' in type_text or 'buy' in type_text else 'sale'

            # Try to extract amount
            amount_elem = element.find(['span', 'div'], class_=['amount', 'size', 'tx-size'])
            if amount_elem:
                trade['amount'] = amount_elem.get_text(strip=True)

            # Only return if we have minimum required fields
            if 'politician' in trade and ('ticker' in trade or 'asset' in trade):
                return trade

            return None

        except Exception as e:
            logger.error(f"Error parsing trade: {e}")
            return None

    def get_politician_trades(self, politician_slug: str, limit: int = 50) -> List[Dict]:
        """
        Get trades for a specific politician

        Args:
            politician_slug: URL slug for politician (e.g., 'nancy-pelosi')
            limit: Maximum number of trades

        Returns:
            List of trades
        """
        try:
            url = f"{self.BASE_URL}/politicians/{politician_slug}"

            soup = self.get_page(url)
            if not soup:
                return []

            trades = []
            trade_elements = soup.find_all(['tr', 'div'], class_=['trade-row', 'trade-card', 'tx-row'])

            for element in trade_elements[:limit]:
                try:
                    trade = self._parse_trade_element(element)
                    if trade:
                        trades.append(trade)
                except Exception as e:
                    logger.error(f"Error parsing trade: {e}")
                    continue

            logger.info(f"Scraped {len(trades)} trades for {politician_slug}")
            return trades

        except Exception as e:
            logger.error(f"Error scraping politician trades: {e}")
            return []

    def get_pelosi_trades(self, limit: int = 50) -> List[Dict]:
        """Get Nancy Pelosi's trades"""
        return self.get_politician_trades('nancy-pelosi', limit)

    def get_summary_data(self) -> Dict:
        """
        Get summary statistics from Capitol Trades

        Returns:
            Dictionary with summary data
        """
        try:
            url = self.BASE_URL

            soup = self.get_page(url)
            if not soup:
                return {}

            summary = {
                'total_trades': 0,
                'recent_purchases': 0,
                'recent_sales': 0,
                'top_politicians': []
            }

            # Try to extract summary statistics
            # This will depend on actual HTML structure
            stat_elements = soup.find_all(['div', 'span'], class_=['stat', 'metric', 'count'])

            return summary

        except Exception as e:
            logger.error(f"Error getting summary data: {e}")
            return {}
