from fastapi import APIRouter, Request, HTTPException
from typing import Dict, List, Optional
import httpx
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """Registry for microservices"""
    
    def __init__(self):
        self.services: Dict[str, Dict] = {}
    
    def register_service(self, name: str, base_url: str, health_endpoint: str = "/health", version: str = "1.0"):
        """Register a microservice"""
        self.services[name] = {
            "base_url": base_url,
            "health_endpoint": health_endpoint,
            "version": version,
            "status": "unknown",
            "last_check": None
        }
        logger.info(f"Registered service: {name} at {base_url}")
    
    def get_service(self, name: str) -> Optional[Dict]:
        """Get service configuration"""
        return self.services.get(name)
    
    def list_services(self) -> List[Dict]:
        """List all registered services"""
        return [
            {"name": name, **config} 
            for name, config in self.services.items()
        ]
    
    async def check_service_health(self, name: str) -> bool:
        """Check if a service is healthy"""
        service = self.get_service(name)
        if not service:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{service['base_url']}{service['health_endpoint']}",
                    timeout=5.0
                )
                is_healthy = response.status_code == 200
                
                self.services[name]["status"] = "healthy" if is_healthy else "unhealthy"
                self.services[name]["last_check"] = datetime.utcnow().isoformat()
                
                return is_healthy
                
        except Exception as e:
            logger.warning(f"Health check failed for service {name}: {e}")
            self.services[name]["status"] = "unhealthy"
            self.services[name]["last_check"] = datetime.utcnow().isoformat()
            return False

class APIGateway:
    """API Gateway for routing requests to microservices"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup gateway routes"""
        
        @self.router.get("/services")
        async def list_services():
            """List all registered services"""
            return {
                "services": self.registry.list_services(),
                "total": len(self.registry.services)
            }
        
        @self.router.get("/services/{service_name}/health")
        async def check_service_health(service_name: str):
            """Check health of a specific service"""
            is_healthy = await self.registry.check_service_health(service_name)
            service = self.registry.get_service(service_name)
            
            if not service:
                raise HTTPException(status_code=404, detail="Service not found")
            
            return {
                "service": service_name,
                "healthy": is_healthy,
                "status": service["status"],
                "last_check": service["last_check"]
            }
        
        @self.router.post("/services/{service_name}/register")
        async def register_service(service_name: str, config: dict):
            """Register a new service"""
            self.registry.register_service(
                name=service_name,
                base_url=config["base_url"],
                health_endpoint=config.get("health_endpoint", "/health"),
                version=config.get("version", "1.0")
            )
            return {"message": f"Service {service_name} registered successfully"}
    
    async def forward_request(self, service_name: str, path: str, method: str, **kwargs):
        """Forward request to a microservice"""
        service = self.registry.get_service(service_name)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        # Check if service is healthy
        is_healthy = await self.registry.check_service_health(service_name)
        if not is_healthy:
            raise HTTPException(status_code=503, detail=f"Service {service_name} is unavailable")
        
        url = f"{service['base_url']}{path}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, timeout=30.0, **kwargs)
                return response
        except Exception as e:
            logger.error(f"Error forwarding request to {service_name}: {e}")
            raise HTTPException(status_code=502, detail="Bad Gateway")

# Global gateway instance
gateway = APIGateway()

# Register internal services (these would be external in a real microservices setup)
gateway.registry.register_service("auth", "http://localhost:8000", "/api/v1/health")
gateway.registry.register_service("monitoring", "http://localhost:8000", "/api/v1/health/")

async def setup_gateway_health_checks():
    """Setup periodic health checks for all services"""
    while True:
        for service_name in gateway.registry.services.keys():
            await gateway.registry.check_service_health(service_name)
        await asyncio.sleep(30)  # Check every 30 seconds

def get_gateway() -> APIGateway:
    """Get the global gateway instance"""
    return gateway 