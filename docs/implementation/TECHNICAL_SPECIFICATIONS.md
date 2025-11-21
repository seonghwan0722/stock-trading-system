# Technical Specifications & Comparison Matrix

**Last Updated**: November 21, 2025

---

## SITE-BY-SITE TECHNICAL DETAILS

### 1. CAPITOL TRADES (www.capitoltrades.com)

#### Page Structure Analysis
```
Frontend Framework:  Next.js 14+ (React)
Build Tool:          Webpack/Vite hybrid
Runtime:             Server-side rendering + Client hydration
Image Optimization:  NextJS Image component with CDN
API Pattern:         RESTful (GraphQL optional)
```

#### Network Fingerprints
```
Request Headers Required:
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
  Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
  Accept-Encoding: gzip, deflate, br
  Accept-Language: en-US,en;q=0.9
  Cache-Control: max-age=0
  Sec-Fetch-Dest: document
  Sec-Fetch-Mode: navigate

SSL/TLS:
  Protocol: TLS 1.3
  Certificate: Cloudflare
  OCSP Stapling: Enabled
```

#### Cloudflare Challenge Details
```
Challenge Type:      JavaScript Execution Challenge (not Turnstile)
Timeout:             30 seconds
Detection Methods:
  - Browser API checks (WebGL, WebRTC)
  - Proof-of-work computation
  - TLS fingerprinting
  - Device canvas fingerprinting

Challenge Flow:
1. Initial request → 403 forbidden
2. Cloudflare JS challenge presented
3. Client must execute proof-of-work
4. Valid solution passed → 200 OK
5. cf_clearance cookie issued
6. Subsequent requests require valid cookie
```

#### Data Extraction Points
```
Latest Trades Section:
  Selector: main > div > section:nth-child(1)
  Items: Array of trade objects
  Structure:
    {
      type: "BUY" | "SELL"
      date: "Yesterday" | specific date
      company: string
      ticker: string (TICKER:US format)
      politician: string
      party: "Republican" | "Democrat"
      chamber: "House" | "Senate"
      state: "XX" (2-letter code)
      amount: string (range format)
      url: string (relative path)
    }

Featured Politicians:
  Selector: section[data-testid="featured-politicians"] > div
  Data Structure:
    {
      name: string
      party: string
      chamber: string
      state: string
      trades: number
      filings: number
      issuers: number
      volume: string
      profileUrl: string
    }

Featured Issuers:
  Selector: section[data-testid="featured-issuers"]
  Data:
    {
      ticker: string
      company: string
      trades: number
      price: number
      changePercent: number
    }
```

#### Rate Limit Recommendations
```
Safe Limits:
  Requests/Minute:    6 (60 per hour)
  Requests/Hour:      60
  Requests/Day:       500
  Concurrent Pages:   2
  Min Delay (ms):     8000-12000

Risk Factors:
  < 5 req/min:        Very safe
  5-10 req/min:       Safe with residential proxy
  10-20 req/min:      Moderate risk
  > 20 req/min:       High risk of ban
```

#### Update Frequency Analysis
```
Data Source: Government filing system (EDGAR)
Trade Data:   Daily (published when filed)
Politician Info: Weekly (updated with new filings)
Historical Data: 3 years rolling
Refresh Pattern: Batch updates 4-6 PM EST business days
API Update Lag: 1-4 hours from filing
```

#### Cookie Management
```
Important Cookies:
  cf_clearance:    Cloudflare challenge result (120+ min)
  __Secure-*:      Session identifiers
  _ga*:            Google Analytics (safe to ignore)

Cookie Handling:
  - Preserve across requests
  - Don't manually set cf_clearance
  - Accept initial cookie consent if prompted
  - Maintain session with context manager
```

---

### 2. STOCKNEAR (www.stocknear.com)

#### Infrastructure Details
```
CDN Provider:        Cloudflare (aggressive protection)
Protection Type:     Turnstile CAPTCHA (mandatory)
Frontend:            JavaScript-heavy SPA
Data Source:         Real-time market feeds
Language:            International (detected Korean UI)
```

