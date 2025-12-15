from fastapi import APIRouter, Depends, Query, HTTPException, Path
from typing import List, Dict, Any, Optional
from app.core.permissions import require_permissions
from app.models.user import User
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Lazy-load OCI service to avoid startup hangs
def get_oci_service():
    from app.services.cloud_service import get_oci_service as _get_service
    return _get_service()

def get_cloud_ops_service():
    from app.services.cloud_service import cloud_ops_service
    return cloud_ops_service

router = APIRouter()

# Test endpoint (no auth required)
@router.get("/test/compartments")
async def test_compartments():
    """
    Test endpoint to verify OCI connection without authentication.
    Use this to test if the backend can connect to OCI.
    """
    try:
        logger.info("🧪 Testing OCI compartments connection (no auth)")
        oci_svc = get_oci_service()
        compartments = await oci_svc.get_compartments()
        return {
            "status": "success",
            "oci_available": oci_svc.oci_available,
            "compartment_count": len(compartments),
            "compartments": compartments
        }
    except Exception as e:
        logger.error(f"❌ Test compartments failed: {e}")
        return {
            "status": "error",
            "oci_available": False,
            "error": str(e),
            "compartments": []
        }

# Response models
class CompartmentResponse(BaseModel):
    id: str
    name: str
    description: str
    lifecycle_state: str
    compartment_id: Optional[str] = None
    time_created: Optional[str] = None

class ResourceResponse(BaseModel):
    id: str
    display_name: str
    lifecycle_state: str
    resource_type: str
    compartment_id: str

class MetricsResponse(BaseModel):
    resource_id: str
    metrics: Dict[str, Any]
    timestamp: str
    health_status: str

class ResourceSummaryResponse(BaseModel):
    compartment_id: str
    resources: Dict[str, List[Dict[str, Any]]]
    total_resources: int
    last_updated: str

