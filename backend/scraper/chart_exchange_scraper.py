"""
ChartExchange Scraper
Scrapes chart and technical analysis data from chartexchange.com
"""
from .base_scraper import BaseScraper
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class ChartExchangeScraper(BaseScraper):
    """Scraper for ChartExchange website"""

    BASE_URL = "https://chartexchange.com"

    def __init__(self):
        super().__init__()

    def get_symbol_data(self, symbol: str) -> Dict:
        """
        Get data for a specific symbol

        Args:
            symbol: Stock symbol (e.g., 'nasdaq-mndr' or 'NASDAQ:MNDR')

        Returns:
            Dictionary with chart and technical data
        """
        try:
            # Normalize symbol format
            symbol = symbol.lower().replace(':', '-')

            url = f"{self.BASE_URL}/symbol/{symbol}/"
            soup = self.get_page(url)

            if not soup:
                return {}

            data = {
                'symbol': symbol.upper(),
                'technicals': self._extract_technicals(soup),
                'patterns': self._extract_patterns(soup),
                'trading': self._extract_trading_data(soup)
            }

            logger.info(f"Scraped data for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error getting symbol data: {e}")
            return {}

    def _extract_technicals(self, soup) -> Dict:
        """Extract technical indicators"""
        technicals = {}

        try:
            # Look for technical indicator tables or sections
            tech_elements = soup.find_all(['div', 'tr'], class_=['technical', 'indicator', 'metric'])

            for elem in tech_elements:
                try:
                    label = elem.find(['span', 'th', 'div'], class_=['label', 'name'])
                    value = elem.find(['span', 'td', 'div'], class_=['value', 'data'])

                    if label and value:
                        technicals[label.get_text(strip=True)] = value.get_text(strip=True)
                except:
                    continue

            # Common technical indicators
            indicators = ['RSI', 'MACD', 'Moving Average', 'Bollinger Bands', 'Volume', 'Support', 'Resistance']

            for indicator in indicators:
                if indicator not in technicals:
                    # Try to find by text search
                    elem = soup.find(text=re.compile(indicator, re.I))
                    if elem:
                        parent = elem.find_parent(['tr', 'div'])
                        if parent:
                            value = parent.find(['td', 'span'], class_=['value', 'data'])
                            if value:
                                technicals[indicator] = value.get_text(strip=True)

        except Exception as e:
            logger.error(f"Error extracting technicals: {e}")

        return technicals

    def _extract_patterns(self, soup) -> List[str]:
        """Extract chart patterns"""
        patterns = []

        try:
            # Look for pattern sections
            pattern_section = soup.find(['div', 'section'], class_=['patterns', 'chart-patterns'])

            if pattern_section:
                pattern_elements = pattern_section.find_all(['div', 'li', 'span'], class_=['pattern', 'signal'])

                for elem in pattern_elements:
                    pattern_text = elem.get_text(strip=True)
                    if pattern_text and len(pattern_text) > 2:
                        patterns.append(pattern_text)

            # Also look for pattern keywords in text
            pattern_keywords = ['Head and Shoulders', 'Double Top', 'Double Bottom', 'Triangle', 'Flag', 'Wedge']

            for keyword in pattern_keywords:
                if soup.find(text=re.compile(keyword, re.I)) and keyword not in patterns:
                    patterns.append(keyword)

        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")

        return patterns

    def _extract_trading_data(self, soup) -> Dict:
        """Extract trading information"""
        trading = {}

        try:
            # Look for trading data
            data_elements = soup.find_all(['div', 'tr'], class_=['trading', 'quote', 'market-data'])

            for elem in data_elements:
                try:
                    label = elem.find(['span', 'th'], class_=['label', 'name'])
                    value = elem.find(['span', 'td'], class_=['value', 'data'])

                    if label and value:
                        trading[label.get_text(strip=True)] = value.get_text(strip=True)
                except:
                    continue

            # Common trading metrics
            metrics = ['Last Price', 'Open', 'High', 'Low', 'Volume', 'Market Cap', 'Bid', 'Ask']

            for metric in metrics:
                if metric not in trading:
                    elem = soup.find(text=re.compile(metric, re.I))
                    if elem:
                        parent = elem.find_parent(['tr', 'div'])
                        if parent:
                            value = parent.find(['td', 'span'], class_=['value', 'data'])
                            if value:
                                trading[metric] = value.get_text(strip=True)

        except Exception as e:
            logger.error(f"Error extracting trading data: {e}")

        return trading

    def get_market_overview(self) -> Dict:
        """
        Get general market overview

        Returns:
            Dictionary with market data
        """
        try:
            url = self.BASE_URL
            soup = self.get_page(url)

            if not soup:
                return {}

            overview = {
                'trending': self._extract_trending_symbols(soup),
                'active': self._extract_active_symbols(soup)
            }

            logger.info("Scraped market overview")
            return overview

        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {}

    def _extract_trending_symbols(self, soup) -> List[Dict]:
        """Extract trending symbols"""
        trending = []

        try:
            trend_elements = soup.find_all(['div', 'tr'], class_=['trending', 'popular'])

            for elem in trend_elements[:10]:
                try:
                    symbol = elem.find(['a', 'span'], class_=['symbol', 'ticker'])
                    name = elem.find(['span', 'div'], class_=['name', 'title'])

                    if symbol:
                        trending.append({
                            'symbol': symbol.get_text(strip=True),
                            'name': name.get_text(strip=True) if name else ''
                        })
                except:
                    continue

        except Exception as e:
            logger.error(f"Error extracting trending symbols: {e}")

        return trending

    def _extract_active_symbols(self, soup) -> List[Dict]:
        """Extract most active symbols"""
        active = []

        try:
            active_elements = soup.find_all(['div', 'tr'], class_=['active', 'most-active'])

            for elem in active_elements[:10]:
                try:
                    symbol = elem.find(['a', 'span'], class_=['symbol', 'ticker'])
                    volume = elem.find(['span', 'td'], class_=['volume'])

                    if symbol:
                        active.append({
                            'symbol': symbol.get_text(strip=True),
                            'volume': volume.get_text(strip=True) if volume else 'N/A'
                        })
                except:
                    continue

        except Exception as e:
            logger.error(f"Error extracting active symbols: {e}")

        return active
