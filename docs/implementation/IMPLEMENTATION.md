# Implementation Guide

## Step-by-Step Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### 1.1 Set Up Development Environment

```bash
# Clone repository
git clone <repo-url>
cd stock-dashboard

# Create directory structure
mkdir -p api-service scraping-service shared infrastructure

# Initialize Node.js API service
cd api-service
npm init -y
npm install express typescript @types/node @types/express \
  pg ioredis bullmq socket.io joi winston helmet cors dotenv

npx tsc --init

# Initialize Python scraping service
cd ../scraping-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn playwright beautifulsoup4 httpx \
  pydantic redis asyncpg sqlalchemy alembic python-dotenv

# Install Playwright browsers
playwright install chromium
```

#### 1.2 Set Up Docker Development Environment

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: stockuser
      POSTGRES_PASSWORD: stockpass
      POSTGRES_DB: stockdb
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infrastructure/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data

  api:
    build:
      context: ./api-service
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: development
      DATABASE_URL: postgresql://stockuser:stockpass@postgres:5432/stockdb
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./api-service:/app
      - /app/node_modules
    depends_on:
      - postgres
      - redis
    command: npm run dev

  scraper:
    build:
      context: ./scraping-service
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://stockuser:stockpass@postgres:5432/stockdb
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./scraping-service:/app
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres-data:
  redis-data:
```

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d
```

#### 1.3 Initialize Database Schema

```sql
-- infrastructure/init.sql
-- Run this after starting PostgreSQL

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Run the schema from ARCHITECTURE.md
-- (Copy the SQL from the database schema section)
```

```bash
# Apply migrations using Alembic (Python) or node-pg-migrate (Node.js)
cd api-service
npm install -D node-pg-migrate
npx node-pg-migrate create initial-schema

# Or use SQL directly
psql postgresql://stockuser:stockpass@localhost:5432/stockdb < infrastructure/schema.sql
```

### Phase 2: API Service Core (Week 2-3)

#### 2.1 Project Structure

```
api-service/
├── src/
│   ├── index.ts              # Entry point
│   ├── app.ts                # Express app setup
│   ├── config/
│   │   ├── database.ts       # Database connection
│   │   ├── redis.ts          # Redis connection
│   │   └── logger.ts         # Logging setup
│   ├── middleware/
│   │   ├── errorHandler.ts   # Global error handler
│   │   ├── validation.ts     # Request validation
│   │   ├── auth.ts           # Authentication
│   │   └── cache.ts          # Caching middleware
│   ├── routes/
│   │   ├── index.ts          # Route aggregator
│   │   ├── politicians.ts
│   │   ├── stocks.ts
│   │   ├── trades.ts
│   │   └── analytics.ts
│   ├── controllers/
│   │   ├── politicians.controller.ts
│   │   ├── stocks.controller.ts
│   │   ├── trades.controller.ts
│   │   └── analytics.controller.ts
│   ├── services/
│   │   ├── politicians.service.ts
│   │   ├── stocks.service.ts
│   │   ├── trades.service.ts
│   │   ├── cache.service.ts
│   │   └── analytics.service.ts
│   ├── models/
│   │   └── types.ts          # TypeScript types
│   └── utils/
│       ├── validation.ts
│       └── helpers.ts
├── tests/
│   ├── unit/
│   └── integration/
├── package.json
├── tsconfig.json
└── Dockerfile
```

#### 2.2 Implement Core API Endpoints

```typescript
// src/app.ts
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import { errorHandler } from './middleware/errorHandler';
import routes from './routes';
import { logger } from './config/logger';

const app = express();

// Security middleware
app.use(helmet());
app.use(cors());

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`);
  next();
});

// Routes
app.use('/api/v1', routes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date() });
});

// Error handling
app.use(errorHandler);

export default app;
```

```typescript
// src/routes/politicians.ts
import { Router } from 'express';
import { PoliticiansController } from '../controllers/politicians.controller';
import { cacheMiddleware } from '../middleware/cache';
import { validate } from '../middleware/validation';
import { getPoliticiansSchema } from '../utils/validation';

const router = Router();
const controller = new PoliticiansController();

router.get(
  '/',
  validate(getPoliticiansSchema),
  cacheMiddleware(600),
  controller.getAll
);

router.get('/:id', cacheMiddleware(600), controller.getById);

router.get('/:id/trades', cacheMiddleware(300), controller.getTrades);

export default router;
```

```typescript
// src/controllers/politicians.controller.ts
import { Request, Response, NextFunction } from 'express';
import { PoliticiansService } from '../services/politicians.service';

export class PoliticiansController {
  private service = new PoliticiansService();

  getAll = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { page = 1, limit = 20, party, state, sort } = req.query;

      const result = await this.service.getPoliticians({
        page: Number(page),
        limit: Number(limit),
        party: party as string,
        state: state as string,
        sort: sort as string,
      });

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getById = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { id } = req.params;
      const politician = await this.service.getPoliticianById(id);

