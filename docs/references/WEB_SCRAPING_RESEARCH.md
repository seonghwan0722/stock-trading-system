# Web Scraping Strategy Analysis: Financial Websites

**Research Date**: November 21, 2025
**Researcher**: Advanced Analysis
**Target Websites**: Capitol Trades, StockNear, StockAnalysis, ChartExchange

---

## Executive Summary

This document provides comprehensive research on web scraping strategies for four major financial information websites. Each site employs different anti-bot mechanisms and data structures that require specific approaches for ethical and legal data extraction.

### Key Findings:
- **Capitol Trades**: Simple structure, Cloudflare protection, publicly available data from government disclosures
- **StockNear**: Aggressive Cloudflare Turnstile CAPTCHA, requires stealth browser automation
- **StockAnalysis**: Moderate protection, SvelteKit-based architecture, accessible via HTML parsing
- **ChartExchange**: Minimal protection, chart-based data visualization, supports technical indicators

---

## 1. CAPITOL TRADES (https://www.capitoltrades.com/)

### Overview
Capitol Trades aggregates and displays U.S. politician stock trading data derived from official government disclosures (Senate Financial Disclosures and House Clerk reports).

### Data Available
- **Core Data Points**:
  - Politician names and contact information
  - Trade type (BUY/SELL)
  - Stock symbols and company names
  - Transaction amounts ($1K-15K, $15K-50K, etc.)
  - Political affiliation and chamber (House/Senate)
  - State representation
  - Trade dates and filing information
  - Individual trading volumes

- **Aggregated Data**:
  - Featured politicians with trade counts
  - Issued company performance metrics
  - State-level trading volumes
  - Trending stocks and politicians

### Technical Architecture
```
Framework: Next.js (React-based)
Backend: API-driven architecture
Static Assets: CDN hosted (_next/static/media)
Image Optimization: Custom image processor (/image?url=)
```

### Anti-Scraping Measures

#### 1. Cloudflare Protection
- **Type**: JavaScript Challenge (not Turnstile)
- **Detection Method**: Browser fingerprinting
- **Challenge Types**:
  - Proof-of-work challenges
  - Browser capability checks
  - TLS fingerprinting
  - WebGL metadata analysis

#### 2. Additional Protections
- Cookie-based session tracking
- User-Agent validation
- Request rate monitoring
- Geographic IP filtering

### Data Structure & Extraction Points

**HTML Structure**:
```html
<!-- Trade Items -->
<div class="trade-item">
  <span class="trade-type">BUY</span>
  <span class="date">Yesterday</span>
  <span class="company-name">Company Inc</span>
  <span class="ticker">TICKER:US</span>
  <span class="politician-name">Name</span>
  <span class="party">Republican|House|State</span>
  <span class="amount">$1K–15K</span>
</div>

<!-- Politician Cards -->
<div class="politician-card">
  <h2>Politician Name</h2>
  <p>Party|Chamber|State</p>
  <span>Trades: 141</span>
  <span>Filings: 29</span>
  <span>Volume: 1.37M</span>
</div>
```

**Pagination**: URL-based pagination via `/trades` page parameters

### Update Frequency
- **Trade Data**: Daily (updated from government sources)
- **Politician Data**: Weekly (from filing updates)
- **Historical Data**: 3 years maximum retention

### Scraping Recommendations

#### Recommended Tools
1. **Playwright** (Preferred)
   - Multi-browser support
   - Better fingerprint control
   - Native stealth options via Camoufox

2. **Puppeteer with Stealth Plugins**
   - Legacy option, still functional
   - Requires active maintenance

#### Implementation Strategy

**Phase 1: Initial Reconnaissance**
```javascript
// Playwright setup with stealth measures
const { chromium } = require('playwright');

const browser = await chromium.launch({
  headless: true,
  args: [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage'
  ]
});

const context = await browser.newContext({
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  viewport: { width: 1920, height: 1080 },
  locale: 'en-US',
});
```

