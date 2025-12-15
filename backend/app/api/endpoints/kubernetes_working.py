"""
Working Kubernetes API endpoints using the proven working service
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging
import asyncio

from app.services.kubernetes_service_working import get_working_kubernetes_service
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.permissions import check_user_permissions

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class KubeConfigRequest(BaseModel):
    kubeconfig_content: str = Field(..., description="Kubeconfig file content as string")
    cluster_name: str = Field(default="default", description="Name to identify this cluster")

class ClusterInfoResponse(BaseModel):
    name: str
    server: str
    version: str
    namespace_count: int
    pod_count: int
    node_count: int
    healthy: bool

@router.get("/health")
async def kubernetes_health():
    """Health check for working Kubernetes service"""
    try:
        loop = asyncio.get_event_loop()
        health_result = await asyncio.wait_for(
            loop.run_in_executor(None, get_working_kubernetes_service().health_check),
            timeout=5.0
        )
        return health_result
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "message": "Health check timed out",
            "clusters_configured": 0
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "message": str(e),
            "clusters_configured": 0
        }

# Cluster configuration endpoint
@router.post("/configure-cluster")
async def configure_cluster(
    request: KubeConfigRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Configure Kubernetes cluster connection with kubeconfig using working service"""
    # Check permissions - only admins can configure clusters
    check_user_permissions(current_user, can_manage_roles=True)
    
    try:
        logger.info(f"Configuring cluster: {request.cluster_name}")
        
        # Run synchronous cluster configuration in executor with timeout
        loop = asyncio.get_event_loop()
        
        success = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: get_working_kubernetes_service().configure_cluster(
                    kubeconfig_content=request.kubeconfig_content,
                    cluster_name=request.cluster_name
                )
            ),
            timeout=15.0  # 15 second timeout
        )
        
        if success:
            # Get cluster info with timeout
            cluster_info = await asyncio.wait_for(
                loop.run_in_executor(None, get_working_kubernetes_service().get_cluster_info),
                timeout=10.0  # 10 second timeout
            )
            
            logger.info(f"Successfully configured cluster: {request.cluster_name}")
            return {
                "message": f"Successfully connected to cluster: {request.cluster_name}",
                "cluster_name": cluster_info.name,
                "status": "configured",
                "cluster_info": {
                    "version": cluster_info.version,
                    "namespaces": cluster_info.namespace_count,
                    "pods": cluster_info.pod_count,
                    "nodes": cluster_info.node_count
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to configure cluster"
            )
            
    except asyncio.TimeoutError:
        logger.error("Cluster configuration timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Cluster configuration timed out"
        )
    except Exception as e:
        logger.error(f"Cluster configuration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cluster connection failed: {str(e)}"
        )

@router.get("/cluster-info", response_model=ClusterInfoResponse)
async def get_cluster_info(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get information about the configured cluster"""
    try:
        if not get_working_kubernetes_service().is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cluster configured"
            )
        
        # Get cluster info with timeout
        loop = asyncio.get_event_loop()
        cluster_info = await asyncio.wait_for(
            loop.run_in_executor(None, get_working_kubernetes_service().get_cluster_info),
            timeout=10.0
        )
        
        return cluster_info
        
    except asyncio.TimeoutError:
        logger.error("Get cluster info timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Cluster info request timed out"
        )
    except Exception as e:
        logger.error(f"Failed to get cluster info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cluster information: {str(e)}"
        )

@router.get("/namespaces")
async def get_namespaces(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all namespaces in the configured cluster"""
    try:
        if not get_working_kubernetes_service().is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cluster configured"
            )
        
        loop = asyncio.get_event_loop()
        namespaces = await asyncio.wait_for(
            loop.run_in_executor(None, get_working_kubernetes_service().get_namespaces),
            timeout=10.0
        )
        
        return {"namespaces": namespaces}
        
    except asyncio.TimeoutError:
        logger.error("Get namespaces timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Get namespaces request timed out"
        )
    except Exception as e:
        logger.error(f"Failed to get namespaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get namespaces: {str(e)}"
        )

@router.get("/pods")
async def get_pods(
    namespace: Optional[str] = Query(None, description="Namespace to filter pods"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get pods in the cluster"""
    try:
        if not get_working_kubernetes_service().is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cluster configured"
            )
        
        loop = asyncio.get_event_loop()
        pods = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: get_working_kubernetes_service().get_pods(namespace)
            ),
            timeout=15.0
        )
        
        return {"pods": [pod.__dict__ for pod in pods]}
        
    except asyncio.TimeoutError:
        logger.error("Get pods timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Get pods request timed out"
        )
    except Exception as e:
        logger.error(f"Failed to get pods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pods: {str(e)}"
        )

@router.get("/pods/{namespace}/{pod_name}/logs")
async def get_pod_logs(
    namespace: str,
    pod_name: str,
    container: Optional[str] = Query(None, description="Container name"),
    lines: int = Query(100, description="Number of log lines to retrieve"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get logs from a specific pod"""
    try:
        if not get_working_kubernetes_service().is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cluster configured"
            )
        
        loop = asyncio.get_event_loop()
        logs = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: get_working_kubernetes_service().get_pod_logs(
                    pod_name=pod_name,
                    namespace=namespace,
                    container=container,
                    lines=lines
                )
            ),
            timeout=15.0
        )
        
        return {
            "logs": logs,
            "pod_name": pod_name,
            "namespace": namespace,
            "container": container,
            "lines": lines
        }
        
    except asyncio.TimeoutError:
        logger.error("Get pod logs timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Get pod logs request timed out"
        )
    except Exception as e:
        logger.error(f"Failed to get pod logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pod logs: {str(e)}"
        )

@router.get("/rbac/roles")
async def get_rbac_roles(
    namespace: Optional[str] = Query(None, description="Namespace to filter roles"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get RBAC roles"""
    try:
        if not get_working_kubernetes_service().is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cluster configured"
            )
        
        loop = asyncio.get_event_loop()
        roles = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: get_working_kubernetes_service().get_rbac_roles(namespace)
            ),
            timeout=15.0
        )
        
        return {"roles": [role.__dict__ for role in roles]}
        
    except asyncio.TimeoutError:
        logger.error("Get RBAC roles timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Get RBAC roles request timed out"
        )
    except Exception as e:
        logger.error(f"Failed to get RBAC roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RBAC roles: {str(e)}"
        )

@router.get("/rbac/bindings")
async def get_rbac_bindings(
    namespace: Optional[str] = Query(None, description="Namespace to filter bindings"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get RBAC bindings"""
    try:
        if not get_working_kubernetes_service().is_configured:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cluster configured"
            )
        
        loop = asyncio.get_event_loop()
        bindings = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: get_working_kubernetes_service().get_rbac_bindings(namespace)
            ),
            timeout=15.0
        )
        
        return {"bindings": [binding.__dict__ for binding in bindings]}
        
    except asyncio.TimeoutError:
        logger.error("Get RBAC bindings timed out")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Get RBAC bindings request timed out"
        )
    except Exception as e:
        logger.error(f"Failed to get RBAC bindings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RBAC bindings: {str(e)}"
        ) 