      if (!politician) {
        return res.status(404).json({ error: 'Politician not found' });
      }

      res.json({ data: politician });
    } catch (error) {
      next(error);
    }
  };

  getTrades = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { id } = req.params;
      const { page = 1, limit = 20, start_date, end_date } = req.query;

      const result = await this.service.getPoliticianTrades(id, {
        page: Number(page),
        limit: Number(limit),
        start_date: start_date as string,
        end_date: end_date as string,
      });

      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}
```

```typescript
// src/services/politicians.service.ts
import { pool } from '../config/database';
import { CacheService } from './cache.service';

export class PoliticiansService {
  private cache = new CacheService();

  async getPoliticians(options: any) {
    const { page, limit, party, state, sort } = options;
    const offset = (page - 1) * limit;

    let query = 'SELECT * FROM politicians WHERE 1=1';
    const params: any[] = [];
    let paramIndex = 1;

    if (party) {
      query += ` AND party = $${paramIndex++}`;
      params.push(party);
    }

    if (state) {
      query += ` AND state = $${paramIndex++}`;
      params.push(state);
    }

    // Add sorting
    const sortField = sort?.startsWith('-') ? sort.slice(1) : sort || 'name';
    const sortOrder = sort?.startsWith('-') ? 'DESC' : 'ASC';
    query += ` ORDER BY ${sortField} ${sortOrder}`;

    // Add pagination
    query += ` LIMIT $${paramIndex++} OFFSET $${paramIndex++}`;
    params.push(limit, offset);

    const result = await pool.query(query, params);

    // Get total count
    const countResult = await pool.query(
      'SELECT COUNT(*) FROM politicians WHERE 1=1' +
        (party ? ' AND party = $1' : '') +
        (state ? ` AND state = $${party ? 2 : 1}` : ''),
      params.filter((_, i) => i < params.length - 2)
    );

    const total = parseInt(countResult.rows[0].count);

    return {
      data: result.rows,
      meta: {
        page,
        limit,
        total,
        total_pages: Math.ceil(total / limit),
      },
    };
  }

  async getPoliticianById(id: string) {
    // Try cache first
    const cached = await this.cache.get(`politician:${id}`);
    if (cached) return cached;

    const result = await pool.query(
      'SELECT * FROM politicians WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) return null;

    const politician = result.rows[0];

    // Cache for 24 hours
    await this.cache.set(`politician:${id}`, politician, 86400);

    return politician;
  }

  async getPoliticianTrades(politicianId: string, options: any) {
    const { page, limit, start_date, end_date } = options;
    const offset = (page - 1) * limit;

    let query = `
      SELECT
        t.*,
        s.ticker,
        s.company_name,
        p.name as politician_name
      FROM trades t
      JOIN stocks s ON t.stock_id = s.id
      JOIN politicians p ON t.politician_id = p.id
      WHERE t.politician_id = $1
    `;
    const params: any[] = [politicianId];
    let paramIndex = 2;

    if (start_date) {
      query += ` AND t.transaction_date >= $${paramIndex++}`;
      params.push(start_date);
    }

    if (end_date) {
      query += ` AND t.transaction_date <= $${paramIndex++}`;
      params.push(end_date);
    }

    query += ` ORDER BY t.transaction_date DESC LIMIT $${paramIndex++} OFFSET $${paramIndex++}`;
    params.push(limit, offset);

    const result = await pool.query(query, params);

    // Get total count
    const countResult = await pool.query(
      'SELECT COUNT(*) FROM trades WHERE politician_id = $1',
      [politicianId]
    );

    const total = parseInt(countResult.rows[0].count);

    return {
      data: result.rows,
      meta: { page, limit, total, total_pages: Math.ceil(total / limit) },
    };
  }
}
```

### Phase 3: Scraping Service (Week 3-4)

#### 3.1 Implement Base Scraper

Refer to `SCRAPING_SERVICE.md` for complete implementation.

Key tasks:
1. Implement base scraper class with anti-bot measures
2. Implement Capitol Trades scraper
3. Implement StockNear scraper
4. Implement StockAnalysis scraper
5. Implement ChartExchange scraper
6. Set up rate limiting
7. Set up retry logic
8. Implement data validation

#### 3.2 Set Up Job Queue

```typescript
// api-service/src/queue/scraping.queue.ts
import { Queue, Worker } from 'bullmq';
import { redis } from '../config/redis';

export const scrapingQueue = new Queue('scraping', {
  connection: redis,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 5000,
    },
  },
});