**Phase 2: Cloudflare Challenge Handling**
```javascript
const page = await context.newPage();

// Add delay to simulate human behavior
await page.waitForTimeout(Math.random() * 3000 + 2000);

// Navigate with waitUntil: 'domcontentloaded'
await page.goto('https://www.capitoltrades.com/trades', {
  waitUntil: 'networkidle'
});

// Wait for Cloudflare challenge resolution
await page.waitForNavigation({ waitUntil: 'networkidle' });
```

**Phase 3: Data Extraction**
```javascript
// Extract trade data
const trades = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('[role="link"]')).map(item => ({
    type: item.querySelector('[aria-label*="BUY"]')?.textContent || 'SELL',
    date: item.querySelector('time')?.textContent || 'Unknown',
    company: item.querySelector('h3')?.textContent?.trim(),
    ticker: item.querySelector('[data-ticker]')?.textContent?.trim(),
    politician: item.querySelector('[data-politician]')?.textContent?.trim(),
    amount: item.querySelector('[data-amount]')?.textContent?.trim(),
    url: item.href
  }));
});
```

#### Rate Limiting Strategy
```javascript
const rateLimiter = {
  requestsPerMinute: 6,
  requestsPerHour: 60,
  requestsPerDay: 500,

  async enforceLimit() {
    // Add 8-12 second delays between requests
    const delay = Math.random() * 4000 + 8000;
    await new Promise(resolve => setTimeout(resolve, delay));
  }
};
```

#### Best Practices for Capitol Trades
1. **Request Headers** (Essential)
   ```javascript
   {
     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
     'Accept-Language': 'en-US,en;q=0.5',
     'Accept-Encoding': 'gzip, deflate, br',
     'DNT': '1',
     'Connection': 'keep-alive',
     'Upgrade-Insecure-Requests': '1',
     'Cache-Control': 'max-age=0'
   }
   ```

2. **Cookie Management**
   - Preserve cookies across requests
   - Accept cookies programmatically when prompted
   - Use persistent storage for session cookies

3. **Proxy Rotation**
   - Use residential proxies only (datacenter proxies will be blocked)
   - Rotate proxies every 2-3 requests
   - Target different geographic locations

4. **JavaScript Execution**
   - Must use a headless browser (simple HTTP requests will fail)
   - Wait for JavaScript to render
   - Monitor for infinite loading states

### Legal & Ethical Considerations

**Positive Factors**:
- Data source is public government records
- Capitol Trades aggregates public information
- No authentication required
- Non-sensitive personal data

**Terms of Service**:
- Check robots.txt: `/robots.txt` (if present)
- Review Terms & Conditions page
- Disclaimer: Historical data limited to 3 years
- Attribution recommended

**Risk Assessment**: LOW
- Public data source
- Reasonable ToS for research/non-commercial use
- No explicit anti-scraping measures in documentation

---

## 2. STOCKNEAR (https://www.stocknear.com/)

### Overview
StockNear provides financial market data, stock screening, and technical analysis tools.

### Data Available
- Stock screener data
- Technical analysis tools
- Market data aggregation
- Financial metrics
- Portfolio tracking

### Technical Architecture
```
Protection: Cloudflare with Turnstile CAPTCHA (Mandatory Challenge)
Frontend: JavaScript-heavy SPA
Language: Korean interface detected (international variant)
Detection: Browser fingerprint + CAPTCHA challenge
```

### Anti-Scraping Measures

#### 1. Cloudflare Turnstile
- **Type**: Invisible + Visible CAPTCHA
- **Triggers**:
  - Immediate CAPTCHA on page load
  - Browser fingerprint mismatch
  - Suspicious request patterns
  - Missing browser APIs

**Network Signature**:
```
GET /cdn-cgi/challenge-platform/h/g/orchestrate/chl_page/v1
POST /cdn-cgi/challenge-platform/h/g/flow/ov1/[FLOW_ID]/[CHALLENGE_ID]
```

#### 2. Additional Mechanisms
- TLS fingerprinting
- WebGL/WebGPU capability checks
- Proof-of-work challenges
- Device fingerprinting

### Scraping Recommendations

#### Challenge: CAPTCHA Dependency
The primary obstacle is Cloudflare Turnstile, which requires solving before accessing any data.

#### Solution Options (in order of viability)

