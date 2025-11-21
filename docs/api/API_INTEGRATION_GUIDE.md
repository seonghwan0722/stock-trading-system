# API Integration Implementation Guide

## Table of Contents
1. Setup & Configuration
2. Data Aggregation Layer
3. Caching Strategy
4. Error Handling
5. Rate Limit Management
6. Background Jobs
7. Testing & Monitoring

---

## 1. SETUP & CONFIGURATION

### Environment Variables (.env)

```env
# IEX Cloud
IEX_CLOUD_TOKEN=pk_xxxxxxxxxxxx
IEX_CLOUD_BASE_URL=https://cloud.iexapis.com/stable

# Finnhub
FINNHUB_API_KEY=xxxxxxxxxxxxxxxx
FINNHUB_BASE_URL=https://finnhub.io/api/v1

# Alpha Vantage
ALPHA_VANTAGE_KEY=xxxxxxxxxxxxxxxx
ALPHA_VANTAGE_BASE_URL=https://www.alphavantage.co/query

# SEC EDGAR
SEC_EDGAR_BASE_URL=https://www.sec.gov/cgi-bin/browse-edgar

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/stock_db

# Redis
REDIS_URL=redis://localhost:6379

# Feature Flags
USE_IEX_REAL_TIME=true
USE_FINNHUB_FUNDAMENTALS=true
USE_ALPHA_VANTAGE_INDICATORS=false
USE_SEC_EDGAR_INSIDER=true

# Rate Limiting
IEX_RATE_LIMIT=100
FINNHUB_RATE_LIMIT=60
ALPHA_RATE_LIMIT=5

# Logging
LOG_LEVEL=info
NODE_ENV=production
```

### Node.js Backend Setup

```javascript
// config/index.js
require('dotenv').config();

module.exports = {
  // API Keys
  apis: {
    iexCloud: {
      token: process.env.IEX_CLOUD_TOKEN,
      baseUrl: process.env.IEX_CLOUD_BASE_URL,
      rateLimit: parseInt(process.env.IEX_RATE_LIMIT) || 100
    },
    finnhub: {
      key: process.env.FINNHUB_API_KEY,
      baseUrl: process.env.FINNHUB_BASE_URL,
      rateLimit: parseInt(process.env.FINNHUB_RATE_LIMIT) || 60
    },
    alphaVantage: {
      key: process.env.ALPHA_VANTAGE_KEY,
      baseUrl: process.env.ALPHA_VANTAGE_BASE_URL,
      rateLimit: parseInt(process.env.ALPHA_RATE_LIMIT) || 5
    },
    secEdgar: {
      baseUrl: process.env.SEC_EDGAR_BASE_URL
    }
  },

  // Database
  database: {
    url: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production'
  },

  // Cache
  redis: {
    url: process.env.REDIS_URL,
    ttl: {
      quotes: 5 * 60, // 5 minutes
      fundamentals: 7 * 24 * 60 * 60, // 7 days
      indicators: 24 * 60 * 60, // 1 day
      news: 60 * 60, // 1 hour
      insider: 24 * 60 * 60 // 1 day
    }
  },

  // Features
  features: {
    useIexRealTime: process.env.USE_IEX_REAL_TIME === 'true',
    useFinnhubFundamentals: process.env.USE_FINNHUB_FUNDAMENTALS === 'true',
    useAlphaIndicators: process.env.USE_ALPHA_VANTAGE_INDICATORS === 'true',
    useSecEdgarInsider: process.env.USE_SEC_EDGAR_INSIDER === 'true'
  }
};
```

---

## 2. DATA AGGREGATION LAYER

### Base API Client

