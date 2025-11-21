# Technology Stack Recommendations

## Backend Services

### API Service
**Recommended: Node.js + Express + TypeScript**

**Rationale**:
- Excellent performance for I/O-heavy operations (API calls, DB queries)
- Rich ecosystem for real-time features (Socket.io)
- TypeScript adds type safety and better developer experience
- Easy horizontal scaling
- Large community and extensive libraries

**Alternative**: Python + FastAPI (if team is more Python-focused)

**Key Dependencies**:
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "typescript": "^5.3.0",
    "@types/node": "^20.10.0",
    "@types/express": "^4.17.21",
    "socket.io": "^4.6.1",
    "pg": "^8.11.3",
    "ioredis": "^5.3.2",
    "bullmq": "^5.1.0",
    "joi": "^17.11.0",
    "winston": "^3.11.0",
    "helmet": "^7.1.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "jsonwebtoken": "^9.0.2",
    "bcrypt": "^5.1.1"
  }
}
```

### Scraping Service
**Recommended: Python 3.11+ with FastAPI**

**Rationale**:
- Python has the best web scraping libraries (BeautifulSoup, Playwright, Scrapy)
- FastAPI provides async support and automatic API documentation
- Easy to integrate ML libraries for data analysis if needed
- Better for complex data parsing and transformation

**Key Dependencies**:
```txt
fastapi==0.108.0
uvicorn[standard]==0.25.0
playwright==1.40.0
beautifulsoup4==4.12.2
lxml==4.9.4
httpx==0.25.2
pydantic==2.5.3
python-dotenv==1.0.0
redis==5.0.1
asyncpg==0.29.0
sqlalchemy==2.0.23
alembic==1.13.1
celery==5.3.4
python-json-logger==2.0.7
```

## Databases

### Primary Database: PostgreSQL 15+
**Rationale**:
- ACID compliance for financial data
- Excellent support for complex queries and joins
- JSON/JSONB support for flexible data
- Robust indexing capabilities
- Proven at scale

**Configuration**:
```sql
-- postgresql.conf optimizations
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200
work_mem = 20MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

### Time-Series Data: TimescaleDB
**Rationale**:
- Extension of PostgreSQL specifically for time-series data
- Automatic partitioning (hypertables)
- Optimized for time-based queries (stock prices)
- Compression for historical data
- Compatible with existing PostgreSQL tools

**Usage**:
```sql
-- Create hypertable for stock prices
SELECT create_hypertable('stock_prices', 'time');

-- Enable compression for data older than 7 days
ALTER TABLE stock_prices SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'stock_id'
);

SELECT add_compression_policy('stock_prices', INTERVAL '7 days');
```

### Cache & Queue: Redis 7+
**Rationale**:
- Extremely fast in-memory data store
- Built-in data structures (strings, hashes, sets, sorted sets)
- Pub/Sub for real-time messaging
- Perfect for BullMQ job queue
- TTL support for cache expiration

**Use Cases**:
- API response caching
- Session storage
- Rate limiting counters
- Real-time data (latest prices)
- Job queue (BullMQ)
- WebSocket pub/sub

## Message Queue & Job Processing

### BullMQ (Redis-based)
**Rationale**:
- Modern, TypeScript-first queue library
- Built on Redis for performance
- Advanced features (retries, rate limiting, priorities, delayed jobs)
- Excellent monitoring UI (Bull Board)
- Better than older alternatives (Kue, Bull)

**Configuration**:
```typescript
// queue.config.ts
import { Queue, Worker, QueueScheduler } from 'bullmq';
import Redis from 'ioredis';

const connection = new Redis({
  host: 'localhost',
  port: 6379,
  maxRetriesPerRequest: null,
});

// Create queue
export const scrapingQueue = new Queue('scraping', { connection });

// Add scheduler for delayed/repeated jobs
export const scheduler = new QueueScheduler('scraping', { connection });

// Worker configuration
export const createWorker = () => new Worker(
  'scraping',
  async (job) => {
    // Job processing logic
  },
  {
    connection,
    concurrency: 5,
    limiter: {
      max: 10,
      duration: 1000, // 10 jobs per second
    },
  }
);
```

## API Gateway & Load Balancer

### NGINX or Kong Gateway

**NGINX** - Simpler setup:
```nginx
upstream api_backend {
    least_conn;
    server api-1:3000 weight=1;
    server api-2:3000 weight=1;
    server api-3:3000 weight=1;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Kong Gateway** - More features (plugins, authentication):
- Built-in authentication, rate limiting, logging
- Plugin ecosystem
- Admin API and GUI
- Better for microservices architecture

## Web Scraping Tools

### Browser Automation: Playwright
**Rationale**:
- Modern, actively maintained (Microsoft)
- Better anti-detection than Puppeteer
- Cross-browser support
- Async/await API
- Built-in auto-waiting
- Network interception

**Alternative for Simple Scraping**: Cheerio + Axios
- Much faster (no browser overhead)
- Use for sites without JavaScript rendering

### Proxy Management: Bright Data or ScraperAPI
**Rationale**:
- Rotating residential proxies
- Automatic retry and IP rotation
- Geographic targeting
- Bypass most anti-bot systems

## Real-time Communication

### WebSocket: Socket.io
**Rationale**:
- Easy to use, well-documented
- Automatic fallback to long-polling
- Room-based broadcasting
- Redis adapter for horizontal scaling
- Reconnection handling

**Configuration**:
```typescript
// websocket.server.ts
import { Server } from 'socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import Redis from 'ioredis';