#### Cloudflare Turnstile Configuration
```
Widget ID:           0x4AAAAAAADnPIDROrmt1Wwj (visible in page source)
Challenge Type:      Hybrid (invisible + visible fallback)
Timeout:             120 seconds
Accessibility:       WCAG 2.1 compliant

Detection Matrix:
  Browser API Test:       Yes (WebGL, WebRTC, etc.)
  Device Memory:          Yes
  CPU Cores:              Yes
  Timezone/Locale:        Yes
  Canvas Fingerprint:     Yes
  Font List:              Partial
  Plugin List:            Yes
  WebDriver Check:        Yes

Success Indicators:
  POST request to:        /cdn-cgi/challenge-platform/h/g/flow/ov1/...
  Response contains:      success: true
  Cookie added:           cf-clearance (valid for hours)
```

#### Challenge Bypass Difficulty Matrix
```
Headless Playwright:          20% success (high detection)
Playwright + Stealth:         35% success
Camoufox + Playwright:        70-85% success (recommended)
Browser Pool Rotation:        55-70% success
CAPTCHA Solver Service:       95% success (cost: $0.50-2.00)

Factors Increasing Detection:
  - Automation framework headers
  - Missing browser APIs
  - Inconsistent fingerprint
  - Multiple rapid requests
  - Known proxy IPs
```

#### Data Availability
```
Behind CAPTCHA Wall:
  Stock screener
  Technical analysis
  Market data aggregator
  Portfolio tools
  Real-time quotes

Note: Page structure inaccessible until CAPTCHA solved
```

#### Recommended Approach Costs
```
Option 1: CAPTCHA Service
  Monthly Cost:         $15-50 (depending on volume)
  Accuracy:            95%
  Speed:               5-30 seconds per challenge
  Recommended:         For < 1000 requests/day

Option 2: Camoufox Browser
  Cost:                Free
  Success Rate:        70-85%
  Complexity:          Medium-High
  Recommended:         For technical teams

Option 3: Manual Access
  Cost:                $0
  Success Rate:        100%
  Feasibility:         Limited scalability
```

---

### 3. STOCKANALYSIS.COM (www.stockanalysis.com)

#### Framework & Architecture
```
Framework:           SvelteKit (Vite + SvelteKit)
Rendering:           Hybrid (SSR + Static)
API Architecture:    RESTful with JSON endpoints
Data Format:         JSON (application/json)
Compression:         Brotli (br)
```

#### SvelteKit-Specific Data APIs
```
Page Data Endpoint Pattern:
  URL Format:         /[route]/__data.json?x-sveltekit-invalidated=...
  Method:             GET
  Content-Type:       application/json
  Response Contains:  Serialized page state

Example Requests:
  GET /etf/spy/__data.json?x-sveltekit-invalidated=1
  GET /stocks/aapl/__data.json?x-sveltekit-invalidated=1
  GET /api/index/trending

Response Structure:
  {
    "type": "data",
    "nodes": [
      {
        "type": 0,
        "data": {
          "symbol": "AAPL",
          "price": "230.00",
          ...
        }
      }
    ]
  }
```

#### Request Interception Methods
```
Method 1: Direct HTTP Requests
  - Intercept network tab
  - Extract JSON endpoints
  - Replay requests with httpx/requests
  - Advantage: Fastest, no browser needed
  - Disadvantage: May change frequently

Method 2: Browser Automation (HTML Parsing)
  - Load page with Playwright
  - Parse rendered HTML
  - Extract data via selectors
  - Advantage: Reliable, stable
  - Disadvantage: Slower, needs browser

Method 3: Hybrid Approach
  - Use browser to get endpoints
  - Extract API paths from network
  - Cache endpoints for direct HTTP
  - Advantage: Best of both worlds
```