```javascript
// clients/baseClient.js
const axios = require('axios');
const rateLimit = require('axios-rate-limit');
const logger = require('../logger');

class BaseAPIClient {
  constructor(config) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.baseUrl,
      timeout: 30000,
      headers: {
        'User-Agent': 'StockApp/1.0 (contact@app.com)'
      }
    });

    // Apply rate limiting
    if (config.rateLimit) {
      this.client = rateLimit(this.client, {
        maxRequests: config.rateLimit,
        windowMs: 60000 // 1 minute
      });
    }

    // Add interceptors
    this.setupInterceptors();
  }

  setupInterceptors() {
    this.client.interceptors.response.use(
      response => response,
      error => {
        logger.error('API Error:', {
          status: error.response?.status,
          message: error.message,
          url: error.config?.url
        });
        throw error;
      }
    );
  }

  async request(method, url, config = {}) {
    try {
      const response = await this.client({
        method,
        url,
        ...config
      });
      return response.data;
    } catch (error) {
      logger.error(`${method} ${url} failed:`, error.message);
      throw error;
    }
  }

  async get(url, config) {
    return this.request('GET', url, config);
  }

  async post(url, data, config) {
    return this.request('POST', url, { data, ...config });
  }
}

module.exports = BaseAPIClient;
```

### IEX Cloud Client

