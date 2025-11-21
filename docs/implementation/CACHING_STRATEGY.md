# Caching Strategy

## Overview

A multi-layer caching strategy to minimize database queries, reduce scraping frequency, and improve response times.

## Cache Layers

```
┌──────────────┐
│   Client     │  Browser cache (Cache-Control headers)
└──────┬───────┘
       │
┌──────▼───────┐
│  CloudFront  │  CDN cache (static + API responses)
└──────┬───────┘
       │
┌──────▼───────┐
│ Application  │  In-memory cache (node-cache, LRU)
│   Memory     │
└──────┬───────┘
       │
┌──────▼───────┐
│    Redis     │  Distributed cache
└──────┬───────┘
       │
┌──────▼───────┐
│  PostgreSQL  │  Database (source of truth)
└──────────────┘
```

## Caching Rules by Data Type

### 1. Static Reference Data (Long TTL)

**Data**: Politicians, stock basic info, sectors, industries

**Strategy**: Cache aggressively, invalidate on updates

**TTL**: 24 hours

**Redis Keys**:
```
politician:{id} => JSON (24h TTL)
stock:{ticker}:info => JSON (24h TTL)
sectors:all => JSON (24h TTL)
```

**Implementation**:
```typescript
// cache.service.ts
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

export async function getPolitician(id: string) {
  const cacheKey = `politician:${id}`;

  // Try cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // Cache miss - fetch from DB
  const politician = await db.query(
    'SELECT * FROM politicians WHERE id = $1',
    [id]
  );

  // Store in cache
  await redis.setex(cacheKey, 86400, JSON.stringify(politician));

  return politician;
}

// Invalidate on update
export async function updatePolitician(id: string, data: any) {
  await db.query('UPDATE politicians SET ... WHERE id = $1', [id]);

  // Invalidate cache
  await redis.del(`politician:${id}`);
}
```

### 2. Frequently Updated Data (Short TTL)

**Data**: Stock prices, recent trades

**Strategy**: Short TTL with cache warming

**TTL**: 5 minutes

**Redis Keys**:
```
stock:{ticker}:price => JSON (5m TTL)
trades:recent => JSON (5m TTL)
stock:{ticker}:trades => JSON (5m TTL)
```

**Implementation**:
```typescript
export async function getStockPrice(ticker: string) {
  const cacheKey = `stock:${ticker}:price`;

  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // Fetch latest price from DB
  const price = await db.query(`
    SELECT * FROM stock_prices
    WHERE stock_id = (SELECT id FROM stocks WHERE ticker = $1)
    ORDER BY time DESC
    LIMIT 1
  `, [ticker]);

  // Cache for 5 minutes
  await redis.setex(cacheKey, 300, JSON.stringify(price));

  return price;
}

// Cache warming - proactively update cache
export async function warmPriceCache(popularTickers: string[]) {
  for (const ticker of popularTickers) {
    await getStockPrice(ticker);
  }
}

// Run cache warming periodically
setInterval(() => {
  const topTickers = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL'];
  warmPriceCache(topTickers);
}, 4 * 60 * 1000); // Every 4 minutes
```

### 3. Real-time Data (Cache-Aside)

**Data**: Latest politician trades, trending stocks

**Strategy**: Cache-aside with pub/sub invalidation

**TTL**: 2-15 minutes (varies by endpoint)

**Redis Keys**:
```
trades:politician:{id}:recent => JSON (15m TTL)
stocks:trending => Sorted Set (10m TTL)
analytics:sector => JSON (30m TTL)
```

**Implementation with Pub/Sub**:
```typescript
// When new trade is inserted
export async function insertTrade(tradeData: any) {
  // Insert to database
  const trade = await db.query('INSERT INTO trades ...', tradeData);

  // Invalidate related caches
  await redis.del(`trades:politician:${tradeData.politician_id}:recent`);
  await redis.del(`trades:stock:${tradeData.ticker}:recent`);
  await redis.del('trades:recent');

  // Publish event for real-time updates
  await redis.publish('new_trade', JSON.stringify(trade));

  return trade;
}

// Subscribe to invalidation events
redis.subscribe('new_trade', 'price_update');

redis.on('message', (channel, message) => {
  if (channel === 'new_trade') {
    const trade = JSON.parse(message);
    // Broadcast to WebSocket clients
    io.to(`politician:${trade.politician_id}`).emit('new_trade', trade);
    io.to(`stock:${trade.ticker}`).emit('new_trade', trade);
  }
});
```

### 4. Computed/Aggregated Data (Medium TTL)

**Data**: Analytics, statistics, portfolio correlations

**Strategy**: Compute once, cache results, background refresh

**TTL**: 30-60 minutes

**Redis Keys**:
```
analytics:politician:{id}:performance => JSON (1h TTL)
analytics:sector:distribution => JSON (30m TTL)
stats:overall => JSON (1h TTL)
```

