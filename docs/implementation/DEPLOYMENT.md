# Deployment Strategy

## Infrastructure Architecture

### Cloud Provider Recommendation: AWS

**Services Used**:
- **EC2/ECS/EKS**: Application hosting
- **RDS PostgreSQL**: Managed database with automatic backups
- **ElastiCache Redis**: Managed Redis cluster
- **CloudFront**: CDN for static assets and API caching
- **S3**: Storage for logs, backups, scraped data archives
- **Lambda**: Serverless functions for lightweight tasks
- **API Gateway**: Optional alternative to NGINX
- **CloudWatch**: Monitoring and alerting
- **Route 53**: DNS management
- **Application Load Balancer**: Traffic distribution

**Alternative**: DigitalOcean (simpler, cheaper for small-medium scale)

## Architecture Environments

### Development
```
Local Docker Compose setup
- All services run on localhost
- Hot reload for rapid development
- Separate database from production
```

### Staging
```
Replica of production with smaller resources
- Test deployments before production
- Integration testing
- Performance testing
```

### Production
```
Highly available, auto-scaling setup
- Multiple availability zones
- Auto-scaling groups
- Load balancing
- Database replication
```

## Kubernetes Deployment Configuration

### Namespace Structure
```yaml
# namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: stock-dashboard-prod
---
apiVersion: v1
kind: Namespace
metadata:
  name: stock-dashboard-staging
```

### API Service Deployment
```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: stock-dashboard-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
      - name: api
        image: your-registry/api-service:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: stock-dashboard-prod
spec:
  selector:
    app: api-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

### WebSocket Service Deployment
```yaml
# websocket-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: websocket-service
  namespace: stock-dashboard-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: websocket-service
  template:
    metadata:
      labels:
        app: websocket-service
    spec:
      containers:
      - name: websocket
        image: your-registry/websocket-service:latest
        ports:
        - containerPort: 4000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: websocket-service
  namespace: stock-dashboard-prod
spec:
  selector:
    app: websocket-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 4000
  sessionAffinity: ClientIP  # Sticky sessions for WebSocket
  type: LoadBalancer
```

### Scraping Service Deployment
```yaml
# scraper-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraping-service
  namespace: stock-dashboard-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scraping-service
  template:
    metadata:
      labels:
        app: scraping-service
    spec:
      containers:
      - name: scraper
        image: your-registry/scraping-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        volumeMounts:
        - name: playwright-cache
          mountPath: /home/playwright/.cache
      volumes:
      - name: playwright-cache
        emptyDir: {}
```

### Worker Deployment
```yaml
# worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraping-worker
  namespace: stock-dashboard-prod
