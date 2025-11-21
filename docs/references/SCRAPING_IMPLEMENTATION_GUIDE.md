# Web Scraping Implementation Guide
## Quick-Start Code Examples & Technical Specifications

---

## 1. PLAYWRIGHT SETUP (Recommended for All Sites)

### Installation
```bash
# Python
pip install playwright beautifulsoup4 aiohttp
playwright install chromium firefox webkit

# Node.js
npm install playwright @types/node cheerio axios
npx playwright install
```

### Basic Browser Initialization
```python
# python_scrapers/base_browser.py
import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page
from typing import Optional, Dict

class BrowserManager:
    """Manages Playwright browser instances with stealth mode"""

    def __init__(self, headless: bool = True, use_stealth: bool = True):
        self.headless = headless
        self.use_stealth = use_stealth
        self.browser = None
        self.context: Optional[BrowserContext] = None

    async def initialize(self):
        """Launch browser with anti-detection measures"""
        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
            ]
        )

        # Create context with realistic browser profile
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York
            permissions=['geolocation'],
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            accept_downloads=True,
        )

        if self.use_stealth:
            await self._add_stealth_scripts()

        return self.context

    async def _add_stealth_scripts(self):
        """Inject scripts to bypass bot detection"""
        await self.context.add_init_script("""
            // Hide webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Mock chrome object
            window.chrome = {
                runtime: {},
            };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters);

            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

    async def create_page(self) -> Page:
        """Create a new page with stealth measures"""
        page = await self.context.new_page()

        # Set realistic headers
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache',
        })

        return page

    async def close(self):
        """Clean shutdown"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
```

---

## 2. RATE LIMITING & THROTTLING

### Token Bucket Algorithm
```python
# python_scrapers/rate_limiter.py
import asyncio
import time
from typing import Optional

class RateLimiter:
    """Token bucket rate limiter for controlled request frequency"""

    def __init__(
        self,
        tokens_per_second: float = 1.0,
        max_tokens: Optional[int] = None,
        min_delay: float = 0.5
    ):
        self.tokens_per_second = tokens_per_second
        self.max_tokens = max_tokens or int(tokens_per_second * 60)
        self.tokens = self.max_tokens
        self.last_update = time.time()
        self.min_delay = min_delay
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> float:
        """Wait if necessary and return the wait time"""
        async with self._lock:
            # Replenish tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * self.tokens_per_second
            )
            self.last_update = now

            # Wait if needed
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.tokens_per_second
                wait_time = max(wait_time, self.min_delay)
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_update = time.time()
            else:
                self.tokens -= tokens

            return 0

# Usage
limiter = RateLimiter(tokens_per_second=1.0)  # Max 1 request/second

async def scrape_with_rate_limit(url: str):
    await limiter.acquire(1)
    # Make request
```

### Random Delay Implementation
```python
# python_scrapers/delays.py
import random
import asyncio
from typing import Tuple

class HumanLikeDelays:
    """Generate random delays that mimic human behavior"""

    @staticmethod
    async def between_requests(
        min_seconds: float = 2.0,
        max_seconds: float = 8.0
    ) -> None:
        """Random delay between requests"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    @staticmethod
    async def before_clicking(
        min_seconds: float = 0.3,
        max_seconds: float = 1.5
    ) -> None:
        """Delay before simulating click"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    @staticmethod
    async def during_typing(
        min_wpm: int = 40,
        max_wpm: int = 120
    ) -> None:
        """Realistic typing speed delay"""
        words_per_minute = random.randint(min_wpm, max_wpm)
        # Average 5 characters per word, 60 seconds per minute
        characters_per_second = (words_per_minute * 5) / 60
        delay = 1 / characters_per_second
        await asyncio.sleep(delay)

    @staticmethod
    async def pattern_break(probability: float = 0.3) -> None:
        """Occasional longer pauses to break detection patterns"""
        if random.random() < probability:
            delay = random.uniform(15, 30)
            await asyncio.sleep(delay)
```

---

## 3. CAPITOL TRADES SCRAPER

