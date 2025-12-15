from typing import Dict, Any, List
import copy

from app.core.config import settings
from .aws_demo_data import (
    AWS_OVERVIEW,
    AWS_MONITORING,
    AWS_COST,
    AWS_SECURITY,
    AWS_AUTOMATION,
    AWS_RESOURCES,
    AWS_MONITORING_SCOPES,
)


class _AWSDemoService:
    """AWS demo-mode service that mirrors OCI features using static datasets."""

    def __init__(self) -> None:
        self._overview = AWS_OVERVIEW
        self._monitoring = AWS_MONITORING
        self._cost = AWS_COST
        self._security = AWS_SECURITY
        self._automation = AWS_AUTOMATION
        self._resources = AWS_RESOURCES
        self._monitoring_scopes = AWS_MONITORING_SCOPES

    def get_overview(self) -> Dict[str, Any]:
        return self._overview

    def get_monitoring_summary(self) -> Dict[str, Any]:
        return self._monitoring

    # --- Monitoring helpers for OCI parity ---

    def list_monitoring_scopes(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self._monitoring_scopes)

    def get_monitoring_alert_summary(self, scope_id: str) -> Dict[str, Any]:
        summary = copy.deepcopy(self._monitoring["summary"])
        summary["compartment_id"] = scope_id
        return summary

    def get_monitoring_active_alarms(self, scope_id: str) -> List[Dict[str, Any]]:
        alarms = copy.deepcopy(self._monitoring.get("active_alarms", []))
        for alarm in alarms:
            alarm["metric_compartment_id"] = scope_id
        return alarms

    def get_monitoring_history(self, scope_id: str) -> List[Dict[str, Any]]:
        history = copy.deepcopy(self._monitoring.get("recent_history", []))
        for record in history:
            record["compartment_id"] = scope_id
        return history

    def get_monitoring_dashboard(self, scope_id: str) -> Dict[str, Any]:
        data = copy.deepcopy(self._monitoring)
        data["summary"]["compartment_id"] = scope_id
        dashboard = {
            "compartment_id": scope_id,
            "summary": data["summary"],
            "active_alarms": data.get("active_alarms", []),
            "recent_history": data.get("recent_history", []),
            "trends": data.get("trends", {}),
            "quick_stats": data.get("quick_stats", {}),
            "eks": data.get("eks", {}),
            "metrics": data.get("metrics", []),
            "alerts": data.get("alerts", []),
            "logs": data.get("logs", {}),
            "last_updated": data.get("last_updated"),
        }
        return dashboard

    def get_cost_summary(self) -> Dict[str, Any]:
        return self._cost

    def get_security_summary(self) -> Dict[str, Any]:
        return self._security

    def get_automation_playbooks(self) -> Dict[str, Any]:
        return self._automation

    def get_resource_inventory(self) -> Dict[str, Any]:
        return self._resources

    def list_namespaces(self) -> List[str]:
        return sorted({metric["namespace"] for metric in self._monitoring["metrics"]})


_demo_service = _AWSDemoService()


def get_aws_service() -> _AWSDemoService:
    """Factory that respects global AWS dummy-mode flag."""

    if getattr(settings, "USE_DUMMY_AWS", True):
        return _demo_service

    # Future enhancement: return live AWS service implementation.
    return _demo_service