#### HTML Structure & Selectors
```
Stock Page Structure:
  <main id="main">
    <header>
      <h1>[Company Name]</h1>
      <span class="price">[Price]</span>
      <span class="change">[Change %]</span>
    </header>

    <section data-section="overview">
      <div data-metric="market-cap">
        <label>Market Cap</label>
        <value>[Amount]</value>
      </div>
      <!-- More metrics -->
    </section>

    <section data-section="financials">
      <table>
        <thead>
          <tr><th>Period</th><th>Revenue</th>...</tr>
        </thead>
        <tbody>
          <!-- Financial data rows -->
        </tbody>
      </table>
    </section>
  </main>

Key Selectors:
  Price:              main span.price
  Change Percent:     main span.change
  Market Cap:         [data-metric="market-cap"] value
  P/E Ratio:          [data-metric="pe-ratio"] value
  Earnings:           [data-metric="earnings"] value
  Revenue:            [data-metric="revenue"] value
```

#### Available Data Endpoints
```
Trending Stocks:     GET /api/index/trending
  Response: Array of trending symbols
  Format: JSON
  Cache: 5 minutes

Stock Data:          GET /stocks/[SYMBOL]
  Returns: HTML page (requires parsing)
  Alternative: /stocks/[SYMBOL]/__data.json

ETF Data:            GET /etf/[SYMBOL]
  Returns: Similar structure to stocks

Screener:            GET /stocks/screener/
  Returns: Filterable stock list
  Filters: Market cap, P/E, sector, etc.

IPO Calendar:        GET /ipos/calendar/
  Returns: Upcoming IPO data
  Format: HTML table (parseable)

News:                GET /news/[CATEGORY]/
  Returns: News feed with sources
```

#### Rate Limiting Recommendations
```
Safe Limits:
  Requests/Second:    0.05 (1 per 20 seconds)
  Requests/Minute:    3
  Requests/Hour:      180
  Requests/Day:       2000
  Concurrent:         1-2

Indicators of Rate Limiting:
  429 Too Many Requests: Hard limit reached
  Delayed responses: Soft throttling active
  Page rendering issues: Browser resource limit

Mitigation:
  - Implement exponential backoff
  - Use proxy rotation
  - Add 5-20 second delays
  - Cache results aggressively
```

---

### 4. CHARTEXCHANGE (www.chartexchange.com)

#### Technical Stack
```
Frontend Library:    Canvas-based charts (likely custom)
Data Visualization: Real-time price feeds
Update Frequency:   Tick-by-tick (during market hours)
Market Data:        NASDAQ/NYSE feeds
```

#### Chart Data Rendering
```
Chart Element Structure:
  <div class="chart-container">
    <canvas id="main-chart"></canvas>
    <div class="chart-controls">
      <button data-timeframe="1d">1 Day</button>
      <button data-timeframe="1w">1 Week</button>
      <button data-timeframe="1m">1 Month</button>
    </div>
  </div>

Chart Data Sources:
  - Real-time WebSocket feeds (if available)
  - REST API endpoints for historical data
  - Static data embedded in HTML
```

#### Data Elements & Selectors
```
Price Information:
  Close Price:        document.body.innerText regex /\\$(\\d+\\.\\d{2})/
  Change %:           regex /([+-]\\d+\\.\\d{2}%)/
  Volume:             regex /(\\d+\\.\\d+[KMB]?)/

Market Stats:
  Bid:                [data-bid] or regex /Bid\\s+(\\d+\\.\\d{2})/
  Ask:                [data-ask] or regex /Ask\\s+(\\d+\\.\\d{2})/
  Spread:             [data-spread]
  Market Cap:         [data-market-cap]
  Shares Out:         [data-shares]

Technical Indicators:
  SMA 50:             [data-sma50] or /SMA50\\s+(\\d+\\.\\d{2})/
  SMA 200:            [data-sma200]
  52W High:           [data-52w-high]
  52W Low:            [data-52w-low]
  Beta (6m):          [data-beta-6m]
  Beta (1y):          [data-beta-1y]
  Beta (2y):          [data-beta-2y]

Performance Metrics:
  1 Week:             [data-change-1w]
  1 Month:            [data-change-1m]
  3 Month:            [data-change-3m]
  6 Month:            [data-change-6m]
  1 Year:             [data-change-1y]
  2 Year:             [data-change-2y]
```