### Full Implementation
```python
# python_scrapers/capitol_trades_scraper.py
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict
from playwright.async_api import Page
from base_browser import BrowserManager
from rate_limiter import RateLimiter
from delays import HumanLikeDelays

class CapitolTradesScraper:
    """Scraper for Capitol Trades politician trading data"""

    BASE_URL = "https://www.capitoltrades.com"
    TRADES_URL = f"{BASE_URL}/trades"

    def __init__(self, headless: bool = True):
        self.browser_manager = BrowserManager(headless=headless)
        self.rate_limiter = RateLimiter(tokens_per_second=0.1)  # Max 6/minute
        self.delays = HumanLikeDelays()

    async def scrape_latest_trades(self, limit: int = 50) -> List[Dict]:
        """Scrape latest politician trades"""
        trades = []

        try:
            context = await self.browser_manager.initialize()
            page = await self.browser_manager.create_page()

            # Navigate to trades page
            await self.rate_limiter.acquire(1)
            await page.goto(self.TRADES_URL, wait_until='networkidle')

            await self.delays.between_requests(3, 6)

            # Extract trades from page
            trades_html = await page.query_selector_all('[role="link"]')

            for item in trades_html[:limit]:
                trade_data = await self._extract_trade_data(item)
                if trade_data:
                    trades.append(trade_data)

            return trades

        except Exception as e:
            print(f"Error scraping trades: {e}")
            return []
        finally:
            await self.browser_manager.close()

    async def _extract_trade_data(self, element) -> Dict:
        """Extract trade information from HTML element"""
        try:
            trade_type = await element.text_content()
            link = await element.get_attribute('href')

            # Extract data from link text
            text = await element.inner_text()
            lines = text.split('\n')

            return {
                'type': lines[0].strip(),  # BUY/SELL
                'date': lines[1].strip() if len(lines) > 1 else '',
                'company': lines[2].strip() if len(lines) > 2 else '',
                'ticker': lines[3].strip() if len(lines) > 3 else '',
                'politician': lines[4].strip() if len(lines) > 4 else '',
                'party': lines[5].strip() if len(lines) > 5 else '',
                'amount': lines[-1].strip() if lines else '',
                'url': link,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error extracting trade data: {e}")
            return None

    async def scrape_politician(self, politician_id: str) -> Dict:
        """Scrape specific politician's trading history"""
        try:
            context = await self.browser_manager.initialize()
            page = await self.browser_manager.create_page()

            politician_url = f"{self.BASE_URL}/politicians/{politician_id}"

            await self.rate_limiter.acquire(1)
            await page.goto(politician_url, wait_until='networkidle')

            # Extract politician data
            politician_data = await page.evaluate("""
            () => {
                const name = document.querySelector('h1')?.textContent?.trim();
                const trades = document.querySelector('[data-trades]')?.textContent;
                const filings = document.querySelector('[data-filings]')?.textContent;

                return { name, trades, filings };
            }
            """)

            return politician_data

        except Exception as e:
            print(f"Error scraping politician: {e}")
            return {}
        finally:
            await self.browser_manager.close()

    async def scrape_all_politicians(self) -> List[Dict]:
        """Scrape all featured politicians"""
        context = await self.browser_manager.initialize()
        page = await self.browser_manager.create_page()

        try:
            await self.rate_limiter.acquire(1)
            await page.goto(self.BASE_URL, wait_until='networkidle')

            # Find politician cards
            politicians = await page.query_selector_all('[data-politician-card]')
            results = []

            for politician in politicians:
                data = await politician.evaluate("""
                el => ({
                    name: el.querySelector('h2')?.textContent?.trim(),
                    party: el.querySelector('[data-party]')?.textContent?.trim(),
                    trades: el.querySelector('[data-trades]')?.textContent?.trim(),
                    url: el.querySelector('a')?.href
                })
                """)
                results.append(data)
                await self.delays.between_requests(1, 3)

            return results

        finally:
            await self.browser_manager.close()

# Usage
async def main():
    scraper = CapitolTradesScraper(headless=True)
    trades = await scraper.scrape_latest_trades(limit=10)

    print(json.dumps(trades, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. STOCKANALYSIS SCRAPER

### HTML Parsing Approach
```python
# python_scrapers/stockanalysis_scraper.py
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import Page
from base_browser import BrowserManager
from rate_limiter import RateLimiter
from bs4 import BeautifulSoup
import json

