# Scraping Service Architecture

## Overview

A Python-based microservice designed to handle web scraping from multiple sources with anti-bot detection, rate limiting, and retry logic.

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Web framework
- **Playwright** - Browser automation (for JavaScript-heavy sites)
- **BeautifulSoup4** - HTML parsing
- **httpx** - Async HTTP client
- **Redis** - Queue management and caching
- **PostgreSQL** - Data persistence
- **Pydantic** - Data validation

## Project Structure

```
scraping-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection
│   ├── redis_client.py         # Redis connection
│   │
│   ├── scrapers/               # Scraper implementations
│   │   ├── __init__.py
│   │   ├── base.py             # Base scraper class
│   │   ├── capitol_trades.py
│   │   ├── stocknear.py
│   │   ├── stock_analysis.py
│   │   ├── chart_exchange.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── browser.py      # Browser automation utilities
│   │       ├── anti_bot.py     # Anti-bot detection bypass
│   │       └── parsers.py      # Common parsing functions
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── trade.py
│   │   ├── stock.py
│   │   └── politician.py
│   │
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   │
│   └── workers/                # Background workers
│       ├── __init__.py
│       ├── scheduler.py        # Job scheduling
│       └── processors.py       # Data processing
│
├── tests/
│   ├── test_scrapers/
│   └── test_api/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Base Scraper Class

```python
# app/scrapers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging
from playwright.async_api import async_playwright, Browser, Page
import httpx
from bs4 import BeautifulSoup
import random

from app.redis_client import get_redis
from app.database import get_db
from app.scrapers.utils.anti_bot import AntiBot

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all scrapers"""

    def __init__(self, use_browser: bool = False):
        self.use_browser = use_browser
        self.browser: Optional[Browser] = None
        self.anti_bot = AntiBot()
        self.session: Optional[httpx.AsyncClient] = None
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    async def __aenter__(self):
        if self.use_browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
        else:
            self.session = httpx.AsyncClient(
                headers=self.anti_bot.get_headers(),
                timeout=30.0,
                follow_redirects=True
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.session:
            await self.session.aclose()

    @abstractmethod
    async def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """Main scraping method to be implemented by subclasses"""
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped data"""
        pass

    async def fetch_page(self, url: str, use_js: bool = False) -> str:
        """Fetch page content with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if use_js and self.browser:
                    return await self._fetch_with_browser(url)
                elif self.session:
                    return await self._fetch_with_httpx(url)
                else:
                    raise ValueError("No fetching method available")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    async def _fetch_with_browser(self, url: str) -> str:
        """Fetch page using Playwright"""
        page = await self.browser.new_page()

        # Apply anti-bot measures
        await self.anti_bot.apply_stealth(page)

        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Random delay to mimic human behavior
            await asyncio.sleep(random.uniform(1, 3))

            content = await page.content()
            return content
        finally:
            await page.close()

    async def _fetch_with_httpx(self, url: str) -> str:
        """Fetch page using httpx"""
        response = await self.session.get(url)
        response.raise_for_status()
        return response.text

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html, 'html.parser')

    async def save_to_db(self, data: List[Dict[str, Any]], table: str):
        """Save scraped data to database"""
        # Implementation depends on your DB layer
        pass

    async def cache_result(self, key: str, data: Any, ttl: int = 3600):
        """Cache scraping results in Redis"""
        redis = await get_redis()
        await redis.setex(key, ttl, json.dumps(data))

    async def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached scraping results"""
        redis = await get_redis()
        cached = await redis.get(key)
        if cached:
            return json.loads(cached)
        return None
```

## Capitol Trades Scraper

```python
# app/scrapers/capitol_trades.py
from typing import List, Dict, Any
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.models.trade import Trade

