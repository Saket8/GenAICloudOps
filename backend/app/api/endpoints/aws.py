from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from pydantic import BaseModel

from app.core.permissions import require_permissions
from app.models.user import User
from app.services.aws_service import get_aws_service

router = APIRouter()


class AWSOverviewResponse(BaseModel):
    account: Dict[str, Any]
    summary: Dict[str, Any]
    highlights: List[Dict[str, Any]]


class AWSMonitoringResponse(BaseModel):
    metrics: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    logs: Dict[str, Any]


class AWSCostResponse(BaseModel):
    summary: Dict[str, Any]
    service_breakdown: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class AWSSecurityResponse(BaseModel):
    summary: Dict[str, Any]
    findings: List[Dict[str, Any]]
    rbac: Dict[str, Any]


class AWSAutomationResponse(BaseModel):
    playbooks: List[Dict[str, Any]]
    approvals: Dict[str, Any]


class AWSResourcesResponse(BaseModel):
    compute: Dict[str, Any]
    storage: Dict[str, Any]
    databases: Dict[str, Any]
    networking: Dict[str, Any]


class AWSMonitoringScope(BaseModel):
    id: str
    name: str
    code: str
    type: str
    lifecycle_state: str
    description: str | None = None


class AWSAlertSummaryResponse(BaseModel):
    compartment_id: str
    total_alarms: int
    active_alarms: int
    severity_breakdown: Dict[str, int]
    recent_activity: Dict[str, Any]
    top_alerts: List[Dict[str, Any]]
    timestamp: str
    health_score: float


class AWSMonitoringDashboardResponse(BaseModel):
    compartment_id: str
    summary: Dict[str, Any]
    active_alarms: List[Dict[str, Any]]
    recent_history: List[Dict[str, Any]]
    trends: Dict[str, Any]
    quick_stats: Dict[str, Any]
    eks: Dict[str, Any] | None = None
    metrics: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    logs: Dict[str, Any]
    last_updated: str | None = None


@router.get("/overview", response_model=AWSOverviewResponse)
async def get_overview(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.get_overview()


@router.get("/monitoring/summary", response_model=AWSMonitoringResponse)
async def get_monitoring_summary(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.get_monitoring_summary()


@router.get("/monitoring/scopes", response_model=List[AWSMonitoringScope])
async def list_monitoring_scopes(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.list_monitoring_scopes()


@router.get("/monitoring/alerts/summary", response_model=AWSAlertSummaryResponse)
async def get_monitoring_alert_summary(
    scope_id: str = Query(..., description="AWS monitoring scope identifier"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    service = get_aws_service()
    return service.get_monitoring_alert_summary(scope_id)


@router.get("/monitoring/alarms", response_model=List[Dict[str, Any]])
async def get_monitoring_alarms(
    scope_id: str = Query(..., description="AWS monitoring scope identifier"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    service = get_aws_service()
    return service.get_monitoring_active_alarms(scope_id)


@router.get("/monitoring/alarms/history", response_model=List[Dict[str, Any]])
async def get_monitoring_alarm_history(
    scope_id: str = Query(..., description="AWS monitoring scope identifier"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    service = get_aws_service()
    return service.get_monitoring_history(scope_id)


@router.get("/monitoring/dashboard", response_model=AWSMonitoringDashboardResponse)
async def get_monitoring_dashboard(
    scope_id: str = Query(..., description="AWS monitoring scope identifier"),
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    service = get_aws_service()
    return service.get_monitoring_dashboard(scope_id)


@router.get("/monitoring/namespaces", response_model=List[str])
async def list_monitoring_namespaces(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.list_namespaces()


@router.get("/cost/summary", response_model=AWSCostResponse)
async def get_cost_summary(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.get_cost_summary()


@router.get("/security/summary", response_model=AWSSecurityResponse)
async def get_security_summary(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.get_security_summary()


@router.get("/automation/playbooks", response_model=AWSAutomationResponse)
async def get_automation_playbooks(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.get_automation_playbooks()


@router.get("/resources/inventory", response_model=AWSResourcesResponse)
async def get_resource_inventory(current_user: User = Depends(require_permissions("can_view_dashboard"))):
    service = get_aws_service()
    return service.get_resource_inventory()
