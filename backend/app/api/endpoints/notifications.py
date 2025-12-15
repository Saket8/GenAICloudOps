from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.permissions import require_permissions
from app.core.exceptions import ExternalServiceError
from app.models.user import User
from app.services.monitoring_service import get_monitoring_service

# Lazy-load OCI service to avoid startup hangs
def get_oci_service():
    from app.services.cloud_service import oci_service
    return oci_service

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

@router.get("/real-time")
async def get_real_time_notifications(
    compartment_id: str = Query(..., description="OCI Compartment ID"),
    severity_filter: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    hours_back: int = Query(24, description="Hours of history to retrieve", ge=1, le=168),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> List[Dict[str, Any]]:
    """
    Get real-time notifications from OCI monitoring and alarms.
    
    **Required permissions:** viewer, operator, or admin
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get active alarms (these become notifications)
        alarms = await get_monitoring_service().get_alarm_status(compartment_id)
        
        # Get alarm history for recent triggered alerts
        alarm_history = await get_monitoring_service().get_alarm_history(compartment_id, start_time, end_time)
        
        notifications = []
        
        # Convert active alarms to notifications
        for alarm in alarms:
            if alarm.get('is_enabled', False):
                severity = alarm.get('severity', 'MEDIUM').upper()
                
                # Apply severity filter if specified
                if severity_filter and severity != severity_filter.upper():
                    continue
                
                # Extract resource information from query
                query = alarm.get('query', '')
                resource_info = _extract_resource_from_query(query)
                service_type = _get_service_type_from_namespace(alarm.get('namespace', ''))
                
                # Create detailed message with resource context
                detailed_message = _create_detailed_alarm_message(alarm, resource_info, service_type)
                    
                notification = {
                    "id": f"alarm_{alarm['id']}",
                    "type": _map_severity_to_type(severity),
                    "title": f"{severity} Alert: {alarm.get('display_name', 'OCI Alarm')}",
                    "message": detailed_message,
                    "timestamp": alarm.get('time_updated', alarm.get('time_created', datetime.utcnow().isoformat())),
                    "read": False,
                    "actionable": True,
                    "resourceType": "monitoring",
                    "severity": severity,
                    "alarm_id": alarm['id'],
                    "compartment_id": compartment_id,
                    "query": query,
                    "namespace": alarm.get('namespace', ''),
                    "lifecycle_state": alarm.get('lifecycle_state', 'UNKNOWN'),
                    "resource_info": resource_info,
                    "service_type": service_type
                }
                notifications.append(notification)
        
        # Convert recent alarm history to notifications (recent triggers)
        for event in alarm_history:
            notification = {
                "id": f"history_{event.get('alarm_id', 'unknown')}_{event.get('timestamp', '')}",
                "type": _map_severity_to_type(event.get('severity', 'MEDIUM')),
                "title": f"Alarm Triggered: {event.get('alarm_name', 'Unknown')}",
                "message": event.get('summary', 'Monitoring alarm was triggered'),
                "timestamp": event.get('timestamp', datetime.utcnow().isoformat()),
                "read": False,
                "actionable": True,
                "resourceType": "monitoring",
                "severity": event.get('severity', 'MEDIUM'),
                "alarm_id": event.get('alarm_id'),
                "compartment_id": compartment_id,
                "status": event.get('status', 'UNKNOWN')
            }
            notifications.append(notification)
        
        # Sort by timestamp (newest first)
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"Retrieved {len(notifications)} real-time notifications for compartment {compartment_id}")
        return notifications
        
    except Exception as e:
        logger.error(f"Failed to get real-time notifications: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve real-time notifications")

@router.post("/system")
async def create_system_notification(
    notification_data: Dict[str, Any],
    current_user: User = Depends(require_permissions("can_execute_remediation"))
) -> Dict[str, str]:
    """
    Create a system notification (for deployment events, errors, etc.)
    
    **Required permissions:** operator or admin
    """
    try:
        # Validate required fields
        required_fields = ['type', 'title', 'message']
        for field in required_fields:
            if field not in notification_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create system notification
        system_notification = {
            "id": f"system_{int(datetime.utcnow().timestamp())}_{current_user.id}",
            "type": notification_data['type'],  # success, error, warning, info
            "title": notification_data['title'],
            "message": notification_data['message'],
            "timestamp": datetime.utcnow().isoformat(),
            "read": False,
            "actionable": notification_data.get('actionable', False),
            "resourceType": notification_data.get('resourceType', 'system'),
            "resourceId": notification_data.get('resourceId'),
            "created_by": current_user.username,
            "severity": notification_data.get('severity', 'MEDIUM')
        }
        
        # Here you would typically:
        # 1. Store in database
        # 2. Send via WebSocket to connected clients
        # 3. Send to external notification systems
        
        logger.info(f"System notification created by {current_user.username}: {notification_data['title']}")
        
        return {
            "status": "success",
            "notification_id": system_notification["id"],
            "message": "System notification created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create system notification: {e}")
        raise HTTPException(status_code=500, detail="Unable to create system notification")

@router.get("/health")
async def get_notification_health(
    current_user: User = Depends(require_permissions("can_view_dashboard"))
) -> Dict[str, Any]:
    """
    Get notification system health status
    """
    try:
        oci_service = get_oci_service()
        
        health_status = {
            "oci_monitoring_available": oci_service.oci_available and 'monitoring' in oci_service.clients,
            "last_check": datetime.utcnow().isoformat(),
            "status": "healthy" if oci_service.oci_available else "degraded",
            "capabilities": {
                "real_time_alarms": oci_service.oci_available and 'monitoring' in oci_service.clients,
                "system_notifications": True,
                "alarm_history": oci_service.oci_available and 'monitoring' in oci_service.clients,
                "metrics_integration": oci_service.oci_available and 'monitoring' in oci_service.clients
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to get notification health: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve notification health status")

def _extract_resource_from_query(query: str) -> str:
    """Extract resource information from OCI monitoring query"""
    if not query:
        return "Unknown Resource"
    
    # Try to extract resource name from OCI monitoring query
    import re
    
    # Look for resourceDisplayName
    resource_matches = re.search(r'resourceDisplayName\s*=\s*"([^"]+)"', query)
    if resource_matches:
        return resource_matches.group(1)
    
    # Look for resourceId
    id_matches = re.search(r'resourceId\s*=\s*"([^"]+)"', query)
    if id_matches:
        resource_id = id_matches.group(1)
        # Extract readable part from OCID
        if 'instance.' in resource_id:
            return f"Instance {resource_id.split('.')[-1][:8]}..."
        elif 'database.' in resource_id:
            return f"Database {resource_id.split('.')[-1][:8]}..."
        return f"Resource {resource_id.split('.')[-1][:8]}..."
    
    # Extract metric name as fallback
    metric_matches = re.search(r'(\w+)\[', query)
    if metric_matches:
        metric_name = metric_matches.group(1)
        return f"{metric_name} metrics"
    
    return "OCI Resource"

def _get_service_type_from_namespace(namespace: str) -> str:
    """Get human-readable service type from OCI namespace"""
    if not namespace:
        return "Unknown Service"
    
    namespace_lower = namespace.lower()
    if 'computeagent' in namespace_lower or 'compute' in namespace_lower:
        return "Compute Instance"
    elif 'database' in namespace_lower:
        return "Database Service"
    elif 'network' in namespace_lower or 'vcn' in namespace_lower:
        return "Network Service"
    elif 'storage' in namespace_lower or 'block' in namespace_lower:
        return "Storage Service"
    elif 'loadbalancer' in namespace_lower:
        return "Load Balancer"
    elif 'functions' in namespace_lower:
        return "Functions Service"
    elif 'kubernetes' in namespace_lower or 'oke' in namespace_lower:
        return "Kubernetes Service"
    else:
        return f"OCI {namespace.replace('oci_', '').title()}"

def _create_detailed_alarm_message(alarm: dict, resource_info: str, service_type: str) -> str:
    """Create detailed alarm message with resource context"""
    query = alarm.get('query', '')
    namespace = alarm.get('namespace', 'Unknown')
    
    # Extract threshold from query if possible
    threshold_info = ""
    import re
    
    # Look for threshold values in query
    threshold_matches = re.search(r'[><=]+\s*(\d+(?:\.\d+)?)', query)
    if threshold_matches:
        threshold_value = threshold_matches.group(1)
        
        # Determine metric type
        if 'cpu' in query.lower() or 'utilization' in query.lower():
            threshold_info = f" (threshold: {threshold_value}%)"
        elif 'memory' in query.lower():
            threshold_info = f" (threshold: {threshold_value}%)"
        elif 'connection' in query.lower():
            threshold_info = f" (threshold: {threshold_value} connections)"
        else:
            threshold_info = f" (threshold: {threshold_value})"
    
    return f"{service_type} '{resource_info}' has triggered monitoring alert{threshold_info}. Service: {namespace}"

def _map_severity_to_type(severity: str) -> str:
    """Map OCI alarm severity to notification type"""
    severity_map = {
        'CRITICAL': 'error',
        'HIGH': 'error', 
        'MEDIUM': 'warning',
        'LOW': 'info'
    }
    return severity_map.get(severity.upper(), 'info') 