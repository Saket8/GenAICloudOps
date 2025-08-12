from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.api.routes import api_router
print("🔄 MAIN.PY: api_router imported - checking for k8s routes")
from app.core.config import settings
from app.core.database import create_tables, init_default_roles
from app.core.middleware import (
    LoggingMiddleware, 
    ErrorHandlingMiddleware, 
    MonitoringMiddleware
)
from app.core.security_middleware import SecurityMiddleware
from app.core.compression_middleware import CompressionMiddleware
from app.services.realtime_service import start_realtime_streaming, stop_realtime_streaming
from app.services.performance_service import performance_service
from app.core.exceptions import (
    BaseCustomException,
    custom_exception_handler,
    validation_exception_handler,
    http_exception_override_handler,
    general_exception_handler
)
import asyncio

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting application services...")
    try:
        # Start real-time streaming in background
        streaming_task = asyncio.create_task(start_realtime_streaming())
        print("✅ Real-time streaming service started")
        
        # Start performance monitoring
        await performance_service.start_monitoring()
        print("✅ Performance monitoring service started")
        
        yield
    except Exception as e:
        print(f"❌ Failed to start services: {e}")
        yield
    finally:
        # Shutdown
        print("🛑 Shutting down application services...")
        try:
            await stop_realtime_streaming()
            print("✅ Real-time streaming service stopped")
            
            await performance_service.stop_monitoring()
            print("✅ Performance monitoring service stopped")
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")

app = FastAPI(
    title="GenAI CloudOps API",
    version="1.0.0",
    lifespan=lifespan,
    description="""
## Advanced Backend API for GenAI CloudOps Platform

A comprehensive microservices-based API providing cloud operations management, 
monitoring, and automated remediation capabilities.

### Key Features

* **🔐 Authentication & RBAC**: JWT-based authentication with role-based access control
* **☁️ Multi-Cloud Support**: Integration with OCI, AWS, and Azure cloud providers  
* **🎛️ API Gateway**: Centralized routing and service discovery
* **📊 Monitoring**: Real-time metrics, logging, and health checks
* **🔒 Security**: Rate limiting, security headers, and automated threat remediation
* **🐳 Kubernetes**: Pod monitoring and cluster management
* **💰 Cost Analysis**: Resource cost optimization and analysis
* **⚡ Async Operations**: High-performance async/await patterns for external APIs

### Architecture

Built using a modular microservices architecture with:
- FastAPI for high-performance async API endpoints
- SQLAlchemy ORM with PostgreSQL/SQLite support
- JWT-based stateless authentication
- Comprehensive middleware stack for logging, monitoring, and security
- Service registry for microservice discovery and health checks

### API Endpoints

All endpoints are available under `/api/v1/` prefix with comprehensive 
OpenAPI documentation.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "GenAI CloudOps Team",
        "email": "support@genai-cloudops.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.genai-cloudops.com",
            "description": "Production server"
        }
    ],
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization operations"
        },
        {
            "name": "health",
            "description": "Service health check and status endpoints"
        },
        {
            "name": "monitoring",
            "description": "Application monitoring, metrics, and statistics"
        },
        {
            "name": "gateway",
            "description": "API gateway and microservice management"
        },
        {
            "name": "cloud-operations",
            "description": "Cloud resource management and operations"
        }
    ]
)

# Add CORS middleware first (order matters - they are executed in reverse order)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add performance and security middleware (order matters - executed in reverse)
if settings.COMPRESSION_ENABLED:
    app.add_middleware(CompressionMiddleware)

# Core middleware stack
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(MonitoringMiddleware)

# Security middleware (includes rate limiting, input validation, and security headers)
if settings.SECURITY_MIDDLEWARE_ENABLED:
    app.add_middleware(SecurityMiddleware)

# Add exception handlers
app.add_exception_handler(BaseCustomException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_override_handler)
app.add_exception_handler(Exception, general_exception_handler)

# @app.on_event("startup")  # TODO: Migrate to lifespan in FastAPI 0.116+
# async def startup_event() -> None:
#     """Initialize database and default data on startup"""
#     try:
#         # Create all database tables
#         create_tables()
#         print("Database tables created successfully")
#         
#         # Initialize default roles
#         init_default_roles()
#         print("Default roles initialized successfully")
#         
#         # Initialize gateway (health checks disabled for now to prevent startup loops)
#         # from app.core.gateway import setup_gateway_health_checks
#         # asyncio.create_task(setup_gateway_health_checks())
#         print("API Gateway initialized (health checks disabled)")
#         
#         print("✅ GenAI CloudOps API started successfully")
#         print("📊 Features enabled: Authentication, RBAC, Security Middleware, "
#               "Rate Limiting, Input Validation, Compression, Performance Monitoring, "
#               "API Gateway")
#         
#     except Exception as e:
#         print(f"❌ Error during startup: {e}")

# Include API routes
app.include_router(api_router, prefix="/api/v1")
print(f"🔄 MAIN.PY: api_router included with {len(api_router.routes)} routes")

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to GenAI CloudOps API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "GenAI CloudOps API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 