```javascript
// clients/iexCloudClient.js
const BaseAPIClient = require('./baseClient');
const logger = require('../logger');

class IEXCloudClient extends BaseAPIClient {
  constructor(config) {
    super(config);
    this.token = config.token;
  }

  async getQuote(symbol) {
    try {
      const data = await this.get(`/stock/${symbol}/quote`, {
        params: { token: this.token }
      });

      return {
        symbol,
        price: data.latestPrice,
        change: data.change,
        changePercent: data.changePercent,
        volume: data.latestVolume,
        marketCap: data.marketCap,
        peRatio: data.peRatio,
        timestamp: new Date(data.latestUpdate),
        dataSource: 'IEX_CLOUD'
      };
    } catch (error) {
      logger.error(`Failed to get IEX quote for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getQuotes(symbols) {
    const promises = symbols.map(symbol => this.getQuote(symbol));
    return Promise.allSettled(promises);
  }

  async getStats(symbol) {
    try {
      const data = await this.get(`/stock/${symbol}/stats`, {
        params: { token: this.token }
      });

      return {
        symbol,
        marketCap: data.marketcap,
        peRatio: data.peRatio,
        eps: data.eps,
        week52High: data.week52high,
        week52Low: data.week52low,
        dividend: data.latestDividend,
        employees: data.employees,
        dataSource: 'IEX_CLOUD'
      };
    } catch (error) {
      logger.error(`Failed to get IEX stats for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getChartData(symbol, range = '1m') {
    try {
      const data = await this.get(`/stock/${symbol}/chart/range/${range}`, {
        params: { token: this.token }
      });

      return {
        symbol,
        range,
        data: data.map(candle => ({
          date: candle.date,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
          volume: candle.volume
        })),
        dataSource: 'IEX_CLOUD'
      };
    } catch (error) {
      logger.error(`Failed to get IEX chart for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getTops(symbols = null) {
    try {
      const params = { token: this.token };
      if (symbols && symbols.length > 0) {
        params.symbols = symbols.join(',');
      }

      const data = await this.get('/tops', { params });

      return {
        symbols: Array.isArray(data) ? data.map(item => ({
          symbol: item.symbol,
          bid: item.bidPrice,
          ask: item.askPrice,
          bidSize: item.bidSize,
          askSize: item.askSize,
          timestamp: new Date(item.time)
        })) : [],
        dataSource: 'IEX_CLOUD'
      };
    } catch (error) {
      logger.error('Failed to get IEX TOPS:', error.message);
      throw error;
    }
  }
}

module.exports = IEXCloudClient;
```

### Finnhub Client

```javascript
// clients/finnhubClient.js
const BaseAPIClient = require('./baseClient');
const logger = require('../logger');

class FinnhubClient extends BaseAPIClient {
  constructor(config) {
    super(config);
    this.key = config.key;
  }

  async getQuote(symbol) {
    try {
      const data = await this.get('/quote', {
        params: { symbol, token: this.key }
      });

      return {
        symbol,
        price: data.c,
        change: data.d,
        changePercent: data.dp,
        timestamp: new Date(data.t * 1000),
        dataSource: 'FINNHUB'
      };
    } catch (error) {
      logger.error(`Failed to get Finnhub quote for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getCompanyProfile(symbol) {
    try {
      const data = await this.get('/stock/profile2', {
        params: { symbol, token: this.key }
      });

      return {
        symbol,
        name: data.name,
        sector: data.finnhubIndustry,
        country: data.country,
        website: data.weburl,
        description: data.description,
        marketCap: data.marketCapitalization,
        employees: data.employees,
        dataSource: 'FINNHUB'
      };
    } catch (error) {
      logger.error(`Failed to get Finnhub profile for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getCandles(symbol, startDate, endDate, resolution = 'D') {
    try {
      const startTs = Math.floor(new Date(startDate).getTime() / 1000);
      const endTs = Math.floor(new Date(endDate).getTime() / 1000);

      const data = await this.get('/stock/candle', {
        params: {
          symbol,
          resolution,
          from: startTs,
          to: endTs,
          token: this.key
        }
      });

      if (data.s === 'ok') {
        return {
          symbol,
          candles: data.t.map((t, i) => ({
            timestamp: new Date(t * 1000),
            open: data.o[i],
            high: data.h[i],
            low: data.l[i],
            close: data.c[i],
            volume: data.v[i]
          })),
          dataSource: 'FINNHUB'
        };
      }

      throw new Error('Invalid candle response');
    } catch (error) {
      logger.error(`Failed to get Finnhub candles for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getNews(symbol, limit = 10) {
    try {
      const data = await this.get('/company-news', {
        params: {
          symbol,
          limit,
          token: this.key
        }
      });

      return {
        symbol,
        news: data.map(item => ({
          headline: item.headline,
          summary: item.summary,
          source: item.source,
          url: item.url,
          image: item.image,
          timestamp: new Date(item.datetime * 1000),
          sentiment: item.sentiment // Pro only
        })),
        dataSource: 'FINNHUB'
      };
    } catch (error) {
      logger.error(`Failed to get Finnhub news for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getEarnings(symbol) {
    try {
      const data = await this.get('/stock/earnings', {
        params: { symbol, token: this.key }
      });

      return {
        symbol,
        earnings: data.map(item => ({
          date: item.date,
          quarter: item.quarter,
          year: item.year,
          actual: item.actual,
          estimate: item.estimate,
          surprise: item.surprise
        })),
        dataSource: 'FINNHUB'
      };
    } catch (error) {
      logger.error(`Failed to get Finnhub earnings for ${symbol}:`, error.message);
      throw error;
    }
  }
}

module.exports = FinnhubClient;
```

### SEC EDGAR Client

```javascript
// clients/secEdgarClient.js
const BaseAPIClient = require('./baseClient');
const cheerio = require('cheerio');
const logger = require('../logger');

class SECEdgarClient extends BaseAPIClient {
  constructor(config) {
    super(config);
    // Increase delay for SEC rate limiting
    this.requestDelay = 1000; // 1 second between requests
  }

  async getForm4Filings(cik, limit = 50) {
    try {
      // Add delay for SEC compliance
      await this.delay(this.requestDelay);

      const params = {
        action: 'getcompany',
        CIK: cik,
        type: '4',
        dateb: '',
        owner: 'exclude',
        count: limit
      };

      const html = await this.get('', { params });

      // Parse HTML to extract filing data
      const $ = cheerio.load(html);
      const filings = [];

      $('tr', '.tableFile').each((i, el) => {
        const cells = $('td', el);
        if (cells.length >= 4) {
          filings.push({
            formType: $(cells[0]).text().trim(),
            filingDate: $(cells[3]).text().trim(),
            accessionNumber: $(cells[1]).find('a').attr('href')?.split('/')[3],
            link: `https://www.sec.gov${$(cells[1]).find('a').attr('href')}`
          });
        }
      });

      return {
        cik,
        filings,
        dataSource: 'SEC_EDGAR'
      };
    } catch (error) {
      logger.error(`Failed to get SEC filings for CIK ${cik}:`, error.message);
      throw error;
    }
  }

  async searchInsiderTransactions(symbol, formType = '4') {
    try {
      const cik = await this.getCIK(symbol);
      return this.getForm4Filings(cik, 100);
    } catch (error) {
      logger.error(`Failed to search SEC insider transactions for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getCIK(symbol) {
    // In production, would use SEC CIK lookup service
    // For now, use external service or database
    // This is simplified - you'd implement full CIK lookup
    logger.warn(`CIK lookup for ${symbol} would need implementation`);
    return null;
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = SECEdgarClient;
```

---

## 3. CACHING STRATEGY

### Redis Cache Manager

```javascript
// cache/cacheManager.js
const redis = require('redis');
const logger = require('../logger');

class CacheManager {
  constructor(config) {
    this.config = config;
    this.client = redis.createClient({
      url: config.url,
      socket: {
        reconnectStrategy: (retries) => Math.min(retries * 50, 500)
      }
    });

    this.client.on('error', err => logger.error('Redis error:', err));
    this.client.on('connect', () => logger.info('Redis connected'));
  }

  async connect() {
    await this.client.connect();
  }

  async disconnect() {
    await this.client.quit();
  }

  async get(key) {
    try {
      const value = await this.client.get(key);
      if (value) {
        logger.debug(`Cache hit: ${key}`);
        return JSON.parse(value);
      }
      logger.debug(`Cache miss: ${key}`);
      return null;
    } catch (error) {
      logger.error(`Cache get error for ${key}:`, error);
      return null;
    }
  }

  async set(key, value, ttl = null) {
    try {
      const options = {};
      if (ttl) {
        options.EX = ttl; // TTL in seconds
      }

      await this.client.setEx(key, ttl || 300, JSON.stringify(value));
      logger.debug(`Cache set: ${key} (TTL: ${ttl}s)`);
      return true;
    } catch (error) {
      logger.error(`Cache set error for ${key}:`, error);
      return false;
    }
  }

  async del(key) {
    try {
      await this.client.del(key);
      logger.debug(`Cache deleted: ${key}`);
      return true;
    } catch (error) {
      logger.error(`Cache delete error for ${key}:`, error);
      return false;
    }
  }

  async invalidatePattern(pattern) {
    try {
      const keys = await this.client.keys(pattern);
      if (keys.length > 0) {
        await this.client.del(keys);
        logger.info(`Invalidated ${keys.length} cache entries for pattern: ${pattern}`);
      }
    } catch (error) {
      logger.error(`Cache invalidate pattern error:`, error);
    }
  }

  getCacheKey(type, symbol, params = '') {
    return `cache:${type}:${symbol}:${params}`;
  }
}

module.exports = CacheManager;
```

### Service Layer with Caching

```javascript
// services/stockService.js
const logger = require('../logger');

class StockService {
  constructor(iexClient, finnhubClient, cacheManager, config) {
    this.iexClient = iexClient;
    this.finnhubClient = finnhubClient;
    this.cacheManager = cacheManager;
    this.config = config;
  }

  async getQuote(symbol) {
    const cacheKey = this.cacheManager.getCacheKey('quote', symbol);

    // Check cache first
    const cached = await this.cacheManager.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      // Fetch from API
      const quote = await this.iexClient.getQuote(symbol);

      // Cache result
      await this.cacheManager.set(
        cacheKey,
        quote,
        this.config.redis.ttl.quotes
      );

      return quote;
    } catch (error) {
      logger.error(`Failed to get quote for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getQuotes(symbols) {
    const quotes = await Promise.all(
      symbols.map(symbol => this.getQuote(symbol))
    );
    return quotes;
  }

  async getFundamentals(symbol) {
    const cacheKey = this.cacheManager.getCacheKey('fundamentals', symbol);

    const cached = await this.cacheManager.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const [profile, stats, earnings] = await Promise.all([
        this.finnhubClient.getCompanyProfile(symbol),
        this.iexClient.getStats(symbol),
        this.finnhubClient.getEarnings(symbol)
      ]);

      const fundamentals = {
        symbol,
        profile,
        stats,
        earnings,
        timestamp: new Date()
      };

      await this.cacheManager.set(
        cacheKey,
        fundamentals,
        this.config.redis.ttl.fundamentals
      );

      return fundamentals;
    } catch (error) {
      logger.error(`Failed to get fundamentals for ${symbol}:`, error.message);
      throw error;
    }
  }

  async getTechnicalData(symbol, startDate, endDate) {
    const cacheKey = this.cacheManager.getCacheKey('technical', symbol, `${startDate}-${endDate}`);

    const cached = await this.cacheManager.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const candles = await this.finnhubClient.getCandles(
        symbol,
        startDate,
        endDate,
        'D'
      );

      // Calculate indicators from candles
      const technicalData = {
        symbol,
        candles: candles.candles,
        indicators: this.calculateIndicators(candles.candles),
        timestamp: new Date()
      };

      await this.cacheManager.set(
        cacheKey,
        technicalData,
        this.config.redis.ttl.indicators
      );

      return technicalData;
    } catch (error) {
      logger.error(`Failed to get technical data for ${symbol}:`, error.message);
      throw error;
    }
  }

  calculateIndicators(candles) {
    if (candles.length === 0) return {};

    const closes = candles.map(c => c.close);

    return {
      sma20: this.calculateSMA(closes, 20),
      sma50: this.calculateSMA(closes, 50),
      sma200: this.calculateSMA(closes, 200),
      rsi14: this.calculateRSI(closes, 14)
    };
  }

  calculateSMA(data, period) {
    if (data.length < period) return null;
    const slice = data.slice(-period);
    return slice.reduce((a, b) => a + b, 0) / period;
  }

  calculateRSI(data, period) {
    if (data.length < period + 1) return null;

    let gains = 0, losses = 0;

    for (let i = 1; i <= period; i++) {
      const change = data[data.length - i] - data[data.length - i - 1];
      if (change >= 0) {
        gains += change;
      } else {
        losses += Math.abs(change);
      }
    }

    const avgGain = gains / period;
    const avgLoss = losses / period;

    if (avgLoss === 0) return 100;

    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  }

  async invalidateQuote(symbol) {
    const cacheKey = this.cacheManager.getCacheKey('quote', symbol);
    await this.cacheManager.del(cacheKey);
  }

  async invalidateFundamentals(symbol) {
    const cacheKey = this.cacheManager.getCacheKey('fundamentals', symbol);
    await this.cacheManager.del(cacheKey);
  }
}

module.exports = StockService;
```

---

## 4. ERROR HANDLING

### Custom Error Classes

```javascript
// errors/apiErrors.js
class APIError extends Error {
  constructor(message, statusCode, originalError = null) {
    super(message);
    this.statusCode = statusCode;
    this.originalError = originalError;
    this.timestamp = new Date();
  }
}

class RateLimitError extends APIError {
  constructor(apiName, retryAfter = null) {
    super(
      `Rate limit exceeded for ${apiName}`,
      429
    );
    this.apiName = apiName;
    this.retryAfter = retryAfter;
  }
}

class DataNotFoundError extends APIError {
  constructor(resource, identifier) {
    super(
      `${resource} not found: ${identifier}`,
      404
    );
    this.resource = resource;
    this.identifier = identifier;
  }
}

class ServiceUnavailableError extends APIError {
  constructor(apiName) {
    super(
      `${apiName} is temporarily unavailable`,
      503
    );
    this.apiName = apiName;
  }
}

class ValidationError extends APIError {
  constructor(message, details = null) {
    super(message, 400);
    this.details = details;
  }
}

module.exports = {
  APIError,
  RateLimitError,
  DataNotFoundError,
  ServiceUnavailableError,
  ValidationError
};
```

### Error Handler Middleware

```javascript
// middleware/errorHandler.js
const logger = require('../logger');
const { APIError, RateLimitError } = require('../errors/apiErrors');

function errorHandler(err, req, res, next) {
  logger.error('Error:', {
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method
  });

  // Handle rate limit errors with retry-after header
  if (err instanceof RateLimitError) {
    res.set('Retry-After', err.retryAfter || 60);
    return res.status(429).json({
      error: 'Rate limit exceeded',
      message: err.message,
      retryAfter: err.retryAfter
    });
  }

  // Handle API errors
  if (err instanceof APIError) {
    return res.status(err.statusCode).json({
      error: err.name,
      message: err.message,
      timestamp: err.timestamp
    });
  }

  // Handle validation errors
  if (err.isJoi) {
    return res.status(400).json({
      error: 'Validation error',
      details: err.details
    });
  }

  // Generic error
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'An error occurred'
  });
}

module.exports = errorHandler;
```

### Retry Logic

```javascript
// utils/retry.js
const logger = require('../logger');
const { RateLimitError } = require('../errors/apiErrors');

async function retryWithBackoff(
  fn,
  maxRetries = 3,
  baseDelay = 1000,
  backoffFactor = 2
) {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      logger.debug(`Attempt ${attempt + 1}/${maxRetries}`);
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry rate limit errors (let client handle with Retry-After)
      if (error instanceof RateLimitError) {
        throw error;
      }

      // Calculate backoff delay
      const delay = baseDelay * Math.pow(backoffFactor, attempt);
      const jitter = Math.random() * 0.1 * delay;

      logger.warn(`Attempt ${attempt + 1} failed, retrying in ${delay}ms...`, {
        error: error.message
      });

      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, delay + jitter));
    }
  }

  logger.error(`All ${maxRetries} attempts failed`);
  throw lastError;
}

module.exports = { retryWithBackoff };
```

---

## 5. RATE LIMIT MANAGEMENT

### Rate Limiter Implementation

```javascript
// utils/rateLimiter.js
const logger = require('../logger');
const { RateLimitError } = require('../errors/apiErrors');

class RateLimiter {
  constructor(maxRequests, windowMs = 60000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.requests = [];
  }

  async acquire() {
    const now = Date.now();

    // Remove old requests outside the window
    this.requests = this.requests.filter(
      time => now - time < this.windowMs
    );

    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = this.requests[0];
      const waitTime = this.windowMs - (now - oldestRequest);

      logger.warn(`Rate limit reached, waiting ${waitTime}ms`);
      throw new RateLimitError(
        'Rate limiter',
        Math.ceil(waitTime / 1000)
      );
    }

    this.requests.push(now);
  }

  async execute(fn) {
    await this.acquire();
    return fn();
  }

  getStatus() {
    const now = Date.now();
    this.requests = this.requests.filter(
      time => now - time < this.windowMs
    );

    return {
      used: this.requests.length,
      available: this.maxRequests - this.requests.length,
      resetTime: this.requests.length > 0 ?
        this.requests[0] + this.windowMs :
        now
    };
  }
}

module.exports = RateLimiter;
```

### Rate Limit Aware Service

```javascript
// services/rateLimitedStockService.js
const RateLimiter = require('../utils/rateLimiter');
const logger = require('../logger');

class RateLimitedStockService {
  constructor(stockService, config) {
    this.stockService = stockService;

    // Create limiters for each API
    this.iexLimiter = new RateLimiter(
      config.apis.iexCloud.rateLimit,
      60000
    );
    this.finnhubLimiter = new RateLimiter(
      config.apis.finnhub.rateLimit,
      60000
    );
  }

  async getQuote(symbol) {
    return this.iexLimiter.execute(async () => {
      return this.stockService.getQuote(symbol);
    });
  }

  async getFundamentals(symbol) {
    return this.finnhubLimiter.execute(async () => {
      return this.stockService.getFundamentals(symbol);
    });
  }

  getStatus() {
    return {
      iex: this.iexLimiter.getStatus(),
      finnhub: this.finnhubLimiter.getStatus()
    };
  }
}

module.exports = RateLimitedStockService;
```

---

## 6. BACKGROUND JOBS

### Queue Setup (Bull)

```javascript
// queue/bullConfig.js
const Bull = require('bull');
const logger = require('../logger');

const queues = {
  quotes: new Bull('fetch-quotes', process.env.REDIS_URL),
  fundamentals: new Bull('fetch-fundamentals', process.env.REDIS_URL),
  news: new Bull('fetch-news', process.env.REDIS_URL),
  insider: new Bull('fetch-insider-trades', process.env.REDIS_URL)
};

// Setup event listeners
Object.values(queues).forEach(queue => {
  queue.on('failed', (job, error) => {
    logger.error(`Job ${job.id} failed:`, error.message);
  });

  queue.on('completed', (job) => {
    logger.debug(`Job ${job.id} completed`);
  });
});

module.exports = queues;
```

### Worker Processors

```javascript
// workers/quoteWorker.js
const logger = require('../logger');

async function processQuoteJob(job, stockService) {
  const { symbols } = job.data;
  logger.info(`Processing ${symbols.length} quotes`);

  const results = await Promise.allSettled(
    symbols.map(symbol => stockService.getQuote(symbol))
  );

  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;

  logger.info(`Quote job completed: ${successful} successful, ${failed} failed`);

  return {
    processedAt: new Date(),
    successful,
    failed,
    total: symbols.length
  };
}

module.exports = { processQuoteJob };
```

### Job Scheduling

```javascript
// services/jobScheduler.js
const logger = require('../logger');
const queues = require('../queue/bullConfig');

class JobScheduler {
  constructor(stockService) {
    this.stockService = stockService;
  }

  async start() {
    logger.info('Starting job scheduler');

    // Schedule quote updates every 5 minutes
    this.scheduleRecurring('quotes', async () => {
      await queues.quotes.add(
        { symbols: ['AAPL', 'MSFT', 'GOOGL'] },
        { repeat: { every: 5 * 60 * 1000 } }
      );
    });

    // Schedule fundamentals updates daily
    this.scheduleRecurring('fundamentals', async () => {
      await queues.fundamentals.add(
        { symbols: ['AAPL', 'MSFT', 'GOOGL'] },
        { repeat: { every: 24 * 60 * 60 * 1000 } }
      );
    });

    // Schedule news updates hourly
    this.scheduleRecurring('news', async () => {
      await queues.news.add(
        { symbols: ['AAPL', 'MSFT', 'GOOGL'] },
        { repeat: { every: 60 * 60 * 1000 } }
      );
    });

    logger.info('Job scheduler started');
  }

  scheduleRecurring(name, setupFn) {
    logger.debug(`Scheduling recurring job: ${name}`);
    setupFn().catch(err => logger.error(`Job setup failed:`, err));
  }
}

module.exports = JobScheduler;
```

---

## 7. TESTING & MONITORING

### API Testing

```javascript
// tests/iexClient.test.js
const IEXCloudClient = require('../clients/iexCloudClient');
const config = require('../config');

describe('IEXCloudClient', () => {
  let client;

  beforeAll(() => {
    client = new IEXCloudClient(config.apis.iexCloud);
  });

  test('getQuote returns valid quote structure', async () => {
    const quote = await client.getQuote('AAPL');

    expect(quote).toHaveProperty('price');
    expect(quote).toHaveProperty('change');
    expect(quote).toHaveProperty('changePercent');
    expect(quote).toHaveProperty('timestamp');
    expect(quote.dataSource).toBe('IEX_CLOUD');
  });

  test('getQuotes handles multiple symbols', async () => {
    const results = await client.getQuotes(['AAPL', 'MSFT', 'GOOGL']);

    expect(results.length).toBe(3);
    results.forEach(result => {
      expect(result.status).toBe('fulfilled');
      expect(result.value).toHaveProperty('price');
    });
  });

  test('handles invalid symbol gracefully', async () => {
    await expect(client.getQuote('INVALID')).rejects.toThrow();
  });
});
```

### Monitoring & Metrics

```javascript
// monitoring/metrics.js
const logger = require('../logger');

class MetricsCollector {
  constructor() {
    this.metrics = {
      apiCalls: {},
      errors: {},
      cacheHits: 0,
      cacheMisses: 0,
      avgResponseTime: {}
    };
  }

  recordAPICall(apiName, responseTime) {
    if (!this.metrics.apiCalls[apiName]) {
      this.metrics.apiCalls[apiName] = [];
    }
    this.metrics.apiCalls[apiName].push(responseTime);

    // Keep only last 100 calls
    if (this.metrics.apiCalls[apiName].length > 100) {
      this.metrics.apiCalls[apiName].shift();
    }
  }

  recordError(apiName, error) {
    if (!this.metrics.errors[apiName]) {
      this.metrics.errors[apiName] = [];
    }
    this.metrics.errors[apiName].push({
      timestamp: new Date(),
      error: error.message
    });
  }

  recordCacheHit() {
    this.metrics.cacheHits++;
  }

  recordCacheMiss() {
    this.metrics.cacheMisses++;
  }

  getMetrics() {
    const avgResponseTime = {};

    for (const [api, times] of Object.entries(this.metrics.apiCalls)) {
      const avg = times.reduce((a, b) => a + b, 0) / times.length;
      avgResponseTime[api] = Math.round(avg);
    }

    return {
      ...this.metrics,
      avgResponseTime,
      cacheHitRate: this.metrics.cacheHits / (this.metrics.cacheHits + this.metrics.cacheMisses),
      timestamp: new Date()
    };
  }
}

module.exports = MetricsCollector;
```

---

## Integration Example

```javascript
// app.js
const express = require('express');
const config = require('./config');
const logger = require('./logger');

// Clients
const IEXCloudClient = require('./clients/iexCloudClient');
const FinnhubClient = require('./clients/finnhubClient');
const SECEdgarClient = require('./clients/secEdgarClient');

// Services
const CacheManager = require('./cache/cacheManager');
const StockService = require('./services/stockService');
const RateLimitedStockService = require('./services/rateLimitedStockService');

// Middleware
const errorHandler = require('./middleware/errorHandler');

// Routes
const stockRoutes = require('./routes/stocks');

const app = express();

// Initialize services
const cacheManager = new CacheManager(config.redis);
const iexClient = new IEXCloudClient(config.apis.iexCloud);
const finnhubClient = new FinnhubClient(config.apis.finnhub);
const secEdgarClient = new SECEdgarClient(config.apis.secEdgar);

const stockService = new StockService(
  iexClient,
  finnhubClient,
  cacheManager,
  config
);

const rateLimitedService = new RateLimitedStockService(stockService, config);

// Middleware
app.use(express.json());

// Routes
app.use('/api/stocks', stockRoutes(rateLimitedService));

// Error handling
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
  cacheManager.connect();
});