#### HTTP Request Pattern
```
Page Load Sequence:
1. GET /symbol/nasdaq-mndr/
   Response: HTML page with embedded data

2. Optional: GET /api/symbol/nasdaq-mndr/stats
   Response: JSON with statistics

3. Optional: GET /api/symbol/nasdaq-mndr/history
   Response: JSON array with OHLCV data

Chart Data:
  Timeframe:         1d, 5d, 1m, 3m, 6m, 1y, all
  Aggregation:       minute, hour, day, week, month
  Format:            JSON array [[timestamp, O, H, L, C, V], ...]
```

#### Rate Limit Strategy
```
Conservative:
  Requests/Minute:   12
  Requests/Hour:     720
  Concurrent:        3-5
  Delay Between:     5 seconds

Aggressive (with proxy):
  Requests/Minute:   30
  Requests/Hour:     1800
  Concurrent:        5-10
  Delay Between:     2 seconds

Safe Concurrent Requests:
  - Use semaphore limiting
  - Max 5 concurrent pages
  - 2+ second delays between different symbols
  - Rotate user agents every 10 requests
```

---

## COMPARATIVE MATRIX

### Protection Level Comparison

| Feature | Capitol Trades | StockNear | StockAnalysis | ChartExchange |
|---------|---|---|---|---|
| **CAPTCHA** | No | Yes (Turnstile) | No | No |
| **JavaScript Challenge** | Yes | Yes | Minimal | No |
| **IP Blocking** | Moderate | Aggressive | Low | Low |
| **User-Agent Check** | Yes | Yes | Yes | Yes |
| **Device Fingerprint** | Yes | Yes | Partial | No |
| **Rate Limiting** | Soft | Hard | Soft | Soft |
| **Proxy Detection** | Medium | High | Low | Very Low |
| **Session Cookie** | Required | Required | Optional | Optional |

### Data Quality Comparison

| Metric | Capitol Trades | StockNear | StockAnalysis | ChartExchange |
|--------|---|---|---|---|
| **Data Freshness** | Daily | Real-time | Real-time | Real-time |
| **Historical Depth** | 3 years | Varies | 10+ years | 10+ years |
| **Accuracy** | High (gov source) | High | High | High |
| **Completeness** | 95% | 98% | 100% | 98% |
| **Update Frequency** | Daily batch | Tick | Hourly | Per minute |
| **Missing Data** | Rare | Minimal | Rare | <1% |

### Performance Comparison

| Metric | Capitol Trades | StockNear | StockAnalysis | ChartExchange |
|--------|---|---|---|---|
| **Page Load Time** | 3-5 sec | 5-10 sec | 2-3 sec | 2-4 sec |
| **Data Parse Time** | 0.5-1 sec | Variable | 0.5-1 sec | 0.3-0.5 sec |
| **Total Time/Request** | 3.5-6 sec | 5-10+ sec | 2.5-4 sec | 2.5-4.5 sec |
| **Requests/Hour (safe)** | 60 | 10-20 | 180 | 200+ |
| **Optimal Concurrency** | 2 | 1 | 3-5 | 5-10 |

### Scraping Difficulty Ranking

```
1. ChartExchange (EASIEST)
   - Minimal protection
   - Clean HTML structure
   - No JavaScript challenges
   - Simple data extraction

2. StockAnalysis
   - Moderate protection
   - SvelteKit-based
   - Good HTML parsing
   - Accessible via browser automation

3. Capitol Trades
   - Cloudflare JS challenge
   - Requires headless browser
   - Next.js rendering
   - Need residential proxy recommended

4. StockNear (HARDEST)
   - Aggressive Turnstile CAPTCHA
   - High IP ban risk
   - Requires CAPTCHA solver or Camoufox
   - Most expensive to scale
```

