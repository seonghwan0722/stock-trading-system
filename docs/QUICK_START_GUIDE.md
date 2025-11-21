# Quick Start Guide: API Setup & Integration

## Table of Contents
1. API Key Setup
2. Backend Configuration
3. cURL Examples
4. Testing First Integration
5. Troubleshooting

---

## 1. API KEY SETUP

### Step 1: IEX Cloud (Real-time Quotes)
**Signup URL**: https://iexcloud.io/console/

```bash
# 1. Visit https://iexcloud.io/console/
# 2. Sign up (free account)
# 3. Copy your publishable token (starts with pk_)
# 4. Save to .env file:

IEX_CLOUD_TOKEN=pk_YOUR_TOKEN_HERE
IEX_CLOUD_BASE_URL=https://cloud.iexapis.com/stable
```

**Test Your Token**:
```bash
curl "https://cloud.iexapis.com/stable/stock/AAPL/quote?token=pk_YOUR_TOKEN"
```

---

### Step 2: Finnhub (Company Data)
**Signup URL**: https://finnhub.io/register

```bash
# 1. Visit https://finnhub.io/register
# 2. Sign up (free tier: 60 API calls/minute)
# 3. Copy your API key from dashboard
# 4. Save to .env file:

FINNHUB_API_KEY=YOUR_API_KEY_HERE
FINNHUB_BASE_URL=https://finnhub.io/api/v1
```

**Test Your Token**:
```bash
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_API_KEY"
```

---

### Step 3: Alpha Vantage (Technical Indicators)
**Signup URL**: https://www.alphavantage.co/

```bash
# 1. Visit https://www.alphavantage.co/
# 2. Sign up (free tier: 5 calls/minute, 500/day)
# 3. Copy your API key
# 4. Save to .env file:

ALPHA_VANTAGE_KEY=YOUR_API_KEY_HERE
ALPHA_VANTAGE_BASE_URL=https://www.alphavantage.co/query
```

**Test Your Token**:
```bash
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"
```

---

### Step 4: PostgreSQL Database

```bash
# Install PostgreSQL (if not already installed)
# macOS:
brew install postgresql

# Linux (Ubuntu/Debian):
sudo apt-get install postgresql postgresql-contrib

# Windows:
# Download from https://www.postgresql.org/download/windows/

# Create database
createdb stock_db

# Test connection
psql stock_db
```

**.env Configuration**:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/stock_db
DATABASE_SSL=false
```

---

### Step 5: Redis Cache

```bash
# Install Redis
# macOS:
brew install redis

# Linux:
sudo apt-get install redis-server

# Windows:
# Use Docker: docker run -d -p 6379:6379 redis:latest

# Test connection
redis-cli ping
# Should return: PONG
```

**.env Configuration**:
```bash
REDIS_URL=redis://localhost:6379
```

---

## 2. BACKEND CONFIGURATION

### Complete .env File Template

```env
# === IEX Cloud ===
IEX_CLOUD_TOKEN=pk_xxxxxxxxxxxx
IEX_CLOUD_BASE_URL=https://cloud.iexapis.com/stable
IEX_RATE_LIMIT=100

# === Finnhub ===
FINNHUB_API_KEY=xxxxxxxxxxxx
FINNHUB_BASE_URL=https://finnhub.io/api/v1
FINNHUB_RATE_LIMIT=60

# === Alpha Vantage ===
ALPHA_VANTAGE_KEY=xxxxxxxxxxxx
ALPHA_VANTAGE_BASE_URL=https://www.alphavantage.co/query
ALPHA_RATE_LIMIT=5

# === SEC EDGAR ===
SEC_EDGAR_BASE_URL=https://www.sec.gov/cgi-bin/browse-edgar

# === Database ===
DATABASE_URL=postgresql://user:password@localhost:5432/stock_db
DATABASE_SSL=false
DATABASE_POOL_SIZE=10

# === Redis ===
REDIS_URL=redis://localhost:6379
REDIS_TTL_QUOTES=300
REDIS_TTL_FUNDAMENTALS=604800
REDIS_TTL_INDICATORS=86400
REDIS_TTL_NEWS=3600

# === Feature Flags ===
USE_IEX_REAL_TIME=true
USE_FINNHUB_FUNDAMENTALS=true
USE_ALPHA_VANTAGE_INDICATORS=false
USE_SEC_EDGAR_INSIDER=true