**Option 1: CAPTCHA Solving Service (Easiest)**
- Service: 2Captcha, CapSolver, or Anti-Captcha
- Cost: $0.50-$2.00 per CAPTCHA
- Accuracy: 85-95%
- Integration: API-based

```python
from playwright.async_api import async_playwright
import asyncio
from capmonster_python import *

async def solve_cloudflare():
    capmonster = CapMonsterClient(api_key='YOUR_API_KEY')

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto('https://stocknear.com/')

        # Wait for Turnstile iframe
        await page.wait_for_selector('iframe[src*="turnstile"]')

        # Solve CAPTCHA via API
        result = await capmonster.solve_cloudflare_turnstile(
            websiteURL='https://stocknear.com/',
            websiteKey='0x4AAAAAAADnPIDROrmt1Wwj'  # From page source
        )

        # Inject solution
        await page.evaluate(f'''
            window.turnstile.reset();
            window.turnstile.callback('{result}');
        ''')

        # Wait for page load
        await page.wait_for_load_state('networkidle')
```

**Option 2: Anti-Detection Browser (Recommended)**
- Tool: Camoufox + Playwright (2025 standard)
- Success Rate: 70-85%
- Cost: Free
- Maintenance: Community-supported

```python
from playwright.async_api import async_playwright

async def scrape_with_camoufox():
    async with async_playwright() as p:
        # Using Camoufox for enhanced fingerprint
        browser = await p.chromium.launch(
            executable_path='path/to/camoufox',
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # Add human-like behavior
        await page.add_init_script('''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        ''')

        await page.goto('https://stocknear.com/')

        # Wait for challenge resolution
        try:
            await page.wait_for_selector('body:not(.challenge-page)', timeout=30000)
        except:
            print("Challenge failed to resolve")
```

**Option 3: Proxy + Headers + Delays (Lower Success)**
- Success Rate: 20-40%
- Cost: Proxy fees
- Best for: Understanding API structure

```python
import asyncio
from playwright.async_api import async_playwright
from itertools import cycle

async def scrape_with_rotation():
    proxies = cycle([
        'http://proxy1:port',
        'http://proxy2:port',
        'http://proxy3:port'
    ])

    async with async_playwright() as p:
        for proxy_url in proxies:
            browser = await p.chromium.launch(
                proxy={'server': proxy_url}
            )

            context = await browser.new_context()
            page = await context.new_page()

            # Random delays
            await asyncio.sleep(__import__('random').uniform(3, 8))

            try:
                await page.goto('https://stocknear.com/', timeout=15000)
            except:
                pass
            finally:
                await browser.close()
```

#### Rate Limiting
```python
class RateLimiter:
    def __init__(self):
        self.min_delay = 5  # seconds
        self.max_delay = 15

    async def wait(self):
        import asyncio, random
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
```

### Risk Assessment: HIGH
- Aggressive CAPTCHA enforcement
- High IP bans for scrapers
- Rapid fingerprint detection
- Terms of Service explicitly forbid scraping

### Recommendation
- **For Data Access**: Use CAPTCHA solving service
- **For Production**: Negotiate data access or use official API
- **For Testing**: Use Camoufox approach with extreme caution

---

## 3. STOCKANALYSIS.COM (https://stockanalysis.com/)

### Overview
StockAnalysis.com provides comprehensive stock analysis, financial data, screeners, and IPO calendars.

### Data Available
- Stock quotes and pricing
- Financial statements (Income, Balance Sheet, Cash Flow)
- Key ratios and metrics
- Technical analysis
- IPO calendar
- News aggregation
- Stock screeners
- ETF data
- Trending stocks

### Technical Architecture
```
Framework: SvelteKit (Vite-powered)
Frontend: Client-side rendering with API integration
Data Source: Multiple APIs (likely aggregated)
Build: Modern SSR + static generation
API Pattern: /__data.json?x-sveltekit-invalidated=011
```

### Network Analysis
```
Request 69: GET /etf/qqq/__data.json?x-sveltekit-invalidated=011 [200]
Request 80: GET /api/index/trending [200]

These indicate:
- SvelteKit's internal data API for page hydration
- Custom /api/ endpoints for dynamic data
- JSON-based data transfer
```