spec:
  replicas: 5
  selector:
    matchLabels:
      app: scraping-worker
  template:
    metadata:
      labels:
        app: scraping-worker
    spec:
      containers:
      - name: worker
        image: your-registry/scraping-service:latest
        command: ["python", "-m", "app.workers.scheduler"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Horizontal Pod Autoscaler
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service-hpa
  namespace: stock-dashboard-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Ingress Configuration
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: stock-dashboard-ingress
  namespace: stock-dashboard-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.stockdashboard.com
    - ws.stockdashboard.com
    secretName: tls-secret
  rules:
  - host: api.stockdashboard.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  - host: ws.stockdashboard.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: websocket-service
            port:
              number: 80
```

### Secrets Management
```yaml
# secrets.yaml (use kubectl create secret, don't commit to git)
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: stock-dashboard-prod
type: Opaque
stringData:
  url: postgresql://user:password@postgres-host:5432/stockdb
---
apiVersion: v1
kind: Secret
metadata:
  name: redis-credentials
  namespace: stock-dashboard-prod
type: Opaque
stringData:
  url: redis://redis-host:6379/0
---
apiVersion: v1
kind: Secret
metadata:
  name: jwt-secret
  namespace: stock-dashboard-prod
type: Opaque
stringData:
  secret: your-super-secret-jwt-key-change-this
```

### ConfigMap for Application Config
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: stock-dashboard-prod
data:
  LOG_LEVEL: "info"
  API_VERSION: "v1"
  SCRAPING_INTERVAL_MINUTES: "15"
  CACHE_TTL_SECONDS: "300"
```

## Database Deployment

### AWS RDS Configuration
```
Instance: db.r6g.xlarge (4 vCPU, 32 GB RAM)
Engine: PostgreSQL 15.x with TimescaleDB extension
Storage: 500 GB GP3 SSD (scalable)
Multi-AZ: Yes (for high availability)
Backup: Automated daily backups, 7-day retention
Read Replicas: 2 (for read-heavy operations)
```

### Connection Pooling
```typescript
// db.config.ts
import { Pool } from 'pg';

export const pool = new Pool({
  host: process.env.DB_HOST,
  port: 5432,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20, // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
  ssl: {
    rejectUnauthorized: false,
  },
});

// Use PgBouncer for connection pooling
// Reduces overhead of connection creation
```

## Redis Deployment

### AWS ElastiCache Configuration
```
Node Type: cache.r6g.large (2 vCPU, 13.07 GB RAM)
Engine: Redis 7.0
Cluster Mode: Enabled (for horizontal scaling)
Replicas: 2 per shard
Automatic Failover: Enabled
Backup: Daily snapshots
```

### Redis Configuration
```conf
# redis.conf
maxmemory 12gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
save 900 1
save 300 10
save 60 10000
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Run linting
        run: npm run lint

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build, tag, and push API image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: api-service
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
                       -t $ECR_REGISTRY/$ECR_REPOSITORY:latest \
                       -f api-service/Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Build, tag, and push Scraper image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: scraping-service
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
                       -t $ECR_REGISTRY/$ECR_REPOSITORY:latest \
                       -f scraping-service/Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name stock-dashboard-cluster --region us-east-1

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api-service \
            api=${{ steps.login-ecr.outputs.registry }}/api-service:${{ github.sha }} \
            -n stock-dashboard-prod
          kubectl set image deployment/scraping-service \
            scraper=${{ steps.login-ecr.outputs.registry }}/scraping-service:${{ github.sha }} \
            -n stock-dashboard-prod

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/api-service -n stock-dashboard-prod
          kubectl rollout status deployment/scraping-service -n stock-dashboard-prod

      - name: Run database migrations
        run: |
          kubectl run migration-job --rm -i --restart=Never \
            --image=${{ steps.login-ecr.outputs.registry }}/api-service:${{ github.sha }} \
            --env="DATABASE_URL=${{ secrets.DATABASE_URL }}" \
            -- npm run migrate:up
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api-service'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - stock-dashboard-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: api-service
        action: keep

  - job_name: 'scraping-service'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - stock-dashboard-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: scraping-service
        action: keep

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards
1. **API Performance Dashboard**
   - Request rate
   - Response time (p50, p95, p99)
   - Error rate
   - Active connections

2. **Database Dashboard**
   - Query performance
   - Connection pool usage
   - Cache hit rate
   - Slow queries

3. **Scraping Dashboard**
   - Jobs queued/processing/completed
   - Scraping success/failure rate
   - Average scraping time per source
   - Rate limit status

4. **System Dashboard**
   - CPU/Memory usage
   - Network I/O
   - Disk usage
   - Pod health

### Alerting Rules
```yaml
# alerts.yaml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/sec"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is {{ $value }}s"

      - alert: DatabaseConnectionPoolExhausted
        expr: pg_pool_waiting_count > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"

      - alert: ScrapingJobFailing
        expr: rate(scraping_jobs_total{status="failed"}[30m]) > 0.1
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High scraping job failure rate"

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage high"
```

## Health Checks

```typescript
// health.routes.ts
import express from 'express';
import { pool } from '../database';
import { redis } from '../redis';

const router = express.Router();

// Basic health check
router.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Detailed readiness check
router.get('/health/ready', async (req, res) => {
  const checks = {
    database: false,
    redis: false,
    overall: false,
  };

  try {
    // Check database
    await pool.query('SELECT 1');
    checks.database = true;

    // Check Redis
    await redis.ping();
    checks.redis = true;

    checks.overall = checks.database && checks.redis;

    const statusCode = checks.overall ? 200 : 503;
    res.status(statusCode).json({
      status: checks.overall ? 'ready' : 'not ready',
      checks,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      checks,
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

export default router;
```

## Backup Strategy

### Database Backups
```bash
# Automated daily backups
# RDS automated backups (AWS handles this)
# Additional manual backups stored in S3

# Backup script (run daily via cron)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="stockdb_backup_${TIMESTAMP}.sql"

pg_dump $DATABASE_URL > /tmp/$BACKUP_FILE
gzip /tmp/$BACKUP_FILE
aws s3 cp /tmp/${BACKUP_FILE}.gz s3://stock-dashboard-backups/database/
rm /tmp/${BACKUP_FILE}.gz

# Retention: Keep 7 daily, 4 weekly, 12 monthly
```

### Redis Persistence
```conf
# Redis snapshot configuration
save 900 1      # Save if at least 1 key changed in 900 seconds
save 300 10     # Save if at least 10 keys changed in 300 seconds
save 60 10000   # Save if at least 10000 keys changed in 60 seconds

# AOF (Append Only File) for better durability
appendonly yes
appendfsync everysec
```

## Disaster Recovery Plan

1. **Database Failure**:
   - Automatic failover to standby replica (Multi-AZ RDS)
   - Recovery time: < 2 minutes

2. **Redis Failure**:
   - ElastiCache automatic failover
   - App continues with degraded performance (no cache)
   - Recovery time: < 1 minute

3. **Complete Regional Outage**:
   - Multi-region deployment (optional for critical systems)
   - DNS failover to backup region
   - Recovery time: < 30 minutes

4. **Data Corruption**:
   - Restore from latest backup
   - Point-in-time recovery (RDS feature)
   - Recovery time: < 1 hour

## Cost Estimation (AWS, per month)

```
EC2/EKS (API + Workers):        $500 - $800
RDS PostgreSQL (Multi-AZ):      $300 - $500
ElastiCache Redis:              $150 - $250
Load Balancer:                  $30 - $50
CloudFront CDN:                 $50 - $100
S3 Storage:                     $20 - $50
Data Transfer:                  $100 - $200
CloudWatch:                     $30 - $50
-------------------------------------------
Total:                          $1,180 - $2,000/month

For smaller scale (DigitalOcean):
- 2x Droplets (4GB RAM):        $48
- Managed PostgreSQL:           $60
- Managed Redis:                $40
- Load Balancer:                $12
- Spaces (S3-like):             $5
-------------------------------------------
Total:                          $165/month
```