# === Application ===
NODE_ENV=development
PORT=3000
LOG_LEVEL=debug
CORS_ORIGIN=http://localhost:3000

# === Monitoring ===
ENABLE_METRICS=true
METRICS_PORT=9090
```

### package.json Dependencies

```json
{
  "dependencies": {
    "express": "^4.18.0",
    "axios": "^1.3.0",
    "axios-rate-limit": "^1.3.0",
    "redis": "^4.6.0",
    "pg": "^8.9.0",
    "bull": "^4.10.0",
    "dotenv": "^16.0.0",
    "joi": "^17.8.0",
    "winston": "^3.8.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "express-rate-limit": "^6.7.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "supertest": "^6.3.0",
    "nodemon": "^2.0.0"
  }
}
```

---

## 3. CURL EXAMPLES

### Real-time Quote from IEX Cloud

```bash
# Get single stock quote
curl -X GET "https://cloud.iexapis.com/stable/stock/AAPL/quote?token=pk_YOUR_TOKEN" \
  -H "Accept: application/json"

# Response:
{
  "symbol": "AAPL",
  "latestPrice": 172.45,
  "change": 1.25,
  "changePercent": 0.0073,
  "latestVolume": 52847100,
  "marketCap": 2741000000000,
  "peRatio": 28.5,
  "latestUpdate": 1700596800000,
  ...
}
```

### Company Fundamentals from Finnhub

```bash
# Get company profile
curl -X GET "https://finnhub.io/api/v1/stock/profile2?symbol=AAPL&token=YOUR_KEY" \
  -H "Accept: application/json"

# Response:
{
  "country": "US",
  "currency": "USD",
  "estimateCurrency": "USD",
  "description": "Apple Inc. is an American technology...",
  "finnhubIndustry": "Consumer Electronics",
  "ipo": "1980-12-12",
  "logo": "https://...",
  "marketCapitalization": 2741,
  "name": "Apple Inc.",
  "phone": "1 408 996 1010",
  "shareOutstanding": 15685.926,
  "ticker": "AAPL",
  "weburl": "https://www.apple.com",
  ...
}
```

### Historical Candle Data from Finnhub

```bash
# Get daily candles for date range
START=$(date -d "2024-01-01" +%s)
END=$(date -d "2024-12-31" +%s)

curl -X GET "https://finnhub.io/api/v1/stock/candle" \
  -G \
  -d "symbol=AAPL" \
  -d "resolution=D" \
  -d "from=$START" \
  -d "to=$END" \
  -d "token=YOUR_KEY"

# Response:
{
  "c": [172.45, 171.50, 172.30, ...],  # Close prices
  "h": [173.50, 172.20, 173.10, ...],  # High prices
  "l": [171.50, 171.20, 171.90, ...],  # Low prices
  "o": [172.00, 171.80, 172.50, ...],  # Open prices
  "s": "ok",
  "t": [1700596800, 1700683200, 1700769600, ...],  # Timestamps
  "v": [52847100, 48923400, 51234500, ...]  # Volumes
}
```

### Technical Indicators from Alpha Vantage

```bash
# Get SMA (Simple Moving Average)
curl -X GET "https://www.alphavantage.co/query" \
  -G \
  -d "function=SMA" \
  -d "symbol=AAPL" \
  -d "interval=daily" \
  -d "time_period=20" \
  -d "series_type=close" \
  -d "apikey=YOUR_KEY"

# Response:
{
  "Meta Data": {
    "1: Symbol": "AAPL",
    "2: Indicator": "Simple Moving Average (SMA)",
    "3: Last Refreshed": "2024-11-21",
    "4: Interval": "daily",
    "5: Time Period": 20,
    "6: Series Type": "close"
  },
  "Technical Analysis: SMA": {
    "2024-11-21": { "SMA": "172.45" },
    "2024-11-20": { "SMA": "171.95" },
    ...
  }
}
```

### SEC EDGAR Form 4 Filings

```bash
# Search insider transactions (Form 4)
curl -X GET "https://www.sec.gov/cgi-bin/browse-edgar" \
  -G \
  -d "action=getcompany" \
  -d "CIK=0000789019" \
  -d "type=4" \
  -d "owner=exclude" \
  -d "count=100" \
  -H "User-Agent: YourApp/1.0 (contact@yourapp.com)"

