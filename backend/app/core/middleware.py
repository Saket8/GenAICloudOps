import time
import json
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import ipaddress
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(lambda: deque())

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Generate request ID
        request_id = f"{int(time.time() * 1000)}-{hash(str(request.url))}"
        
        # Log request details
        logger.info(f"Request ID: {request_id} | Method: {request.method} | URL: {request.url} | Client IP: {request.client.host}")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(f"Request ID: {request_id} | Status: {response.status_code} | Process Time: {process_time:.4f}s")
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request ID: {request_id} | Error: {str(e)} | Process Time: {process_time:.4f}s")
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        current_time = datetime.now()
        
        # Clean old entries
        cutoff_time = current_time - timedelta(seconds=self.period)
        
        # Get client's request history
        client_requests = rate_limit_storage[client_ip]
        
        # Remove old requests
        while client_requests and client_requests[0] < cutoff_time:
            client_requests.popleft()
        
        # Check if limit exceeded
        if len(client_requests) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Max {self.calls} requests per {self.period} seconds.",
                    "retry_after": self.period
                }
            )
        
        # Add current request
        client_requests.append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(client_requests))
        response.headers["X-RateLimit-Reset"] = str(int((current_time + timedelta(seconds=self.period)).timestamp()))
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}", exc_info=True)
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error_type": type(e).__name__,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for application monitoring and metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_count = defaultdict(int)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        method_path = f"{request.method} {request.url.path}"
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Update metrics
            self.request_count[method_path] += 1
            self.response_times[method_path].append(process_time)
            
            # Keep only last 100 response times for each endpoint
            if len(self.response_times[method_path]) > 100:
                self.response_times[method_path] = self.response_times[method_path][-100:]
            
            # Add monitoring headers
            response.headers["X-Request-Count"] = str(self.request_count[method_path])
            
            return response
            
        except Exception as e:
            self.error_count[method_path] += 1
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get application metrics"""
        metrics = {
            "request_counts": dict(self.request_count),
            "error_counts": dict(self.error_count),
            "average_response_times": {}
        }
        
        for endpoint, times in self.response_times.items():
            if times:
                metrics["average_response_times"][endpoint] = sum(times) / len(times)
        
        return metrics

# Global monitoring instance storage
_monitoring_instances = []

def get_monitoring_metrics() -> Dict[str, Any]:
    """Get current monitoring metrics"""
    if _monitoring_instances:
        return _monitoring_instances[-1].get_metrics()
    return {}

# Monkey patch to track instances
original_init = MonitoringMiddleware.__init__

def tracking_init(self, app):
    original_init(self, app)
    _monitoring_instances.append(self)

MonitoringMiddleware.__init__ = tracking_init 