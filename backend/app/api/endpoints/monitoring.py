from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.permissions import require_permissions
from app.models.user import User
from app.services.monitoring_service import get_monitoring_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class AlertSummaryResponse(BaseModel):
    compartment_id: str
    total_alarms: int
    active_alarms: int
    severity_breakdown: Dict[str, int]
    recent_activity: Dict[str, Any]
    top_alerts: List[Dict[str, Any]]
    timestamp: str
    health_score: float

class MetricsRequest(BaseModel):
    namespace: str
    metric_name: str
    start_time: datetime
    end_time: datetime
    resource_group: Optional[str] = None

class LogSearchRequest(BaseModel):
    search_query: str
    start_time: datetime
    end_time: datetime
    limit: Optional[int] = 1000

# Monitoring Endpoints
@router.get("/alerts/summary")
async def get_alert_summary(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> AlertSummaryResponse:
    """
    Get comprehensive alert summary for a compartment.
    
    **Required permissions:** viewer or higher
    
    Returns alert counts by severity, recent activity, and health score.
    """
    try:
        logger.info(f"Getting alert summary for compartment {compartment_id} by user {current_user.username}")
        
        summary = await get_monitoring_service().get_alert_summary(compartment_id)
        return AlertSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Failed to get alert summary: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve alert summary")

@router.get("/alarms")
async def get_alarms(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> List[Dict[str, Any]]:
    """
    Get current alarm status from OCI Monitoring.
    
    **Required permissions:** viewer or higher
    
    Returns list of active alarms with their configuration and status.
    """
    try:
        logger.info(f"Getting alarms for compartment {compartment_id}")
        
        alarms = await get_monitoring_service().get_alarm_status(compartment_id)
        return alarms
        
    except Exception as e:
        logger.error(f"Failed to get alarms: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve alarms")

@router.get("/alarms/history")
async def get_alarm_history(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    hours_back: int = Query(24, description="Hours of history to retrieve", ge=1, le=168),
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> List[Dict[str, Any]]:
    """
    Get alarm history from OCI Monitoring.
    
    **Required permissions:** viewer or higher
    
    Returns alarm status changes over the specified time period.
    """
    try:
        logger.info(f"Getting alarm history for compartment {compartment_id}, {hours_back} hours back")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        history = await get_monitoring_service().get_alarm_history(compartment_id, start_time, end_time)
        return history
        
    except Exception as e:
        logger.error(f"Failed to get alarm history: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve alarm history")

@router.post("/metrics")
async def get_metrics_data(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    metrics_request: MetricsRequest = None,
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> Dict[str, Any]:
    """
    Get metrics data from OCI Monitoring.
    
    **Required permissions:** viewer or higher
    
    Returns time-series metrics data for the specified metric and time range.
    """
    try:
        logger.info(f"Getting metrics data for {metrics_request.namespace}.{metrics_request.metric_name}")
        
        metrics_data = await get_monitoring_service().get_metrics_data(
            compartment_id=compartment_id,
            namespace=metrics_request.namespace,
            metric_name=metrics_request.metric_name,
            start_time=metrics_request.start_time,
            end_time=metrics_request.end_time,
            resource_group=metrics_request.resource_group
        )
        
        return metrics_data
        
    except Exception as e:
        logger.error(f"Failed to get metrics data: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve metrics data")

@router.get("/metrics/namespaces")
async def get_metric_namespaces(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> List[str]:
    """
    Get available metric namespaces for the compartment.
    
    **Required permissions:** viewer or higher
    """
    try:
        # Return common OCI metric namespaces
        namespaces = [
            "oci_computeagent",
            "oci_database",
            "oci_lbaas",
            "oci_apigateway",
            "oci_containerengine",
            "oci_autonomous_database",
            "oci_objectstorage",
            "oci_network_load_balancer"
        ]
        
        return namespaces
        
    except Exception as e:
        logger.error(f"Failed to get metric namespaces: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve metric namespaces")

@router.post("/logs/search")
async def search_logs(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    log_request: LogSearchRequest = None,
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> List[Dict[str, Any]]:
    """
    Search logs using OCI Log Search API.
    
    **Required permissions:** viewer or higher
    
    Returns log entries matching the search criteria.
    """
    try:
        logger.info(f"Searching logs for compartment {compartment_id}")
        
        logs = await get_monitoring_service().search_logs(
            compartment_id=compartment_id,
            search_query=log_request.search_query,
            start_time=log_request.start_time,
            end_time=log_request.end_time,
            limit=log_request.limit
        )
        
        return logs
        
    except Exception as e:
        logger.error(f"Failed to search logs: {e}")
        raise HTTPException(status_code=500, detail="Unable to search logs")

@router.get("/health")
async def get_monitoring_health(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> Dict[str, Any]:
    """
    Get overall monitoring health status for a compartment.
    
    **Required permissions:** viewer or higher
    
    Returns aggregated health metrics and status indicators.
    """
    try:
        logger.info(f"Getting monitoring health for compartment {compartment_id}")
        
        # Get alert summary to calculate health
        summary = await get_monitoring_service().get_alert_summary(compartment_id)
        
        # Determine overall health status
        health_score = summary.get("health_score", 0)
        if health_score >= 90:
            status = "HEALTHY"
            status_color = "green"
        elif health_score >= 70:
            status = "WARNING"
            status_color = "yellow"
        elif health_score >= 50:
            status = "DEGRADED"
            status_color = "orange"
        else:
            status = "CRITICAL"
            status_color = "red"
        
        health_data = {
            "compartment_id": compartment_id,
            "overall_status": status,
            "status_color": status_color,
            "health_score": health_score,
            "critical_alerts": summary.get("severity_breakdown", {}).get("CRITICAL", 0),
            "high_alerts": summary.get("severity_breakdown", {}).get("HIGH", 0),
            "total_active_alarms": summary.get("active_alarms", 0),
            "alert_rate_24h": summary.get("recent_activity", {}).get("alert_rate", 0),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to get monitoring health: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve monitoring health")

@router.get("/dashboard")
async def get_monitoring_dashboard(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    current_user: User = Depends(require_permissions("can_view_alerts"))
) -> Dict[str, Any]:
    """
    Get comprehensive monitoring dashboard data.
    
    **Required permissions:** viewer or higher
    
    Returns all monitoring data needed for the dashboard view.
    """
    try:
        logger.info(f"Getting monitoring dashboard for compartment {compartment_id}")
        
        # Get all monitoring data in parallel
        import asyncio
        
        # Create tasks for parallel execution
        tasks = []
        tasks.append(get_monitoring_service().get_alert_summary(compartment_id))
        tasks.append(get_monitoring_service().get_alarm_status(compartment_id))
        
        # Get recent alarm history (last 24 hours)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        tasks.append(get_monitoring_service().get_alarm_history(compartment_id, start_time, end_time))
        
        # Execute all tasks
        summary, alarms, history = await asyncio.gather(*tasks)
        
        # Build dashboard response
        dashboard = {
            "compartment_id": compartment_id,
            "summary": summary,
            "active_alarms": alarms[:10],  # Top 10 alarms
            "recent_history": history[:50],  # Last 50 history entries
            "trends": {
                "total_alarms_trend": len(alarms),
                "critical_alerts_trend": summary.get("severity_breakdown", {}).get("CRITICAL", 0),
                "health_score_trend": summary.get("health_score", 0)
            },
            "quick_stats": {
                "uptime_score": min(100, summary.get("health_score", 0) + 10),
                "performance_score": summary.get("health_score", 0),
                "security_alerts": sum([
                    summary.get("severity_breakdown", {}).get("CRITICAL", 0),
                    summary.get("severity_breakdown", {}).get("HIGH", 0)
                ])
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve monitoring dashboard")

# Test endpoint (no auth required for development)
@router.get("/test")
async def test_monitoring_integration():
    """
    Test endpoint to verify monitoring service integration.
    Use this to test if monitoring APIs are working.
    """
    try:
        logger.info("🧪 Testing monitoring integration")
        
        # Test with a mock compartment (use same format as UI for consistency)
        test_compartment = "test-compartment"
        
        # Note: Cache clearing now handled via cache_service async API if needed
        
        # Test basic monitoring service
        summary = await get_monitoring_service().get_alert_summary(test_compartment)
        
        logger.info(f"Test result - Health Score: {summary.get('health_score', 'N/A')}, "
                   f"Critical: {summary.get('severity_breakdown', {}).get('CRITICAL', 0)}, "
                   f"High: {summary.get('severity_breakdown', {}).get('HIGH', 0)}")
        
        return {
            "status": "success",
            "monitoring_available": True,
            "test_summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Monitoring test failed: {e}")
        return {
            "status": "error",
            "monitoring_available": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Alert Management Endpoints
class AlertResolveRequest(BaseModel):
    resolution: str

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, current_user: User = Depends(require_permissions("can_execute_remediation"))) -> Dict[str, str]:
    """Acknowledge an alert/alarm. Required permissions: operator or higher"""
    try:
        logger.info(f"Acknowledging alert {alert_id} by user {current_user.username}")
        
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_by": current_user.username,
            "acknowledged_at": datetime.utcnow().isoformat(),
            "message": "Alert acknowledged successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to acknowledge alert")

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, request: AlertResolveRequest, current_user: User = Depends(require_permissions("can_execute_remediation"))) -> Dict[str, str]:
    """Resolve an alert/alarm. Required permissions: operator or higher"""
    try:
        logger.info(f"Resolving alert {alert_id} by user {current_user.username}")
        
        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_by": current_user.username,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution": request.resolution,
            "message": "Alert resolved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to resolve alert") 