# Note: Returns HTML, requires parsing
# Look for rows in the filing table with Form 4 entries
```

### Your Backend API Examples

```bash
# Get real-time quote from your API
curl -X GET "http://localhost:3000/api/v1/stocks/AAPL/quote" \
  -H "Accept: application/json"

# Response:
{
  "symbol": "AAPL",
  "price": 172.45,
  "change": 1.25,
  "changePercent": 0.73,
  "volume": 52847100,
  "marketCap": 2741000000000,
  "peRatio": 28.5,
  "timestamp": "2024-11-21T16:00:00Z",
  "dataSource": "IEX_CLOUD",
  "cached": false
}

# Get multiple quotes
curl -X POST "http://localhost:3000/api/v1/stocks/quotes/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"]
  }'

# Get fundamentals
curl -X GET "http://localhost:3000/api/v1/stocks/AAPL/fundamentals" \
  -H "Accept: application/json"

# Get technical data
curl -X GET "http://localhost:3000/api/v1/stocks/AAPL/technical" \
  -H "Accept: application/json" \
  -G \
  -d "startDate=2024-01-01" \
  -d "endDate=2024-12-31"

# Get insider trades
curl -X GET "http://localhost:3000/api/v1/insider-trades" \
  -H "Accept: application/json" \
  -G \
  -d "symbol=AAPL" \
  -d "days=30" \
  -d "limit=50"
```

---

## 4. TESTING FIRST INTEGRATION

### Step 1: Verify API Credentials

```bash
#!/bin/bash
# test-apis.sh - Verify all API connections

echo "Testing IEX Cloud..."
curl -s "https://cloud.iexapis.com/stable/stock/AAPL/quote?token=$IEX_CLOUD_TOKEN" \
  | head -c 100
echo "\n"

echo "Testing Finnhub..."
curl -s "https://finnhub.io/api/v1/quote?symbol=AAPL&token=$FINNHUB_API_KEY" \
  | head -c 100
echo "\n"

echo "Testing Alpha Vantage..."
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=$ALPHA_VANTAGE_KEY" \
  | head -c 100
echo "\n"

echo "Testing SEC EDGAR..."
curl -s "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019&type=4&owner=exclude&count=10" \
  | grep -o "Form 4" | head -1
echo "\n"

echo "All basic API tests complete!"
```

### Step 2: Test Database Connection

```bash
# Test PostgreSQL
psql $DATABASE_URL -c "SELECT version();"

# Create initial schema
psql $DATABASE_URL << EOF
CREATE TABLE IF NOT EXISTS stock_quotes (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(10) NOT NULL,
  price DECIMAL(10,2),
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

SELECT COUNT(*) FROM stock_quotes;
EOF
```

### Step 3: Test Redis Connection

```bash
# Test Redis
redis-cli -u $REDIS_URL PING
# Should return: PONG

# Set and get test data
redis-cli -u $REDIS_URL SET test-key "test-value"
redis-cli -u $REDIS_URL GET test-key
# Should return: "test-value"
```

### Step 4: Run First Backend Test

```bash
# Create simple test file
cat > test-api-integration.js << 'EOF'
const axios = require('axios');

const apiTests = async () => {
  try {
    // Test IEX Cloud
    console.log('Testing IEX Cloud...');
    const iexResponse = await axios.get(
      `https://cloud.iexapis.com/stable/stock/AAPL/quote?token=${process.env.IEX_CLOUD_TOKEN}`
    );
    console.log('IEX Quote:', {
      price: iexResponse.data.latestPrice,
      change: iexResponse.data.change
    });

    // Test Finnhub
    console.log('\nTesting Finnhub...');
    const finnhubResponse = await axios.get(
      `https://finnhub.io/api/v1/quote?symbol=AAPL&token=${process.env.FINNHUB_API_KEY}`
    );
    console.log('Finnhub Quote:', {
      price: finnhubResponse.data.c,
      change: finnhubResponse.data.d
    });

    console.log('\nAll API tests passed!');
  } catch (error) {
    console.error('Test failed:', error.message);
    process.exit(1);
  }
};

apiTests();
EOF

# Run test
node test-api-integration.js
```

---

## 5. TROUBLESHOOTING

### Issue: "Invalid API Key"

```bash
# Check your .env file has correct format
grep "IEX_CLOUD_TOKEN" .env
# Should show: IEX_CLOUD_TOKEN=pk_xxxx

# Test directly with curl
curl "https://cloud.iexapis.com/stable/stock/AAPL/quote?token=YOUR_ACTUAL_TOKEN"

# If you see: {"message":"Invalid API token"}
# - Regenerate your token in IEX Cloud dashboard
# - Copy/paste carefully (no extra spaces)
# - Reload your environment variables
```

### Issue: Rate Limit Exceeded (429)

```bash
# Check rate limit with -v flag
curl -v "https://cloud.iexapis.com/stable/stock/AAPL/quote?token=pk_YOUR_TOKEN" 2>&1 | grep "Retry-After"

# Solution: Add delay between requests
# Implement exponential backoff:
async function retryRequest(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.response?.status === 429) {
        const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
        await new Promise(r => setTimeout(r, delay));
      } else {
        throw error;
      }
    }
  }
}
```

### Issue: Database Connection Failed

```bash
# Check PostgreSQL is running
ps aux | grep postgres

