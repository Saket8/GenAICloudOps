from fastapi import APIRouter
from app.api.endpoints import health, auth, monitoring, cloud, notifications, genai, remediation, chatbot, kubernetes, kubernetes_working, access_analyzer, cost_analyzer, websocket, vault, optional_enhancements, performance, aws, providers, users, roles, intelligence

from app.core.gateway import get_gateway

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(cloud.router, prefix="/cloud", tags=["cloud-operations"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(genai.router, prefix="/genai", tags=["artificial-intelligence"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["conversational-agent"])
api_router.include_router(remediation.router, prefix="/remediation", tags=["remediation"])
api_router.include_router(kubernetes.router, prefix="/kubernetes", tags=["kubernetes-integration"])
api_router.include_router(kubernetes_working.router, prefix="/k8s", tags=["kubernetes-working"])
api_router.include_router(access_analyzer.router, prefix="/access", tags=["access-analyzer"])
api_router.include_router(cost_analyzer.router, prefix="/cost", tags=["cost-analyzer"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket-realtime"])
api_router.include_router(vault.router, prefix="/vault", tags=["secrets-management"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance-monitoring"])
api_router.include_router(optional_enhancements.router, tags=["optional-enhancements"])
api_router.include_router(providers.router, prefix="/providers", tags=["cloud-providers"])
api_router.include_router(aws.router, prefix="/aws", tags=["aws"])
api_router.include_router(users.router, prefix="/users", tags=["user-management"])
api_router.include_router(roles.router, prefix="/roles", tags=["role-management"])
api_router.include_router(intelligence.router, tags=["intelligence"])

# Force reload timestamp
import time
print(f" Routes loaded at {time.strftime('%H:%M:%S')} - k8s endpoints registered")

# Include gateway routes
gateway = get_gateway()
api_router.include_router(gateway.router, prefix="/gateway", tags=["gateway"])

@api_router.get("/")
async def api_root():
    return {
        "message": "GenAI CloudOps API v1.0", 
        "status": "running",
        "features": [
            "authentication", 
            "role-based-access-control",
            "monitoring", 
            "api-gateway", 
            "advanced-rate-limiting",
            "input-validation",
            "security-hardening",
            "performance-monitoring",
            "response-compression",
            "redis-caching",
            "cloud-operations",
            "kubernetes-integration",
            "async-microservices",
            "real-time-notifications",
            "ai-powered-analytics",
            "intelligent-remediation",
            "automated-remediation",
            "conversational-ai",
            "access-control-analysis",
            "cost-optimization",
            "real-time-updates"
        ],
        "endpoints": {
            "health": "/health",
            "auth": "/auth", 
            "monitoring": "/monitoring",
            "gateway": "/gateway",
            "cloud": "/cloud",
            "notifications": "/notifications",
            "genai": "/genai",
            "chatbot": "/chatbot",
            "remediation": "/remediation",
            "kubernetes": "/kubernetes",
            "k8s": "/k8s",
            "access": "/access",
            "cost": "/cost",
            "performance": "/performance",
            "websocket": "/ws"
        },
        "microservices": {
            "authentication": "User management and JWT-based auth",
            "cloud-operations": "OCI/AWS/Azure resource management",
            "kubernetes": "Real-time OKE cluster monitoring, RBAC analysis, and pod health management",
            "security": "Alert management and remediation",
            "cost-analyzer": "Advanced cost analysis, optimization recommendations, and forecasting",
            "genai": "AI-powered insights, chat, and intelligent automation",
            "chatbot": "Advanced conversational agent with intent recognition and OCI integration",
            "remediation": "Automated infrastructure remediation with approval workflows",
            "access-analyzer": "Unified RBAC and IAM policy analysis with AI-powered security recommendations",
            "performance": "Comprehensive performance monitoring, optimization, and health tracking",
            "websocket-realtime": "Real-time data streaming with WebSocket connections for live metrics, alerts, and status updates"
        }
    } 