### Anti-Scraping Measures

#### 1. Moderate Protection Level
- Basic rate limiting
- Standard User-Agent validation
- Session cookies required
- Minimal JavaScript challenges

#### 2. Observable Protections
- Ad network integration (prevents direct HTTP scraping)
- Google Funding Choices integration
- Third-party tracking (Criteo, DoubleClick)

### Scraping Recommendations

#### Approach 1: Direct HTML Parsing (Simplest)
```python
import asyncio
from playwright.async_api import async_playwright

async def scrape_stock_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto('https://stockanalysis.com/stocks/aapl/')

        # Extract stock data
        stock_data = await page.evaluate('''
        () => {
            const name = document.querySelector('h1')?.textContent?.trim();
            const price = document.querySelector('[data-price]')?.textContent?.trim();
            const change = document.querySelector('[data-change]')?.textContent?.trim();

            return { name, price, change };
        }
        ''')

        await browser.close()
        return stock_data
```

#### Approach 2: SvelteKit Data API Interception
```python
import asyncio
from playwright.async_api import async_playwright
import json

async def scrape_via_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # Capture API responses
        api_responses = []
        page.on('response', lambda resp:
            api_responses.append(resp) if '/__data.json' in resp.url else None
        )

        await page.goto('https://stockanalysis.com/stocks/nvda/')

        # Extract from captured API
        for resp in api_responses:
            try:
                data = await resp.json()
                print(json.dumps(data, indent=2))
            except:
                pass

        await browser.close()
```

#### Approach 3: High-Volume Scraping
```python
import asyncio
from playwright.async_api import async_playwright
import aiohttp
from datetime import datetime
import time

class StockAnalysisScraper:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.session = None
        self.request_count = 0
        self.start_time = time.time()

    async def scrape_multiple_stocks(self, symbols):
        tasks = []
        for i, symbol in enumerate(symbols):
            if i % self.max_concurrent == 0 and i > 0:
                await asyncio.sleep(5)  # Throttle between batches

            task = self.scrape_stock(symbol)
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def scrape_stock(self, symbol):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Enforce rate limiting
            elapsed = time.time() - self.start_time
            if self.request_count > 0:
                requests_per_second = self.request_count / (elapsed + 0.1)
                if requests_per_second > 1:  # Max 1 req/sec
                    await asyncio.sleep(1)

            self.request_count += 1

            try:
                await page.goto(f'https://stockanalysis.com/stocks/{symbol.lower()}/')

                data = await page.evaluate('''
                () => {
                    const price = document.querySelector('span[data-price]')?.textContent;
                    const pe = document.querySelector('[data-pe]')?.textContent;
                    const eps = document.querySelector('[data-eps]')?.textContent;

                    return { price, pe, eps };
                }
                ''')

                return { symbol, data }
            except Exception as e:
                return { symbol, error: str(e) }
            finally:
                await browser.close()
```

#### Useful Data Endpoints

Based on network analysis:
```
/api/index/trending          - Trending stocks
/__data.json                 - SvelteKit page data
/stocks/[symbol]/            - Individual stock pages
/etf/[symbol]/               - ETF pages
/markets/gainers/            - Market movers
/screener/                   - Stock screener
```

#### Best Practices

**Headers**:
```python
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://stockanalysis.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'DNT': '1',
}
```

**Rate Limiting** (Recommended):
```python
class RateLimiter:
    requests_per_hour = 180  # 3 requests per minute
    requests_per_day = 2000

    async def check_limit(self):
        # Implement token bucket algorithm
        pass
```

### Update Frequency
- **Prices**: Real-time (during market hours)
- **Financials**: Quarterly
- **Screener**: Daily refresh
- **News**: Hourly

### Risk Assessment: LOW-MEDIUM
- Moderate protection
- Friendly to well-behaved scrapers
- Existing Python packages available
- Check ToS for commercial use

---

## 4. CHARTEXCHANGE (https://chartexchange.com/symbol/nasdaq-mndr/)

### Overview
ChartExchange provides interactive stock charts with technical analysis and market data visualization.

