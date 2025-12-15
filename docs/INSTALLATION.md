# ⚙️ Installation Guide

This guide provides detailed instructions for installing and setting up the GenAI CloudOps Dashboard in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Docker Installation](#docker-installation)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB free space
- **Network**: Internet connectivity for external services

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ free space
- **Network**: High-speed internet connection

### Software Dependencies

#### Required Software
- **Python 3.11+** with pip package manager
- **Node.js 18+** with npm or yarn
- **Git** for version control

#### Optional Software (for enhanced features)
- **Docker 20+** and Docker Compose
- **PostgreSQL 13+** (production database)
- **Redis 6+** (caching and sessions)
- **Kubernetes 1.28+** (container orchestration)

### External Service Requirements

#### Oracle Cloud Infrastructure (OCI)
- Valid OCI account with appropriate permissions
- OCI CLI installed and configured
- Access to required OCI services:
  - Compute instances
  - Database services
  - Kubernetes Engine (OKE)
  - Monitoring and logging
  - Cost Management
  - Identity and Access Management (IAM)

#### AI Services
- **Groq API Key** (recommended) - Free tier available
- **OpenAI API Key** (alternative) - Paid service

#### Optional External Services
- **SMTP Server** for email notifications
- **Slack Workspace** for Slack notifications
- **Prometheus Server** for metrics collection
- **Grafana Instance** for dashboard visualization

## Development Setup

### 1. Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/souravb-dev/GenAIOps.git
cd GenAI-CloudOps

# Verify the clone
ls -la
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Verify activation (should show venv path)
which python
```

#### Install Dependencies
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Verify installation
pip list | grep fastapi
```

#### Database Setup
```bash
# Initialize database (SQLite by default)
python init_db.py

# Create admin user (optional)
python create_admin_user.py

# Verify database
python -c "from app.core.database import engine; print('Database connection successful')"
```

#### Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (see Configuration section below)
nano .env  # or your preferred editor
```

#### Start Backend Server
```bash
# Start development server
python main.py

# Alternative using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Verify server is running
curl http://localhost:8000/api/v1/health
```

### 3. Frontend Setup

#### Install Dependencies
```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install

# Alternative using yarn
yarn install

# Verify installation
npm list react
```

#### Environment Configuration
```bash
# Copy example environment file
cp .env.example .env.local

# Edit frontend configuration
nano .env.local
```

Example `.env.local`:
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENVIRONMENT=development
```

#### Start Frontend Server
```bash
# Start development server
npm run dev

# Alternative with custom port
npm run dev -- --port 3001

# Verify server is running
curl http://localhost:3000
```

### 4. Development Verification

```bash
# Test backend API
curl http://localhost:8000/docs

# Test frontend
open http://localhost:3000  # macOS
start http://localhost:3000  # Windows

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

## Production Deployment

### 1. Server Preparation

#### System Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
sudo yum update -y  # RHEL/CentOS

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git postgresql-client redis-tools

# Create application user
sudo useradd -m -s /bin/bash genai-cloudops
sudo usermod -aG sudo genai-cloudops  # Optional: sudo access
```

#### Directory Structure
```bash
# Create application directories
sudo mkdir -p /opt/genai-cloudops
sudo chown genai-cloudops:genai-cloudops /opt/genai-cloudops

# Switch to application user
sudo su - genai-cloudops

# Create standard directories
mkdir -p /opt/genai-cloudops/{app,logs,data,config}
```

### 2. Application Deployment

#### Clone and Build
```bash
# Navigate to application directory
cd /opt/genai-cloudops

# Clone repository
git clone https://github.com/souravb-dev/GenAIOps.git app
cd app

# Build backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd ../frontend
npm install
npm run build
```

#### Configuration
```bash
# Create production configuration
cd /opt/genai-cloudops/config

# Backend configuration
cat > backend.env << 'EOF'
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql://genai_user:password@localhost/genai_cloudops
REDIS_URL=redis://localhost:6379/0

# OCI Configuration
OCI_CONFIG_FILE=/opt/genai-cloudops/config/oci_config
OCI_PROFILE=PRODUCTION
OCI_REGION=us-ashburn-1

# GenAI Configuration
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama3-8b-8192

# Security
CORS_ORIGINS=["https://yourdomain.com"]
EOF

# Set secure permissions
chmod 600 backend.env
```

### 3. Database Setup (PostgreSQL)

#### Installation
```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Database Configuration
```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
createdb genai_cloudops
createuser genai_user

# Set password and permissions
psql << 'EOF'
ALTER USER genai_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE genai_cloudops TO genai_user;
\q
EOF
```

#### Initialize Application Database
```bash
# Switch back to application user
sudo su - genai-cloudops
cd /opt/genai-cloudops/app/backend

# Load environment
source /opt/genai-cloudops/config/backend.env
source venv/bin/activate

# Initialize database
python init_db.py

# Create admin user
python create_admin_user.py
```

### 4. Process Management (systemd)

#### Backend Service
```bash
# Create systemd service file
sudo tee /etc/systemd/system/genai-cloudops-backend.service << 'EOF'
[Unit]
Description=GenAI CloudOps Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=genai-cloudops
Group=genai-cloudops
WorkingDirectory=/opt/genai-cloudops/app/backend
Environment=PATH=/opt/genai-cloudops/app/backend/venv/bin
EnvironmentFile=/opt/genai-cloudops/config/backend.env
ExecStart=/opt/genai-cloudops/app/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable genai-cloudops-backend
sudo systemctl start genai-cloudops-backend
```

#### Frontend Service (Nginx)
```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/genai-cloudops << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend static files
    location / {
        root /opt/genai-cloudops/app/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/genai-cloudops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL/TLS Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

## Docker Installation

### 1. Development with Docker

#### Prerequisites
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin
```

#### Build and Run
```bash
# Clone repository
git clone https://github.com/souravb-dev/GenAIOps.git
cd GenAI-CloudOps

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit configuration
nano backend/.env

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Access application
open http://localhost:3000
```

### 2. Production with Docker

#### Production Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://genai_user:password@postgres:5432/genai_cloudops
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=genai_cloudops
      - POSTGRES_USER=genai_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Deploy Production
```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Monitor services
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs backend
```

## Kubernetes Deployment

### 1. Prerequisites

#### Kubernetes Cluster
```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes

# Create namespace
kubectl create namespace genai-cloudops
```

#### Helm Installation
```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
helm version
```

### 2. Deploy with Helm

#### Prepare Configuration
```bash
# Navigate to Helm chart
cd deployment/helm-chart

# Copy values file
cp values.yaml values-prod.yaml

# Edit production values
nano values-prod.yaml
```

#### Install Application
```bash
# Install the Helm chart
helm install genai-cloudops . \
  -f values-prod.yaml \
  --namespace genai-cloudops

# Check deployment status
kubectl get pods -n genai-cloudops
kubectl get services -n genai-cloudops

# View application logs
kubectl logs -f deployment/genai-cloudops-backend -n genai-cloudops
```

#### Setup Ingress (Optional)
```bash
# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx

# Apply ingress configuration
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: genai-cloudops-ingress
  namespace: genai-cloudops
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: genai-cloudops-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: genai-cloudops-frontend
            port:
              number: 80
EOF
```

## Configuration

### 1. Backend Configuration

#### Core Settings
```bash
# Required settings
ENVIRONMENT=production
SECRET_KEY=your-super-secure-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# OCI Settings
OCI_CONFIG_FILE=/path/to/oci/config
OCI_PROFILE=DEFAULT
OCI_REGION=us-ashburn-1
OCI_TENANCY_ID=ocid1.tenancy.oc1..xxx
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxx

# GenAI Settings
GROQ_API_KEY=gsk_xxx
GROQ_MODEL=llama3-8b-8192
```

#### Optional Enhancements
```bash
# Prometheus Metrics
PROMETHEUS_ENABLED=true
PROMETHEUS_URL=http://localhost:9090

# Grafana Integration
GRAFANA_ENABLED=true
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=your-grafana-api-key

# Email Notifications
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-app-password

# Slack Notifications
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Auto-Remediation
AUTO_REMEDIATION_ENABLED=true
AUTO_APPROVAL_ENABLED=false
REMEDIATION_DRY_RUN=false
```

### 2. OCI Configuration

#### OCI CLI Setup
```bash
# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Configure OCI CLI
oci setup config

# Test configuration
oci iam user list
```

#### Service Account (For OKE)
```bash
# Create service account for pod-based access
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: genai-cloudops-sa
  namespace: genai-cloudops
  annotations:
    oci.oraclecloud.com/principal-name: "ocid1.instanceprincipal.oc1..xxx"
EOF
```

### 3. Kubernetes Configuration

#### RBAC Setup
```bash
# Create ClusterRole for monitoring
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: genai-cloudops-monitor
rules:
- apiGroups: [""]
  resources: ["pods", "nodes", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
EOF

# Bind to service account
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: genai-cloudops-monitor-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: genai-cloudops-monitor
subjects:
- kind: ServiceAccount
  name: genai-cloudops-sa
  namespace: genai-cloudops
EOF
```

## Verification

### 1. Health Checks

#### Backend Health
```bash
# API health check
curl http://localhost:8000/api/v1/health

# Database connectivity
curl http://localhost:8000/api/v1/health/database

# External services
curl http://localhost:8000/api/v1/health/external
```

#### Frontend Verification
```bash
# Frontend accessibility
curl -I http://localhost:3000

# API connectivity from frontend
curl http://localhost:3000/api/v1/health
```

### 2. Feature Testing

#### Authentication
```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

#### OCI Integration
```bash
# Test OCI connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/cloud/resources
```

#### GenAI Service
```bash
# Test AI service
curl -X POST http://localhost:8000/api/v1/genai/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of my infrastructure?"}'
```

### 3. Performance Testing

#### Load Testing
```bash
# Install Apache Bench
sudo apt install -y apache2-utils

# Basic load test
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# API endpoint testing
ab -n 100 -c 5 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/monitoring/status
```

## Troubleshooting

### Common Issues

#### Backend Issues

**Issue**: Database connection failed
```bash
# Check database service
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U genai_user -d genai_cloudops

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

**Issue**: OCI authentication failed
```bash
# Verify OCI config
oci iam user list

# Check config file
cat ~/.oci/config

# Test with debug
export OCI_CLI_RC_FILE=/dev/null
oci --debug iam user list
```

**Issue**: GenAI service unavailable
```bash
# Test API key
curl -H "Authorization: Bearer YOUR_GROQ_KEY" \
  https://api.groq.com/openai/v1/models

# Check logs
docker-compose logs backend | grep -i genai
```

#### Frontend Issues

**Issue**: Backend API not accessible
```bash
# Check network connectivity
curl http://localhost:8000/api/v1/health

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: X-Requested-With" \
  -X OPTIONS http://localhost:8000/api/v1/health
```

**Issue**: Build failures
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version
npm --version
```

#### Docker Issues

**Issue**: Container startup failures
```bash
# Check container logs
docker-compose logs backend
docker-compose logs frontend

# Inspect container
docker inspect genai-cloudops_backend_1

# Check resource usage
docker stats
```

**Issue**: Port conflicts
```bash
# Check port usage
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000

# Kill conflicting processes
sudo fuser -k 8000/tcp
```

#### Kubernetes Issues

**Issue**: Pod startup failures
```bash
# Check pod status
kubectl get pods -n genai-cloudops

# Describe failing pod
kubectl describe pod POD_NAME -n genai-cloudops

# Check logs
kubectl logs POD_NAME -n genai-cloudops

# Check events
kubectl get events -n genai-cloudops --sort-by='.lastTimestamp'
```

**Issue**: Service connectivity
```bash
# Test service endpoints
kubectl get svc -n genai-cloudops

# Port forward for testing
kubectl port-forward svc/genai-cloudops-backend 8000:80 -n genai-cloudops

# Check ingress
kubectl get ingress -n genai-cloudops
```

### Log Analysis

#### Backend Logs
```bash
# Development logs
tail -f backend/logs/application.log

# Production logs (systemd)
sudo journalctl -u genai-cloudops-backend -f

# Docker logs
docker-compose logs -f backend
```

#### Frontend Logs
```bash
# Development console
# Check browser developer tools console

# Production logs (Nginx)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Optimization

#### Database Optimization
```bash
# Check database performance
sudo -u postgres psql genai_cloudops << 'EOF'
SELECT schemaname,tablename,attname,n_distinct,correlation 
FROM pg_stats WHERE tablename = 'audit_logs';
\q
EOF

# Analyze slow queries
sudo -u postgres psql genai_cloudops << 'EOF'
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
\q
EOF
```

#### Memory Optimization
```bash
# Check memory usage
free -h
ps aux | grep -E "(python|node)" | sort -k 4 -nr

# Optimize Python memory
export PYTHONMALLOC=malloc
ulimit -v 2000000  # Limit virtual memory to 2GB
```

### Security Hardening

#### File Permissions
```bash
# Set secure permissions
chmod 600 /opt/genai-cloudops/config/backend.env
chmod 600 ~/.oci/config
chmod 700 /opt/genai-cloudops/logs
```

#### Firewall Configuration
```bash
# Configure UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8000/tcp   # Block direct backend access
sudo ufw enable
```

#### SSL/TLS Verification
```bash
# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check certificate expiration
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

For additional help, please refer to the [Troubleshooting Guide](TROUBLESHOOTING.md) or contact support. 