const pubClient = new Redis();
const subClient = pubClient.duplicate();

const io = new Server(server, {
  cors: { origin: '*' },
  adapter: createAdapter(pubClient, subClient),
});

io.on('connection', (socket) => {
  // Join ticker-specific rooms
  socket.on('subscribe', (ticker) => {
    socket.join(`stock:${ticker}`);
  });

  socket.on('unsubscribe', (ticker) => {
    socket.leave(`stock:${ticker}`);
  });
});

// Broadcast price update
export function broadcastPriceUpdate(ticker: string, data: any) {
  io.to(`stock:${ticker}`).emit('price_update', data);
}
```

## Monitoring & Logging

### Application Monitoring: Prometheus + Grafana
**Prometheus** - Metrics collection:
```typescript
import client from 'prom-client';

// Register default metrics
client.collectDefaultMetrics();

// Custom metrics
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
});

const scrapingJobsTotal = new client.Counter({
  name: 'scraping_jobs_total',
  help: 'Total number of scraping jobs',
  labelNames: ['source', 'status'],
});
```

**Grafana** - Visualization and alerting

### Logging: Winston (Node.js) / Python logging
**Structured JSON logging**:
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});
```

### Error Tracking: Sentry
**Rationale**:
- Automatic error tracking
- Source map support
- Performance monitoring
- User context and breadcrumbs

## Containerization & Orchestration

### Docker + Docker Compose (Development)
```yaml
version: '3.8'
services:
  api:
    build: ./api-service
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/db
      REDIS_URL: redis://redis:6379
    depends_on: [postgres, redis]

  scraper:
    build: ./scraping-service
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/db
      REDIS_URL: redis://redis:6379
    depends_on: [postgres, redis]

  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: password
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
```

### Kubernetes (Production)
For production at scale, use Kubernetes with:
- Horizontal Pod Autoscaler
- Persistent volumes for databases
- Ingress for load balancing
- ConfigMaps and Secrets for configuration

## CI/CD

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Deploy commands
```

## Development Tools

### API Documentation: Swagger/OpenAPI
**FastAPI** (automatic):
```python
from fastapi import FastAPI

app = FastAPI(
    title="Stock Dashboard API",
    version="1.0.0",
    description="API for stock trading dashboard"
)
# Automatic docs at /docs and /redoc
```

**Express** (manual):
```typescript
import swaggerJSDoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Stock Dashboard API',
      version: '1.0.0',
    },
  },
  apis: ['./src/routes/*.ts'],
};

const swaggerSpec = swaggerJSDoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
```

### Database Migrations: Alembic (Python) / node-pg-migrate (Node.js)

### Testing:
- **Unit Tests**: Jest (Node.js), pytest (Python)
- **Integration Tests**: Supertest (Node.js), TestClient (FastAPI)
- **Load Testing**: k6 or Apache JMeter

## Security

### Authentication: JWT
```typescript
import jwt from 'jsonwebtoken';

export function generateToken(userId: string): string {
  return jwt.sign({ userId }, process.env.JWT_SECRET!, {
    expiresIn: '7d',
  });
}

export function verifyToken(token: string): any {
  return jwt.verify(token, process.env.JWT_SECRET!);
}
```

### Rate Limiting: express-rate-limit + Redis
```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import Redis from 'ioredis';

const limiter = rateLimit({
  store: new RedisStore({
    client: new Redis(),
    prefix: 'rl:',
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP',
});

app.use('/api/', limiter);
```

### Environment Variables: dotenv
```env
# .env
NODE_ENV=production
PORT=3000
DATABASE_URL=postgresql://user:pass@localhost:5432/stockdb
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key
SENTRY_DSN=https://...
```

## Cost Optimization

1. **Database**: Use connection pooling, read replicas for heavy reads
2. **Redis**: Use appropriate eviction policies, compress large values
3. **Scraping**: Cache aggressively, use CDN for static content
4. **Compute**: Autoscale based on demand, use spot instances for workers

## Summary Table

| Component | Technology | Why |
|-----------|-----------|-----|
| API Service | Node.js + Express + TypeScript | Fast, async I/O, large ecosystem |
| Scraping Service | Python + FastAPI + Playwright | Best scraping libraries, async support |
| Primary DB | PostgreSQL + TimescaleDB | ACID, time-series optimization |
| Cache/Queue | Redis 7 | Speed, versatility, BullMQ support |
| Job Queue | BullMQ | Modern, feature-rich, TypeScript |
| Load Balancer | NGINX | Simple, fast, proven |
| WebSocket | Socket.io | Easy, scalable, auto-reconnect |
| Monitoring | Prometheus + Grafana | Industry standard, powerful |
| Logging | Winston / Python logging | Structured, flexible |
| Error Tracking | Sentry | Automatic, detailed |
| Container | Docker + Kubernetes | Scalability, portability |
| CI/CD | GitHub Actions | Integrated, easy to configure |