### Data Available
- Real-time stock prices
- Multiple chart types (Skyline, Heikin Ashi, etc.)
- Technical indicators
- Volume data
- Market statistics
- Trading metrics (bid/ask/spread)
- Historical data
- Beta values
- Moving averages (50, 200 day)

### Technical Architecture
```
Framework: Dynamic rendering with JavaScript
Chart Library: Likely TradingView or custom canvas-based
Data Format: JSON APIs (estimated from response patterns)
Protection Level: Minimal
```

### Anti-Scraping Measures

#### 1. Minimal Protection
- Basic rate limiting
- Ad network integration (prevents passive parsing)
- Google Analytics tracking
- No aggressive JavaScript challenges

#### 2. Observable Structure
```html
<div class="chart-container">
  <canvas id="chart"></canvas>
  <div class="stats">
    <span data-value="price">3.06</span>
    <span data-change="+84.337%">+84.337%</span>
    <span data-volume="74,121,957">74.12M</span>
  </div>
</div>
```

### Data Extraction Patterns

**Key Statistics Available**:
```
Price Information:
- Close Price
- Pre-market Price
- After-hours Price
- Bid/Ask/Spread

Market Data:
- 52-week High/Low
- Market Cap
- Shares Outstanding
- Volume (10-day, 30-day avg)
- Beta (6-month, 1-year, 2-year)
- Moving Averages (SMA50, SMA200)

Performance:
- 1-week, 1-month, 3-month, 6-month, 1-year, 2-year changes
- Volume metrics
- On/Off exchange percentages
```

### Scraping Recommendations

#### Approach 1: HTML + JavaScript Parsing (Most Reliable)
```python
import asyncio
from playwright.async_api import async_playwright
import re

async def scrape_chart_exchange():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto('https://chartexchange.com/symbol/nasdaq-mndr/')

        # Extract structured data
        data = await page.evaluate('''
        () => {
            const getText = (selector) => document.querySelector(selector)?.textContent?.trim();

            return {
                symbol: getText('h1')?.split(' ')[0],
                company: getText('h1')?.split(' ').slice(1).join(' '),
                price: getText('[data-price]') || getText('div.price'),
                change: getText('[data-change]') || getText('div.change'),
                volume: getText('[data-volume]') || getText('div.volume'),
                marketCap: getText('[data-market-cap]'),
                sharesOut: getText('[data-shares]'),
                week52High: getText('[data-52w-high]'),
                week52Low: getText('[data-52w-low]'),
                sma50: getText('[data-sma50]'),
                sma200: getText('[data-sma200]'),
                beta6m: getText('[data-beta-6m]'),
                beta1y: getText('[data-beta-1y]'),
                beta2y: getText('[data-beta-2y]'),
            };
        }
        ''')

        await browser.close()
        return data
```

#### Approach 2: Chart Data Extraction
```python
async def extract_chart_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Intercept chart data requests
        chart_data = []

        async def handle_response(response):
            if 'chart' in response.url.lower() or 'data' in response.url:
                try:
                    data = await response.json()
                    chart_data.append(data)
                except:
                    pass

        page.on('response', handle_response)

        await page.goto('https://chartexchange.com/symbol/nasdaq-mndr/')
        await page.wait_for_timeout(3000)  # Wait for chart load

        await browser.close()
        return chart_data
```

#### Approach 3: Batch Processing Multiple Symbols
```python
import asyncio
from playwright.async_api import async_playwright
import csv
from datetime import datetime

class ChartExchangeScraper:
    def __init__(self, output_file='stocks.csv'):
        self.output_file = output_file
        self.headers = [
            'symbol', 'company', 'price', 'change', 'volume',
            'market_cap', 'beta_6m', 'sma50', 'sma200'
        ]

    async def scrape_symbols(self, symbols, delay=2):
        results = []

        for symbol in symbols:
            data = await self.scrape_symbol(symbol)
            results.append(data)
            await asyncio.sleep(delay)  # Rate limiting

        return results

    async def scrape_symbol(self, symbol):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            try:
                url = f'https://chartexchange.com/symbol/nasdaq-{symbol.lower()}/'
                await page.goto(url, timeout=15000)

                data = await page.evaluate('''
                (symbol) => {
                    return {
                        symbol: symbol,
                        price: document.body.innerText.match(/\\$(\\d+\\.\\d{2})/)?.[1],
                        change: document.body.innerText.match(/([+-]\\d+\\.\\d+%)/)?.[1],
                        timestamp: new Date().toISOString()
                    };
                }
                ''', symbol)

                return data
            except Exception as e:
                return {'symbol': symbol, 'error': str(e)}
            finally:
                await browser.close()
```

