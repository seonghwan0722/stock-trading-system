# API Integration Implementation Roadmap

## Executive Summary

This document provides a phased implementation plan for integrating financial data APIs with your stock market and congressional trading platform, replacing or supplementing web scraping.

**Recommended Approach**: Hybrid strategy combining multiple APIs with strategic scraping where necessary.

**Total Estimated Cost**: $150-300/month for production-ready system
**Development Time**: 4-6 weeks for full implementation

---

## Phase 1: Foundation (Week 1-2)
### Objective: Setup core infrastructure and basic data flow

**Tasks**:
1. Setup Node.js backend with Express
2. Configure PostgreSQL database
3. Setup Redis caching
4. Create base API client classes
5. Implement real-time quote functionality
6. Deploy to development environment

**APIs to Integrate**:
- **IEX Cloud** (Real-time quotes)
  - Signup: https://iexcloud.io/console/
  - Free tier: 100 messages/month
  - Cost: $0.01 per quote
  - Implementation time: 2-3 hours

**Deliverables**:
- Working backend API with `/api/v1/quotes` endpoint
- Basic caching with 5-minute TTL
- Error handling and rate limiting
- Unit tests for API clients

**Example Endpoint Response**:
```json
GET /api/v1/quotes/AAPL

{
  "symbol": "AAPL",
  "price": 172.45,
  "change": 1.25,
  "changePercent": 0.73,
  "volume": 52847100,
  "timestamp": "2024-11-21T16:00:00Z",
  "dataSource": "IEX_CLOUD",
  "cached": false
}
```

**Estimated Cost**: $0-30 (IEX Cloud pay-as-you-go)

---

## Phase 2: Data Enrichment (Week 2-3)
### Objective: Add company fundamentals and insider trading data

**Tasks**:
1. Integrate Finnhub API
2. Implement fundamentals endpoint
3. Setup SEC EDGAR scraping/parsing
4. Create insider trades endpoints
5. Implement data aggregation layer
6. Setup background job queue

**APIs to Integrate**:
- **Finnhub** (Company fundamentals, news, earnings)
  - Signup: https://finnhub.io/register
  - Free tier: 60 API calls/minute
  - Cost: $0 for fundamentals
  - Implementation time: 4-5 hours

- **SEC EDGAR** (Insider trades)
  - No signup required
  - Free unlimited access
  - Rate limit: 10 requests/second (recommended)
  - Implementation time: 6-8 hours

**Database Schema Updates**:
```sql
-- Company fundamentals cache
CREATE TABLE company_fundamentals (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(10) UNIQUE NOT NULL,
  name VARCHAR(255),
  sector VARCHAR(100),
  market_cap BIGINT,
  pe_ratio DECIMAL(10,2),
  eps DECIMAL(10,2),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  cached_until TIMESTAMPTZ
);

-- Insider transactions
CREATE TABLE insider_transactions (
  id SERIAL PRIMARY KEY,
  filer_name VARCHAR(255) NOT NULL,
  filer_title VARCHAR(100),
  symbol VARCHAR(10) NOT NULL,
  transaction_date DATE NOT NULL,
  transaction_type VARCHAR(20),
  shares BIGINT,
  price DECIMAL(10,2),
  total_value DECIMAL(15,2),
  form_type VARCHAR(10),
  sec_filing_link VARCHAR(500),
  source VARCHAR(50) DEFAULT 'SEC_EDGAR',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(sec_filing_link, transaction_date, filer_name, symbol)
);

CREATE INDEX idx_insider_symbol ON insider_transactions(symbol);
CREATE INDEX idx_insider_date ON insider_transactions(transaction_date);
CREATE INDEX idx_insider_filer ON insider_transactions(filer_name);
```

**New Endpoints**:
- `GET /api/v1/stocks/{symbol}/fundamentals` - Company profile, stats, earnings
- `GET /api/v1/insider-trades` - Query insider transactions
- `GET /api/v1/insider-trades/{tradeId}` - Individual trade details

**Estimated Cost**: $0-50 (using free Finnhub tier + free SEC EDGAR)

---

## Phase 3: Technical Analysis & Advanced Features (Week 3-4)
### Objective: Add technical indicators and additional data sources

**Tasks**:
1. Integrate Alpha Vantage for technical indicators
2. Implement technical analysis endpoints
3. Add company news/sentiment
4. Create chart data endpoints
5. Implement data comparison/arbitrage
6. Add filtering and search capabilities

