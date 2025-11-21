"""
StockAnalysis Scraper
Scrapes stock analysis data from stockanalysis.com
"""
from .base_scraper import BaseScraper
import logging
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)


class StockAnalysisScraper(BaseScraper):
    """Scraper for StockAnalysis website"""

    BASE_URL = "https://stockanalysis.com"

    def __init__(self):
        super().__init__()

    def get_stock_overview(self, symbol: str) -> Dict:
        """
        Get stock overview data

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Dictionary with stock overview data
        """
        try:
            url = f"{self.BASE_URL}/stocks/{symbol.lower()}/"
            soup = self.get_page(url)

            if not soup:
                return {}

            overview = {
                'symbol': symbol.upper(),
                'metrics': self._extract_metrics(soup),
                'financials': self._extract_financials(soup),
                'valuation': self._extract_valuation(soup)
            }

            logger.info(f"Scraped overview for {symbol}")
            return overview

        except Exception as e:
            logger.error(f"Error getting stock overview: {e}")
            return {}

    def _extract_metrics(self, soup) -> Dict:
        """Extract key metrics from page"""
        metrics = {}

        try:
            # Look for metric tables or cards
            metric_elements = soup.find_all(['div', 'tr'], class_=['metric', 'data-row', 'stat'])

            for elem in metric_elements:
                try:
                    label_elem = elem.find(['span', 'th', 'div'], class_=['label', 'name'])
                    value_elem = elem.find(['span', 'td', 'div'], class_=['value', 'data'])

                    if label_elem and value_elem:
                        label = label_elem.get_text(strip=True)
                        value = value_elem.get_text(strip=True)
                        metrics[label] = value
                except:
                    continue

            # Common metrics to look for
            metric_names = ['Market Cap', 'P/E Ratio', 'EPS', 'Dividend Yield', 'Volume', '52 Week High', '52 Week Low']

            for metric_name in metric_names:
                if metric_name not in metrics:
                    # Try alternative search
                    elem = soup.find(text=re.compile(metric_name, re.I))
                    if elem:
                        parent = elem.find_parent(['tr', 'div', 'dl'])
                        if parent:
                            value = parent.find(['td', 'dd', 'span'], class_=['value', 'data'])
                            if value:
                                metrics[metric_name] = value.get_text(strip=True)

        except Exception as e:
            logger.error(f"Error extracting metrics: {e}")

        return metrics

    def _extract_financials(self, soup) -> Dict:
        """Extract financial data"""
        financials = {}

        try:
            # Look for financial tables
            tables = soup.find_all('table', class_=['financials', 'data-table'])

            for table in tables:
                rows = table.find_all('tr')

                for row in rows:
                    try:
                        cells = row.find_all(['th', 'td'])
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            financials[label] = value
                    except:
                        continue

        except Exception as e:
            logger.error(f"Error extracting financials: {e}")

        return financials

    def _extract_valuation(self, soup) -> Dict:
        """Extract valuation metrics"""
        valuation = {}

        try:
            # Look for valuation-specific elements
            valuation_section = soup.find(['div', 'section'], class_=['valuation', 'ratios'])

            if valuation_section:
                items = valuation_section.find_all(['div', 'tr'], class_=['item', 'row'])

                for item in items:
                    try:
                        label = item.find(['span', 'th'], class_=['label', 'name'])
                        value = item.find(['span', 'td'], class_=['value', 'data'])

                        if label and value:
                            valuation[label.get_text(strip=True)] = value.get_text(strip=True)
                    except:
                        continue

        except Exception as e:
            logger.error(f"Error extracting valuation: {e}")

        return valuation

    def get_market_overview(self) -> Dict:
        """
        Get overall market overview

        Returns:
            Dictionary with market data
        """
        try:
            url = self.BASE_URL
            soup = self.get_page(url)

            if not soup:
                return {}

            overview = {
                'indices': self._extract_indices(soup),
                'trending': self._extract_trending(soup)
            }

            logger.info("Scraped market overview")
            return overview

        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {}

    def _extract_indices(self, soup) -> Dict:
        """Extract market indices"""
        indices = {}

        try:
            index_elements = soup.find_all(['div', 'tr'], class_=['index', 'market-index'])

            for elem in index_elements:
                try:
                    name = elem.find(['span', 'th'], class_=['name', 'symbol'])
                    value = elem.find(['span', 'td'], class_=['value', 'price'])
                    change = elem.find(['span', 'td'], class_=['change', 'percent'])

                    if name:
                        indices[name.get_text(strip=True)] = {
                            'value': value.get_text(strip=True) if value else 'N/A',
                            'change': change.get_text(strip=True) if change else 'N/A'
                        }
                except:
                    continue

        except Exception as e:
            logger.error(f"Error extracting indices: {e}")

        return indices

    def _extract_trending(self, soup) -> list:
        """Extract trending stocks"""
        trending = []

        try:
            trend_elements = soup.find_all(['div', 'tr'], class_=['trending', 'popular', 'top-stock'])

            for elem in trend_elements[:10]:
                try:
                    symbol = elem.find(['a', 'span'], class_=['symbol', 'ticker'])
                    if symbol:
                        trending.append(symbol.get_text(strip=True))
                except:
                    continue

        except Exception as e:
            logger.error(f"Error extracting trending stocks: {e}")

        return trending

    def search_stock(self, query: str) -> list:
        """
        Search for stocks

        Args:
            query: Search query

        Returns:
            List of matching stocks
        """
        try:
            url = f"{self.BASE_URL}/search/"
            params = {'q': query}

            soup = self.get_page(url, params=params)

            if not soup:
                return []

            results = []
            result_elements = soup.find_all(['div', 'li'], class_=['result', 'search-result'])

            for elem in result_elements:
                try:
                    symbol = elem.find(['span', 'a'], class_=['symbol', 'ticker'])
                    name = elem.find(['span', 'div'], class_=['name', 'company'])

                    if symbol:
                        results.append({
                            'symbol': symbol.get_text(strip=True),
                            'name': name.get_text(strip=True) if name else ''
                        })
                except:
                    continue

            logger.info(f"Found {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