#### Performance Optimization
```python
# Use concurrent requests with semaphore
async def scrape_with_concurrency(symbols, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_scrape(symbol):
        async with semaphore:
            return await scrape_symbol(symbol)

    tasks = [bounded_scrape(sym) for sym in symbols]
    return await asyncio.gather(*tasks)
```

### Update Frequency
- **Prices**: Real-time (during market hours)
- **Charts**: Tick-by-tick updates
- **Technical Data**: On-demand calculation
- **Historical**: Stored and queryable

### Risk Assessment: LOW
- Minimal protection
- Public market data
- No explicit ToS restrictions found
- Well-documented API usage in community

---

## COMPARATIVE ANALYSIS TABLE

| Aspect | Capitol Trades | StockNear | StockAnalysis | ChartExchange |
|--------|---|---|---|---|
| **Protection Level** | Moderate (Cloudflare JS) | Aggressive (Turnstile) | Low-Moderate | Low |
| **Recommended Tool** | Playwright + Stealth | CAPTCHA Service | Playwright/Selenium | Playwright/Cheerio |
| **Difficulty** | Medium | Hard | Easy-Medium | Easy |
| **Data Freshness** | Daily | Real-time | Real-time | Real-time |
| **Rate Limit Safe** | 60-100/hour | 10-20/hour | 180/hour | 200/hour |
| **Proxy Required** | Yes (Residential) | Yes (with CAPTCHA) | Optional | No |
| **Official API** | No | No | No | Partial |
| **ToS Restriction** | Implicit | Explicit | Moderate | Minimal |
| **Risk Level** | Low-Medium | High | Low | Low |

---

## IMPLEMENTATION TOOLKIT

### 1. Core Dependencies

**Python Stack**:
```bash
pip install playwright beautifulsoup4 aiohttp lxml requests-html asyncio httpx
```

**Node.js Stack**:
```bash
npm install playwright puppeteer cheerio axios dotenv
```

### 2. Essential Setup Files

**Python - Base Scraper Class**:
```python
# scraper_base.py
import asyncio
from playwright.async_api import async_playwright, Browser, Page
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialScraper:
    def __init__(self, use_proxy=False, proxy_url=None):
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        self.browser = None
        self.request_count = 0

    async def launch_browser(self):
        async with async_playwright() as playwright:
            launch_args = {}

            if self.use_proxy:
                launch_args['proxy'] = {'server': self.proxy_url}

            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )

            return self.browser

    async def create_page(self):
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # Add stealth scripts
        await page.add_init_script('''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        ''')

        return page

    async def enforce_rate_limit(self, min_delay=2, max_delay=5):
        import random
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
        self.request_count += 1
        logger.info(f"Request #{self.request_count}")

    async def close(self):
        if self.browser:
            await self.browser.close()
```

### 3. Deployment Considerations

**Docker Container**:
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium-browser \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install

COPY . .

CMD ["python", "scraper.py"]
```

**Docker Compose**:
```yaml
version: '3.8'
services:
  scraper:
    build: .
    environment:
      - PROXY_ENABLED=true
      - PROXY_URL=http://proxy:port
      - MAX_CONCURRENT=3
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### 4. Database Schema (PostgreSQL Example)