**APIs to Integrate**:
- **Alpha Vantage** (Technical indicators)
  - Signup: https://www.alphavantage.co
  - Free tier: 5 calls/minute, 500/day
  - Cost: $99.99/month for unlimited
  - Implementation time: 4-5 hours

- **Finnhub News** (Company news)
  - Already integrated
  - Free tier included
  - Cost: $0

**New Endpoints**:
- `GET /api/v1/stocks/{symbol}/technical` - Candles + indicators (SMA, RSI)
- `GET /api/v1/stocks/{symbol}/chart` - Historical OHLCV data
- `GET /api/v1/stocks/{symbol}/news` - Latest company news

**Estimated Cost**: $0-100 (free Finnhub tier + Alpha Vantage)

---

## Phase 4: Production Optimization (Week 4+)
### Objective: Performance, monitoring, and cost optimization

**Tasks**:
1. Performance optimization and caching strategy refinement
2. Implement monitoring and alerting
3. Cost tracking dashboard
4. Rate limit optimization
5. Database indexing and query optimization
6. Load testing and scaling preparation
7. Documentation and runbooks
8. Production deployment

**Performance Goals**:
- Quote endpoint: < 100ms (cached)
- Fundamentals endpoint: < 500ms
- Insider trades query: < 1000ms
- Cache hit rate: > 85%

**Monitoring Setup**:
```javascript
// Key metrics to track
{
  "apiMetrics": {
    "iexCloud": { "callsPerDay": 0, "avgResponseTime": 0 },
    "finnhub": { "callsPerDay": 0, "avgResponseTime": 0 },
    "secEdgar": { "callsPerDay": 0, "avgResponseTime": 0 }
  },
  "cacheMetrics": {
    "hitRate": 0.85,
    "missRate": 0.15,
    "entriesStored": 0
  },
  "costMetrics": {
    "dailyEstimate": 0,
    "monthlyEstimate": 0,
    "costPerRequest": 0
  }
}
```

**Estimated Cost**: $0-200 (optimization of existing APIs)

---

## API Selection Recommendations by Use Case

### 1. Real-Time Stock Quotes (Critical)
**Recommendation**: IEX Cloud (Primary) + Finnhub (Fallback)

**Why**:
- IEX Cloud: True real-time data, no delay, pay-as-you-go
- Finnhub: Free tier sufficient for fallback, 60 calls/min

**Cost**: $50-100/month for 50-100 stocks, 4 updates/day

**Example Implementation**:
```javascript
async getQuote(symbol) {
  try {
    // Primary: IEX Cloud (real-time)
    return await iexClient.getQuote(symbol);
  } catch (error) {
    // Fallback: Finnhub (slightly delayed)
    logger.warn(`IEX failed for ${symbol}, using Finnhub`);
    return await finnhubClient.getQuote(symbol);
  }
}
```

---

### 2. Company Fundamentals (Important)
**Recommendation**: Finnhub (Primary) + IEX Stats (Secondary)

**Why**:
- Finnhub: Best free tier for fundamentals, earnings data
- IEX Stats: Comprehensive metrics, real-time P/E and other ratios

**Cost**: $0/month (using free tiers)

**Cache Strategy**: 7-day TTL (fundamentals change slowly)

**Example Data Coverage**:
- Company profile (name, sector, industry)
- Market cap, P/E ratio, EPS
- Dividend info
- Earnings history and estimates
- 52-week price range

---

### 3. Technical Indicators (Important for Analysis)
**Recommendation**: Alpha Vantage OR calculate from raw data

**Option A: Alpha Vantage (Dedicated)**
- Cost: Free tier (5 calls/min) OR $99.99/month unlimited
- Indicators: 30+ technical indicators
- Best for: When you need pre-calculated indicators
- Implementation time: 4 hours

**Option B: Calculate from Candles (Cost-Free)**
- Cost: Free (using Finnhub/Polygon candles)
- Calculate: SMA, EMA, RSI, MACD locally
- Best for: Cost-conscious, custom indicators
- Implementation time: 8 hours

**Recommendation**: Start with Option B (calculate from free candle data), upgrade to Option A if needed

---

### 4. Insider Trading & Congressional Trades (Core Feature)
**Recommendation**: SEC EDGAR (Primary) + Capitol Trades Scraping (Supplement)

**Why**:
- SEC EDGAR: Official, free, comprehensive Form 4 data
- Capitol Trades: Aggregates data, better UX, requires scraping

**SEC EDGAR Implementation**:
- Cost: FREE
- Data: Form 4 filings (most comprehensive)
- Update: Real-time (daily filing updates)
- Rate limit: 10 requests/second (recommended)