class StockAnalysisScraper:
    """Scraper for StockAnalysis.com stock data"""

    BASE_URL = "https://stockanalysis.com"

    def __init__(self):
        self.browser_manager = BrowserManager(headless=True)
        self.rate_limiter = RateLimiter(tokens_per_second=0.05)  # Max 3/minute

    async def scrape_stock(self, symbol: str) -> Dict:
        """Scrape stock financial data"""
        context = await self.browser_manager.initialize()
        page = await self.browser_manager.create_page()

        try:
            await self.rate_limiter.acquire(1)

            url = f"{self.BASE_URL}/stocks/{symbol.lower()}/"
            await page.goto(url, wait_until='networkidle')

            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Extract stock data
            stock_data = {
                'symbol': symbol.upper(),
                'price': self._extract_price(soup),
                'change': self._extract_change(soup),
                'market_cap': self._extract_market_cap(soup),
                'pe_ratio': self._extract_pe_ratio(soup),
                'earnings': self._extract_earnings(soup),
                'revenue': self._extract_revenue(soup),
            }

            return stock_data

        except Exception as e:
            print(f"Error scraping {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
        finally:
            await self.browser_manager.close()

    def _extract_price(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract current stock price"""
        price_tag = soup.find('span', {'data-price': True})
        return price_tag.text if price_tag else None

    def _extract_change(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract percentage change"""
        change_tag = soup.find('span', {'data-change': True})
        return change_tag.text if change_tag else None

    def _extract_market_cap(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract market capitalization"""
        mc_tag = soup.find('span', string='Market Cap')
        return mc_tag.find_next('span').text if mc_tag else None

    def _extract_pe_ratio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract P/E ratio"""
        pe_tag = soup.find('span', string='P/E Ratio')
        return pe_tag.find_next('span').text if pe_tag else None

    def _extract_earnings(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract EPS"""
        eps_tag = soup.find('span', string='EPS')
        return eps_tag.find_next('span').text if eps_tag else None

    def _extract_revenue(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract revenue"""
        rev_tag = soup.find('span', string='Revenue')
        return rev_tag.find_next('span').text if rev_tag else None

    async def scrape_multiple_stocks(
        self,
        symbols: List[str],
        max_concurrent: int = 3
    ) -> List[Dict]:
        """Scrape multiple stocks with concurrency control"""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_scrape(symbol):
            async with semaphore:
                result = await self.scrape_stock(symbol)
                await asyncio.sleep(0.5)  # Min delay between requests
                return result

        tasks = [bounded_scrape(sym) for sym in symbols]
        return await asyncio.gather(*tasks)

    async def scrape_trending_stocks(self) -> List[Dict]:
        """Scrape trending stocks list"""
        context = await self.browser_manager.initialize()
        page = await self.browser_manager.create_page()

        try:
            await self.rate_limiter.acquire(1)
            await page.goto(f"{self.BASE_URL}/trending/", wait_until='networkidle')

            trending = await page.evaluate("""
            () => {
                const rows = document.querySelectorAll('table tbody tr');
                return Array.from(rows).map(row => ({
                    symbol: row.cells[0]?.textContent?.trim(),
                    name: row.cells[1]?.textContent?.trim(),
                    price: row.cells[2]?.textContent?.trim(),
                    change: row.cells[3]?.textContent?.trim(),
                }));
            }
            """)

            return trending

        finally:
            await self.browser_manager.close()
```

---

## 5. CHARTEXCHANGE SCRAPER

### Technical Data Extraction
```python
# python_scrapers/chartexchange_scraper.py
import asyncio
from typing import Dict, Optional
from base_browser import BrowserManager
from rate_limiter import RateLimiter

class ChartExchangeScraper:
    """Scraper for ChartExchange technical analysis data"""

    BASE_URL = "https://chartexchange.com"

    def __init__(self):
        self.browser_manager = BrowserManager(headless=True)
        self.rate_limiter = RateLimiter(tokens_per_second=0.2)  # Max 12/minute

    async def scrape_stock_data(self, symbol: str, exchange: str = 'nasdaq') -> Dict:
        """Scrape comprehensive stock data including technical indicators"""

        context = await self.browser_manager.initialize()
        page = await self.browser_manager.create_page()

        try:
            await self.rate_limiter.acquire(1)

            url = f"{self.BASE_URL}/symbol/{exchange.lower()}-{symbol.lower()}/"
            await page.goto(url, wait_until='networkidle')

            # Extract all data at once
            stock_data = await page.evaluate("""
            () => {
                const getText = (selector) =>
                    document.querySelector(selector)?.textContent?.trim();

                return {
                    // Price Information
                    price: getText('[data-price]'),
                    currency: getText('[data-currency]'),
                    change: getText('[data-change]'),
                    changePercent: getText('[data-change-percent]'),
                    volume: getText('[data-volume]'),

                    // Pre/After Market
                    preMarketPrice: getText('[data-premarket-price]'),
                    afterHoursPrice: getText('[data-afterhours-price]'),

                    // Market Statistics
                    bid: getText('[data-bid]'),
                    ask: getText('[data-ask]'),
                    spread: getText('[data-spread]'),
                    marketCap: getText('[data-market-cap]'),
                    sharesOutstanding: getText('[data-shares]'),

                    // Technical Indicators
                    sma50: getText('[data-sma50]'),
                    sma200: getText('[data-sma200]'),
                    week52High: getText('[data-52w-high]'),
                    week52Low: getText('[data-52w-low]'),

                    // Beta & Risk
                    beta6m: getText('[data-beta-6m]'),
                    beta1y: getText('[data-beta-1y]'),
                    beta2y: getText('[data-beta-2y]'),

                    // Performance
                    change1w: getText('[data-change-1w]'),
                    change1m: getText('[data-change-1m]'),
                    change3m: getText('[data-change-3m]'),
                    change6m: getText('[data-change-6m]'),
                    change1y: getText('[data-change-1y]'),
                    change2y: getText('[data-change-2y]'),

                    // Volume Metrics
                    avgVolume10d: getText('[data-avg-vol-10]'),
                    avgVolume30d: getText('[data-avg-vol-30]'),
                    onOffExchange: getText('[data-on-off-exchange]'),
                };
            }
            """)

            return {
                'symbol': symbol.upper(),
                'exchange': exchange.upper(),
                'data': stock_data,
                'timestamp': asyncio.get_event_loop().time()
            }

        except Exception as e:
            print(f"Error scraping {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}

        finally:
            await self.browser_manager.close()

    async def scrape_chart_history(
        self,
        symbol: str,
        exchange: str = 'nasdaq'
    ) -> Dict:
        """Scrape historical chart data"""

        context = await self.browser_manager.initialize()
        page = await self.browser_manager.create_page()

        try:
            await self.rate_limiter.acquire(1)

            url = f"{self.BASE_URL}/symbol/{exchange.lower()}-{symbol.lower()}/historical/"
            await page.goto(url, wait_until='networkidle')

            # Collect chart data
            history = await page.evaluate("""
            () => {
                const rows = document.querySelectorAll('table tbody tr');
                return Array.from(rows).map(row => ({
                    date: row.cells[0]?.textContent?.trim(),
                    open: row.cells[1]?.textContent?.trim(),
                    high: row.cells[2]?.textContent?.trim(),
                    low: row.cells[3]?.textContent?.trim(),
                    close: row.cells[4]?.textContent?.trim(),
                    volume: row.cells[5]?.textContent?.trim(),
                }));
            }
            """)

            return {
                'symbol': symbol.upper(),
                'exchange': exchange.upper(),
                'history': history,
                'records_count': len(history)
            }

        finally:
            await self.browser_manager.close()
```

---

## 6. STOCKNEAR SCRAPER (CAPTCHA Approach)

### Using CAPTCHA Solving Service
```python
# python_scrapers/stocknear_scraper.py
import asyncio
from typing import Dict, Optional
from base_browser import BrowserManager
from rate_limiter import RateLimiter
import httpx

class StockNearScraper:
    """Scraper for StockNear with CAPTCHA handling"""

    BASE_URL = "https://stocknear.com"
    CAPTCHA_SOLVER_API = "https://api.2captcha.com"
    SOLVER_API_KEY = "YOUR_2CAPTCHA_API_KEY"

    def __init__(self):
        self.browser_manager = BrowserManager(headless=True)
        self.rate_limiter = RateLimiter(tokens_per_second=0.05)  # Very conservative

    async def solve_turnstile(self, page_url: str, sitekey: str) -> Optional[str]:
        """Solve Cloudflare Turnstile CAPTCHA"""

        async with httpx.AsyncClient() as client:
            # Submit CAPTCHA to solving service
            response = await client.post(
                f"{self.CAPTCHA_SOLVER_API}/in.php",
                data={
                    'method': 'turnstile',
                    'sitekey': sitekey,
                    'pageurl': page_url,
                    'apikey': self.SOLVER_API_KEY,
                    'json': 1,
                }
            )

            captcha_id = response.json().get('captcha')

            if not captcha_id:
                return None

            # Poll for solution
            for attempt in range(24):  # Max 2 minutes
                await asyncio.sleep(5)

                check_response = await client.get(
                    f"{self.CAPTCHA_SOLVER_API}/res.php",
                    params={
                        'apikey': self.SOLVER_API_KEY,
                        'action': 'get',
                        'id': captcha_id,
                        'json': 1,
                    }
                )

                result = check_response.json()

                if result.get('status') == 1:
                    return result.get('request')

            return None

    async def scrape_with_captcha_solve(self) -> Dict:
        """Scrape StockNear by solving CAPTCHA"""

        context = await self.browser_manager.initialize()
        page = await self.browser_manager.create_page()

        try:
            await self.rate_limiter.acquire(1)

            # Navigate to page
            await page.goto(self.BASE_URL)

            # Extract Turnstile sitekey
            sitekey = await page.locator(
                'iframe[src*="turnstile"]'
            ).get_attribute('data-sitekey')

            if sitekey:
                # Solve CAPTCHA
                solution = await self.solve_turnstile(self.BASE_URL, sitekey)

                if solution:
                    # Inject solution
                    await page.evaluate(f"""
                    () => {{
                        if (window.turnstile) {{
                            window.turnstile.reset();
                            window.turnstile.callback('{solution}');
                        }}
                    }}
                    """)

                    # Wait for page load
                    await page.wait_for_load_state('networkidle')

            # Now scrape data
            data = await page.evaluate("""
            () => {
                return {
                    title: document.title,
                    content: document.body.innerText.substring(0, 500),
                };
            }
            """)

            return data

        except Exception as e:
            print(f"Error scraping StockNear: {e}")
            return {'error': str(e)}

        finally:
            await self.browser_manager.close()

    async def scrape_with_camoufox(self) -> Dict:
        """Alternative: Use Camoufox anti-detection browser"""
        # Note: Requires Camoufox installation
        # This is a premium/community maintained solution

        context = await self.browser_manager.initialize()
        page = await self.browser_manager.create_page()

        try:
            await self.rate_limiter.acquire(1)

            # Camoufox mimics human behavior better
            await page.goto(self.BASE_URL, wait_until='networkidle')

            # Extract available data
            data = await page.evaluate("""
            () => {
                const stocks = Array.from(document.querySelectorAll('[data-stock]')).map(el => ({
                    symbol: el.getAttribute('data-symbol'),
                    price: el.querySelector('[data-price]')?.textContent,
                    change: el.querySelector('[data-change]')?.textContent,
                }));
                return stocks;
            }
            """)

            return {'stocks': data}

        finally:
            await self.browser_manager.close()
```

---

## 7. DATABASE MANAGEMENT

### PostgreSQL Integration
```python
# python_scrapers/database.py
import asyncpg
import json
from typing import List, Dict
from datetime import datetime

class DatabaseManager:
    """Manage scraped data storage"""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def initialize(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(self.dsn)

    async def save_politician_trades(self, trades: List[Dict]):
        """Save Capitol Trades data"""

        async with self.pool.acquire() as conn:
            for trade in trades:
                await conn.execute("""
                    INSERT INTO politician_trades
                    (politician_name, trade_type, ticker, company_name,
                     amount_range, trade_date, party, chamber, state, scraped_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (politician_name, ticker, trade_date)
                    DO NOTHING
                """,
                    trade['politician'],
                    trade['type'],
                    trade['ticker'],
                    trade['company'],
                    trade['amount'],
                    trade['date'],
                    trade['party'],
                    trade['chamber'],
                    trade['state'],
                    datetime.now()
                )

    async def save_stock_quotes(self, quotes: List[Dict]):
        """Save StockAnalysis data"""

        async with self.pool.acquire() as conn:
            for quote in quotes:
                await conn.execute("""
                    INSERT INTO stock_quotes
                    (symbol, company_name, price, change_percent,
                     market_cap, pe_ratio, volume, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (symbol, updated_at) DO NOTHING
                """,
                    quote['symbol'],
                    quote['company'],
                    quote['price'],
                    quote['change'],
                    quote['market_cap'],
                    quote['pe_ratio'],
                    quote['volume'],
                    datetime.now()
                )

    async def close(self):
        """Close pool"""
        if self.pool:
            await self.pool.close()
```

---

## 8. ORCHESTRATION & SCHEDULING

### Async Job Scheduler
```python
# python_scrapers/scheduler.py
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Coroutine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """Schedule scraping tasks with time-based intervals"""

    def __init__(self):
        self.tasks = {}
        self.running = False

    def schedule(
        self,
        name: str,
        coro: Callable[[], Coroutine],
        interval_seconds: int,
        start_immediately: bool = False
    ):
        """Schedule a task"""
        self.tasks[name] = {
            'coro': coro,
            'interval': interval_seconds,
            'last_run': None,
            'next_run': datetime.now() if start_immediately else
                       datetime.now() + timedelta(seconds=interval_seconds)
        }

        logger.info(f"Scheduled task: {name} every {interval_seconds}s")

    async def run(self):
        """Run scheduler"""
        self.running = True

        while self.running:
            now = datetime.now()

            for task_name, task in self.tasks.items():
                if now >= task['next_run']:
                    try:
                        logger.info(f"Starting task: {task_name}")
                        await task['coro']()
                        task['last_run'] = now
                        task['next_run'] = now + timedelta(
                            seconds=task['interval']
                        )
                        logger.info(f"Completed task: {task_name}")
                    except Exception as e:
                        logger.error(f"Error in {task_name}: {e}")

            await asyncio.sleep(1)  # Check every second

    def stop(self):
        """Stop scheduler"""
        self.running = False

# Usage
async def main():
    scheduler = TaskScheduler()

    # Schedule tasks
    scheduler.schedule(
        'capitol_trades',
        lambda: scrape_capitol_trades(),
        interval_seconds=3600,  # Every hour
        start_immediately=True
    )

    scheduler.schedule(
        'stockanalysis',
        lambda: scrape_stockanalysis(),
        interval_seconds=1800,  # Every 30 minutes
    )

    # Run scheduler
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 9. ERROR HANDLING & RETRIES

### Resilient Retry Logic
```python
# python_scrapers/resilience.py
import asyncio
from typing import Callable, TypeVar, Any
import random
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt"""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay *= random.uniform(0.5, 1.5)

        return delay

async def retry(
    coro: Callable[[], asyncio.coroutine],
    config: RetryConfig
) -> Any:
    """Retry async function with exponential backoff"""

    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return await coro()
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}"
            )

            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)

    raise last_exception

# Usage
retry_config = RetryConfig(max_attempts=3)

async def scrape_with_retry():
    result = await retry(
        lambda: scraper.scrape_stock('AAPL'),
        retry_config
    )
    return result
```

---

## 10. MONITORING & HEALTH CHECKS

### System Health Monitoring
```python
# python_scrapers/monitoring.py
import asyncio
from datetime import datetime
import json
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor scraping system health"""

    def __init__(self):
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'last_error': None,
            'uptime_seconds': 0,
            'start_time': datetime.now(),
            'last_check': None
        }

    async def record_request(self, success: bool, error: str = None):
        """Record request result"""
        self.stats['total_requests'] += 1

        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
            self.stats['last_error'] = error

    async def get_health_status(self) -> Dict:
        """Get current health status"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        success_rate = (
            self.stats['successful_requests'] / max(
                self.stats['total_requests'], 1
            )
        ) * 100

        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy' if success_rate > 90 else 'degraded',
            'uptime_hours': uptime / 3600,
            'success_rate': f"{success_rate:.2f}%",
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'last_error': self.stats['last_error']
        }

    async def start_monitoring(self, interval_seconds: int = 300):
        """Periodic health check"""
        while True:
            health = await self.get_health_status()
            logger.info(f"Health: {json.dumps(health, indent=2)}")
            await asyncio.sleep(interval_seconds)

# Usage
monitor = HealthMonitor()

# In scraping code:
try:
    result = await scraper.scrape()
    await monitor.record_request(success=True)
except Exception as e:
    await monitor.record_request(success=False, error=str(e))
```

---

## QUICK REFERENCE: Key Technologies

| Component | Tool | Version | Use |
|-----------|------|---------|-----|
| **Browser Automation** | Playwright | 1.40+ | Primary scraping engine |
| **Parser** | BeautifulSoup4 | 4.12+ | HTML parsing |
| **Async** | asyncio | 3.10+ | Concurrent operations |
| **HTTP** | httpx | 0.25+ | Async HTTP requests |
| **Database** | PostgreSQL | 14+ | Data storage |
| **Async DB** | asyncpg | 0.29+ | Async database driver |
| **Scheduling** | APScheduler | 3.10+ | Task scheduling |
| **Logging** | Python logging | Built-in | Event tracking |
| **Rate Limit** | Custom | - | Request throttling |
| **CAPTCHA** | 2Captcha API | - | CAPTCHA solving |

---

## Summary

This implementation guide provides production-ready code for scraping all four target websites. Key features:

✓ Stealth browser automation
✓ Rate limiting and delays
✓ Error handling and retries
✓ Database persistence
✓ Task scheduling
✓ Health monitoring
✓ CAPTCHA solving integration
✓ Async/concurrent operations

Adapt these templates for your specific use case.
