# 🐛 Troubleshooting Guide

Comprehensive troubleshooting guide for resolving common issues with the GenAI CloudOps Dashboard.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Database Issues](#database-issues)
- [OCI Integration Issues](#oci-integration-issues)
- [GenAI Service Issues](#genai-service-issues)
- [Kubernetes Issues](#kubernetes-issues)
- [Docker Issues](#docker-issues)
- [Performance Issues](#performance-issues)
- [Security Issues](#security-issues)
- [Monitoring & Logging](#monitoring--logging)

## Quick Diagnostics

### Health Check Commands

Run these commands to quickly assess system health:

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check detailed health
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/health/detailed

# Check frontend
curl -I http://localhost:3000

# Test database connection
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/health/database

# Test OCI connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/health/external
```

### System Information

```bash
# Check running processes
ps aux | grep -E "(python|node|uvicorn)"

# Check port usage
netstat -tlnp | grep -E "(8000|3000|5432|6379)"

# Check disk space
df -h

# Check memory usage
free -h

# Check logs
tail -f /var/log/genai-cloudops/application.log
```

## Backend Issues

### Issue: Backend Server Won't Start

#### Symptoms
- `Connection refused` errors
- Port binding failures
- Import errors on startup

#### Diagnostic Steps
```bash
# Check if port is already in use
sudo netstat -tlnp | grep :8000

# Test Python environment
cd backend
source venv/bin/activate
python -c "import fastapi; print('FastAPI OK')"

# Check environment variables
cat .env | grep -v PASSWORD

# Test database connection
python -c "
from app.core.database import engine
try:
    engine.connect()
    print('Database connection OK')
except Exception as e:
    print(f'Database error: {e}')
"
```

#### Solutions

**Port Already in Use:**
```bash
# Find and kill process using port 8000
sudo fuser -k 8000/tcp

# Or use a different port
uvicorn main:app --port 8001
```

**Missing Dependencies:**
```bash
# Reinstall requirements
pip install -r requirements.txt

# For specific import errors
pip install package-name
```

**Environment Configuration:**
```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

**Database Issues:**
```bash
# Initialize database
python init_db.py

# Reset database (CAUTION: Data loss)
rm genai_cloudops.db
python init_db.py
```

### Issue: API Returns 500 Internal Server Error

#### Symptoms
- HTTP 500 responses
- Stack traces in logs
- Intermittent failures

#### Diagnostic Steps
```bash
# Check application logs
tail -f logs/application.log

# Check uvicorn logs
ps aux | grep uvicorn
sudo journalctl -u genai-cloudops-backend -f

# Test specific endpoints
curl -v http://localhost:8000/api/v1/health
```

#### Solutions

**Check Configuration:**
```bash
# Verify all required environment variables
python -c "
import os
from app.core.config import settings
print('SECRET_KEY:', bool(settings.SECRET_KEY))
print('DATABASE_URL:', bool(settings.DATABASE_URL))
print('OCI_CONFIG_FILE:', os.path.exists(settings.OCI_CONFIG_FILE))
"
```

**Database Connection:**
```bash
# Test database connectivity
python -c "
from sqlalchemy import create_engine
from app.core.config import settings
engine = create_engine(settings.DATABASE_URL)
engine.connect()
print('Database connection successful')
"
```

**OCI Configuration:**
```bash
# Test OCI configuration
oci iam user list
```

### Issue: Slow API Response Times

#### Symptoms
- High response times (>2 seconds)
- Timeout errors
- Poor user experience

#### Diagnostic Steps
```bash
# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# Check system resources
top
htop
iotop

# Monitor database queries
# (If using PostgreSQL)
sudo -u postgres psql -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;"
```

#### Solutions

**Database Optimization:**
```bash
# Add database indexes
python -c "
from app.core.database import engine
# Add specific indexes based on slow queries
"

# Optimize queries
# Review and optimize N+1 query patterns
```

**Caching:**
```bash
# Enable Redis caching
export REDIS_ENABLED=true
export REDIS_URL=redis://localhost:6379

# Check Redis connection
redis-cli ping
```

**Resource Scaling:**
```bash
# Increase worker processes
uvicorn main:app --workers 4

# Increase memory limits (Docker)
docker run -m 2g your-image
```

## Frontend Issues

### Issue: Frontend Won't Load

#### Symptoms
- Blank page
- Build errors
- JavaScript console errors

#### Diagnostic Steps
```bash
# Check if development server is running
curl -I http://localhost:3000

# Check Node.js version
node --version
npm --version

# Check for build errors
cd frontend
npm run build
```

#### Solutions

**Install Dependencies:**
```bash
# Clear and reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Fix npm audit issues
npm audit fix
```

**Environment Configuration:**
```bash
# Create frontend environment file
cat > .env.local << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENVIRONMENT=development
EOF
```

**Port Conflicts:**
```bash
# Check port usage
sudo netstat -tlnp | grep :3000

# Use different port
npm run dev -- --port 3001
```

### Issue: API Connection Errors

#### Symptoms
- "Network Error" messages
- Failed API requests
- CORS errors

#### Diagnostic Steps
```bash
# Test API connectivity from frontend host
curl http://localhost:8000/api/v1/health

# Check browser console for CORS errors
# Check browser network tab for failed requests

# Test CORS configuration
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: X-Requested-With" \
  -X OPTIONS http://localhost:8000/api/v1/health
```

#### Solutions

**CORS Configuration:**
```python
# In backend/app/core/config.py
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://yourdomain.com"
]
```

**Proxy Configuration:**
```javascript
// In frontend/vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

## Database Issues

### Issue: Database Connection Failed

#### Symptoms
- "Connection refused" errors
- "Database doesn't exist" errors
- Authentication failures

#### Diagnostic Steps
```bash
# Check database service status
sudo systemctl status postgresql

# Test direct connection
psql -h localhost -U genai_user -d genai_cloudops

# Check database exists
sudo -u postgres psql -l | grep genai_cloudops

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### Solutions

**PostgreSQL Service:**
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Reset PostgreSQL password
sudo -u postgres psql
ALTER USER genai_user WITH PASSWORD 'newpassword';
```

**Database Setup:**
```bash
# Create database and user
sudo -u postgres createdb genai_cloudops
sudo -u postgres createuser genai_user

# Grant permissions
sudo -u postgres psql << 'EOF'
ALTER USER genai_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE genai_cloudops TO genai_user;
\q
EOF
```

**SQLite Issues:**
```bash
# Check SQLite file permissions
ls -la genai_cloudops.db

# Reset SQLite database
rm genai_cloudops.db
python init_db.py
```

### Issue: Database Migration Errors

#### Symptoms
- Alembic migration failures
- Schema version conflicts
- Table creation errors

#### Diagnostic Steps
```bash
# Check current migration status
cd backend
alembic current

# Check migration history
alembic history

# Verify database schema
python -c "
from app.core.database import engine
print(engine.table_names())
"
```

#### Solutions

**Reset Migrations:**
```bash
# Drop all tables and recreate
python -c "
from app.core.database import Base, engine
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
"

# Reset Alembic
alembic stamp head
```

**Manual Schema Fix:**
```bash
# Connect to database and fix manually
psql -h localhost -U genai_user -d genai_cloudops

# Add missing columns/tables as needed
```

## OCI Integration Issues

### Issue: OCI Authentication Failed

#### Symptoms
- "Invalid credentials" errors
- "Unauthorized" responses
- OCI SDK authentication errors

#### Diagnostic Steps
```bash
# Test OCI CLI configuration
oci iam user list

# Check OCI config file
cat ~/.oci/config

# Test with debug mode
export OCI_CLI_RC_FILE=/dev/null
oci --debug iam user list

# Verify API key
openssl rsa -pubin -in ~/.oci/oci_api_key_public.pem -text -noout
```

#### Solutions

**Reconfigure OCI CLI:**
```bash
# Run OCI setup again
oci setup config

# Test specific profile
oci --profile YOUR_PROFILE iam user list
```

**Check Permissions:**
```bash
# Verify user has required permissions
oci iam user list-groups --user-id YOUR_USER_ID

# Check compartment access
oci iam compartment list
```

**Fix API Key:**
```bash
# Generate new API key
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem

# Upload public key to OCI console
# Update fingerprint in config
```

### Issue: Resource Discovery Failures

#### Symptoms
- Empty resource lists
- "Compartment not found" errors
- Partial data loading

#### Diagnostic Steps
```bash
# Test resource access directly
oci compute instance list --compartment-id YOUR_COMPARTMENT_ID

# Check compartment permissions
oci iam compartment get --compartment-id YOUR_COMPARTMENT_ID

# Verify region configuration
oci iam region list
```

#### Solutions

**Compartment Configuration:**
```bash
# List all available compartments
oci iam compartment list --include-root

# Update environment with correct compartment ID
export OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxx
```

**Regional Issues:**
```bash
# Set correct region
export OCI_REGION=us-ashburn-1

# List available regions
oci iam region list
```

## GenAI Service Issues

### Issue: AI Service Unavailable

#### Symptoms
- "GenAI service error" messages
- Timeout on AI requests
- Invalid API key errors

#### Diagnostic Steps
```bash
# Test Groq API directly
curl -H "Authorization: Bearer YOUR_GROQ_KEY" \
  https://api.groq.com/openai/v1/models

# Check API key configuration
python -c "
from app.core.config import settings
print('GROQ_API_KEY set:', bool(settings.GROQ_API_KEY))
print('Key length:', len(settings.GROQ_API_KEY) if settings.GROQ_API_KEY else 0)
"

# Test GenAI service endpoint
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' \
  http://localhost:8000/api/v1/genai/chat
```

#### Solutions

**API Key Issues:**
```bash
# Get new API key from Groq console
# Update environment variable
export GROQ_API_KEY=gsk_your_new_key_here

# Verify in configuration
grep GROQ_API_KEY .env
```

**Rate Limiting:**
```bash
# Check rate limiting status
curl -I -H "Authorization: Bearer YOUR_GROQ_KEY" \
  https://api.groq.com/openai/v1/models

# Implement backoff strategy
# Check logs for rate limit messages
```

**Service Configuration:**
```python
# In backend/.env
GROQ_API_KEY=your_api_key
GROQ_MODEL=llama3-8b-8192
GROQ_MAX_TOKENS=1024
GROQ_TIMEOUT=30
```

### Issue: Poor AI Response Quality

#### Symptoms
- Irrelevant responses
- Incomplete information
- Slow response times

#### Diagnostic Steps
```bash
# Check prompt templates
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/genai/prompts/types

# Monitor response times
# Check model configuration
```

#### Solutions

**Prompt Optimization:**
```python
# Use more specific prompts
# Include more context
# Try different models

# Example optimized prompt
{
  "message": "What's wrong with my infrastructure?",
  "context": {
    "compartment_id": "ocid1.compartment.oc1..xxx",
    "include_metrics": true,
    "time_range": "1h"
  }
}
```

**Model Configuration:**
```bash
# Try different models
export GROQ_MODEL=mixtral-8x7b-32768
# or
export GROQ_MODEL=llama3-70b-8192
```

## Kubernetes Issues

### Issue: Cluster Connection Failed

#### Symptoms
- "Unable to connect to cluster" errors
- kubectl command failures
- Empty pod lists

#### Diagnostic Steps
```bash
# Test kubectl configuration
kubectl cluster-info
kubectl get nodes
kubectl get pods --all-namespaces

# Check kubeconfig
cat ~/.kube/config

# Verify cluster endpoint
curl -k https://YOUR_CLUSTER_ENDPOINT/api/v1
```

#### Solutions

**Update Kubeconfig:**
```bash
# For OKE clusters
oci ce cluster create-kubeconfig \
  --cluster-id YOUR_CLUSTER_ID \
  --file ~/.kube/config \
  --region YOUR_REGION \
  --token-version 2.0.0

# Test connection
kubectl get nodes
```

**RBAC Permissions:**
```bash
# Create service account
kubectl create serviceaccount genai-cloudops-sa

# Create cluster role binding
kubectl create clusterrolebinding genai-cloudops-binding \
  --clusterrole=view \
  --serviceaccount=default:genai-cloudops-sa

# Get service account token
kubectl describe secret $(kubectl get secrets | grep genai-cloudops-sa | cut -f1 -d ' ')
```

### Issue: Pod Health Monitoring Failures

#### Symptoms
- Incorrect pod status
- Missing pod metrics
- Health score calculation errors

#### Diagnostic Steps
```bash
# Check pod status directly
kubectl get pods --all-namespaces

# Get pod details
kubectl describe pod POD_NAME -n NAMESPACE

# Check metrics server
kubectl top pods
kubectl get apiservice v1beta1.metrics.k8s.io -o yaml
```

#### Solutions

**Install Metrics Server:**
```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify installation
kubectl get pods -n kube-system | grep metrics-server
```

**Fix Permissions:**
```bash
# Update RBAC for monitoring
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: genai-cloudops-monitor
rules:
- apiGroups: [""]
  resources: ["pods", "nodes", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["pods", "nodes"]
  verbs: ["get", "list"]
EOF
```

## Docker Issues

### Issue: Container Startup Failures

#### Symptoms
- Containers exit immediately
- Port binding failures
- Volume mount errors

#### Diagnostic Steps
```bash
# Check container status
docker ps -a

# Check container logs
docker logs CONTAINER_NAME

# Inspect container configuration
docker inspect CONTAINER_NAME

# Check resource usage
docker stats
```

#### Solutions

**Port Conflicts:**
```bash
# Check port usage
sudo netstat -tlnp | grep :8000

# Change port mapping
docker run -p 8001:8000 your-image
```

**Volume Issues:**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 /path/to/volume

# Use absolute paths
docker run -v /absolute/path:/container/path your-image
```

**Memory Issues:**
```bash
# Increase memory limit
docker run -m 2g your-image

# Check Docker system resources
docker system df
docker system prune
```

### Issue: Docker Compose Issues

#### Symptoms
- Services fail to start
- Network connectivity issues
- Volume mount failures

#### Diagnostic Steps
```bash
# Check docker-compose status
docker-compose ps

# View logs for all services
docker-compose logs

# Check specific service
docker-compose logs backend

# Validate compose file
docker-compose config
```

#### Solutions

**Service Dependencies:**
```yaml
# Fix service dependencies
services:
  backend:
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
```

**Network Issues:**
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

**Environment Variables:**
```bash
# Verify environment files
cat .env
cat backend/.env

# Pass environment explicitly
docker-compose --env-file .env up -d
```

## Performance Issues

### Issue: High Memory Usage

#### Symptoms
- Out of memory errors
- Slow response times
- System freezing

#### Diagnostic Steps
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Monitor application memory
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Check for memory leaks
valgrind --tool=memcheck python main.py
```

#### Solutions

**Optimize Application:**
```python
# Add memory limits
import resource
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))  # 2GB limit

# Use generators instead of lists
# Implement proper connection pooling
# Clear caches periodically
```

**System Configuration:**
```bash
# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: High CPU Usage

#### Symptoms
- Slow response times
- High load averages
- Fan noise (physical servers)

#### Diagnostic Steps
```bash
# Check CPU usage
top
htop
iostat 1

# Profile Python application
python -m cProfile -o profile.stats main.py

# Check for high CPU processes
ps aux --sort=-%cpu | head -10
```

#### Solutions

**Optimize Code:**
```python
# Use async/await properly
# Implement caching
# Optimize database queries
# Use connection pooling

# Example optimization
import asyncio
async def optimized_function():
    # Use async operations
    pass
```

**Scale Horizontally:**
```bash
# Add more workers
uvicorn main:app --workers 4

# Use load balancer
# Scale with Docker/Kubernetes
```

## Security Issues

### Issue: Authentication Failures

#### Symptoms
- Cannot login
- Token validation errors
- Unauthorized access

#### Diagnostic Steps
```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Check user in database
python -c "
from app.core.database import SessionLocal
from app.models.user import User
db = SessionLocal()
users = db.query(User).all()
for user in users:
    print(f'{user.email}: {user.role}')
"

# Verify JWT configuration
python -c "
from app.core.config import settings
print('SECRET_KEY length:', len(settings.SECRET_KEY))
print('Algorithm:', settings.ALGORITHM)
"
```

#### Solutions

**Reset Admin User:**
```bash
# Create new admin user
python create_admin_user.py

# Or reset password
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService
db = SessionLocal()
user = db.query(User).filter(User.email == 'admin@example.com').first()
if user:
    user.hashed_password = AuthService.get_password_hash('newpassword')
    db.commit()
"
```

**JWT Configuration:**
```bash
# Generate new secret key
python -c "
import secrets
print('SECRET_KEY=' + secrets.token_urlsafe(32))
"

# Update environment
echo "SECRET_KEY=your_new_secret_key" >> .env
```

### Issue: CORS Errors

#### Symptoms
- "Access blocked by CORS policy" errors
- Failed preflight requests
- Cross-origin request failures

#### Diagnostic Steps
```bash
# Test CORS headers
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS \
  -v http://localhost:8000/api/v1/health

# Check browser console for CORS errors
# Inspect network requests in browser dev tools
```

#### Solutions

**Update CORS Configuration:**
```python
# In backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring & Logging

### Setting Up Comprehensive Logging

#### Application Logging
```python
# Configure logging in main.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
```

#### System Monitoring
```bash
# Setup log rotation
sudo tee /etc/logrotate.d/genai-cloudops << 'EOF'
/opt/genai-cloudops/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    copytruncate
}
EOF

# Setup monitoring
# Install htop, iotop for system monitoring
sudo apt install htop iotop

# Monitor logs in real-time
tail -f /var/log/genai-cloudops/application.log
```

### Performance Monitoring

#### Application Metrics
```bash
# Enable Prometheus metrics
export PROMETHEUS_ENABLED=true

# Access metrics endpoint
curl http://localhost:8000/api/v1/enhancements/metrics

# Setup Grafana dashboards
# Import provided dashboard configurations
```

#### Database Monitoring
```sql
-- PostgreSQL monitoring queries
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation 
FROM pg_stats 
WHERE tablename = 'users';

-- Monitor slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

### Alerting Setup

#### Health Check Monitoring
```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8000/api/v1/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "Health check failed: HTTP $RESPONSE"
    # Send alert notification
    # curl -X POST webhook_url -d "{'text': 'Health check failed'}"
    exit 1
fi

echo "Health check passed"
EOF

chmod +x health_check.sh

# Setup cron for regular checks
echo "*/5 * * * * /path/to/health_check.sh" | crontab -
```

## Getting Additional Help

### Log Collection for Support

```bash
# Collect logs and system information
cat > collect_logs.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="genai_cloudops_logs_$TIMESTAMP"

mkdir -p $LOG_DIR

# System information
uname -a > $LOG_DIR/system_info.txt
free -h > $LOG_DIR/memory_info.txt
df -h > $LOG_DIR/disk_info.txt
ps aux > $LOG_DIR/processes.txt

# Application logs
cp -r logs/ $LOG_DIR/app_logs/ 2>/dev/null || true
cp .env $LOG_DIR/environment.txt 2>/dev/null || true

# Docker logs (if using Docker)
docker ps -a > $LOG_DIR/docker_containers.txt 2>/dev/null || true
docker-compose logs > $LOG_DIR/docker_compose_logs.txt 2>/dev/null || true

# Database info
python -c "
from app.core.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT version();')
        print('Database version:', result.fetchone()[0])
except Exception as e:
    print('Database error:', e)
" > $LOG_DIR/database_info.txt 2>/dev/null || true

tar -czf $LOG_DIR.tar.gz $LOG_DIR
echo "Logs collected in: $LOG_DIR.tar.gz"
EOF

chmod +x collect_logs.sh
./collect_logs.sh
```

### Support Channels

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check docs/ directory for detailed guides  
- **Email Support**: support@genai-cloudops.com
- **Community**: Join GitHub Discussions for community support

### Emergency Procedures

#### Quick Recovery
```bash
# Stop all services
docker-compose down  # or
sudo systemctl stop genai-cloudops-backend

# Reset to known good state
git reset --hard HEAD
git pull origin main

# Restart services
docker-compose up -d  # or
sudo systemctl start genai-cloudops-backend
```

#### Disaster Recovery
```bash
# Backup current state
cp -r /opt/genai-cloudops /opt/genai-cloudops.backup.$(date +%Y%m%d)

# Restore from backup
# (Implement your backup/restore procedures)

# Verify restoration
./health_check.sh
```

Remember: Always test solutions in a development environment before applying to production! 