**Capitol Trades Scraping**:
- Cost: Infrastructure only (no API)
- Data: Pre-aggregated congressional trades
- Update: Daily
- Complexity: Medium (JavaScript-rendered)

**Recommended Hybrid Approach**:
```javascript
async getInsiderTrades(symbol) {
  // Source 1: SEC EDGAR (official, comprehensive)
  const secTrades = await secEdgarClient.getForm4Filings(cik);

  // Source 2: Capitol Trades (aggregated, congressional focus)
  const capTrades = await capitolTradesScraper.getTradesFor(symbol);

  // Merge and deduplicate
  return mergeAndDedup(secTrades, capTrades);
}
```

**Estimated Data Overlap**: 60-70% (some trades appear in both)

---

### 5. Company News & Sentiment (Nice to Have)
**Recommendation**: Finnhub (Free) + NewsAPI (Alternative)

**Why**:
- Finnhub: Free tier included, good coverage
- NewsAPI: Alternative if Finnhub insufficient

**Cost**: $0 (using free Finnhub)

**Cache Strategy**: 1-hour TTL (news changes frequently)

---

## Cost Analysis & Optimization

### Scenario: 100 stocks tracked, 4 quote updates/day

#### Minimal Setup (MVP)
```
IEX Cloud: 100 stocks × 4 updates × 30 days = 12,000 quotes
12,000 × $0.01 = $120/month

Finnhub: Free tier (60 calls/min is sufficient)
Cost: $0/month

SEC EDGAR: Free unlimited
Cost: $0/month

Alpha Vantage: Free tier
Cost: $0/month

TOTAL: $120/month (~$1,440/year)
```

#### Standard Setup (Recommended)
```
IEX Cloud: Same as above
Cost: $120/month

Finnhub: Free tier
Cost: $0/month

SEC EDGAR: Free
Cost: $0/month

Alpha Vantage: Free tier
Cost: $0/month

Infrastructure (Heroku/AWS): ~$50/month
Database (Postgres): ~$15/month
Cache (Redis): ~$10/month

TOTAL: ~$195/month (~$2,340/year)
```

#### Premium Setup (Highest Quality)
```
IEX Cloud: Same as above
Cost: $120/month

Finnhub: Professional tier ($75/month)
Cost: $75/month
Benefits: Real-time data, higher rate limits

Alpha Vantage: Unlimited ($99.99/month)
Cost: $99.99/month
Benefits: All 30+ technical indicators

SEC EDGAR: Free
Cost: $0/month

Infrastructure & Hosting: ~$100/month
Database & Cache: ~$50/month

TOTAL: ~$445/month (~$5,340/year)
```

### Cost Optimization Strategies

1. **Cache Aggressively**:
   - Quotes: 5-minute TTL
   - Fundamentals: 7-day TTL
   - Indicators: 1-day TTL
   - Target: 85%+ cache hit rate
   - Savings: 15-30% on API costs

2. **Batch Requests**:
   - Use bulk quote endpoints instead of individual calls
   - Reduces message count by 80-90%
   - Example: GET /quotes/bulk instead of 100 individual calls

3. **Smart Update Scheduling**:
   - Update quotes only during market hours (9:30 AM - 4:00 PM ET)
   - Update fundamentals once per day
   - Update insider trades once per day
   - Savings: 40-50% on unnecessary calls

4. **Use Free Tiers Optimally**:
   - Finnhub free: 60 calls/min (sufficient for 100 stocks)
   - Alpha Vantage free: 500 calls/day (calculate indicators instead)
   - Savings: $100-200/month

5. **Data Aggregation**:
   - Combine calls to reduce total requests
   - Get quote + stats in one call when possible
   - Savings: 20-30% reduction in API calls

---

## Architecture Decisions

### Caching Layer
```
Request -> Cache (Redis) -> If miss -> API -> Store in Cache -> Return
```

**TTL Values**:
- Real-time quotes: 5 minutes
- Company fundamentals: 7 days
- Technical indicators: 1 day
- Company info: 30 days
- News: 1 hour
- Insider trades: 6 hours

### Rate Limiting Strategy
```
Primary: Token bucket algorithm
Backup: Sliding window
Implementation: Use axios-rate-limit + custom rate limiter

Per API:
- IEX Cloud: 100 requests/min (free tier: adapt as needed)
- Finnhub: 60 requests/min
- Alpha Vantage: 5 requests/min
- SEC EDGAR: 10 requests/min (respect their guidelines)
```

