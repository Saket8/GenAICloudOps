# 🔧 Configuration Reference

Complete reference for configuring the GenAI CloudOps Dashboard.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Core Configuration](#core-configuration)
- [OCI Configuration](#oci-configuration)
- [GenAI Configuration](#genai-configuration)
- [Database Configuration](#database-configuration)
- [Optional Features](#optional-features)
- [Security Configuration](#security-configuration)
- [Performance Configuration](#performance-configuration)
- [Development Configuration](#development-configuration)

## Environment Variables

### Configuration File Locations

- **Backend**: `backend/.env`
- **Frontend**: `frontend/.env.local`
- **Docker**: `.env` (root directory)
- **Kubernetes**: ConfigMaps and Secrets

### Environment Priority

1. System environment variables (highest priority)
2. `.env` file variables
3. Default values in code (lowest priority)

## Core Configuration

### Application Settings

```bash
# Environment mode
ENVIRONMENT=development|staging|production
DEBUG=true|false

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME="GenAI CloudOps API"

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1
RELOAD=true
```

**Details:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENVIRONMENT` | string | `development` | Environment mode |
| `DEBUG` | boolean | `true` | Enable debug mode |
| `API_V1_STR` | string | `/api/v1` | API base path |
| `PROJECT_NAME` | string | `GenAI CloudOps API` | Application name |
| `HOST` | string | `0.0.0.0` | Server bind address |
| `PORT` | integer | `8000` | Server port |
| `WORKERS` | integer | `1` | Uvicorn workers (production) |
| `RELOAD` | boolean | `true` | Auto-reload on changes |

### CORS Configuration

```bash
# CORS Origins (JSON array)
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

**Example Values:**
```bash
# Development
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000"]

# Production
BACKEND_CORS_ORIGINS=["https://dashboard.yourcompany.com","https://app.yourcompany.com"]
```

## OCI Configuration

### Basic OCI Settings

```bash
# OCI Configuration File
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT

# Primary Settings
OCI_REGION=us-ashburn-1
OCI_TENANCY_ID=ocid1.tenancy.oc1..xxxxxxxxxx
OCI_USER_ID=ocid1.user.oc1..xxxxxxxxxx
OCI_FINGERPRINT=aa:bb:cc:dd:ee:ff:gg:hh:ii:jj:kk:ll:mm:nn:oo:pp
OCI_KEY_FILE=~/.oci/oci_api_key.pem

# Compartment Configuration
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxxxxxxxxx
```

**Details:**

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `OCI_CONFIG_FILE` | string | No | Path to OCI config file |
| `OCI_PROFILE` | string | No | OCI profile name |
| `OCI_REGION` | string | Yes | OCI region identifier |
| `OCI_TENANCY_ID` | string | Yes | OCI tenancy OCID |
| `OCI_USER_ID` | string | Yes | OCI user OCID |
| `OCI_FINGERPRINT` | string | Yes | API key fingerprint |
| `OCI_KEY_FILE` | string | Yes | Path to private key file |
| `OCI_COMPARTMENT_ID` | string | Yes | Default compartment OCID |

### Advanced OCI Settings

```bash
# Instance Principal (for OKE deployments)
OCI_USE_INSTANCE_PRINCIPAL=false

# Service-specific timeouts
OCI_COMPUTE_TIMEOUT=30
OCI_DATABASE_TIMEOUT=60
OCI_MONITORING_TIMEOUT=45

# Rate limiting
OCI_API_RATE_LIMIT=100
OCI_API_BURST_LIMIT=200
```

### OCI Vault Configuration

```bash
# Vault Service
OCI_VAULT_ENABLED=true
OCI_VAULT_ID=ocid1.vault.oc1..xxxxxxxxxx
OCI_KMS_KEY_ID=ocid1.key.oc1..xxxxxxxxxx

# Vault Cache Settings
VAULT_CACHE_TTL_MINUTES=15
VAULT_ENABLE_CACHING=true
VAULT_MAX_CACHE_SIZE=1000
```

## GenAI Configuration

### Groq Configuration

```bash
# Groq API Settings
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama3-8b-8192
GROQ_FALLBACK_MODEL=mixtral-8x7b-32768

# Request Settings
GROQ_MAX_TOKENS=1024
GROQ_TEMPERATURE=0.7
GROQ_TIMEOUT=30

# Performance Settings
GENAI_CACHE_TTL=3600
GENAI_RATE_LIMIT_PER_MINUTE=100
GENAI_MAX_CONTEXT_LENGTH=4000
GENAI_ENABLE_CACHING=true
GENAI_ENABLE_BATCHING=true
GENAI_BATCH_SIZE=5
```

**Model Options:**

| Model | Context Length | Speed | Quality |
|-------|----------------|-------|---------|
| `llama3-8b-8192` | 8,192 tokens | Fast | Good |
| `llama3-70b-8192` | 8,192 tokens | Medium | Excellent |
| `mixtral-8x7b-32768` | 32,768 tokens | Medium | Very Good |
| `gemma-7b-it` | 8,192 tokens | Fast | Good |

### OpenAI Configuration (Alternative)

```bash
# OpenAI API Settings
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2048
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=30
```

### AI Service Selection

```bash
# Primary AI Provider
GENAI_PROVIDER=groq|openai
GENAI_ENABLE_FALLBACK=true
```

## Database Configuration

### SQLite (Default)

```bash
# SQLite Configuration
DATABASE_URL=sqlite:///./genai_cloudops.db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0
```

### PostgreSQL (Production)

```bash
# PostgreSQL Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/genai_cloudops

# Connection Pool Settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=false

# SSL Settings
DATABASE_SSL_REQUIRE=true
DATABASE_SSL_CERT=/path/to/client-cert.pem
DATABASE_SSL_KEY=/path/to/client-key.pem
DATABASE_SSL_CA=/path/to/ca-cert.pem
```

### Redis Configuration

```bash
# Redis Settings
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379/0

# Connection Settings
REDIS_MAX_CONNECTIONS=50
REDIS_RETRY_ON_TIMEOUT=true
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

## Optional Features

### Prometheus Metrics

```bash
# Prometheus Configuration
PROMETHEUS_ENABLED=true
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_NAMESPACE=genai_cloudops
PROMETHEUS_METRICS_PATH=/metrics
```

### Grafana Integration

```bash
# Grafana Configuration
GRAFANA_ENABLED=false
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=admin

# Dashboard Settings
GRAFANA_ORG_ID=1
GRAFANA_FOLDER_ID=0
GRAFANA_DATASOURCE_NAME=prometheus
```

### Email Notifications

```bash
# Email Service
EMAIL_ENABLED=false

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Email Settings
SENDER_EMAIL=noreply@genai-cloudops.com
SENDER_NAME=GenAI CloudOps Dashboard

# Recipients
ADMIN_EMAIL=admin@genai-cloudops.com
DEVOPS_EMAIL=devops@genai-cloudops.com
BUSINESS_EMAIL=business@genai-cloudops.com
```

**SMTP Provider Examples:**

```bash
# Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true

# Outlook
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true

# SendGrid
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true

# AWS SES
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### Slack Notifications

```bash
# Slack Configuration
SLACK_ENABLED=false
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_DEFAULT_CHANNEL=#alerts

# User Settings
ADMIN_SLACK_ID=U1234567890
DEVOPS_SLACK_ID=U0987654321
```

### Auto-Remediation

```bash
# Auto-Remediation Settings
AUTO_REMEDIATION_ENABLED=false
AUTO_APPROVAL_ENABLED=false
MAX_CONCURRENT_REMEDIATIONS=3
REMEDIATION_DRY_RUN=true

# Risk Thresholds
AUTO_APPROVE_RISK_THRESHOLD=low
AUTO_EXECUTE_RISK_THRESHOLD=very_low

# Execution Settings
REMEDIATION_TIMEOUT_SECONDS=300
REMEDIATION_MAX_RETRIES=3
REMEDIATION_ROLLBACK_ENABLED=true
```

## Security Configuration

### Authentication

```bash
# JWT Configuration
SECRET_KEY=your-super-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SYMBOLS=true
```

### Session Management

```bash
# Session Configuration
SESSION_TIMEOUT_MINUTES=480
SESSION_RENEWAL_THRESHOLD=60
MAX_CONCURRENT_SESSIONS=5
SESSION_STORE=redis

# Security Headers
SECURITY_HEADERS_ENABLED=true
HSTS_MAX_AGE=31536000
CSP_ENABLED=true
```

### API Security

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=200
RATE_LIMIT_ADMIN_MULTIPLIER=5

# Request Validation
REQUEST_SIZE_LIMIT=10485760  # 10MB
REQUEST_TIMEOUT=30
VALIDATE_JSON_SCHEMAS=true
```

### Encryption

```bash
# Data Encryption
ENCRYPTION_ENABLED=true
ENCRYPTION_KEY=base64-encoded-key-here
ENCRYPTION_ALGORITHM=AES-256-GCM

# TLS Configuration
TLS_ENABLED=true
TLS_CERT_FILE=/path/to/cert.pem
TLS_KEY_FILE=/path/to/key.pem
TLS_CA_FILE=/path/to/ca.pem
```

## Performance Configuration

### Application Performance

```bash
# Worker Configuration
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
WORKER_CONNECTIONS=1000
MAX_REQUESTS=10000
MAX_REQUESTS_JITTER=1000

# Threading
THREAD_POOL_SIZE=20
ENABLE_ASYNC_ENDPOINTS=true
```

### Caching Configuration

```bash
# Application Cache
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
CACHE_MAX_SIZE=1000
CACHE_BACKEND=redis

# Response Caching
HTTP_CACHE_ENABLED=true
HTTP_CACHE_TTL=60
STATIC_CACHE_TTL=86400
```

### Resource Limits

```bash
# Memory Limits
MAX_MEMORY_MB=2048
MEMORY_WARNING_THRESHOLD=80
MEMORY_CRITICAL_THRESHOLD=95

# CPU Limits
MAX_CPU_PERCENT=80
CPU_WARNING_THRESHOLD=70
CPU_CRITICAL_THRESHOLD=90

# Request Limits
MAX_CONCURRENT_REQUESTS=100
REQUEST_QUEUE_SIZE=1000
```

### Monitoring Configuration

```bash
# Monitoring Settings
MONITORING_CACHE_TTL=300
ALERT_HISTORY_HOURS=24
MAX_LOG_SEARCH_RESULTS=1000

# Health Thresholds
HEALTH_SCORE_THRESHOLD_HEALTHY=90.0
HEALTH_SCORE_THRESHOLD_WARNING=70.0
HEALTH_SCORE_THRESHOLD_DEGRADED=50.0

# Metrics Collection
METRICS_COLLECTION_INTERVAL=30
METRICS_RETENTION_DAYS=30
DETAILED_METRICS_ENABLED=true
```

## Development Configuration

### Development Mode

```bash
# Development Settings
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG

# Development Tools
ENABLE_DOCS=true
ENABLE_PROFILER=true
ENABLE_DEBUG_TOOLBAR=true

# Testing
TESTING=false
TEST_DATABASE_URL=sqlite:///./test_genai_cloudops.db
SKIP_OCI_TESTS=false
MOCK_OCI_RESPONSES=true
```

### Logging Configuration

```bash
# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=detailed
LOG_FILE=/var/log/genai-cloudops/application.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5

# Component Logging
LOG_LEVEL_OCI=INFO
LOG_LEVEL_GENAI=INFO
LOG_LEVEL_DATABASE=WARNING
LOG_LEVEL_KUBERNETES=INFO
```

### Feature Flags

```bash
# Feature Toggles
FEATURE_COST_ANALYSIS=true
FEATURE_ACCESS_ANALYZER=true
FEATURE_AUTO_REMEDIATION=true
FEATURE_CHATBOT=true
FEATURE_KUBERNETES=true
FEATURE_NOTIFICATIONS=true
FEATURE_PROMETHEUS=true
FEATURE_GRAFANA=false

# Experimental Features
EXPERIMENTAL_FEATURES=false
FEATURE_AI_FORECASTING=false
FEATURE_ANOMALY_DETECTION=false
FEATURE_MULTI_CLOUD=false
```

## Configuration Examples

### Development Environment

```bash
# .env file for development
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-not-for-production

# Database
DATABASE_URL=sqlite:///./genai_cloudops.db

# OCI (using personal account)
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT
OCI_REGION=us-ashburn-1
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxx

# GenAI
GROQ_API_KEY=gsk_your_dev_key_here
GROQ_MODEL=llama3-8b-8192

# Redis (optional for development)
REDIS_ENABLED=false

# Features
PROMETHEUS_ENABLED=true
NOTIFICATIONS_ENABLED=false
AUTO_REMEDIATION_ENABLED=false
REMEDIATION_DRY_RUN=true
```

### Production Environment

```bash
# .env file for production
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=super-secure-production-key-here

# Database
DATABASE_URL=postgresql://genai_user:secure_password@db.internal:5432/genai_cloudops
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100

# OCI (using instance principal or service account)
OCI_USE_INSTANCE_PRINCIPAL=true
OCI_REGION=us-ashburn-1
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxx

# GenAI
GROQ_API_KEY=gsk_your_production_key_here
GROQ_MODEL=llama3-70b-8192

# Redis
REDIS_ENABLED=true
REDIS_URL=redis://redis.internal:6379/0
REDIS_MAX_CONNECTIONS=100

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
GRAFANA_URL=https://grafana.internal
GRAFANA_API_KEY=your_grafana_api_key

# Notifications
EMAIL_ENABLED=true
SMTP_SERVER=smtp.yourcompany.com
SMTP_USERNAME=noreply@yourcompany.com
SMTP_PASSWORD=smtp_password

SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb_production_token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Auto-Remediation
AUTO_REMEDIATION_ENABLED=true
AUTO_APPROVAL_ENABLED=false
REMEDIATION_DRY_RUN=false

# Security
RATE_LIMIT_ENABLED=true
TLS_ENABLED=true
ENCRYPTION_ENABLED=true

# Performance
WORKERS=8
MAX_CONCURRENT_REQUESTS=500
CACHE_ENABLED=true
```

### Docker Compose Configuration

```yaml
# docker-compose.yml environment section
environment:
  - ENVIRONMENT=production
  - DATABASE_URL=postgresql://genai_user:${DB_PASSWORD}@postgres:5432/genai_cloudops
  - REDIS_URL=redis://redis:6379/0
  - OCI_COMPARTMENT_ID=${OCI_COMPARTMENT_ID}
  - GROQ_API_KEY=${GROQ_API_KEY}
  - SECRET_KEY=${SECRET_KEY}
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: genai-cloudops-config
data:
  ENVIRONMENT: "production"
  OCI_REGION: "us-ashburn-1"
  GROQ_MODEL: "llama3-8b-8192"
  PROMETHEUS_ENABLED: "true"
  GRAFANA_ENABLED: "true"
  EMAIL_ENABLED: "true"
  SLACK_ENABLED: "true"
  AUTO_REMEDIATION_ENABLED: "true"
  WORKERS: "4"
  REDIS_ENABLED: "true"
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: genai-cloudops-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  DATABASE_URL: "postgresql://user:pass@host:5432/db"
  GROQ_API_KEY: "gsk_your_key_here"
  SMTP_PASSWORD: "smtp_password"
  SLACK_BOT_TOKEN: "xoxb_token"
  GRAFANA_API_KEY: "grafana_key"
```

## Configuration Validation

### Environment Validation Script

```python
#!/usr/bin/env python3
"""Configuration validation script"""

import os
import sys
from urllib.parse import urlparse

def validate_config():
    errors = []
    warnings = []
    
    # Required settings
    required_vars = [
        'SECRET_KEY',
        'OCI_REGION',
        'OCI_COMPARTMENT_ID',
        'GROQ_API_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Required variable {var} is not set")
    
    # Validate SECRET_KEY strength
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 32:
        errors.append("SECRET_KEY should be at least 32 characters long")
    
    # Validate database URL
    db_url = os.getenv('DATABASE_URL', '')
    if db_url:
        parsed = urlparse(db_url)
        if not parsed.scheme:
            errors.append("Invalid DATABASE_URL format")
    
    # Validate OCI compartment OCID format
    compartment_id = os.getenv('OCI_COMPARTMENT_ID', '')
    if compartment_id and not compartment_id.startswith('ocid1.compartment.oc1'):
        warnings.append("OCI_COMPARTMENT_ID doesn't appear to be a valid OCID")
    
    # Print results
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration validation passed")
    
    return len(errors) == 0

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)
```

### Usage

```bash
# Run validation
python validate_config.py

# Check specific environment
env $(cat .env | xargs) python validate_config.py
```

## Best Practices

### Security Best Practices

1. **Secret Management**
   - Use environment variables for secrets
   - Never commit secrets to version control
   - Rotate secrets regularly
   - Use dedicated secret management systems

2. **Database Security**
   - Use strong passwords
   - Enable SSL/TLS for connections
   - Limit database user permissions
   - Regular security updates

3. **API Security**
   - Enable rate limiting
   - Use strong JWT secrets
   - Implement proper CORS policies
   - Enable security headers

### Performance Best Practices

1. **Resource Optimization**
   - Set appropriate worker counts
   - Configure connection pooling
   - Enable caching where appropriate
   - Monitor resource usage

2. **Database Optimization**
   - Use connection pooling
   - Set appropriate timeouts
   - Monitor slow queries
   - Regular maintenance

### Monitoring Best Practices

1. **Observability**
   - Enable comprehensive logging
   - Set up metrics collection
   - Configure health checks
   - Implement alerting

2. **Capacity Planning**
   - Monitor resource trends
   - Set up alerts for thresholds
   - Plan for growth
   - Regular performance reviews

Remember to restart the application after making configuration changes! 