module.exports = app;
```

```javascript
// routes/stocks.js
const express = require('express');
const { validateSymbol } = require('../middleware/validation');

function createStockRoutes(stockService) {
  const router = express.Router();

  // Get single quote
  router.get('/:symbol/quote', validateSymbol, async (req, res, next) => {
    try {
      const quote = await stockService.getQuote(req.params.symbol);
      res.json(quote);
    } catch (error) {
      next(error);
    }
  });

  // Get multiple quotes
  router.post('/quotes/bulk', async (req, res, next) => {
    try {
      const { symbols } = req.body;
      const quotes = await stockService.getQuotes(symbols);
      res.json(quotes);
    } catch (error) {
      next(error);
    }
  });

  // Get fundamentals
  router.get('/:symbol/fundamentals', validateSymbol, async (req, res, next) => {
    try {
      const fundamentals = await stockService.getFundamentals(req.params.symbol);
      res.json(fundamentals);
    } catch (error) {
      next(error);
    }
  });

  // Get technical data
  router.get('/:symbol/technical', validateSymbol, async (req, res, next) => {
    try {
      const { startDate, endDate } = req.query;
      const technical = await stockService.getTechnicalData(
        req.params.symbol,
        startDate,
        endDate
      );
      res.json(technical);
    } catch (error) {
      next(error);
    }
  });

  return router;
}

module.exports = createStockRoutes;
```

---

This implementation guide provides a complete foundation for integrating multiple financial data APIs with proper caching, error handling, rate limiting, and background job processing.