**Implementation with Background Refresh**:
```typescript
// Heavy computation - cache and refresh in background
export async function getPoliticianPerformance(politicianId: string) {
  const cacheKey = `analytics:politician:${politicianId}:performance`;

  const cached = await redis.get(cacheKey);
  if (cached) {
    // Check if cache is about to expire (< 10 minutes left)
    const ttl = await redis.ttl(cacheKey);
    if (ttl < 600) {
      // Trigger background refresh (don't wait)
      refreshPoliticianPerformance(politicianId);
    }
    return JSON.parse(cached);
  }

  // Cache miss - compute now
  return await computeAndCachePoliticianPerformance(politicianId);
}

async function computeAndCachePoliticianPerformance(politicianId: string) {
  // Heavy DB query with joins and calculations
  const performance = await db.query(`
    SELECT
      p.name,
      COUNT(t.id) as total_trades,
      AVG(sp.close - sp_entry.close) / sp_entry.close as avg_return,
      -- More complex calculations
    FROM politicians p
    JOIN trades t ON t.politician_id = p.id
    JOIN stock_prices sp ON ...
    WHERE p.id = $1
    GROUP BY p.id
  `, [politicianId]);

  const cacheKey = `analytics:politician:${politicianId}:performance`;
  await redis.setex(cacheKey, 3600, JSON.stringify(performance));

  return performance;
}

async function refreshPoliticianPerformance(politicianId: string) {
  // Run in background
  computeAndCachePoliticianPerformance(politicianId).catch(err => {
    logger.error('Failed to refresh cache', { politicianId, error: err });
  });
}
```

### 5. API Response Caching

**Strategy**: Cache complete API responses based on query parameters

**TTL**: Varies by endpoint

**Implementation**:
```typescript
// cache.middleware.ts
import crypto from 'crypto';

export function cacheMiddleware(ttl: number) {
  return async (req, res, next) => {
    // Only cache GET requests
    if (req.method !== 'GET') {
      return next();
    }

    // Generate cache key from URL + query params
    const cacheKey = `api:cache:${req.path}:${hashQuery(req.query)}`;

    // Try cache
    const cached = await redis.get(cacheKey);
    if (cached) {
      return res.json(JSON.parse(cached));
    }

    // Override res.json to cache response
    const originalJson = res.json.bind(res);
    res.json = (data) => {
      // Cache the response
      redis.setex(cacheKey, ttl, JSON.stringify(data));
      return originalJson(data);
    };

    next();
  };
}

function hashQuery(query: any): string {
  const queryString = JSON.stringify(query);
  return crypto.createHash('md5').update(queryString).digest('hex');
}

// Usage in routes
app.get('/api/v1/politicians', cacheMiddleware(600), async (req, res) => {
  // Handler code
});

app.get('/api/v1/stocks/:ticker', cacheMiddleware(300), async (req, res) => {
  // Handler code
});
```

## Cache Invalidation Strategies

### 1. Time-based Invalidation (TTL)
Most common, suitable for most data types.

### 2. Event-based Invalidation
Invalidate cache when data changes.

```typescript
// After scraping new trades
export async function afterScrapingCompleted(source: string, newRecords: any[]) {
  // Invalidate relevant caches
  const keysToDelete = [
    'trades:recent',
    'stocks:trending',
  ];

  // Also invalidate politician-specific caches
  const politicianIds = [...new Set(newRecords.map(r => r.politician_id))];
  for (const id of politicianIds) {
    keysToDelete.push(`trades:politician:${id}:recent`);
  }

  await redis.del(...keysToDelete);
}
```

### 3. Pattern-based Invalidation
Delete multiple keys matching a pattern.

```typescript
export async function invalidateStockCaches(ticker: string) {
  // Get all keys matching pattern
  const pattern = `stock:${ticker}:*`;
  const keys = await redis.keys(pattern);

  if (keys.length > 0) {
    await redis.del(...keys);
  }
}

// Better approach: Use Redis Sets to track related keys
export async function trackCacheKey(group: string, key: string) {
  await redis.sadd(`cache:group:${group}`, key);
}

export async function invalidateCacheGroup(group: string) {
  const keys = await redis.smembers(`cache:group:${group}`);
  if (keys.length > 0) {
    await redis.del(...keys);
    await redis.del(`cache:group:${group}`);
  }
}
```

### 4. Cache Stampede Prevention
Prevent multiple requests from hitting DB when cache expires.