class CapitolTradesScraper(BaseScraper):
    """Scraper for capitoltrades.com"""

    BASE_URL = "https://www.capitoltrades.com"

    def __init__(self):
        # Capitol Trades has JavaScript rendering
        super().__init__(use_browser=True)

    async def scrape(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Scrape recent trades from Capitol Trades

        Args:
            days: Number of days to look back

        Returns:
            List of trade dictionaries
        """
        trades = []

        # Capitol Trades shows trades in a table format
        url = f"{self.BASE_URL}/trades"
        html = await self.fetch_page(url, use_js=True)
        soup = self.parse_html(html)

        # Example parsing (adjust based on actual HTML structure)
        trade_rows = soup.select('table.trades-table tbody tr')

        for row in trade_rows:
            try:
                trade_data = self._parse_trade_row(row)

                # Filter by date
                if trade_data and self._is_within_days(trade_data['transaction_date'], days):
                    if self.validate_data(trade_data):
                        trades.append(trade_data)
            except Exception as e:
                logger.error(f"Error parsing trade row: {str(e)}")
                continue

        return trades

    def _parse_trade_row(self, row: BeautifulSoup) -> Dict[str, Any]:
        """Parse individual trade row"""
        cells = row.find_all('td')

        if len(cells) < 6:
            return None

        # Extract data (adjust selectors based on actual HTML)
        politician_name = cells[0].get_text(strip=True)
        ticker = cells[1].get_text(strip=True)
        transaction_type = cells[2].get_text(strip=True)
        transaction_date = self._parse_date(cells[3].get_text(strip=True))
        disclosure_date = self._parse_date(cells[4].get_text(strip=True))
        amount_range = cells[5].get_text(strip=True)

        # Parse amount range (e.g., "$1,001 - $15,000")
        amount_min, amount_max = self._parse_amount_range(amount_range)

        return {
            'politician_name': politician_name,
            'ticker': ticker,
            'transaction_type': transaction_type,
            'transaction_date': transaction_date,
            'disclosure_date': disclosure_date,
            'amount_range': amount_range,
            'amount_min': amount_min,
            'amount_max': amount_max,
            'source': 'capitol_trades',
            'scraped_at': datetime.utcnow().isoformat()
        }

    def _parse_date(self, date_str: str) -> str:
        """Parse date string to ISO format"""
        # Example: "11/20/2025" -> "2025-11-20"
        try:
            dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
            return dt.date().isoformat()
        except:
            return None

    def _parse_amount_range(self, range_str: str) -> tuple:
        """Parse amount range string"""
        # Example: "$1,001 - $15,000"
        amounts = re.findall(r'\$[\d,]+', range_str)
        if len(amounts) == 2:
            min_amt = int(amounts[0].replace('$', '').replace(',', ''))
            max_amt = int(amounts[1].replace('$', '').replace(',', ''))
            return min_amt, max_amt
        return None, None

    def _is_within_days(self, date_str: str, days: int) -> bool:
        """Check if date is within specified days"""
        if not date_str:
            return False
        trade_date = datetime.fromisoformat(date_str).date()
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
        return trade_date >= cutoff_date

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate trade data"""
        required_fields = [
            'politician_name', 'ticker', 'transaction_type',
            'transaction_date', 'amount_range'
        ]
        return all(data.get(field) for field in required_fields)
```

## Anti-Bot Detection Utilities

```python
# app/scrapers/utils/anti_bot.py
import random
from typing import Dict
from playwright.async_api import Page

class AntiBot:
    """Utilities to bypass bot detection"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]

    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    async def apply_stealth(self, page: Page):
        """Apply stealth techniques to Playwright page"""

        # Override navigator.webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Override plugins
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # Override languages
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        # Override chrome runtime
        await page.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)

        # Override permissions
        await page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        # Set random user agent
        await page.set_extra_http_headers(self.get_headers())

        # Set viewport to random common resolution
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
        ]
        viewport = random.choice(viewports)
        await page.set_viewport_size(viewport)
```

## Scraper Implementations for Other Sources

```python
# app/scrapers/stocknear.py
class StockNearScraper(BaseScraper):
    """Scraper for stocknear.com"""

    BASE_URL = "https://stocknear.com"

    def __init__(self):
        # StockNear likely has bot detection
        super().__init__(use_browser=True)

    async def scrape_stock_data(self, ticker: str) -> Dict[str, Any]:
        """Scrape stock data for a specific ticker"""
        url = f"{self.BASE_URL}/stocks/{ticker}"
        html = await self.fetch_page(url, use_js=True)
        soup = self.parse_html(html)

        # Parse stock metrics (adjust selectors)
        data = {
            'ticker': ticker,
            'price': self._extract_price(soup),
            'pe_ratio': self._extract_metric(soup, 'P/E'),
            'market_cap': self._extract_metric(soup, 'Market Cap'),
            # Add more metrics
        }

        return data

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data.get('ticker') and data.get('price')


# app/scrapers/stock_analysis.py
class StockAnalysisScraper(BaseScraper):
    """Scraper for stockanalysis.com"""

    BASE_URL = "https://stockanalysis.com"

    def __init__(self):
        super().__init__(use_browser=False)  # Try without browser first

    async def scrape_fundamentals(self, ticker: str) -> Dict[str, Any]:
        """Scrape fundamental data"""
        url = f"{self.BASE_URL}/stocks/{ticker}/statistics/"
        html = await self.fetch_page(url)
        soup = self.parse_html(html)

        # Parse tables
        data = self._parse_statistics_table(soup)
        return data

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return bool(data)


# app/scrapers/chart_exchange.py
class ChartExchangeScraper(BaseScraper):
    """Scraper for chartexchange.com (short interest data)"""

    BASE_URL = "https://chartexchange.com"

    async def scrape_short_interest(self, ticker: str) -> Dict[str, Any]:
        """Scrape short interest data"""
        url = f"{self.BASE_URL}/symbol/{ticker}/short-volume/"
        html = await self.fetch_page(url)
        soup = self.parse_html(html)

        data = {
            'ticker': ticker,
            'short_volume': self._extract_short_volume(soup),
            'short_volume_ratio': self._extract_ratio(soup),
            # More metrics
        }

        return data

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return data.get('ticker') and data.get('short_volume') is not None
```

## API Endpoints

```python
# app/api/routes.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional

router = APIRouter()

@router.post("/scrape/capitol-trades")
async def trigger_capitol_trades_scrape(
    background_tasks: BackgroundTasks,
    days: int = 7
):
    """Trigger Capitol Trades scraping job"""
    job_id = await queue_scraping_job('capitol_trades', {'days': days})
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Scraping job queued successfully"
    }

@router.get("/scrape/status/{job_id}")
async def get_scrape_status(job_id: str):
    """Get status of scraping job"""
    status = await get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.post("/scrape/stock/{ticker}")
async def scrape_stock_data(ticker: str, background_tasks: BackgroundTasks):
    """Scrape data for specific stock from all sources"""
    job_id = await queue_scraping_job('stock_data', {'ticker': ticker})
    return {"job_id": job_id, "ticker": ticker}
```

## Rate Limiting Strategy

```python
# app/scrapers/utils/rate_limiter.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict
import redis.asyncio as redis

class RateLimiter:
    """Rate limiter for scraping requests"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.limits = {
            'capitol_trades': {'requests': 60, 'period': 60},  # 60 req/min
            'stocknear': {'requests': 30, 'period': 60},
            'stock_analysis': {'requests': 100, 'period': 60},
            'chart_exchange': {'requests': 50, 'period': 60},
        }

    async def acquire(self, source: str) -> bool:
        """Acquire rate limit token"""
        limit = self.limits.get(source, {'requests': 30, 'period': 60})
        key = f"ratelimit:{source}"

        current = await self.redis.incr(key)

        if current == 1:
            await self.redis.expire(key, limit['period'])

        if current > limit['requests']:
            ttl = await self.redis.ttl(key)
            await asyncio.sleep(ttl if ttl > 0 else limit['period'])
            return await self.acquire(source)

        return True

    async def wait_if_needed(self, source: str):
        """Wait if rate limit is exceeded"""
        await self.acquire(source)
```

## Deployment Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  scraping-service:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/stockdb
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 2G
    volumes:
      - ./logs:/app/logs

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: python -m app.workers.scheduler
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/stockdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 5
```

## Monitoring and Logging

```python
# app/config.py
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging"""
    logger = logging.getLogger()
    handler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger
```

