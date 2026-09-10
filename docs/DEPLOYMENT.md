# DEPLOYMENT.md

## Development Deployment

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or use Docker)
- Redis (or use Docker)

### Quick Start

```bash
# Clone and setup
git clone https://github.com/yashasbm25/SAPTHA_SAGARA.git
cd SAPTHA_SAGARA
cp .env.example .env

# Configure .env with your keys
# OPENAI_API_KEY=your_key_here

# Run with Docker
docker-compose up --build

# Access
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Production Deployment

### 1. Environment Configuration

```bash
# Create secure .env
OPENAI_API_KEY=<production-key>
DATABASE_URL=postgresql://user:pass@prod-db:5432/saptha_sagara
REDIS_URL=redis://prod-redis:6379
FASTAPI_ENV=production
FASTAPI_DEBUG=false
```

### 2. Database Setup

```bash
# Initialize database
alembic upgrade head

# Create PostGIS extension
psql -c "CREATE EXTENSION postgis;"
```

### 3. Backend Deployment (Gunicorn)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gdal-bin libgdal-dev libpq-dev
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY backend/ .
EXPOSE 8000
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 4. Frontend Build

```bash
cd frontend
npm ci
npm run build
# Output in frontend/dist/
```

### 5. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saptha-sagara-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: saptha-sagara
  template:
    metadata:
      labels:
        app: saptha-sagara
    spec:
      containers:
      - name: backend
        image: your-registry/saptha-sagara:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: saptha-secrets
              key: openai-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: saptha-secrets
              key: db-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: saptha-sagara-service
spec:
  selector:
    app: saptha-sagara
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 6. Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.saptha-sagara.in;

    client_max_body_size 10M;

    # CORS
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req zone=api_limit burst=20;

    # Backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Documentation
    location /docs {
        proxy_pass http://backend:8000/docs;
    }
}

server {
    listen 80;
    server_name saptha-sagara.in;

    # Frontend
    location / {
        root /var/www/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://api.saptha-sagara.in/api/;
    }
}
```

### 7. SSL/TLS

```bash
# Let's Encrypt with Certbot
certbot certonly --nginx -d saptha-sagara.in -d api.saptha-sagara.in

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 8. Monitoring & Logging

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'saptha-sagara'
    static_configs:
      - targets: ['localhost:8000']

# logstash config
input {
  tcp {
    port => 5000
    codec => json
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "saptha-sagara-%{+YYYY.MM.dd}"
  }
}
```

### 9. Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database
psql $DATABASE_URL -c "SELECT 1"

# Redis
redis-cli ping
```

### 10. Scaling

- Horizontal: Add backend replicas
- Vertical: Increase CPU/RAM per instance
- Database: Read replicas for queries
- Cache: Redis cluster for scalability
- CDN: CloudFront for static assets

## Backup & Recovery

```bash
# Database backup
pg_dump $DATABASE_URL > backup.sql

# Automated daily backups
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/db-$(date +\%Y\%m\%d).sql.gz

# Restore
psql $DATABASE_URL < backup.sql
```

## Troubleshooting

### Port already in use
```bash
lsof -i :8000
kill -9 <PID>
```

### Database connection issues
```bash
# Check connection
psql -h localhost -U saptha -d saptha_sagara -c "SELECT 1"
```

### API not responding
```bash
# Check logs
docker-compose logs backend

# Restart
docker-compose restart backend
```
