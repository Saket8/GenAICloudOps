# GenAI CloudOps - Docker Containerization Setup

This document provides comprehensive instructions for building, deploying, and managing the GenAI CloudOps application using Docker containers.

## 📋 Overview

The application is fully containerized with the following components:
- **Frontend**: React application served by Nginx (production) or Vite dev server (development)
- **Backend**: FastAPI application running with Gunicorn (production) or Uvicorn (development)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Networking**: Custom Docker network for service communication

## 🏗️ Architecture

### Development Environment
```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   (Vite:3000)   │◄──►│  (Uvicorn:8000) │
│   Hot Reload    │    │   Hot Reload    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
    ┌─────────────────────────────┐
    │       Services              │
    │  ┌─────────┐ ┌──────────┐   │
    │  │PostgreSQL│ │  Redis   │   │
    │  │  :5432   │ │  :6379   │   │
    │  └─────────┘ └──────────┘   │
    └─────────────────────────────┘
```

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   (Nginx:80)    │◄──►│ (Gunicorn:8000) │
│   Optimized     │    │  Multi-worker   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
    ┌─────────────────────────────┐
    │       Services              │
    │  ┌─────────┐ ┌──────────┐   │
    │  │PostgreSQL│ │  Redis   │   │
    │  │  :5432   │ │  :6379   │   │
    │  └─────────┘ └──────────┘   │
    └─────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- PowerShell (Windows) or Bash (Linux/Mac)
- Git

### 1. Clone and Setup
```powershell
git clone <repository-url>
cd GenAI-CloudOps
```

### 2. Environment Configuration
```powershell
# Copy environment template
copy .env.example .env

# Edit .env file with your specific configuration
notepad .env
```

### 3. Start Development Environment
```powershell
# Using PowerShell script
.\scripts\deploy.ps1

# Or using Docker Compose directly
docker-compose up -d
```

### 4. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 File Structure

```
├── backend/
│   ├── Dockerfile              # Production multi-stage build
│   ├── Dockerfile.dev          # Development with hot reload
│   └── .dockerignore          # Exclude unnecessary files
├── frontend/
│   ├── Dockerfile              # Production with Nginx
│   ├── Dockerfile.dev          # Development with Vite
│   ├── nginx.conf             # Nginx configuration
│   └── .dockerignore          # Exclude unnecessary files
├── scripts/
│   ├── build.ps1              # PowerShell build script
│   ├── deploy.ps1             # PowerShell deployment script
│   ├── build.sh               # Bash build script (Linux/Mac)
│   └── deploy.sh              # Bash deployment script (Linux/Mac)
├── docker-compose.yml         # Development configuration
├── docker-compose.prod.yml    # Production configuration
├── .env.example              # Environment template
└── DOCKER_SETUP.md           # This documentation
```

## 🛠️ Build Scripts

### PowerShell (Windows)

#### Build Images
```powershell
# Build development images
.\scripts\build.ps1

# Build production images
.\scripts\build.ps1 -Environment production -Version v1.0.0

# Build and push to registry
.\scripts\build.ps1 -Environment production -Version v1.0.0 -Registry myregistry.com -Push true
```

#### Deploy Application
```powershell
# Start development environment
.\scripts\deploy.ps1

# Start production environment
.\scripts\deploy.ps1 -Environment production

# Show logs
.\scripts\deploy.ps1 -Action logs

# Check health status
.\scripts\deploy.ps1 -Action health

# Stop services
.\scripts\deploy.ps1 -Action down
```

### Bash (Linux/Mac)

#### Build Images
```bash
# Build development images
./scripts/build.sh

# Build production images
./scripts/build.sh v1.0.0 production

# Build and push to registry
./scripts/build.sh v1.0.0 production myregistry.com true
```

#### Deploy Application
```bash
# Start development environment
./scripts/deploy.sh

# Start production environment
./scripts/deploy.sh production

# Show logs
./scripts/deploy.sh development logs

# Check health status
./scripts/deploy.sh development health
```

## 🔧 Docker Compose Commands

### Development
```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Check service status
docker-compose ps
```

### Production
```powershell
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production services
docker-compose -f docker-compose.prod.yml down
```

## 🔍 Health Checks

All services include comprehensive health checks:

- **Frontend**: HTTP check on port 80/3000
- **Backend**: HTTP check on `/health` endpoint
- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli ping` command

Health check status:
- ✅ **Healthy**: Service is running correctly
- ❌ **Unhealthy**: Service has issues
- ⚠️ **Starting**: Service is initializing

## 🔒 Security Features

### Container Security
- Non-root users for all services
- Minimal base images (Alpine Linux where possible)
- Security headers in Nginx configuration
- Resource limits and constraints

### Network Security
- Custom Docker network isolation
- No exposed unnecessary ports
- Service-to-service communication only

### Image Security
- Multi-stage builds to reduce attack surface
- No sensitive data in images
- Regular base image updates

## 📊 Monitoring and Logging

### Log Management
- Structured JSON logging in production
- Log rotation with size and file limits
- Centralized logging via Docker

### Resource Monitoring
- CPU and memory limits configured
- Health check monitoring
- Container restart policies

### Performance Optimization
- Nginx gzip compression
- Static asset caching
- Database connection pooling
- Redis caching layer

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```powershell
# Check what's using the port
netstat -ano | findstr :3000

# Stop conflicting service or change port in docker-compose.yml
```

#### 2. Docker Not Running
```powershell
# Start Docker Desktop
# Or restart Docker service
```

#### 3. Permission Issues (Linux/Mac)
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

#### 4. Build Failures
```powershell
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Debugging Commands

```powershell
# View container logs
docker-compose logs [service-name]

# Execute commands in running container
docker-compose exec backend bash
docker-compose exec frontend sh

# Inspect container details
docker inspect [container-name]

# View network information
docker network ls
docker network inspect genai-cloudops_genai-cloudops
```

## 🚀 Deployment to Production

### Container Registry
1. Build production images:
   ```powershell
   .\scripts\build.ps1 -Environment production -Version v1.0.0
   ```

2. Tag and push to registry:
   ```powershell
   .\scripts\build.ps1 -Environment production -Version v1.0.0 -Registry your-registry.com -Push true
   ```

### OCI OKE Deployment
The containers are designed to work with Oracle Cloud Infrastructure (OCI) Oracle Kubernetes Engine (OKE):

1. **Helm Charts**: Use provided Helm charts in `/deployment/helm-chart/`
2. **Kubernetes Manifests**: Container configs are K8s-ready
3. **Health Checks**: Built-in readiness and liveness probes
4. **Scaling**: Horizontal pod autoscaling supported

## 📈 Performance Tuning

### Production Optimizations
- **Frontend**: Static asset optimization, CDN integration
- **Backend**: Gunicorn worker tuning, connection pooling
- **Database**: Connection limits, query optimization
- **Cache**: Redis memory policies, TTL configuration

### Resource Allocation
Recommended production resources:
- **Frontend**: 128MB RAM, 0.25 CPU
- **Backend**: 512MB RAM, 0.5 CPU  
- **PostgreSQL**: 256MB RAM, 0.25 CPU
- **Redis**: 128MB RAM, 0.25 CPU

## 🆘 Support

For issues and questions:
1. Check this documentation
2. Review Docker and Docker Compose logs
3. Verify environment configuration
4. Check service health status

---

**Last Updated**: Task 22 Implementation
**Version**: 1.0.0 