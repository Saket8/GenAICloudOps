import time
import json
import hashlib
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import re
import html
from urllib.parse import unquote
from app.services.cache_service import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.window_size = 60  # 1 minute window
        self.max_requests = 100  # Default max requests per window
        
        # Different rate limits for different endpoints
        self.endpoint_limits = {
            "/api/v1/genai/": {"requests": 20, "window": 60},
            "/api/v1/auth/login": {"requests": 5, "window": 60},
            "/api/v1/remediation/execute": {"requests": 10, "window": 300},
            "/api/v1/monitoring/": {"requests": 200, "window": 60},
        }
    
    async def is_rate_limited(self, client_id: str, endpoint: str) -> tuple[bool, Dict[str, Any]]:
        """Check if client is rate limited with detailed info"""
        
        # Get rate limit config for endpoint
        limit_config = self._get_limit_config(endpoint)
        max_requests = limit_config["requests"]
        window_size = limit_config["window"]
        
        # Create cache key for rate limiting
        cache_key = f"rate_limit:{client_id}:{endpoint}"
        
        # Get current request count
        cached_data = await cache_service.get("rate_limit", cache_key)
        
        now = time.time()
        window_start = now - window_size
        
        if cached_data:
            request_timestamps = cached_data.get("timestamps", [])
            # Filter out old timestamps
            request_timestamps = [ts for ts in request_timestamps if ts > window_start]
        else:
            request_timestamps = []
        
        # Check if rate limited
        if len(request_timestamps) >= max_requests:
            oldest_request = min(request_timestamps) if request_timestamps else now
            reset_time = oldest_request + window_size
            
            return True, {
                "rate_limited": True,
                "requests_made": len(request_timestamps),
                "max_requests": max_requests,
                "window_size": window_size,
                "reset_time": reset_time,
                "retry_after": max(0, reset_time - now)
            }
        
        # Add current request timestamp
        request_timestamps.append(now)
        
        # Store updated timestamps
        await cache_service.set(
            "rate_limit", 
            cache_key, 
            {"timestamps": request_timestamps},
            ttl=window_size
        )
        
        return False, {
            "rate_limited": False,
            "requests_made": len(request_timestamps),
            "max_requests": max_requests,
            "window_size": window_size,
            "remaining_requests": max_requests - len(request_timestamps)
        }
    
    def _get_limit_config(self, endpoint: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint"""
        for pattern, config in self.endpoint_limits.items():
            if endpoint.startswith(pattern):
                return config
        
        return {"requests": self.max_requests, "window": self.window_size}

class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    def __init__(self):
        # Common attack patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
        ]
        
        self.sql_injection_patterns = [
            r'(\bunion\b.*\bselect\b)',
            r'(\bselect\b.*\bfrom\b)',
            r'(\binsert\b.*\binto\b)',
            r'(\bupdate\b.*\bset\b)',
            r'(\bdelete\b.*\bfrom\b)',
            r'(\bdrop\b.*\btable\b)',
            r'(\balter\b.*\btable\b)',
            r'(--|#|/\*|\*/)',
        ]
        
        self.command_injection_patterns = [
            r'[;&|`]',
            r'\$\([^)]*\)',
            r'`[^`]*`',
            r'\|\s*\w+',
        ]
    
    def validate_and_sanitize(self, data: Any) -> tuple[bool, Any, List[str]]:
        """Validate and sanitize input data"""
        security_issues = []
        
        if isinstance(data, str):
            return self._validate_string(data)
        elif isinstance(data, dict):
            return self._validate_dict(data)
        elif isinstance(data, list):
            return self._validate_list(data)
        else:
            return True, data, security_issues
    
    def _validate_string(self, text: str) -> tuple[bool, str, List[str]]:
        """Validate and sanitize string input"""
        security_issues = []
        original_text = text
        
        # Check for XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                security_issues.append(f"Potential XSS detected: {pattern}")
        
        # Check for SQL injection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                security_issues.append(f"Potential SQL injection detected: {pattern}")
        
        # Check for command injection
        for pattern in self.command_injection_patterns:
            if re.search(pattern, text):
                security_issues.append(f"Potential command injection detected: {pattern}")
        
        # Sanitize
        sanitized_text = html.escape(text)
        sanitized_text = unquote(sanitized_text)
        
        # Length validation
        if len(sanitized_text) > 10000:  # 10KB limit
            security_issues.append("Input too long")
            sanitized_text = sanitized_text[:10000]
        
        is_safe = len(security_issues) == 0
        return is_safe, sanitized_text, security_issues
    
    def _validate_dict(self, data: dict) -> tuple[bool, dict, List[str]]:
        """Validate dictionary input"""
        security_issues = []
        sanitized_data = {}
        is_safe = True
        
        for key, value in data.items():
            # Validate key
            key_safe, sanitized_key, key_issues = self._validate_string(str(key))
            if not key_safe:
                is_safe = False
                security_issues.extend([f"Key '{key}': {issue}" for issue in key_issues])
            
            # Validate value
            value_safe, sanitized_value, value_issues = self.validate_and_sanitize(value)
            if not value_safe:
                is_safe = False
                security_issues.extend([f"Value for key '{key}': {issue}" for issue in value_issues])
            
            sanitized_data[sanitized_key] = sanitized_value
        
        return is_safe, sanitized_data, security_issues
    
    def _validate_list(self, data: list) -> tuple[bool, list, List[str]]:
        """Validate list input"""
        security_issues = []
        sanitized_data = []
        is_safe = True
        
        for i, item in enumerate(data):
            item_safe, sanitized_item, item_issues = self.validate_and_sanitize(item)
            if not item_safe:
                is_safe = False
                security_issues.extend([f"Item {i}: {issue}" for issue in item_issues])
            
            sanitized_data.append(sanitized_item)
        
        return is_safe, sanitized_data, security_issues

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        
        # Security configurations
        self.blocked_user_agents = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "gobuster",
            "dirb",
            "wfuzz"
        ]
        
        self.suspicious_headers = [
            "x-forwarded-for",
            "x-originating-ip",
            "x-cluster-client-ip"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main security middleware handler"""
        start_time = time.time()
        
        try:
            # 1. Basic security checks
            security_check = await self._basic_security_checks(request)
            if security_check:
                return security_check
            
            # 2. Rate limiting
            rate_limit_check = await self._check_rate_limiting(request)
            if rate_limit_check:
                return rate_limit_check
            
            # 3. Input validation (for POST/PUT requests)
            if request.method in ["POST", "PUT", "PATCH"]:
                validation_check = await self._validate_input(request)
                if validation_check:
                    return validation_check
            
            # 4. Process request
            response = await call_next(request)
            
            # 5. Add security headers
            response = self._add_security_headers(response)
            
            # 6. Log security metrics
            processing_time = time.time() - start_time
            await self._log_security_metrics(request, response, processing_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"}
            )
    
    async def _basic_security_checks(self, request: Request) -> Optional[Response]:
        """Perform basic security checks"""
        
        # Check user agent
        user_agent = request.headers.get("user-agent", "").lower()
        for blocked_agent in self.blocked_user_agents:
            if blocked_agent in user_agent:
                logger.warning(f"Blocked suspicious user agent: {user_agent}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )
        
        # Check for suspicious headers
        for header in self.suspicious_headers:
            if header in request.headers:
                header_value = request.headers[header]
                # Log for monitoring
                logger.info(f"Suspicious header detected: {header}={header_value}")
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            logger.warning(f"Request too large: {content_length} bytes")
            return JSONResponse(
                status_code=413,
                content={"error": "Request entity too large"}
            )
        
        return None
    
    async def _check_rate_limiting(self, request: Request) -> Optional[Response]:
        """Check rate limiting"""
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, "user_id", None)
        client_id = user_id or client_ip
        
        # Check rate limit
        is_limited, rate_info = await self.rate_limiter.is_rate_limited(
            client_id, request.url.path
        )
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for client {client_id} on {request.url.path}")
            
            headers = {
                "X-RateLimit-Limit": str(rate_info["max_requests"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                "Retry-After": str(int(rate_info["retry_after"]))
            }
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {int(rate_info['retry_after'])} seconds"
                },
                headers=headers
            )
        
        return None
    
    async def _validate_input(self, request: Request) -> Optional[Response]:
        """Validate request input"""
        
        try:
            # Skip validation for certain content types
            content_type = request.headers.get("content-type", "")
            if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
                return None
            
            # Get request body
            body = await request.body()
            if not body:
                return None
            
            # Parse JSON body
            try:
                json_data = json.loads(body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning("Invalid JSON in request body")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid JSON format"}
                )
            
            # Validate and sanitize
            is_safe, sanitized_data, security_issues = self.input_validator.validate_and_sanitize(json_data)
            
            if not is_safe:
                logger.warning(f"Security issues in request: {security_issues}")
                
                # In production, you might want to block the request
                # For now, we'll log and continue with sanitized data
                if settings.ENVIRONMENT == "production":
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Input validation failed",
                            "issues": security_issues[:5]  # Limit exposed issues
                        }
                    )
            
            # Store sanitized data for the request
            request.state.sanitized_data = sanitized_data
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={"error": "Input validation failed"}
            )
        
        return None
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers"""
        
        security_headers = {
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'"
            ),
            
            # Security headers
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            
            # Cache control for sensitive endpoints
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Custom security headers
            "X-API-Version": "1.0",
            "X-Security-Middleware": "enabled"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support"""
        
        # Check for forwarded headers (in order of preference)
        forwarded_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-client-ip",
            "cf-connecting-ip"  # Cloudflare
        ]
        
        for header in forwarded_headers:
            if header in request.headers:
                ip = request.headers[header].split(",")[0].strip()
                if ip and ip != "unknown":
                    return ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    async def _log_security_metrics(self, request: Request, response: Response, processing_time: float):
        """Log security metrics for monitoring"""
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "client_ip": self._get_client_ip(request),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "user_agent": request.headers.get("user-agent", ""),
            "content_length": request.headers.get("content-length", "0")
        }
        
        # Store metrics in cache for monitoring dashboard
        await cache_service.set(
            "security_metrics",
            f"request_{int(time.time())}_{hash(str(metrics))}",
            metrics,
            ttl=3600  # Keep for 1 hour
        ) 