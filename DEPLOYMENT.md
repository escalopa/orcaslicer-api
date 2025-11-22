# Deployment Guide

This guide covers deploying the OrcaSlicer API in various environments.

## Docker Deployment (Recommended)

### Quick Start

1. **Build the image**

```bash
docker build -t orcaslicer-api:latest .
```

2. **Run with Docker Compose**

```bash
docker-compose up -d
```

3. **Verify**

```bash
curl http://localhost:8000/health
```

### Production Considerations

#### Volume Mounts

The service requires persistent storage for:
- Uploaded models
- Generated outputs
- SQLite database
- Profile configurations

```yaml
volumes:
  - /path/to/data:/data  # Persistent storage
```

#### Environment Variables

Set these in `docker-compose.yml` or via Docker run:

```yaml
environment:
  - LOG_LEVEL=INFO
  - LOG_JSON=true
  - ORCA_CLI_PATH=/app/squashfs-root/AppRun
  - DATA_DIR=/data
```

#### Resource Limits

Add resource constraints for production:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
    reservations:
      cpus: '2'
      memory: 4G
```

### Custom OrcaSlicer Build

If you need a specific OrcaSlicer version:

1. Edit the Dockerfile:

```dockerfile
ARG ORCA_VERSION=v2.1.0  # Change version
RUN wget "https://github.com/SoftFever/OrcaSlicer/releases/download/${ORCA_VERSION}/..."
```

2. Rebuild:

```bash
docker build --build-arg ORCA_VERSION=v2.1.0 -t orcaslicer-api:v2.1.0 .
```

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orcaslicer-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orcaslicer-api
  template:
    metadata:
      labels:
        app: orcaslicer-api
    spec:
      containers:
      - name: api
        image: orcaslicer-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: LOG_JSON
          value: "true"
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "8Gi"
            cpu: "4"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: orcaslicer-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: orcaslicer-api
spec:
  selector:
    app: orcaslicer-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Persistent Volume Claim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: orcaslicer-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

## Reverse Proxy (Nginx)

If running behind a reverse proxy:

```nginx
server {
    listen 80;
    server_name slicer-api.example.com;

    client_max_body_size 500M;  # Allow large model uploads

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout for long slicing operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

## Monitoring & Logging

### Health Checks

The `/health` endpoint provides:
- Service status
- OrcaSlicer CLI availability
- Profile count
- Uptime

Use it for:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems

### Structured Logging

The service outputs JSON logs to stdout. Collect them with:

**Docker:**
```bash
docker logs orcaslicer-api
```

**Kubernetes:**
```bash
kubectl logs -f deployment/orcaslicer-api
```

**Log aggregation systems:**
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- CloudWatch Logs
- Datadog

### Metrics

For production monitoring, consider adding:
- Prometheus metrics endpoint
- Request rate tracking
- Slicing job success/failure rates
- Processing time histograms

## Scaling Considerations

### Horizontal Scaling

The API is designed to be stateless except for:
- Database (SQLite - use PostgreSQL for multi-instance)
- File storage (use shared storage like NFS, S3, etc.)

For horizontal scaling:

1. **Replace SQLite with PostgreSQL**

Update `config.py`:
```python
database_url: str = "postgresql+asyncpg://user:pass@host/db"
```

Update `requirements.txt`:
```
asyncpg==0.29.0
```

2. **Use shared file storage**

Options:
- NFS mount
- S3-compatible storage (MinIO, AWS S3)
- Distributed file system

3. **Deploy multiple replicas**

```yaml
replicas: 3  # In Kubernetes
```

### Vertical Scaling

Slicing is CPU and memory intensive. For large models:
- CPU: 4+ cores recommended
- Memory: 4-8GB minimum, 16GB+ for large models
- Storage: Fast SSD for temporary working directories

## Backup & Recovery

### What to Backup

1. **Database** (`/data/orcaslicer.db`)
   - Model metadata
   - Profile configurations
   - Job history

2. **Uploaded models** (`/data/models/`)
   - Original model files
   - Only if you need to retain them

3. **Generated outputs** (`/data/outputs/`)
   - G-code files
   - 3MF projects
   - Optionally, based on retention policy

### Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec orcaslicer-api cp /data/orcaslicer.db /tmp/
docker cp orcaslicer-api:/tmp/orcaslicer.db "$BACKUP_DIR/"

# Backup models (optional)
docker cp orcaslicer-api:/data/models "$BACKUP_DIR/"

# Compress
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

## Security

### Recommendations

1. **API Authentication**
   - Add JWT or API key authentication
   - Consider OAuth2 for user-based access

2. **Network Security**
   - Run behind firewall
   - Use TLS/HTTPS in production
   - Limit file upload sizes

3. **File Validation**
   - Validate uploaded files
   - Scan for malicious content
   - Enforce size limits

4. **Rate Limiting**
   - Implement request rate limits
   - Prevent abuse of slicing resources

## Troubleshooting

### OrcaSlicer CLI Not Found

Check the CLI path:
```bash
docker exec orcaslicer-api ls -la /app/squashfs-root/AppRun
```

### Database Locked

If using SQLite with multiple connections:
- Increase timeout
- Consider PostgreSQL for production

### Out of Disk Space

Monitor `/data` directory:
```bash
docker exec orcaslicer-api df -h /data
```

Implement cleanup policies for old jobs.

### Slicing Jobs Failing

Check logs:
```bash
docker logs orcaslicer-api | grep -A 10 "job_id"
```

Common issues:
- Invalid model file
- Unsupported format
- Memory limit reached
- OrcaSlicer configuration issue

## Performance Tuning

### Database

For PostgreSQL:
```python
pool_size = 20
max_overflow = 10
```

### Async Workers

Adjust Uvicorn workers:
```bash
uvicorn src.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### File I/O

Use fast storage:
- Local SSD for working directory
- Network storage can be slower for models/outputs

## Contact

For deployment assistance, open an issue on GitHub.