```typescript
import { AsyncLock } from 'async-lock';

const lock = new AsyncLock();

export async function getWithLock<T>(
  cacheKey: string,
  ttl: number,
  fetchFn: () => Promise<T>
): Promise<T> {
  // Try cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // Use lock to prevent stampede
  return await lock.acquire(cacheKey, async () => {
    // Double-check cache (another request might have filled it)
    const cached = await redis.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // Fetch from source
    const data = await fetchFn();

    // Cache result
    await redis.setex(cacheKey, ttl, JSON.stringify(data));

    return data;
  });
}

// Usage
const politician = await getWithLock(
  `politician:${id}`,
  86400,
  () => db.query('SELECT * FROM politicians WHERE id = $1', [id])
);
```

## In-Memory Application Cache

For extremely hot data, use in-memory cache.

```typescript
// app-cache.ts
import NodeCache from 'node-cache';

// Create in-memory cache with 5-minute TTL
const appCache = new NodeCache({
  stdTTL: 300,
  checkperiod: 60,
  useClones: false, // Better performance, but be careful with mutations
});

// Cache popular tickers list (refreshed every 5 min)
export async function getPopularTickers(): Promise<string[]> {
  const cacheKey = 'popular:tickers';

  // Check app cache first
  const cached = appCache.get<string[]>(cacheKey);
  if (cached) {
    return cached;
  }

  // Check Redis
  const redisData = await redis.get(cacheKey);
  if (redisData) {
    const data = JSON.parse(redisData);
    appCache.set(cacheKey, data);
    return data;
  }

  // Fetch from DB
  const result = await db.query(`
    SELECT s.ticker
    FROM stocks s
    JOIN trades t ON t.stock_id = s.id
    WHERE t.transaction_date > NOW() - INTERVAL '30 days'
    GROUP BY s.ticker
    ORDER BY COUNT(*) DESC
    LIMIT 50
  `);

  const tickers = result.rows.map(r => r.ticker);

  // Cache in both layers
  await redis.setex(cacheKey, 300, JSON.stringify(tickers));
  appCache.set(cacheKey, tickers);

  return tickers;
}
```

## Cache Monitoring

### Key Metrics to Track

```typescript
// cache.metrics.ts
import { Counter, Histogram } from 'prom-client';

export const cacheHits = new Counter({
  name: 'cache_hits_total',
  help: 'Total number of cache hits',
  labelNames: ['cache_type', 'key_pattern'],
});

export const cacheMisses = new Counter({
  name: 'cache_misses_total',
  help: 'Total number of cache misses',
  labelNames: ['cache_type', 'key_pattern'],
});

export const cacheLatency = new Histogram({
  name: 'cache_operation_duration_seconds',
  help: 'Cache operation latency',
  labelNames: ['operation', 'cache_type'],
});

// Wrapper function with metrics
export async function getCached<T>(
  key: string,
  fetchFn: () => Promise<T>,
  ttl: number
): Promise<T> {
  const timer = cacheLatency.startTimer({ operation: 'get', cache_type: 'redis' });

  try {
    const cached = await redis.get(key);

    if (cached) {
      cacheHits.inc({ cache_type: 'redis', key_pattern: getKeyPattern(key) });
      timer();
      return JSON.parse(cached);
    }

    cacheMisses.inc({ cache_type: 'redis', key_pattern: getKeyPattern(key) });

    const data = await fetchFn();
    await redis.setex(key, ttl, JSON.stringify(data));

    timer();
    return data;
  } catch (error) {
    timer();
    throw error;
  }
}

function getKeyPattern(key: string): string {
  // Extract pattern from key (e.g., "stock:AAPL:price" => "stock:*:price")
  const parts = key.split(':');
  return parts.map((p, i) => i % 2 === 0 ? p : '*').join(':');
}
```

### Cache Hit Rate Dashboard

Monitor cache effectiveness:
- Overall hit rate (target: >80%)
- Hit rate by key pattern
- Cache memory usage
- Eviction rate

```promql
# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Cache latency
histogram_quantile(0.95, cache_operation_duration_seconds_bucket)
```

## Best Practices

1. **Always set TTL**: Never use infinite TTL, memory is not infinite
2. **Use appropriate TTL**: Balance freshness vs load
3. **Cache at the right layer**: Don't cache everything in Redis if app memory works
4. **Monitor hit rates**: Low hit rate = wasted memory
5. **Handle cache failures gracefully**: App should work even if Redis is down
6. **Use compression for large values**: Reduce memory usage
7. **Implement circuit breaker**: Don't overwhelm cache if it's slow
8. **Warm cache proactively**: For predictable access patterns

## Cache Configuration Summary

| Data Type | TTL | Layer | Invalidation |
|-----------|-----|-------|--------------|
| Politicians | 24h | Redis | Event-based |
| Stocks (basic) | 24h | Redis | Event-based |
| Stock prices | 5m | Redis | TTL + Events |
| Recent trades | 15m | Redis | Event-based |
| Trending stocks | 10m | Redis + App | TTL |
| Analytics | 1h | Redis | Background refresh |
| API responses | 5-10m | Redis | TTL |
| Popular tickers | 5m | App + Redis | TTL |