### Error Handling
```
Tier 1: Cache (stale data is better than error)
Tier 2: Secondary API source (fallback)
Tier 3: Return error with retry-after header
Tier 4: Alert operations team
```

---

## Web Scraping Elimination Strategy

### Current Scraping Targets
1. **Capitol Trades** (capitoltrades.com)
   - Replacement: SEC EDGAR API + limited scraping
   - Scraping eliminated: 80%
   - Remaining scraping: Congressional member identification only

2. **Stock fundamentals** (stockanalysis.com)
   - Replacement: Finnhub API
   - Scraping eliminated: 100%

3. **Stock charts** (chartexchange.com)
   - Replacement: Polygon.io or Finnhub
   - Scraping eliminated: 100%

4. **Real-time quotes** (various)
   - Replacement: IEX Cloud
   - Scraping eliminated: 100%

### Scraping Reduction Summary
- **Before**: 100% scraping dependency
- **After**: 10-20% targeted scraping (congressional data only)
- **Benefits**:
  - 90% reduction in infrastructure burden
  - No IP blocking or bot detection issues
  - 10x faster data retrieval
  - Legal compliance
  - Reliable SLAs

---

## Testing Strategy

### Unit Tests
```javascript
// Test API clients
describe('IEXCloudClient', () => {
  test('getQuote returns valid structure');
  test('getQuotes handles arrays');
  test('handles rate limits gracefully');
  test('retries on transient errors');
});
```

### Integration Tests
```javascript
// Test service layer
describe('StockService', () => {
  test('getQuote uses cache when available');
  test('fallback to secondary API on error');
  test('normalizes data from different sources');
});
```

### Load Tests
```javascript
// Test performance under load
- 100 concurrent quote requests
- Target: All complete within 5 seconds
- Cache hit rate: > 85%
```

---

## Deployment Checklist

### Pre-Production
- [ ] All API keys secured in environment variables
- [ ] Rate limiting configured and tested
- [ ] Caching strategy validated (85%+ hit rate)
- [ ] Error handling for all API failures
- [ ] Monitoring and alerting configured
- [ ] Database backups automated
- [ ] Load tests passed
- [ ] Cost projections validated

### Production Deployment
- [ ] Gradual rollout (10% → 50% → 100%)
- [ ] Real-time monitoring of API calls and costs
- [ ] Alert on rate limit approaching
- [ ] Daily cost reports
- [ ] Weekly performance reviews

---

## Long-Term Considerations

### Scaling (6+ months)
- As user base grows, costs will increase
- Consider data warehouse for historical data
- Implement advanced caching (CDN)
- Evaluate alternative data providers

### Feature Expansion
- Add more technical indicators
- Expand congressional trading coverage
- Add international stocks
- Add options and derivatives data
- Add sentiment analysis

### API Alternatives to Monitor
- **Polygon.io**: Growing, good free tier improvements
- **Twelve Data**: Emerging competitor, good pricing
- **Finnhub**: Continues to improve free tier
- **Tradier**: Good for options data

---

## Recommended Reading & Resources

### API Documentation
- IEX Cloud: https://iexcloud.io/docs
- Finnhub: https://finnhub.io/docs/api
- Alpha Vantage: https://www.alphavantage.co/documentation
- SEC EDGAR: https://www.sec.gov/edgar/developer

### Libraries & Tools
- Axios: HTTP client for Node.js
- Bull: Job queue for Node.js
- Redis: Caching layer
- Jest: Testing framework
- Postman: API testing tool

### Best Practices
- API Rate Limiting Patterns
- Caching Strategies for Financial Data
- Error Handling in Distributed Systems
- Monitoring and Alerting for APIs

---

## Summary

### Quick Start (This Week)
1. Sign up for IEX Cloud free tier
2. Get Finnhub API key
3. Setup basic backend with one API client
4. Deploy `/api/v1/quotes/{symbol}` endpoint
5. Test with 10 stocks

### Month 1
1. Integrate all APIs (IEX, Finnhub, SEC EDGAR)
2. Implement caching layer
3. Add fundamentals and insider trades
4. Deploy to production
5. Monitor costs and performance

### Month 2+
1. Optimize based on real usage patterns
2. Add advanced features (technical indicators, alerts)
3. Expand to new data sources as needed
4. Continuously optimize costs

---

**Total Development Effort**: 4-6 weeks
**Team Size**: 1-2 developers
**Estimated Monthly Cost**: $150-300 (production)
**Time to Production**: 3-4 weeks (MVP)

---

**Document Version**: 1.0
**Last Updated**: November 21, 2025
**Status**: Ready for Implementation

