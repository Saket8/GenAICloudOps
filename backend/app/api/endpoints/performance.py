from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import logging
from app.services.performance_service import performance_service
from app.services.cache_service import cache_service
from app.api.endpoints.auth import get_current_user
from app.core.permissions import RequireAdminRole, RequireOperatorRole
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/system/metrics", tags=["performance"])
async def get_system_metrics(
    current_user: User = Depends(RequireAdminRole)
) -> Dict[str, Any]:
    """Get current system performance metrics"""
    try:
        # Require admin role for system metrics
        _ = current_user  # already validated by dependency

        
        metrics = performance_service.system_monitor.get_system_metrics()
        process_metrics = await performance_service.system_monitor.get_process_metrics()
        
        return {
            "success": True,
            "data": {
                "system": metrics,
                "process": process_metrics,
                "timestamp": performance_service.system_monitor.get_system_metrics().get("timestamp")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )

@router.get("/summary", tags=["performance"])
async def get_performance_summary(
    current_user: User = Depends(RequireOperatorRole)
) -> Dict[str, Any]:
    """Get comprehensive performance summary"""
    try:
        # Require admin or operator role
        require_role(current_user, ["Admin", "Operator"])
        
        summary = await performance_service.get_performance_summary()
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance summary: {str(e)}"
        )

@router.get("/cache/stats", tags=["performance"])
async def get_cache_stats(
    current_user: User = Depends(RequireOperatorRole)
) -> Dict[str, Any]:
    """Get cache performance statistics"""
    try:
        # Require admin or operator role
        require_role(current_user, ["Admin", "Operator"])
        
        stats = cache_service.get_stats()
        health = await cache_service.health_check()
        
        return {
            "success": True,
            "data": {
                "statistics": stats,
                "health": health
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )

@router.get("/database/optimization", tags=["performance"])
async def get_database_optimization(
    current_user: User = Depends(RequireAdminRole)
) -> Dict[str, Any]:
    """Get database optimization suggestions"""
    try:
        # Require admin role for database optimization
        require_role(current_user, ["Admin"])
        
        optimization = await performance_service.db_optimizer.optimize_database_indexes()
        slow_queries = await performance_service.db_optimizer.analyze_slow_queries()
        pool_stats = await performance_service.db_optimizer.get_connection_pool_stats()
        
        return {
            "success": True,
            "data": {
                "optimization_suggestions": optimization,
                "slow_queries": slow_queries,
                "connection_pool": pool_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting database optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database optimization: {str(e)}"
        )

@router.get("/health", tags=["performance"])
async def get_performance_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get performance health status"""
    try:
        # Allow all authenticated users to check performance health
        
        # Get health information
        cache_health = await cache_service.health_check()
        system_metrics = performance_service.system_monitor.get_system_metrics()
        
        # Calculate overall health
        overall_status = "healthy"
        issues = []
        
        # Check cache health
        if cache_health["status"] != "healthy":
            issues.append("Cache system issues detected")
            overall_status = "warning"
        
        # Check system resources
        if system_metrics.get("cpu", {}).get("status") != "healthy":
            issues.append("High CPU usage detected")
            overall_status = "warning"
        
        if system_metrics.get("memory", {}).get("status") != "healthy":
            issues.append("High memory usage detected")
            overall_status = "warning"
        
        if system_metrics.get("disk", {}).get("status") != "healthy":
            issues.append("High disk usage detected")
            if overall_status != "critical":
                overall_status = "critical"
        
        return {
            "success": True,
            "data": {
                "status": overall_status,
                "issues": issues,
                "components": {
                    "cache": cache_health,
                    "system": {
                        "cpu_status": system_metrics.get("cpu", {}).get("status"),
                        "memory_status": system_metrics.get("memory", {}).get("status"),
                        "disk_status": system_metrics.get("disk", {}).get("status")
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance health: {str(e)}"
        )

@router.get("/report", tags=["performance"])
async def get_optimization_report(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive optimization report"""
    try:
        # Require admin role for full optimization report
        require_role(current_user, ["Admin"])
        
        report = await performance_service.get_optimization_report()
        
        return {
            "success": True,
            "data": report
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimization report: {str(e)}"
        )

@router.post("/cache/clear", tags=["performance"])
async def clear_cache(
    namespace: str = None,
    current_user: User = Depends(RequireAdminRole)
) -> Dict[str, Any]:
    """Clear cache data"""
    try:
        # Require admin role for cache management
        require_role(current_user, ["Admin"])
        
        if namespace:
            await cache_service.clear_namespace(namespace)
            message = f"Cache cleared for namespace: {namespace}"
        else:
            # Clear all performance metrics cache
            await cache_service.clear_namespace("performance")
            await cache_service.clear_namespace("rate_limit")
            await cache_service.clear_namespace("security_metrics")
            message = "Performance-related cache cleared"
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/alerts", tags=["performance"])
async def get_performance_alerts(
    current_user: User = Depends(RequireOperatorRole)
) -> Dict[str, Any]:
    """Get current performance alerts"""
    try:
        # Require admin or operator role
        require_role(current_user, ["Admin", "Operator"])
        
        system_metrics = performance_service.system_monitor.get_system_metrics()
        process_metrics = await performance_service.system_monitor.get_process_metrics()
        
        alerts = performance_service._check_performance_alerts(system_metrics, process_metrics)
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "alert_count": len(alerts)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance alerts: {str(e)}"
        ) 