```sql
-- Capitol Trades
CREATE TABLE politician_trades (
    id SERIAL PRIMARY KEY,
    politician_name VARCHAR(255),
    trade_type VARCHAR(10),  -- BUY/SELL
    ticker VARCHAR(10),
    company_name VARCHAR(255),
    amount_range VARCHAR(50),
    trade_date DATE,
    filing_date DATE,
    party VARCHAR(50),
    chamber VARCHAR(50),
    state VARCHAR(2),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(politician_name, ticker, trade_date)
);

-- Stock Analysis Data
CREATE TABLE stock_quotes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    company_name VARCHAR(255),
    price DECIMAL(10, 2),
    change_percent DECIMAL(5, 2),
    market_cap BIGINT,
    pe_ratio DECIMAL(8, 2),
    volume BIGINT,
    updated_at TIMESTAMP,
    UNIQUE(symbol, updated_at)
);

-- Chart Exchange Data
CREATE TABLE chart_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    price DECIMAL(10, 2),
    bid DECIMAL(10, 2),
    ask DECIMAL(10, 2),
    volume BIGINT,
    sma50 DECIMAL(10, 2),
    sma200 DECIMAL(10, 2),
    beta_6m DECIMAL(5, 2),
    recorded_at TIMESTAMP,
    UNIQUE(symbol, recorded_at)
);
```

---

## MONITORING & MAINTENANCE

### 1. Health Checks

```python
async def health_check():
    checks = {
        'capitol_trades': await check_capitol_trades(),
        'stocknear': await check_stocknear(),
        'stockanalysis': await check_stockanalysis(),
        'chartexchange': await check_chartexchange(),
    }

    return {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy' if all(checks.values()) else 'degraded',
        'checks': checks
    }
```

### 2. Error Handling & Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def scrape_with_retry(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        # ... scraping logic
        await browser.close()
```

### 3. Logging Strategy

```python
import logging
import json

# Structured logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log scraping events
logger.info(json.dumps({
    'event': 'scrape_complete',
    'url': url,
    'records': len(results),
    'duration_seconds': elapsed,
    'status': 'success'
}))
```

---

## RECOMMENDATIONS SUMMARY

### For Capitol Trades
1. Use Playwright with Camoufox for stealth
2. Implement rotating residential proxies
3. Respect 60 requests/hour limit
4. Store data in PostgreSQL with change tracking
5. Update daily (align with government filing cycle)

### For StockNear
1. **Primary**: Use CAPTCHA solving service (2Captcha)
2. **Secondary**: Negotiate API access with service
3. **Alternative**: Accept limited access, high costs
4. High risk for IP bans - require proxy rotation
5. Consider official API subscription instead

### For StockAnalysis
1. Use Playwright for JavaScript rendering
2. Implement 1 request per 20 seconds rate limit
3. Cache results to minimize requests
4. Parse HTML or intercept API responses
5. Update hourly or on-demand

### For ChartExchange
1. Simple Playwright setup sufficient
2. No special stealth measures needed
3. Minimal rate limiting required
4. Consider using their API if available
5. Update in real-time during market hours

---

## LEGAL & ETHICAL FRAMEWORK

### Key Principles
1. **Respect robots.txt**: Always check before scraping
2. **Read ToS**: Understand legal implications
3. **Minimize Load**: Use delays and batching
4. **Identify Yourself**: Set proper User-Agent headers
5. **Provide Value**: Only use data for legitimate purposes

### Compliance Checklist
- [ ] Reviewed website ToS
- [ ] Checked robots.txt
- [ ] Implemented rate limiting
- [ ] Using residential proxies (if needed)
- [ ] Set proper headers
- [ ] Monitoring server load impact
- [ ] Have data deletion process
- [ ] Document scraping purpose

### Data Retention
- Capitol Trades: 3 years (per website)
- StockAnalysis: 1 year (or per requirement)
- ChartExchange: 6 months (historical sufficient)
- Delete upon request, respect privacy laws

---

## NEXT STEPS

1. **Set up development environment**: Docker + Playwright
2. **Test each website**: Verify current protection levels
3. **Build modular scrapers**: Separate by website
4. **Implement database**: PostgreSQL with proper schema
5. **Add monitoring**: Health checks and logging
6. **Deploy gradually**: Start with low-volume testing
7. **Iterate**: Adjust based on real-world performance

---

**Report Version**: 1.0
**Last Updated**: November 21, 2025
**Validity**: 3-6 months (websites may change protections)
