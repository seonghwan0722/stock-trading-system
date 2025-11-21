"""
StockNear Scraper
Scrapes stock data from stocknear.com with bot detection bypass
Uses Playwright for JavaScript rendering and CAPTCHA handling
"""
import logging
from typing import List, Dict, Optional
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import json

logger = logging.getLogger(__name__)


class StockNearScraper:
    """Scraper for StockNear website with bot bypass"""

    BASE_URL = "https://stocknear.com"

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )

            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # Add stealth scripts to evade detection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            self.page = await context.new_page()
            logger.info("Playwright browser initialized")

        except Exception as e:
            logger.error(f"Error initializing Playwright: {e}")
            raise

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def wait_for_cloudflare(self):
        """Wait for Cloudflare challenge to complete"""
        try:
            # Wait for Cloudflare challenge
            await self.page.wait_for_load_state('networkidle', timeout=30000)

            # Check if we're still on Cloudflare page
            title = await self.page.title()
            if 'Just a moment' in title or 'Checking your browser' in title:
                logger.info("Waiting for Cloudflare challenge...")
                await asyncio.sleep(5)
                await self.page.wait_for_load_state('networkidle', timeout=30000)

        except Exception as e:
            logger.warning(f"Cloudflare wait timeout: {e}")

    async def get_trending_stocks(self, limit: int = 10) -> List[Dict]:
        """
        Get trending stocks

        Args:
            limit: Number of stocks to return

        Returns:
            List of trending stock dictionaries
        """
        try:
            if not self.page:
                await self.initialize()

            url = f"{self.BASE_URL}/trending"
            logger.info(f"Navigating to {url}")

            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            await self.wait_for_cloudflare()

            # Wait for content to load
            await asyncio.sleep(3)

            # Extract trending stocks
            stocks = await self.page.evaluate("""
                () => {
                    const stockElements = document.querySelectorAll('.stock-item, .ticker-card, [class*="stock"]');
                    const stocks = [];

                    for (let elem of stockElements) {
                        try {
                            const symbol = elem.querySelector('.symbol, .ticker, [class*="symbol"]')?.textContent?.trim();
                            const name = elem.querySelector('.name, .company, [class*="name"]')?.textContent?.trim();
                            const priceText = elem.querySelector('.price, [class*="price"]')?.textContent?.trim();
                            const changeText = elem.querySelector('.change, [class*="change"]')?.textContent?.trim();

                            if (symbol) {
                                stocks.push({
                                    symbol: symbol,
                                    name: name || '',
                                    price: priceText || '',
                                    change: parseFloat(changeText?.replace('%', '')) || 0
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing stock:', e);
                        }
                    }

                    return stocks.slice(0, 10);
                }
            """)

            logger.info(f"Scraped {len(stocks)} trending stocks")
            return stocks

        except Exception as e:
            logger.error(f"Error getting trending stocks: {e}")
            return []

    async def get_high_volume_stocks(self, limit: int = 10) -> List[Dict]:
        """
        Get stocks with high trading volume

        Args:
            limit: Number of stocks to return

        Returns:
            List of stock dictionaries
        """
        try:
            if not self.page:
                await self.initialize()

            url = f"{self.BASE_URL}/volume"
            logger.info(f"Navigating to {url}")

            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            await self.wait_for_cloudflare()

            await asyncio.sleep(3)

            stocks = await self.page.evaluate("""
                () => {
                    const stockElements = document.querySelectorAll('.stock-item, .ticker-card, [class*="stock"]');
                    const stocks = [];

                    for (let elem of stockElements) {
                        try {
                            const symbol = elem.querySelector('.symbol, .ticker')?.textContent?.trim();
                            const name = elem.querySelector('.name, .company')?.textContent?.trim();
                            const volume = elem.querySelector('.volume, [class*="volume"]')?.textContent?.trim();

                            if (symbol) {
                                stocks.push({
                                    symbol: symbol,
                                    name: name || '',
                                    volume: volume || 'N/A'
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing stock:', e);
                        }
                    }

                    return stocks.slice(0, 10);
                }
            """)

            logger.info(f"Scraped {len(stocks)} high volume stocks")
            return stocks

        except Exception as e:
            logger.error(f"Error getting high volume stocks: {e}")
            return []

    async def get_insider_trades(self, limit: int = 10) -> List[Dict]:
        """
        Get recent insider trading activity

        Args:
            limit: Number of trades to return

        Returns:
            List of insider trade dictionaries
        """
        try:
            if not self.page:
                await self.initialize()

            url = f"{self.BASE_URL}/insider"
            logger.info(f"Navigating to {url}")

            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            await self.wait_for_cloudflare()

            await asyncio.sleep(3)

            trades = await self.page.evaluate("""
                () => {
                    const tradeElements = document.querySelectorAll('.trade-item, .insider-trade, [class*="trade"]');
                    const trades = [];

                    for (let elem of tradeElements) {
                        try {
                            const symbol = elem.querySelector('.symbol, .ticker')?.textContent?.trim();
                            const insider = elem.querySelector('.insider, .name')?.textContent?.trim();
                            const type = elem.querySelector('.type, [class*="type"]')?.textContent?.trim();

                            if (symbol) {
                                trades.push({
                                    symbol: symbol,
                                    insider: insider || 'N/A',
                                    type: type || 'N/A'
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing trade:', e);
                        }
                    }

                    return trades.slice(0, 10);
                }
            """)

            logger.info(f"Scraped {len(trades)} insider trades")
            return trades

        except Exception as e:
            logger.error(f"Error getting insider trades: {e}")
            return []

    async def get_all_data(self) -> Dict:
        """
        Get all data from StockNear

        Returns:
            Dictionary with all scraped data
        """
        try:
            await self.initialize()

            data = {
                'trending': await self.get_trending_stocks(),
                'volume': await self.get_high_volume_stocks(),
                'insider': await self.get_insider_trades(),
                'detail': {}
            }

            return data

        except Exception as e:
            logger.error(f"Error getting all data: {e}")
            return {'trending': [], 'volume': [], 'insider': [], 'detail': {}}

        finally:
            await self.close()


# Synchronous wrapper for easier use in Flask
def scrape_stocknear_sync() -> Dict:
    """Synchronous wrapper for get_all_data"""
    try:
        scraper = StockNearScraper()
        return asyncio.run(scraper.get_all_data())
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
        return {'trending': [], 'volume': [], 'insider': [], 'detail': {}}