// Schedule recurring jobs
export async function scheduleScrapingJobs() {
  // Capitol Trades - every 15 minutes
  await scrapingQueue.add(
    'capitol-trades',
    { days: 7 },
    {
      repeat: {
        pattern: '*/15 * * * *',
      },
    }
  );

  // StockNear - every 30 minutes
  await scrapingQueue.add(
    'stocknear',
    { tickers: ['AAPL', 'NVDA', 'TSLA'] },
    {
      repeat: {
        pattern: '*/30 * * * *',
      },
    }
  );

  // Analytics - every hour
  await scrapingQueue.add(
    'analytics',
    {},
    {
      repeat: {
        pattern: '0 * * * *',
      },
    }
  );
}

// Worker
const worker = new Worker(
  'scraping',
  async (job) => {
    const { name, data } = job;

    switch (name) {
      case 'capitol-trades':
        // Call scraping service API
        await fetch('http://scraper:8000/scrape/capitol-trades', {
          method: 'POST',
          body: JSON.stringify(data),
        });
        break;
      // Handle other job types
    }
  },
  {
    connection: redis,
    concurrency: 5,
  }
);

worker.on('completed', (job) => {
  console.log(`Job ${job.id} completed`);
});

worker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err);
});
```

### Phase 4: WebSocket Service (Week 4)

```typescript
// websocket-service/src/index.ts
import { Server } from 'socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import Redis from 'ioredis';
import { createServer } from 'http';

const httpServer = createServer();

const pubClient = new Redis(process.env.REDIS_URL);
const subClient = pubClient.duplicate();

const io = new Server(httpServer, {
  cors: { origin: '*' },
  adapter: createAdapter(pubClient, subClient),
});

// Authentication middleware
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  // Verify JWT token
  // ...
  next();
});

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Subscribe to stock updates
  socket.on('subscribe:stock', (ticker: string) => {
    socket.join(`stock:${ticker}`);
  });

  socket.on('unsubscribe:stock', (ticker: string) => {
    socket.leave(`stock:${ticker}`);
  });

  // Subscribe to politician updates
  socket.on('subscribe:politician', (politicianId: string) => {
    socket.join(`politician:${politicianId}`);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Listen to Redis pub/sub for updates
subClient.subscribe('new_trade', 'price_update');

subClient.on('message', (channel, message) => {
  const data = JSON.parse(message);

  if (channel === 'new_trade') {
    io.to(`stock:${data.ticker}`).emit('new_trade', data);
    io.to(`politician:${data.politician_id}`).emit('new_trade', data);
  } else if (channel === 'price_update') {
    io.to(`stock:${data.ticker}`).emit('price_update', data);
  }
});

httpServer.listen(4000, () => {
  console.log('WebSocket server listening on port 4000');
});
```

### Phase 5: Testing (Week 5)

#### 5.1 Unit Tests

```typescript
// api-service/tests/unit/politicians.service.test.ts
import { PoliticiansService } from '../../src/services/politicians.service';

describe('PoliticiansService', () => {
  let service: PoliticiansService;

  beforeEach(() => {
    service = new PoliticiansService();
  });

  describe('getPoliticians', () => {
    it('should return paginated politicians', async () => {
      const result = await service.getPoliticians({
        page: 1,
        limit: 20,
      });

      expect(result).toHaveProperty('data');
      expect(result).toHaveProperty('meta');
      expect(result.meta.page).toBe(1);
      expect(result.meta.limit).toBe(20);
    });

    it('should filter by party', async () => {
      const result = await service.getPoliticians({
        page: 1,
        limit: 20,
        party: 'Democrat',
      });

      expect(result.data.every(p => p.party === 'Democrat')).toBe(true);
    });
  });
});
```

#### 5.2 Integration Tests

```typescript
// api-service/tests/integration/api.test.ts
import request from 'supertest';
import app from '../../src/app';

describe('Politicians API', () => {
  it('GET /api/v1/politicians should return 200', async () => {
    const response = await request(app).get('/api/v1/politicians');

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('data');
    expect(response.body).toHaveProperty('meta');
  });

  it('GET /api/v1/politicians/:id should return politician', async () => {
    // Assume we have a test politician with known ID
    const testId = 'test-politician-id';

    const response = await request(app).get(`/api/v1/politicians/${testId}`);

    expect(response.status).toBe(200);
    expect(response.body.data).toHaveProperty('id', testId);
  });
});
```

### Phase 6: Deployment (Week 6)

1. Set up CI/CD pipeline (GitHub Actions)
2. Deploy to staging environment
3. Run load tests
4. Deploy to production
5. Set up monitoring and alerting

### Phase 7: Optimization (Ongoing)

1. Monitor performance metrics
2. Optimize slow queries
3. Adjust cache TTLs based on usage
4. Scale services based on load
5. Implement additional features

## Quick Start Commands

```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Run tests
npm test

# Build for production
docker build -t stock-api:latest ./api-service
docker build -t stock-scraper:latest ./scraping-service

# Deploy to Kubernetes
kubectl apply -f infrastructure/k8s/
```

