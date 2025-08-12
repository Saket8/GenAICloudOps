"""
API endpoints for OCI Vault secrets management
Provides secure endpoints for managing secrets, API keys, and credentials
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime

from ...core.database import get_db
from ...core.permissions import require_permissions, RequireAdminRole
from ...models.user import User
from ...services.auth_service import AuthService
from ...services.oci_vault_service import (
    vault_service, 
    SecretType, 
    SecretMetadata,
    get_secret,
    get_api_key
)
from ...core.config import settings

router = APIRouter()
security = HTTPBearer()


# Pydantic models for request/response
from pydantic import BaseModel, Field


class SecretCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the secret")
    value: str = Field(..., description="Secret value to store")
    secret_type: SecretType = Field(SecretType.GENERIC, description="Type of secret")
    description: Optional[str] = Field(None, description="Description of the secret")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags for the secret")


class SecretUpdateRequest(BaseModel):
    value: str = Field(..., description="New secret value")
    description: Optional[str] = Field(None, description="Updated description")
    tags: Optional[Dict[str, str]] = Field(None, description="Updated tags")


class SecretResponse(BaseModel):
    name: str
    secret_type: str
    version_number: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    tags: Optional[Dict[str, str]] = None


class SecretListResponse(BaseModel):
    secrets: List[SecretResponse]
    total_count: int


class APIKeyRequest(BaseModel):
    service_name: str = Field(..., description="Name of the service")
    api_key: str = Field(..., description="API key value")
    description: Optional[str] = Field(None, description="Description of the API key")


class VaultStatsResponse(BaseModel):
    total_secrets: int
    secrets_by_type: Dict[str, int]
    cache_stats: Dict[str, Any]
    vault_enabled: bool


@router.get("/stats", response_model=VaultStatsResponse)
async def get_vault_statistics(
    current_user: User = Depends(RequireAdminRole)
):
    """Get vault statistics and health information"""
    try:
        # Get all secrets
        secrets = await vault_service.list_secrets()
        
        # Count by type
        secrets_by_type = {}
        for secret in secrets:
            secret_type = secret.secret_type.value
            secrets_by_type[secret_type] = secrets_by_type.get(secret_type, 0) + 1
        
        # Get cache stats
        cache_stats = vault_service.get_cache_stats()
        
        return VaultStatsResponse(
            total_secrets=len(secrets),
            secrets_by_type=secrets_by_type,
            cache_stats=cache_stats,
            vault_enabled=settings.OCI_VAULT_ENABLED
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vault statistics: {str(e)}"
        )


@router.get("/secrets", response_model=SecretListResponse)
async def list_secrets(
    secret_type: Optional[str] = None,
    current_user: User = Depends(RequireAdminRole)
):
    """List all secrets in the vault (metadata only)"""
    try:
        # Convert string to enum if provided
        filter_type = None
        if secret_type:
            try:
                filter_type = SecretType(secret_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid secret type: {secret_type}"
                )
        
        secrets = await vault_service.list_secrets(filter_type)
        
        secret_responses = [
            SecretResponse(
                name=secret.name,
                secret_type=secret.secret_type.value,
                version_number=secret.version_number,
                created_at=secret.created_at,
                expires_at=secret.expires_at,
                tags=secret.tags
            )
            for secret in secrets
        ]
        
        return SecretListResponse(
            secrets=secret_responses,
            total_count=len(secret_responses)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list secrets: {str(e)}"
        )


@router.post("/secrets", status_code=status.HTTP_201_CREATED)
async def create_secret(
    request: SecretCreateRequest,
    current_user: User = Depends(RequireAdminRole)
):
    """Create a new secret in the vault"""
    try:
        success = await vault_service.store_secret(
            secret_name=request.name,
            secret_value=request.value,
            secret_type=request.secret_type,
            description=request.description or "",
            tags=request.tags
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store secret in vault"
            )
        
        return {"message": f"Secret '{request.name}' created successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create secret: {str(e)}"
        )


@router.put("/secrets/{secret_name}/rotate")
async def rotate_secret(
    secret_name: str,
    request: SecretUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(RequireAdminRole)
):
    """Rotate a secret by creating a new version"""
    try:
        success = await vault_service.rotate_secret(secret_name, request.value)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rotate secret '{secret_name}'"
            )
        
        # Add background task to notify services if needed
        background_tasks.add_task(notify_secret_rotation, secret_name)
        
        return {"message": f"Secret '{secret_name}' rotated successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate secret: {str(e)}"
        )


@router.delete("/secrets/{secret_name}")
async def delete_secret(
    secret_name: str,
    permanent: bool = False,
    current_user: User = Depends(RequireAdminRole)
):
    """Delete a secret from the vault"""
    try:
        success = await vault_service.delete_secret(secret_name, permanent=permanent)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete secret '{secret_name}'"
            )
        
        action = "permanently deleted" if permanent else "scheduled for deletion"
        return {"message": f"Secret '{secret_name}' {action} successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete secret: {str(e)}"
        )


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def store_api_key(
    request: APIKeyRequest,
    current_user: User = Depends(RequireAdminRole)
):
    """Store an API key for a service"""
    try:
        success = await AuthService.store_api_key(
            service_name=request.service_name,
            api_key=request.api_key,
            description=request.description or f"API key for {request.service_name}"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store API key for {request.service_name}"
            )
        
        return {"message": f"API key for '{request.service_name}' stored successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store API key: {str(e)}"
        )


@router.put("/api-keys/{service_name}/rotate")
async def rotate_api_key(
    service_name: str,
    new_api_key: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(RequireAdminRole)
):
    """Rotate an API key for a service"""
    try:
        success = await AuthService.rotate_api_key(service_name, new_api_key)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rotate API key for {service_name}"
            )
        
        # Add background task to notify the service
        background_tasks.add_task(notify_api_key_rotation, service_name)
        
        return {"message": f"API key for '{service_name}' rotated successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate API key: {str(e)}"
        )


@router.post("/jwt-secret/rotate")
async def rotate_jwt_secret(
    background_tasks: BackgroundTasks,
    new_secret: Optional[str] = None,
    current_user: User = Depends(RequireAdminRole)
):
    """Rotate the JWT signing secret"""
    try:
        success = await AuthService.rotate_jwt_secret(new_secret)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rotate JWT secret"
            )
        
        # Add background task to invalidate existing tokens gracefully
        background_tasks.add_task(handle_jwt_secret_rotation)
        
        return {
            "message": "JWT secret rotated successfully",
            "warning": "Existing tokens will remain valid until expiry. Consider implementing graceful token invalidation."
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate JWT secret: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_vault_cache(
    current_user: User = Depends(RequireAdminRole)
):
    """Clear the vault cache to force refresh from OCI Vault"""
    try:
        vault_service.clear_cache()
        return {"message": "Vault cache cleared successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


# Background task functions
async def notify_secret_rotation(secret_name: str):
    """Notify services about secret rotation"""
    # This would implement logic to notify relevant services
    # For example, restarting pods that use the rotated secret
    print(f"Secret '{secret_name}' rotated - notifying dependent services")


async def notify_api_key_rotation(service_name: str):
    """Notify a specific service about API key rotation"""
    print(f"API key for '{service_name}' rotated - service should refresh")


async def handle_jwt_secret_rotation():
    """Handle JWT secret rotation implications"""
    # This would implement logic for graceful JWT token invalidation
    # For example, maintaining a blacklist of old tokens
    print("JWT secret rotated - implementing graceful token transition")


# Health check endpoint
@router.get("/health")
async def vault_health_check():
    """Check vault service health"""
    try:
        # Test vault connectivity
        if settings.OCI_VAULT_ENABLED:
            # Try to list secrets (without returning data)
            secrets = await vault_service.list_secrets()
            vault_accessible = True
            secret_count = len(secrets)
        else:
            vault_accessible = False
            secret_count = 0
        
        cache_stats = vault_service.get_cache_stats()
        
        return {
            "status": "healthy" if vault_accessible or not settings.OCI_VAULT_ENABLED else "degraded",
            "vault_enabled": settings.OCI_VAULT_ENABLED,
            "vault_accessible": vault_accessible,
            "secret_count": secret_count,
            "cache_stats": cache_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 