@router.get("/compartments", response_model=List[CompartmentResponse])
async def get_compartments(
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[CompartmentResponse]:
    """
    Get all accessible OCI compartments.
    
    **Required permissions:** viewer, operator, or admin
    
    Returns a list of compartments the user has access to view.
    """
    logger.info(f"🔍 User {current_user.username} requesting compartments")
    try:
        oci_svc = get_oci_service()
        compartments = await oci_svc.get_compartments()
        return [CompartmentResponse(**comp) for comp in compartments]
    except Exception as e:
        logger.warning(f"OCI not configured, returning mock data: {e}")
        # Return simple mock compartment when OCI is not configured
        return [
            CompartmentResponse(
                id="ocid1.compartment.oc1..demo",
                name="Demo Compartment",
                description="Demo compartment - OCI not configured",
                lifecycle_state="ACTIVE"
            )
        ]

@router.get("/compartments/{compartment_id}/resources", response_model=ResourceSummaryResponse)
async def get_compartment_resources(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    resource_types: Optional[str] = Query(None, description="Comma-separated list of resource types to filter"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> ResourceSummaryResponse:
    """
    Get all resources in a specific compartment.
    
    **Required permissions:** viewer, operator, or admin
    
    **Parameters:**
    - **compartment_id**: OCI compartment OCID
    - **resource_types**: Optional filter for specific resource types (compute,databases,oke_clusters,api_gateways,load_balancers)
    
    Returns comprehensive resource information for the specified compartment.
    """
    try:
        resource_filter = None
        if resource_types:
            resource_filter = [rt.strip() for rt in resource_types.split(",")]
        
        oci_svc = get_oci_service()
        resources = await oci_svc.get_all_resources(compartment_id, resource_filter)
        return ResourceSummaryResponse(**resources)
    except Exception as e:
        logger.error(f"Failed to get compartment resources: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve compartment resources")

@router.get("/compartments/{compartment_id}/compute-instances")
async def get_compute_instances(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get compute instances in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        instances = await oci_svc.get_compute_instances(compartment_id)
        return instances
    except Exception as e:
        logger.error(f"Failed to get compute instances: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve compute instances")

@router.get("/compartments/{compartment_id}/databases")
async def get_databases(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get database services in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        databases = await oci_svc.get_databases(compartment_id)
        return databases
    except Exception as e:
        logger.error(f"Failed to get databases: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve databases")

@router.get("/compartments/{compartment_id}/oke-clusters")
async def get_oke_clusters(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get OKE clusters in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        clusters = await oci_svc.get_oke_clusters(compartment_id)
        return clusters
    except Exception as e:
        logger.error(f"Failed to get OKE clusters: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve OKE clusters")

@router.get("/compartments/{compartment_id}/api-gateways")
async def get_api_gateways(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get API Gateways in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        gateways = await oci_svc.get_api_gateways(compartment_id)
        return gateways
    except Exception as e:
        logger.error(f"Failed to get API gateways: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve API gateways")

@router.get("/compartments/{compartment_id}/load-balancers")
async def get_load_balancers(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get load balancers in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        load_balancers = await oci_svc.get_load_balancers(compartment_id)
        return load_balancers
    except Exception as e:
        logger.error(f"Failed to get load balancers: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve load balancers")

@router.get("/compartments/{compartment_id}/network-resources")
async def get_network_resources(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get network resources (VCNs, subnets) in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        network_resources = await oci_svc.get_network_resources(compartment_id)
        return network_resources
    except Exception as e:
        logger.error(f"Failed to get network resources: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve network resources")

@router.get("/compartments/{compartment_id}/block-volumes")
async def get_block_volumes(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get block volumes in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        block_volumes = await oci_svc.get_block_volumes(compartment_id)
        return block_volumes
    except Exception as e:
        logger.error(f"Failed to get block volumes: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve block volumes")

@router.get("/compartments/{compartment_id}/file-systems")
async def get_file_systems(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get file systems in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        file_systems = await oci_svc.get_file_systems(compartment_id)
        return file_systems
    except Exception as e:
        logger.error(f"Failed to get file systems: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve file systems")

@router.get("/compartments/{compartment_id}/object-storage-buckets")
async def get_object_storage_buckets(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get Object Storage buckets in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        buckets = await oci_svc.get_object_storage_buckets(compartment_id)
        return buckets
    except Exception as e:
        logger.error(f"Failed to get Object Storage buckets: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve Object Storage buckets")

@router.get("/compartments/{compartment_id}/vaults")
async def get_vaults(
    compartment_id: str = Path(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get Vaults and their secrets in a compartment.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        oci_svc = get_oci_service()
        vaults = await oci_svc.get_vaults(compartment_id)
        return vaults
    except Exception as e:
        logger.error(f"Failed to get vaults: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve vaults")

@router.get("/resources/{resource_id}/metrics", response_model=MetricsResponse)
async def get_resource_metrics(
    resource_id: str = Path(..., description="OCI Resource ID"),
    resource_type: str = Query(..., description="Type of resource (compute_instance, database, etc.)"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> MetricsResponse:
    """
    Get real-time metrics for a specific resource.
    
    **Required permissions:** viewer, operator, or admin
    
    **Parameters:**
    - **resource_id**: OCI resource OCID
    - **resource_type**: Type of resource to get metrics for
    
    Returns CPU, memory, network metrics and health status.
    """
    try:
        oci_svc = get_oci_service()
        metrics = await oci_svc.get_resource_metrics(resource_id, resource_type)
        return MetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Failed to get resource metrics: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve resource metrics")

# Legacy endpoints for backward compatibility
@router.get("/resources")
async def get_cloud_resources(
    provider: str = Query("oci", description="Cloud provider"),
    compartment_id: Optional[str] = Query(None, description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> Dict[str, Any]:
    """
    Legacy endpoint: Get cloud resources from specified provider.
    
    **Required permissions:** viewer, operator, or admin
    
    **Note:** This endpoint is maintained for backward compatibility.
    Use the new compartment-specific endpoints for better performance.
    """
    try:
        cloud_ops_svc = get_cloud_ops_service()
        resources = await cloud_ops_svc.get_cloud_resources(provider, compartment_id)
        return resources
    except Exception as e:
        logger.error(f"Failed to get cloud resources: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve cloud resources")

@router.post("/resources/{resource_id}/actions/{action}")
async def execute_resource_action(
    resource_id: str = Path(..., description="OCI Resource ID"),
    action: str = Path(..., description="Action to execute"),
    current_user: User = Depends(require_permissions("can_execute_remediation"))
) -> Dict[str, Any]:
    """
    Execute an action on a specific resource.
    
    **Required permissions:** operator or admin
    
    **Supported actions:**
    - start: Start a stopped resource
    - stop: Stop a running resource  
    - restart: Restart a resource
    - terminate: Terminate a resource (admin only)
    
    **Note:** This is a placeholder for future implementation.
    """
    if action == "terminate" and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Terminate action requires admin role")
    
    try:
        # Placeholder implementation
        result = {
            "resource_id": resource_id,
            "action": action,
            "status": "PENDING",
            "message": f"Action '{action}' initiated for resource {resource_id}",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        logger.info(f"Resource action executed: {action} on {resource_id} by {current_user.username}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute resource action: {e}")
        raise HTTPException(status_code=500, detail="Unable to execute resource action") 


# Phase 3: Lifecycle Events Endpoint (Audit API)
class LifecycleResponse(BaseModel):
    """Response model for lifecycle events"""
    resource_id: str
    compartment_id: str
    stopped_days: Optional[int] = None
    events: List[Dict[str, Any]] = []
    last_checked: str


@router.get("/resources/{resource_id}/lifecycle", response_model=LifecycleResponse)
async def get_resource_lifecycle(
    resource_id: str = Path(..., description="OCI Resource ID"),
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get lifecycle events for a resource (stopped duration, state changes).
    
    **Required permissions:** viewer, operator, or admin
    
    Uses OCI Audit API to query lifecycle state changes and calculate
    how long the resource has been in its current state.
    
    **Parameters:**
    - **resource_id**: OCI resource OCID
    - **compartment_id**: OCI compartment OCID
    
    **Returns:**
    - lifecycle events with timestamps
    - stopped_days: number of days resource has been stopped (null if running)
    """
    try:
        oci_service = get_oci_service()
        
        # Get lifecycle events
        events = await oci_service.get_instance_lifecycle_events(
            compartment_id, resource_id
        )
        
        # Get stopped duration
        stopped_days = await oci_service.get_instance_stopped_duration(
            compartment_id, resource_id
        )
        
        from datetime import datetime
        return LifecycleResponse(
            resource_id=resource_id,
            compartment_id=compartment_id,
            stopped_days=stopped_days,
            events=events,
            last_checked=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get lifecycle events: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to get lifecycle events: {str(e)}")