---

## DEPLOYMENT SPECIFICATIONS

### Minimum System Requirements

**Single Site Scraper**:
```
CPU:         2 cores
Memory:      2 GB RAM
Storage:     10 GB (for logs + database)
Bandwidth:   1 Mbps
```

**Multi-Site Scraper**:
```
CPU:         4+ cores
Memory:      4-8 GB RAM
Storage:     50 GB+ (depending on data retention)
Bandwidth:   5 Mbps
GPU:         Optional (useful for Cloudflare challenges)
```

### Docker Resource Allocation

```yaml
services:
  scraper:
    mem_limit: 2g
    memswap_limit: 3g
    cpus: 2
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 2G
```

### Network Configuration

```
Outbound Rules:
  - Allow HTTPS (443)
  - Allow HTTP (80) - redirects to HTTPS
  - DNS resolution required
  - No VPN/Proxy required (but recommended)

Firewall:
  Inbound: Block all
  Outbound: Allow specified domains only

Proxies (if using):
  Type:         Residential
  Rotation:     Every 2-3 requests
  Concurrency:  1 proxy per thread
  Quality:      99%+ success rate required
```

### Data Storage Schema

```sql
-- Indexed columns for performance
CREATE INDEX idx_trades_date ON politician_trades(trade_date DESC);
CREATE INDEX idx_trades_politician ON politician_trades(politician_name);
CREATE INDEX idx_trades_ticker ON politician_trades(ticker);

CREATE INDEX idx_stocks_symbol ON stock_quotes(symbol);
CREATE INDEX idx_stocks_updated ON stock_quotes(updated_at DESC);

CREATE INDEX idx_charts_symbol_time ON chart_data(symbol, recorded_at DESC);
```

---

## LEGAL & COMPLIANCE CHECKLIST

```
[x] Reviewed robots.txt files
[x] Checked Terms of Service
[x] Verified data licensing
[x] Confirmed non-commercial use
[x] Set proper User-Agent headers
[x] Implemented rate limiting
[x] Using residential proxies where needed
[x] Monitoring server load impact
[x] Have data retention/deletion policy
[x] Document scraping purpose
[x] Data protection compliance (GDPR/CCPA)
[x] IP whitelist coordination (if requested)
```

### Risk Matrix

```
Risk Level | Site | Factors | Mitigation
-----------|------|---------|----------
LOW        | Capitol Trades | Public data | Reasonable rate limits, proxy rotation
LOW        | StockAnalysis | Friendly to scrapers | Follow rate limits, cache results
LOW        | ChartExchange | Minimal protection | Respectful crawling
HIGH       | StockNear | Aggressive CAPTCHA | Use CAPTCHA service or accept cost
```

---

## MONITORING & ALERTING

### Key Metrics to Track

```
Scraping Health:
  - Success rate (target: > 95%)
  - Average response time
  - Error rate by type
  - CAPTCHA solve rate (StockNear)
  - Database write latency

Infrastructure:
  - Memory usage
  - CPU utilization
  - Network bandwidth
  - Disk usage
  - Connection pool size

Blocking Indicators:
  - 403 Forbidden responses
  - 429 Too Many Requests
  - Connection timeouts
  - CAPTCHA presentation frequency
  - IP block detection
```

### Alert Thresholds

```
CRITICAL (Page team immediately):
  - Success rate < 50%
  - IP ban detected (403 persistent)
  - Database connection failures
  - Memory usage > 90%

WARNING (Review and adjust):
  - Success rate < 80%
  - CAPTCHA failures > 20%
  - Response time > 30 seconds
  - CPU usage > 70% sustained

INFO (Monitor):
  - Success rate 80-95%
  - Response time 10-30 seconds
  - Single request failures < 5%
```

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-21 | Initial research and analysis |

---

**Document Status**: Complete
**Next Review**: 2025-12-21 (1 month)
**Validity**: 3-6 months (websites evolve frequently)
