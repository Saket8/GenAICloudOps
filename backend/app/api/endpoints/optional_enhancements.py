"""
Optional Enhancements API Endpoints
==================================

This module provides REST API endpoints for optional enhancement features including
Prometheus metrics, Grafana integration, notification services, and auto-remediation.

Author: GenAI CloudOps Dashboard Team
Created: January 2025
Task: 028 - Implement Optional Enhancements
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Response
from fastapi.responses import PlainTextResponse

from app.core.permissions import require_permissions
from app.services.auth_service import AuthService
from app.models.user import User
from app.services.prometheus_service import get_prometheus_service, MetricDefinition
from app.services.grafana_service import get_grafana_service, GrafanaDataSource, GrafanaDashboard
from app.services.notification_service import (
    get_notification_service, 
    NotificationRequest, 
    NotificationType, 
    NotificationSeverity, 
    NotificationChannel
)
from app.services.auto_remediation_service import (
    get_auto_remediation_service, 
    RemediationRisk, 
    RemediationStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enhancements", tags=["Optional Enhancements"])

# Prometheus Metrics Endpoints

@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """Export Prometheus metrics in standard format"""
    try:
        prometheus_service = get_prometheus_service()
        metrics_data = prometheus_service.export_metrics()
        
        return Response(
            content=metrics_data,
            media_type=prometheus_service.get_metrics_content_type()
        )
        
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")

@router.get("/metrics/health", response_model=Dict[str, Any])
async def get_metrics_health(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get metrics service health and status"""
    try:
        # Check permissions
        if not require_permissions("monitoring", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        prometheus_service = get_prometheus_service()
        health_data = prometheus_service.get_health_metrics()
        
        return {
            "status": "success",
            "health": health_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics health")

@router.post("/metrics/custom", response_model=Dict[str, Any])
async def create_custom_metric(
    metric_definition: Dict[str, Any] = Body(...),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create a custom metric"""
    try:
        # Check admin permissions
        if not require_permissions("monitoring", "admin")(current_user):
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        prometheus_service = get_prometheus_service()
        
        # Convert dict to MetricDefinition
        definition = MetricDefinition(**metric_definition)
        
        # Create custom metric
        metric = prometheus_service.create_custom_metric(definition)
        
        return {
            "status": "success",
            "metric_name": definition.name,
            "metric_type": definition.metric_type,
            "created": metric is not None
        }
        
    except Exception as e:
        logger.error(f"Failed to create custom metric: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create custom metric: {str(e)}")

@router.post("/metrics/record", response_model=Dict[str, Any])
async def record_custom_metric(
    metric_name: str = Body(...),
    value: float = Body(...),
    labels: Dict[str, str] = Body(default={}),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Record a value for a custom metric"""
    try:
        # Check permissions
        if not require_permissions("monitoring", "use")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        prometheus_service = get_prometheus_service()
        
        # Get custom metric
        metric = prometheus_service.get_custom_metric(metric_name)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Custom metric '{metric_name}' not found")
        
        # Record value based on metric type
        if hasattr(metric, 'inc'):  # Counter
            metric.labels(**labels).inc(value)
        elif hasattr(metric, 'set'):  # Gauge
            metric.labels(**labels).set(value)
        elif hasattr(metric, 'observe'):  # Histogram/Summary
            metric.labels(**labels).observe(value)
        
        return {
            "status": "success",
            "metric_name": metric_name,
            "value": value,
            "labels": labels
        }
        
    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record metric: {str(e)}")

# Grafana Integration Endpoints

@router.get("/grafana/status", response_model=Dict[str, Any])
async def get_grafana_status(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get Grafana integration status"""
    try:
        # Check permissions
        if not require_permissions("monitoring", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        grafana_service = get_grafana_service()
        connection_status = await grafana_service.test_connection()
        
        return {
            "status": "success",
            "grafana": connection_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Grafana status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Grafana status")

@router.post("/grafana/setup", response_model=Dict[str, Any])
async def setup_grafana_configuration(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Setup default Grafana configuration"""
    try:
        # Check admin permissions
        if not require_permissions("monitoring", "admin")(current_user):
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        grafana_service = get_grafana_service()
        setup_results = await grafana_service.setup_default_configuration()
        
        return {
            "status": "success",
            "setup_results": setup_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to setup Grafana: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to setup Grafana: {str(e)}")

@router.get("/grafana/dashboards", response_model=Dict[str, Any])
async def list_grafana_dashboards(
    current_user: User = Depends(AuthService.get_current_user)
):
    """List all Grafana dashboards"""
    try:
        # Check permissions
        if not require_permissions("monitoring", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        grafana_service = get_grafana_service()
        dashboards = await grafana_service.get_dashboards()
        
        return {
            "status": "success",
            "dashboards": dashboards,
            "count": len(dashboards)
        }
        
    except Exception as e:
        logger.error(f"Failed to list dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to list dashboards")

@router.post("/grafana/dashboards", response_model=Dict[str, Any])
async def create_grafana_dashboard(
    dashboard_config: Dict[str, Any] = Body(...),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create a new Grafana dashboard"""
    try:
        # Check admin permissions
        if not require_permissions("monitoring", "admin")(current_user):
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        grafana_service = get_grafana_service()
        
        # Convert dict to GrafanaDashboard (simplified)
        dashboard = GrafanaDashboard(**dashboard_config)
        
        result = await grafana_service.create_dashboard(dashboard)
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {str(e)}")

@router.delete("/grafana/dashboards/{dashboard_uid}", response_model=Dict[str, Any])
async def delete_grafana_dashboard(
    dashboard_uid: str,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Delete a Grafana dashboard"""
    try:
        # Check admin permissions
        if not require_permissions("monitoring", "admin")(current_user):
            raise HTTPException(status_code=403, detail="Admin permissions required")
        
        grafana_service = get_grafana_service()
        result = await grafana_service.delete_dashboard(dashboard_uid)
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to delete dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete dashboard: {str(e)}")

# Notification Service Endpoints

@router.get("/notifications/status", response_model=Dict[str, Any])
async def get_notification_status(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get notification service status"""
    try:
        # Check permissions
        if not require_permissions("notifications", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        notification_service = get_notification_service()
        status = notification_service.get_service_status()
        
        return {
            "status": "success",
            "notification_service": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification status")

@router.post("/notifications/send", response_model=Dict[str, Any])
async def send_notification(
    notification_request: Dict[str, Any] = Body(...),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Send a notification"""
    try:
        # Check permissions
        if not require_permissions("notifications", "use")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        notification_service = get_notification_service()
        
        # Convert dict to NotificationRequest
        request = NotificationRequest(
            notification_type=NotificationType(notification_request["notification_type"]),
            severity=NotificationSeverity(notification_request["severity"]),
            title=notification_request["title"],
            message=notification_request["message"],
            data=notification_request.get("data", {}),
            recipients=notification_request.get("recipients", []),
            channels=[NotificationChannel(ch) for ch in notification_request.get("channels", [])],
            urgent=notification_request.get("urgent", False),
            template_name=notification_request.get("template_name"),
            escalation_rule_id=notification_request.get("escalation_rule_id")
        )
        
        result = await notification_service.send_notification(request)
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.post("/notifications/alert", response_model=Dict[str, Any])
async def send_alert_notification(
    alert_title: str = Body(...),
    severity: str = Body(...),
    description: str = Body(...),
    source: str = Body(...),
    affected_resources: List[str] = Body(default=[]),
    recommended_actions: List[str] = Body(default=[]),
    dashboard_url: str = Body(default=""),
    recipients: List[str] = Body(default=[]),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Send an alert notification (convenience method)"""
    try:
        # Check permissions
        if not require_permissions("notifications", "use")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        notification_service = get_notification_service()
        
        result = await notification_service.send_alert_notification(
            alert_title=alert_title,
            severity=NotificationSeverity(severity),
            description=description,
            source=source,
            affected_resources=affected_resources,
            recommended_actions=recommended_actions,
            dashboard_url=dashboard_url,
            recipients=recipients if recipients else None
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")

@router.get("/notifications/history", response_model=Dict[str, Any])
async def get_notification_history(
    limit: int = Query(100, ge=1, le=1000),
    notification_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get notification history"""
    try:
        # Check permissions
        if not require_permissions("notifications", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        notification_service = get_notification_service()
        
        # Convert optional parameters
        type_filter = NotificationType(notification_type) if notification_type else None
        severity_filter = NotificationSeverity(severity) if severity else None
        
        history = notification_service.get_notification_history(
            limit=limit,
            notification_type=type_filter,
            severity=severity_filter
        )
        
        return {
            "status": "success",
            "history": history,
            "count": len(history),
            "filters": {
                "limit": limit,
                "notification_type": notification_type,
                "severity": severity
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get notification history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification history")

# Auto-Remediation Endpoints

@router.get("/remediation/status", response_model=Dict[str, Any])
async def get_remediation_status(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get auto-remediation service status"""
    try:
        # Check permissions
        if not require_permissions("remediation", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        remediation_service = get_auto_remediation_service()
        status = remediation_service.get_service_status()
        
        return {
            "status": "success",
            "remediation_service": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get remediation status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get remediation status")

@router.get("/remediation/plans", response_model=Dict[str, Any])
async def list_remediation_plans(
    current_user: User = Depends(AuthService.get_current_user)
):
    """List all available remediation plans"""
    try:
        # Check permissions
        if not require_permissions("remediation", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        remediation_service = get_auto_remediation_service()
        plans = remediation_service.list_remediation_plans()
        
        # Convert to serializable format
        serialized_plans = []
        for plan in plans:
            serialized_plans.append({
                "id": plan.id,
                "title": plan.title,
                "description": plan.description,
                "overall_risk": plan.overall_risk.value,
                "estimated_duration_minutes": plan.estimated_duration_minutes,
                "affected_resources": plan.affected_resources,
                "prerequisites": plan.prerequisites,
                "approval_required": plan.approval_required,
                "auto_execute": plan.auto_execute,
                "actions_count": len(plan.actions)
            })
        
        return {
            "status": "success",
            "plans": serialized_plans,
            "count": len(serialized_plans)
        }
        
    except Exception as e:
        logger.error(f"Failed to list remediation plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to list remediation plans")

@router.get("/remediation/plans/{plan_id}", response_model=Dict[str, Any])
async def get_remediation_plan(
    plan_id: str,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get details of a specific remediation plan"""
    try:
        # Check permissions
        if not require_permissions("remediation", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        remediation_service = get_auto_remediation_service()
        plan = remediation_service.get_remediation_plan(plan_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail=f"Remediation plan '{plan_id}' not found")
        
        # Convert to serializable format
        serialized_plan = {
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "overall_risk": plan.overall_risk.value,
            "estimated_duration_minutes": plan.estimated_duration_minutes,
            "affected_resources": plan.affected_resources,
            "prerequisites": plan.prerequisites,
            "approval_required": plan.approval_required,
            "auto_execute": plan.auto_execute,
            "actions": [
                {
                    "id": action.id,
                    "name": action.name,
                    "type": action.type.value,
                    "description": action.description,
                    "risk_level": action.risk_level.value,
                    "timeout_seconds": action.timeout_seconds,
                    "requires_approval": action.requires_approval
                }
                for action in plan.actions
            ]
        }
        
        return {
            "status": "success",
            "plan": serialized_plan
        }
        
    except Exception as e:
        logger.error(f"Failed to get remediation plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get remediation plan: {str(e)}")

@router.post("/remediation/submit", response_model=Dict[str, Any])
async def submit_remediation_request(
    plan_id: str = Body(...),
    context: Dict[str, Any] = Body(...),
    force_approval: bool = Body(default=False),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Submit a remediation request"""
    try:
        # Check permissions
        if not require_permissions("remediation", "execute")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        remediation_service = get_auto_remediation_service()
        
        result = await remediation_service.submit_remediation_request(
            plan_id=plan_id,
            context=context,
            user_id=current_user.id,
            force_approval=force_approval
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to submit remediation request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit remediation request: {str(e)}")

@router.post("/remediation/approve/{execution_id}", response_model=Dict[str, Any])
async def approve_remediation(
    execution_id: str,
    comments: str = Body(default=""),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Approve a pending remediation execution"""
    try:
        # Check admin permissions
        if not require_permissions("remediation", "approve")(current_user):
            raise HTTPException(status_code=403, detail="Approval permissions required")
        
        remediation_service = get_auto_remediation_service()
        
        result = await remediation_service.approve_remediation(
            execution_id=execution_id,
            user_id=current_user.id,
            comments=comments
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to approve remediation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve remediation: {str(e)}")

@router.post("/remediation/cancel/{execution_id}", response_model=Dict[str, Any])
async def cancel_remediation(
    execution_id: str,
    reason: str = Body(default=""),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Cancel a pending or executing remediation"""
    try:
        # Check permissions
        if not require_permissions("remediation", "cancel")(current_user):
            raise HTTPException(status_code=403, detail="Cancellation permissions required")
        
        remediation_service = get_auto_remediation_service()
        
        result = await remediation_service.cancel_remediation(
            execution_id=execution_id,
            user_id=current_user.id,
            reason=reason
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel remediation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel remediation: {str(e)}")

@router.get("/remediation/executions", response_model=Dict[str, Any])
async def list_remediation_executions(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(AuthService.get_current_user)
):
    """List remediation executions"""
    try:
        # Check permissions
        if not require_permissions("remediation", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        remediation_service = get_auto_remediation_service()
        
        # Convert status filter
        status_filter = RemediationStatus(status) if status else None
        
        executions = remediation_service.list_executions(
            status_filter=status_filter,
            limit=limit
        )
        
        return {
            "status": "success",
            "executions": executions,
            "count": len(executions),
            "filters": {
                "status": status,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list executions")

@router.get("/remediation/executions/{execution_id}", response_model=Dict[str, Any])
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get the status of a specific remediation execution"""
    try:
        # Check permissions
        if not require_permissions("remediation", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        remediation_service = get_auto_remediation_service()
        execution = remediation_service.get_execution_status(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")
        
        return {
            "status": "success",
            "execution": execution
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")

# Feature Toggle Endpoints

@router.get("/features/status", response_model=Dict[str, Any])
async def get_features_status(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get status of all optional enhancement features"""
    try:
        # Check permissions
        if not require_permissions("system", "view")(current_user):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get status from all services
        prometheus_service = get_prometheus_service()
        grafana_service = get_grafana_service()
        notification_service = get_notification_service()
        remediation_service = get_auto_remediation_service()
        
        features = {
            "prometheus_metrics": {
                "enabled": prometheus_service.enabled,
                "description": "Metrics collection and monitoring"
            },
            "grafana_integration": {
                "enabled": grafana_service.enabled,
                "description": "Dashboard and visualization platform"
            },
            "notifications": {
                "enabled": notification_service.enabled,
                "email_enabled": notification_service.email_enabled,
                "slack_enabled": notification_service.slack_enabled,
                "description": "Email and Slack notifications"
            },
            "auto_remediation": {
                "enabled": remediation_service.enabled,
                "auto_approval_enabled": remediation_service.auto_approval_enabled,
                "dry_run_mode": remediation_service.dry_run_mode,
                "description": "Automated issue remediation"
            }
        }
        
        return {
            "status": "success",
            "features": features,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get features status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get features status") 