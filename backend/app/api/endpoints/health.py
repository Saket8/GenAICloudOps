from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "genai-cloudops-api"}

@router.get("/detailed")
async def detailed_health_check() -> Dict[str, str]:
    """Detailed health check with more information"""
    return {
        "status": "healthy",
        "service": "genai-cloudops-api",
        "version": "1.0.0",
        "environment": "development"
    } 