from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.kubernetes_service import get_kubernetes_service, ClusterConnectionError
from app.services.kubernetes_service_working import get_working_kubernetes_service
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.permissions import require_permissions, check_user_permissions

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

class NamespaceResponse(BaseModel):
    name: str
    status: str
    created_time: str
    labels: Dict[str, str]
    annotations: Dict[str, str]

class PodResponse(BaseModel):
    name: str
    namespace: str
    status: str
    restart_count: int
    node_name: str
    created_time: str
    containers: List[Dict[str, Any]]
    labels: Dict[str, str]
    owner_references: List[Dict[str, Any]]

class RBACRoleResponse(BaseModel):
    name: str
    namespace: Optional[str]
    kind: str
    rules: List[Dict[str, Any]]
    created_time: str
    labels: Dict[str, str]

class RBACBindingResponse(BaseModel):
    name: str
    namespace: Optional[str]
    kind: str
    role_ref: Dict[str, str]
    subjects: List[Dict[str, Any]]
    created_time: str

class PodLogsResponse(BaseModel):
    pod_name: str
    namespace: str
    container: Optional[str]
    logs: str
    lines_fetched: int

# Health check endpoint (no auth required)
@router.get("/health")
async def kubernetes_health():
    """Health check for Kubernetes service - USING WORKING SERVICE"""
    try:
        health_status = get_working_kubernetes_service().health_check()
        health_status["service"] = "WorkingKubernetes"  # Mark as working service
        return health_status
    except Exception as e:
        logger.error(f"Working Kubernetes health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "clusters_configured": 0,
            "service": "WorkingKubernetes"
        }

