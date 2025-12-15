import gzip
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware for response compression"""
    
    def __init__(self, app, min_size: int = None, compression_level: int = None):
        super().__init__(app)
        self.min_size = min_size or settings.COMPRESSION_MIN_SIZE
        self.compression_level = compression_level or settings.COMPRESSION_LEVEL
        
        # Content types that should be compressed
        self.compressible_types = {
            "application/json",
            "application/javascript",
            "application/xml",
            "text/html",
            "text/css",
            "text/javascript",
            "text/plain",
            "text/xml",
            "text/csv"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle request compression"""
        
        if not settings.COMPRESSION_ENABLED:
            return await call_next(request)
        
        # Check if client accepts gzip compression
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return await call_next(request)
        
        # Process request
        response = await call_next(request)
        
        # Check if response should be compressed
        if not self._should_compress(response):
            return response
        
        # Compress response
        return await self._compress_response(response)
    
    def _should_compress(self, response: StarletteResponse) -> bool:
        """Determine if response should be compressed"""
        
        # Check if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type not in self.compressible_types:
            return False
        
        # Check content length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.min_size:
            return False
        
        return True
    
    async def _compress_response(self, response: StarletteResponse) -> StarletteResponse:
        """Compress response content"""
        try:
            # Get response body
            if hasattr(response, 'body'):
                body = response.body
            else:
                # For streaming responses, we'll skip compression for now
                return response
            
            # Check minimum size
            if len(body) < self.min_size:
                return response
            
            # Compress body
            compressed_body = gzip.compress(body, compresslevel=self.compression_level)
            
            # Calculate compression ratio
            compression_ratio = len(compressed_body) / len(body)
            
            # Only use compression if it actually reduces size significantly
            if compression_ratio > 0.9:  # Less than 10% reduction
                return response
            
            # Create new response with compressed body
            compressed_response = StarletteResponse(
                content=compressed_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            # Update headers
            compressed_response.headers["content-encoding"] = "gzip"
            compressed_response.headers["content-length"] = str(len(compressed_body))
            
            # Add compression info header
            compressed_response.headers["x-compression-ratio"] = f"{compression_ratio:.2f}"
            
            logger.debug(f"Compressed response: {len(body)} -> {len(compressed_body)} bytes (ratio: {compression_ratio:.2f})")
            
            return compressed_response
            
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return response 