# Start PostgreSQL if not running
# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# Verify connection string format
# Should be: postgresql://username:password@host:port/database
# NOT: postgres://... (outdated)

# Test directly
psql "postgresql://user:password@localhost:5432/stock_db" -c "SELECT 1"
```

### Issue: Redis Connection Failed

```bash
# Check Redis is running
redis-cli ping

# Start Redis if not running
redis-server

# Or with Docker:
docker run -d -p 6379:6379 redis:latest

# Verify connection
redis-cli -u redis://localhost:6379 PING
```

### Issue: Slow API Responses

```bash
# Check API response time:
time curl "https://cloud.iexapis.com/stable/stock/AAPL/quote?token=pk_YOUR_TOKEN"

# Expected times:
# IEX Cloud: 200-500ms
# Finnhub: 300-800ms
# Alpha Vantage: 500-1500ms (slower)
# SEC EDGAR: 1-5 seconds (HTML response)

# If slower than expected:
# 1. Check internet connection
# 2. Check if API service is degraded
# 3. Try different symbol (some may be slower)
# 4. Implement caching to avoid repeated calls
```

### Issue: Cached Data Not Updating

```bash
# Check Redis TTL
redis-cli -u redis://localhost:6379 TTL "cache:quote:AAPL"
# Returns: remaining seconds

# Manually flush cache for testing
redis-cli -u redis://localhost:6379 FLUSHDB

# In code, ensure TTL is set:
await cache.set(key, value, 300); // 5 minutes
```

---

## Quick Health Check Script

```bash
#!/bin/bash
# health-check.sh - Comprehensive API health check

echo "=== API Health Check ==="
echo "Time: $(date)"
echo ""

# Check APIs
apis=(
  "IEX:https://cloud.iexapis.com/stable/stock/AAPL/quote?token=$IEX_CLOUD_TOKEN"
  "Finnhub:https://finnhub.io/api/v1/quote?symbol=AAPL&token=$FINNHUB_API_KEY"
  "Alpha Vantage:https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=$ALPHA_VANTAGE_KEY"
)

for api_test in "${apis[@]}"; do
  IFS=':' read -r name url <<< "$api_test"
  echo -n "Testing $name... "
  response=$(curl -s -w "%{http_code}" -o /dev/null "$url")
  if [ "$response" = "200" ]; then
    echo "OK"
  else
    echo "FAILED (HTTP $response)"
  fi
done

# Check services
echo ""
echo "=== Services ==="
echo -n "PostgreSQL... "
psql -c "SELECT 1" &>/dev/null && echo "OK" || echo "FAILED"

echo -n "Redis... "
redis-cli ping &>/dev/null && echo "OK" || echo "FAILED"

echo ""
echo "=== Summary ==="
echo "All checks complete. Check any FAILED items above."
```

---

## Next Steps

1. **Setup all API keys** (10-15 minutes)
2. **Configure environment variables** (5 minutes)
3. **Test API connections** (5 minutes)
4. **Create first backend endpoint** (30 minutes)
5. **Deploy and test** (30 minutes)

**Total Time to First API Integration**: ~2 hours

---

## Support Resources

- **IEX Cloud Docs**: https://iexcloud.io/docs
- **Finnhub Docs**: https://finnhub.io/docs/api
- **Alpha Vantage Docs**: https://www.alphavantage.co/documentation
- **SEC EDGAR**: https://www.sec.gov/edgar/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/docs/

---

**Document Version**: 1.0
**Last Updated**: November 21, 2025

