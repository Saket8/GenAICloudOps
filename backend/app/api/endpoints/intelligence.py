"""
Intelligence API Endpoints

Provides multi-dimensional analytics for cloud resources,
combining data from multiple OCI APIs for insights not
available in OCI Console.
"""
import logging
from fastapi import APIRouter, Query, Path, Depends, HTTPException
from typing import Optional

from app.core.permissions import require_permissions
from app.services.intelligence_service import get_intelligence_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/health-matrix")
async def get_health_matrix(
    compartment_id: str = Query(..., description="OCI Compartment OCID"),
    _: dict = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get resource health matrix for visualization.
    
    Returns a grid of all resources with composite health scores
    calculated from multiple data sources (state, cost, backup, activity).
    
    Health Score: 0-10
    - 8-10: Healthy (green)
    - 5-7: Warning (yellow)  
    - 0-4: Critical (red)
    """
    try:
        service = get_intelligence_service()
        matrix = await service.get_health_matrix(compartment_id)
        return service.matrix_to_dict(matrix)
    
    except Exception as e:
        logger.error(f"Failed to get health matrix: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to compute health matrix: {str(e)}"
        )


@router.get("/resource/{resource_id}/health")
async def get_resource_health(
    resource_id: str = Path(..., description="OCI Resource OCID"),
    compartment_id: str = Query(..., description="OCI Compartment OCID"),
    _: dict = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get detailed health information for a specific resource.
    
    Returns the health score breakdown with:
    - List of issues affecting the score
    - Recommendations for each issue
    - Estimated cost impact
    """
    try:
        service = get_intelligence_service()
        health = service.get_resource_health_details(resource_id, compartment_id)
        
        if health is None:
            # Try to recompute matrix
            await service.get_health_matrix(compartment_id)
            health = service.get_resource_health_details(resource_id, compartment_id)
        
        if health is None:
            raise HTTPException(
                status_code=404,
                detail=f"Resource not found: {resource_id}"
            )
        
        return service.to_dict(health)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resource health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to get resource health: {str(e)}"
        )


@router.get("/summary")
async def get_intelligence_summary(
    compartment_id: str = Query(..., description="OCI Compartment OCID"),
    _: dict = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get quick summary of intelligence metrics.
    
    Returns counts and totals without full resource details.
    Useful for dashboard widgets.
    """
    try:
        service = get_intelligence_service()
        matrix = await service.get_health_matrix(compartment_id)
        
        return {
            'compartment_id': compartment_id,
            'timestamp': matrix.timestamp.isoformat(),
            'total_resources': matrix.total_resources,
            'healthy_count': matrix.healthy_count,
            'warning_count': matrix.warning_count,
            'critical_count': matrix.critical_count,
            'total_waste': matrix.total_waste,
            'health_distribution': {
                'healthy': round(matrix.healthy_count / max(matrix.total_resources, 1) * 100, 1),
                'warning': round(matrix.warning_count / max(matrix.total_resources, 1) * 100, 1),
                'critical': round(matrix.critical_count / max(matrix.total_resources, 1) * 100, 1),
            },
            'by_type_counts': {
                rtype: len(resources)
                for rtype, resources in matrix.by_type.items()
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get intelligence summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to get intelligence summary: {str(e)}"
        )


@router.post("/refresh")
async def refresh_health_matrix(
    compartment_id: str = Query(..., description="OCI Compartment OCID"),
    _: dict = Depends(require_permissions("can_view_dashboard"))
):
    """
    Force refresh of health matrix cache.
    
    Clears cached data and recomputes health scores from fresh API data.
    """
    try:
        service = get_intelligence_service()
        
        # Clear cache for this compartment
        cache_key = service._get_cache_key('health_matrix', compartment_id)
        if cache_key in service._cache:
            del service._cache[cache_key]
        if f"{cache_key}:timestamp" in service._cache:
            del service._cache[f"{cache_key}:timestamp"]
        
        # Recompute
        matrix = await service.get_health_matrix(compartment_id)
        
        return {
            'status': 'success',
            'message': 'Health matrix refreshed',
            'total_resources': matrix.total_resources,
            'timestamp': matrix.timestamp.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to refresh health matrix: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to refresh health matrix: {str(e)}"
        )


@router.get("/top-actions")
async def get_top_actions(
    compartment_id: str = Query(..., description="OCI Compartment OCID"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of actions to return"),
    _: dict = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get prioritized list of top actions to optimize infrastructure.
    
    Returns actionable recommendations sorted by potential $ savings:
    - 🧟 Zombie resources (stopped >90 days) 
    - ⏸️ Idle resources (stopped 30-90 days)
    - 🔒 Security gaps (missing backups)
    - ⚡ Optimization opportunities
    
    Each action includes:
    - Estimated savings
    - Risk level
    - Quick action buttons
    """
    try:
        service = get_intelligence_service()
        actions = await service.generate_top_actions(compartment_id, limit)
        return actions
    
    except Exception as e:
        logger.error(f"Failed to generate top actions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate top actions: {str(e)}"
        )