# Reset endpoint for clearing cached configurations
@router.post("/reset")
async def reset_kubernetes_service(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Reset all cluster configurations and clear cached clients"""
    # Check permissions - only admins can reset the service
    check_user_permissions(current_user, can_manage_roles=True)
    
    try:
        kubernetes_service = get_kubernetes_service()
        kubernetes_service.reset_all_clusters()
        return {
            "message": "Kubernetes service has been reset successfully",
            "clusters_configured": 0,
            "status": "reset_complete"
        }
    except Exception as e:
        logger.error(f"Failed to reset Kubernetes service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset service: {str(e)}"
        )

# Cluster configuration endpoint
@router.post("/configure-cluster")
async def configure_cluster(
    request: KubeConfigRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Configure Kubernetes cluster connection with kubeconfig - USING WORKING SERVICE"""
    # Check permissions - only admins can configure clusters
    check_user_permissions(current_user, can_manage_roles=True)
    
    try:
        # Use the WORKING service instead of the broken one
        success = get_working_kubernetes_service().configure_cluster(
            kubeconfig_content=request.kubeconfig_content,
            cluster_name=request.cluster_name
        )
        
        if success:
            cluster_info = get_working_kubernetes_service().get_cluster_info()
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
            
    except Exception as e:
        logger.error(f"Working cluster configuration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cluster connection failed: {str(e)}"
        )

# File upload endpoint for kubeconfig
@router.post("/upload-kubeconfig")
async def upload_kubeconfig(
    cluster_name: str = Form(default="default"),
    file: UploadFile = File(...),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Upload kubeconfig file to configure cluster connection"""
    # Check permissions - only admins can configure clusters
    check_user_permissions(current_user, can_manage_roles=True)
    
    try:
        # Read file content
        content = await file.read()
        kubeconfig_content = content.decode('utf-8')
        
        kubernetes_service = get_kubernetes_service()
        success = await kubernetes_service.configure_cluster(
            kubeconfig_content=kubeconfig_content,
            cluster_name=cluster_name
        )
        
        if success:
            cluster_info = await kubernetes_service.get_cluster_info(cluster_name)
            return {
                "message": f"Successfully uploaded and connected to cluster: {cluster_name}",
                "filename": file.filename,
                "cluster_info": cluster_info.__dict__
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to configure cluster with uploaded kubeconfig"
            )
            
    except ClusterConnectionError as e:
        logger.error(f"Cluster connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cluster connection failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error uploading kubeconfig: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload error: {str(e)}"
        )

# Cluster information endpoint
@router.get("/cluster-info", response_model=ClusterInfoResponse)
async def get_cluster_info(
    cluster_name: Optional[str] = Query(None, description="Cluster name"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get cluster information"""
    try:
        kubernetes_service = get_kubernetes_service()
        cluster_info = kubernetes_service.get_cluster_info(cluster_name)
        return cluster_info
    except ClusterConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting cluster info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cluster info: {str(e)}"
        )

# Namespaces endpoint
@router.get("/namespaces", response_model=List[NamespaceResponse])
async def get_namespaces(
    cluster_name: Optional[str] = Query(None, description="Cluster name"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all namespaces in the cluster"""
    try:
        kubernetes_service = get_kubernetes_service()
        namespaces = kubernetes_service.get_namespaces(cluster_name)
        return namespaces
    except ClusterConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting namespaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get namespaces: {str(e)}"
        )

# Pods endpoint
@router.get("/pods", response_model=List[PodResponse])
async def get_pods(
    namespace: Optional[str] = Query(None, description="Namespace filter"),
    cluster_name: Optional[str] = Query(None, description="Cluster name"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get pods in specified namespace or all namespaces"""
    try:
        kubernetes_service = get_kubernetes_service()
        pods = await kubernetes_service.get_pods(namespace, cluster_name)
        
        # Convert PodInfo objects to dictionaries for response
        result = []
        for pod in pods:
            result.append({
                "name": pod.name,
                "namespace": pod.namespace,
                "status": pod.status,
                "restart_count": pod.restart_count,
                "node_name": pod.node_name,
                "created_time": pod.created_time.isoformat(),
                "containers": pod.containers,
                "labels": pod.labels,
                "owner_references": pod.owner_references
            })
        
        return result
    except ClusterConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting pods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pods: {str(e)}"
        )

# Pod logs endpoint
@router.get("/pods/{namespace}/{pod_name}/logs", response_model=PodLogsResponse)
async def get_pod_logs(
    namespace: str,
    pod_name: str,
    container: Optional[str] = Query(None, description="Container name"),
    lines: int = Query(100, ge=1, le=1000, description="Number of log lines"),
    cluster_name: Optional[str] = Query(None, description="Cluster name"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get logs for a specific pod"""
    try:
        kubernetes_service = get_kubernetes_service()
        logs = kubernetes_service.get_pod_logs(
            pod_name=pod_name,
            namespace=namespace,
            container=container,
            lines=lines,
            cluster_name=cluster_name
        )
        
        return PodLogsResponse(
            pod_name=pod_name,
            namespace=namespace,
            container=container,
            logs=logs,
            lines_fetched=len(logs.split('\n')) if logs else 0
        )
    except ClusterConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting pod logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pod logs: {str(e)}"
        )

# RBAC roles endpoint
@router.get("/rbac/roles", response_model=List[RBACRoleResponse])
async def get_rbac_roles(
    namespace: Optional[str] = Query(None, description="Namespace filter"),
    cluster_name: Optional[str] = Query(None, description="Cluster name"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get RBAC roles (both Role and ClusterRole)"""
    # Check permissions for access analyzer
    check_user_permissions(current_user, can_view_access_analyzer=True)
    
    try:
        kubernetes_service = get_kubernetes_service()
        roles = kubernetes_service.get_rbac_roles(namespace, cluster_name)
        
        # Convert RBACRole objects to dictionaries for response
        result = []
        for role in roles:
            result.append({
                "name": role.name,
                "namespace": role.namespace,
                "kind": role.kind,
                "rules": role.rules,
                "created_time": role.created_time.isoformat(),
                "labels": role.labels
            })
        
        return result
    except ClusterConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting RBAC roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RBAC roles: {str(e)}"
        )

# RBAC bindings endpoint
@router.get("/rbac/bindings", response_model=List[RBACBindingResponse])
async def get_rbac_bindings(
    namespace: Optional[str] = Query(None, description="Namespace filter"),
    cluster_name: Optional[str] = Query(None, description="Cluster name"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get RBAC role bindings (both RoleBinding and ClusterRoleBinding)"""
    # Check permissions for access analyzer
    check_user_permissions(current_user, can_view_access_analyzer=True)
    
    try:
        kubernetes_service = get_kubernetes_service()
        bindings = kubernetes_service.get_rbac_bindings(namespace, cluster_name)
        
        # Convert RBACBinding objects to dictionaries for response
        result = []
        for binding in bindings:
            result.append({
                "name": binding.name,
                "namespace": binding.namespace,
                "kind": binding.kind,
                "role_ref": binding.role_ref,
                "subjects": binding.subjects,
                "created_time": binding.created_time.isoformat()
            })
        
        return result
    except ClusterConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting RBAC bindings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RBAC bindings: {str(e)}"
        )

# Pod status summary endpoint
@router.get("/pods/status-summary")
async def get_pod_status_summary(
    namespace: Optional[str] = Query(None, description="Namespace filter"),
    cluster_name: Optional[str] = Query(None, description="Cluster name"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get summary of pod statuses for monitoring dashboard"""
    try:
        kubernetes_service = get_kubernetes_service()
        pods = kubernetes_service.get_pods(namespace, cluster_name)
        
        # Analyze pod statuses
        status_counts = {}
        problem_pods = []
        total_restarts = 0
        
        for pod in pods:
            status = pod.status
            status_counts[status] = status_counts.get(status, 0) + 1
            total_restarts += pod.restart_count
            
            # Identify problem pods
            if (status not in ['Running', 'Succeeded'] or 
                pod.restart_count > 5):
                problem_pods.append({
                    'name': pod.name,
                    'namespace': pod.namespace,
                    'status': pod.status,
                    'restart_count': pod.restart_count,
                    'node_name': pod.node_name
                })
        
        return {
            "total_pods": len(pods),
            "status_counts": status_counts,
            "total_restarts": total_restarts,
            "problem_pods": problem_pods[:10],  # Limit to top 10 problem pods
            "healthy_percentage": round(
                (status_counts.get('Running', 0) / max(len(pods), 1)) * 100, 2
            )
        }
    except ClusterConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting pod status summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pod status summary: {str(e)}"
        )

# ===== WORKING K8S ENDPOINTS (alternative to separate module) =====

@router.get("/working/health")
async def working_kubernetes_health():
    """Health check for working Kubernetes service"""
    try:
        health_status = get_working_kubernetes_service().health_check()
        return health_status
    except Exception as e:
        logger.error(f"Working Kubernetes health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "clusters_configured": 0
        }

@router.post("/working/configure-cluster")
async def working_configure_cluster(
    request: KubeConfigRequest,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Configure Kubernetes cluster using working service"""
    check_user_permissions(current_user, can_manage_roles=True)
    
    try:
        success = get_working_kubernetes_service().configure_cluster(
            kubeconfig_content=request.kubeconfig_content,
            cluster_name=request.cluster_name
        )
        
        if success:
            cluster_info = get_working_kubernetes_service().get_cluster_info()
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
            
    except Exception as e:
        logger.error(f"Working cluster configuration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cluster connection failed: {str(e)}"
        )

@router.get("/working/cluster-info")
async def working_get_cluster_info(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get cluster information using working service"""
    try:
        cluster_info = get_working_kubernetes_service().get_cluster_info()
        return {
            "name": cluster_info.name,
            "server": cluster_info.server,
            "version": cluster_info.version,
            "namespace_count": cluster_info.namespace_count,
            "pod_count": cluster_info.pod_count,
            "node_count": cluster_info.node_count,
            "healthy": cluster_info.healthy
        }
    except Exception as e:
        logger.error(f"Failed to get working cluster info: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get cluster info: {str(e)}"
        )

@router.get("/working/pods")
async def working_get_pods(
    namespace: Optional[str] = Query(None, description="Namespace to filter pods"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get pods using working service"""
    try:
        pods = get_working_kubernetes_service().get_pods(namespace)
        
        result = []
        for pod in pods:
            result.append({
                "name": pod.name,
                "namespace": pod.namespace,
                "status": pod.status,
                "node_name": pod.node_name,
                "restart_count": pod.restart_count,
                "age": pod.age,
                "ready": pod.ready
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to get working pods: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get pods: {str(e)}"
        )

@router.get("/working/rbac/roles")
async def working_get_rbac_roles(
    namespace: Optional[str] = Query(None, description="Namespace to filter roles"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get RBAC roles using working service"""
    check_user_permissions(current_user, can_view_access_analyzer=True)
    
    try:
        roles = get_working_kubernetes_service().get_rbac_roles(namespace)
        
        result = []
        for role in roles:
            result.append({
                "name": role.name,
                "namespace": role.namespace,
                "kind": role.kind,
                "rules": role.rules,
                "created_time": role.created_time,
                "labels": role.labels
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to get working RBAC roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get RBAC roles: {str(e)}"
        )

@router.get("/working/rbac/bindings")
async def working_get_rbac_bindings(
    namespace: Optional[str] = Query(None, description="Namespace to filter bindings"),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get RBAC bindings using working service"""
    check_user_permissions(current_user, can_view_access_analyzer=True)
    
    try:
        bindings = get_working_kubernetes_service().get_rbac_bindings(namespace)
        
        result = []
        for binding in bindings:
            result.append({
                "name": binding.name,
                "namespace": binding.namespace,
                "kind": binding.kind,
                "role_ref": binding.role_ref,
                "subjects": binding.subjects,
                "created_time": binding.created_time
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to get working RBAC bindings: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get RBAC bindings: {str(e)}"
        ) 