"""
Grafana Integration Service
=========================

This service provides integration with Grafana for creating and managing dashboards,
alerts, and visualizations for the GenAI CloudOps Dashboard metrics.

Author: GenAI CloudOps Dashboard Team
Created: January 2025
Task: 028 - Implement Optional Enhancements
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import asyncio
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

class PanelType(Enum):
    """Grafana panel types"""
    GRAPH = "graph"
    STAT = "stat"
    TABLE = "table"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    BAR_GAUGE = "bargauge"
    TEXT = "text"
    ALERT_LIST = "alertlist"
    DASHBOARD_LIST = "dashlist"
    LOGS = "logs"

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class GrafanaDataSource:
    """Grafana data source configuration"""
    name: str
    type: str  # prometheus, loki, etc.
    url: str
    access: str = "proxy"
    is_default: bool = False
    basic_auth: bool = False
    basic_auth_user: str = ""
    basic_auth_password: str = ""
    json_data: Dict[str, Any] = None
    secure_json_data: Dict[str, Any] = None

@dataclass
class GrafanaPanel:
    """Grafana dashboard panel configuration"""
    id: int
    title: str
    type: str
    targets: List[Dict[str, Any]]
    grid_pos: Dict[str, int]
    field_config: Dict[str, Any] = None
    options: Dict[str, Any] = None
    transformations: List[Dict[str, Any]] = None
    alert: Dict[str, Any] = None

@dataclass
class GrafanaDashboard:
    """Grafana dashboard configuration"""
    title: str
    tags: List[str]
    panels: List[GrafanaPanel]
    time_from: str = "now-6h"
    time_to: str = "now"
    refresh: str = "30s"
    timezone: str = "browser"
    schema_version: int = 36
    version: int = 1
    uid: str = ""
    folder_id: int = 0

class GrafanaService:
    """Service for Grafana integration and dashboard management"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'GRAFANA_ENABLED', False)
        self.base_url = getattr(settings, 'GRAFANA_URL', 'http://localhost:3000')
        self.api_key = getattr(settings, 'GRAFANA_API_KEY', '')
        self.username = getattr(settings, 'GRAFANA_USERNAME', 'admin')
        self.password = getattr(settings, 'GRAFANA_PASSWORD', 'admin')
        
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.client = None
        if self.enabled:
            self._initialize_client()
            logger.info("Grafana service initialized")
        else:
            logger.info("Grafana integration disabled in configuration")
    
    def _initialize_client(self):
        """Initialize HTTP client for Grafana API"""
        auth = None
        if not self.api_key and self.username and self.password:
            auth = (self.username, self.password)
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            auth=auth,
            timeout=30.0,
            verify=False  # For development environments
        )
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Grafana API"""
        if not self.enabled or not self.client:
            return {"status": "disabled", "message": "Grafana integration disabled"}
        
        try:
            response = await self.client.get("/api/health")
            response.raise_for_status()
            
            # Get org info
            org_response = await self.client.get("/api/org")
            org_data = org_response.json() if org_response.status_code == 200 else {}
            
            return {
                "status": "connected",
                "health": response.json(),
                "organization": org_data,
                "api_version": "v1"
            }
            
        except Exception as e:
            logger.error(f"Grafana connection test failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def create_data_source(self, data_source: GrafanaDataSource) -> Dict[str, Any]:
        """Create a new data source in Grafana"""
        if not self.enabled or not self.client:
            return {"status": "disabled"}
        
        try:
            payload = {
                "name": data_source.name,
                "type": data_source.type,
                "url": data_source.url,
                "access": data_source.access,
                "isDefault": data_source.is_default,
                "basicAuth": data_source.basic_auth,
                "basicAuthUser": data_source.basic_auth_user,
                "basicAuthPassword": data_source.basic_auth_password,
                "jsonData": data_source.json_data or {},
                "secureJsonData": data_source.secure_json_data or {}
            }
            
            response = await self.client.post("/api/datasources", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created Grafana data source: {data_source.name}")
            
            return {
                "status": "success",
                "data_source": result
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                return {
                    "status": "exists",
                    "message": f"Data source {data_source.name} already exists"
                }
            else:
                logger.error(f"Failed to create data source: {e}")
                return {
                    "status": "error",
                    "message": str(e)
                }
        except Exception as e:
            logger.error(f"Failed to create data source: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_data_sources(self) -> List[Dict[str, Any]]:
        """Get all data sources from Grafana"""
        if not self.enabled or not self.client:
            return []
        
        try:
            response = await self.client.get("/api/datasources")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get data sources: {e}")
            return []
    
    async def create_dashboard(self, dashboard: GrafanaDashboard) -> Dict[str, Any]:
        """Create a new dashboard in Grafana"""
        if not self.enabled or not self.client:
            return {"status": "disabled"}
        
        try:
            dashboard_json = {
                "dashboard": {
                    "id": None,
                    "title": dashboard.title,
                    "tags": dashboard.tags,
                    "timezone": dashboard.timezone,
                    "panels": [asdict(panel) for panel in dashboard.panels],
                    "time": {
                        "from": dashboard.time_from,
                        "to": dashboard.time_to
                    },
                    "timepicker": {},
                    "templating": {"list": []},
                    "annotations": {"list": []},
                    "refresh": dashboard.refresh,
                    "schemaVersion": dashboard.schema_version,
                    "version": dashboard.version,
                    "links": [],
                    "uid": dashboard.uid or None
                },
                "folderId": dashboard.folder_id,
                "overwrite": True
            }
            
            response = await self.client.post("/api/dashboards/db", json=dashboard_json)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created Grafana dashboard: {dashboard.title}")
            
            return {
                "status": "success",
                "dashboard": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboards from Grafana"""
        if not self.enabled or not self.client:
            return []
        
        try:
            response = await self.client.get("/api/search")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get dashboards: {e}")
            return []
    
    async def delete_dashboard(self, uid: str) -> Dict[str, Any]:
        """Delete a dashboard by UID"""
        if not self.enabled or not self.client:
            return {"status": "disabled"}
        
        try:
            response = await self.client.delete(f"/api/dashboards/uid/{uid}")
            response.raise_for_status()
            
            logger.info(f"Deleted Grafana dashboard: {uid}")
            return {
                "status": "success",
                "message": f"Dashboard {uid} deleted"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete dashboard: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def create_genai_cloudops_dashboards(self) -> List[GrafanaDashboard]:
        """Create pre-configured dashboards for GenAI CloudOps"""
        dashboards = []
        
        # Main Application Dashboard
        main_dashboard = self._create_main_dashboard()
        dashboards.append(main_dashboard)
        
        # GenAI Service Dashboard
        genai_dashboard = self._create_genai_dashboard()
        dashboards.append(genai_dashboard)
        
        # OCI Resources Dashboard
        oci_dashboard = self._create_oci_dashboard()
        dashboards.append(oci_dashboard)
        
        # Kubernetes Dashboard
        k8s_dashboard = self._create_kubernetes_dashboard()
        dashboards.append(k8s_dashboard)
        
        # Business Metrics Dashboard
        business_dashboard = self._create_business_dashboard()
        dashboards.append(business_dashboard)
        
        return dashboards
    
    def _create_main_dashboard(self) -> GrafanaDashboard:
        """Create main application monitoring dashboard"""
        panels = [
            GrafanaPanel(
                id=1,
                title="HTTP Requests per Second",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_http_requests_total[5m])",
                    "legendFormat": "{{method}} {{endpoint}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 0}
            ),
            GrafanaPanel(
                id=2,
                title="Response Time 95th Percentile",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "histogram_quantile(0.95, rate(genai_cloudops_http_request_duration_seconds_bucket[5m]))",
                    "legendFormat": "{{method}} {{endpoint}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 0}
            ),
            GrafanaPanel(
                id=3,
                title="CPU Usage",
                type=PanelType.GAUGE.value,
                targets=[{
                    "expr": "genai_cloudops_cpu_usage_percent",
                    "legendFormat": "CPU %",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 6, "x": 0, "y": 8}
            ),
            GrafanaPanel(
                id=4,
                title="Memory Usage",
                type=PanelType.GAUGE.value,
                targets=[{
                    "expr": "genai_cloudops_memory_usage_bytes{type='used'} / genai_cloudops_memory_usage_bytes{type='total'} * 100",
                    "legendFormat": "Memory %",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 6, "x": 6, "y": 8}
            ),
            GrafanaPanel(
                id=5,
                title="Active Users",
                type=PanelType.STAT.value,
                targets=[{
                    "expr": "genai_cloudops_users_active{time_window='1h'}",
                    "legendFormat": "Users (1h)",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 6, "x": 12, "y": 8}
            ),
            GrafanaPanel(
                id=6,
                title="Error Rate",
                type=PanelType.STAT.value,
                targets=[{
                    "expr": "rate(genai_cloudops_http_requests_total{status_code=~'5..'}[5m]) / rate(genai_cloudops_http_requests_total[5m]) * 100",
                    "legendFormat": "Error Rate %",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 6, "x": 18, "y": 8}
            )
        ]
        
        return GrafanaDashboard(
            title="GenAI CloudOps - Application Overview",
            tags=["genai-cloudops", "application", "overview"],
            panels=panels,
            uid="genai-cloudops-main"
        )
    
    def _create_genai_dashboard(self) -> GrafanaDashboard:
        """Create GenAI service specific dashboard"""
        panels = [
            GrafanaPanel(
                id=1,
                title="GenAI Requests per Second",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_genai_requests_total[5m])",
                    "legendFormat": "{{prompt_type}} - {{model}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 0}
            ),
            GrafanaPanel(
                id=2,
                title="Average Response Time by Prompt Type",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_genai_request_duration_seconds_sum[5m]) / rate(genai_cloudops_genai_request_duration_seconds_count[5m])",
                    "legendFormat": "{{prompt_type}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 0}
            ),
            GrafanaPanel(
                id=3,
                title="Token Usage",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_genai_tokens_used_total[5m])",
                    "legendFormat": "{{prompt_type}} - {{model}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 8}
            ),
            GrafanaPanel(
                id=4,
                title="Cache Hit Rate",
                type=PanelType.STAT.value,
                targets=[{
                    "expr": "rate(genai_cloudops_genai_cache_hits_total[5m]) / rate(genai_cloudops_genai_requests_total[5m]) * 100",
                    "legendFormat": "Cache Hit Rate %",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 6, "x": 12, "y": 8}
            ),
            GrafanaPanel(
                id=5,
                title="Quality Score Distribution",
                type=PanelType.HEATMAP.value,
                targets=[{
                    "expr": "genai_cloudops_genai_quality_score",
                    "legendFormat": "{{prompt_type}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 6, "x": 18, "y": 8}
            )
        ]
        
        return GrafanaDashboard(
            title="GenAI CloudOps - GenAI Service Metrics",
            tags=["genai-cloudops", "genai", "ai", "llm"],
            panels=panels,
            uid="genai-cloudops-genai"
        )
    
    def _create_oci_dashboard(self) -> GrafanaDashboard:
        """Create OCI resources dashboard"""
        panels = [
            GrafanaPanel(
                id=1,
                title="OCI API Calls per Second",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_oci_api_calls_total[5m])",
                    "legendFormat": "{{service}} - {{operation}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 0}
            ),
            GrafanaPanel(
                id=2,
                title="OCI API Response Time",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "histogram_quantile(0.95, rate(genai_cloudops_oci_api_duration_seconds_bucket[5m]))",
                    "legendFormat": "{{service}} - {{operation}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 0}
            ),
            GrafanaPanel(
                id=3,
                title="Resources by Compartment",
                type=PanelType.BAR_GAUGE.value,
                targets=[{
                    "expr": "genai_cloudops_oci_resources_discovered",
                    "legendFormat": "{{compartment}} - {{resource_type}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 8}
            ),
            GrafanaPanel(
                id=4,
                title="Resource Health Scores",
                type=PanelType.HEATMAP.value,
                targets=[{
                    "expr": "genai_cloudops_oci_resource_health_score",
                    "legendFormat": "{{compartment}} - {{resource_type}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 8}
            ),
            GrafanaPanel(
                id=5,
                title="Current Costs by Service",
                type=PanelType.TABLE.value,
                targets=[{
                    "expr": "genai_cloudops_oci_cost_current_dollars",
                    "legendFormat": "{{compartment}} - {{service}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 24, "x": 0, "y": 16}
            )
        ]
        
        return GrafanaDashboard(
            title="GenAI CloudOps - OCI Resources",
            tags=["genai-cloudops", "oci", "oracle-cloud", "resources"],
            panels=panels,
            uid="genai-cloudops-oci"
        )
    
    def _create_kubernetes_dashboard(self) -> GrafanaDashboard:
        """Create Kubernetes/OKE dashboard"""
        panels = [
            GrafanaPanel(
                id=1,
                title="Pods by Status",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "genai_cloudops_k8s_pods_total",
                    "legendFormat": "{{namespace}} - {{status}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 0}
            ),
            GrafanaPanel(
                id=2,
                title="Pod Restarts",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_k8s_pod_restarts_total[5m])",
                    "legendFormat": "{{namespace}} - {{pod}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 0}
            ),
            GrafanaPanel(
                id=3,
                title="Cluster Health Score",
                type=PanelType.GAUGE.value,
                targets=[{
                    "expr": "genai_cloudops_k8s_cluster_health_score",
                    "legendFormat": "{{cluster}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 8, "x": 0, "y": 8}
            ),
            GrafanaPanel(
                id=4,
                title="Resource Usage",
                type=PanelType.GAUGE.value,
                targets=[{
                    "expr": "genai_cloudops_k8s_resource_usage_percent",
                    "legendFormat": "{{cluster}} - {{resource_type}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 16, "x": 8, "y": 8}
            )
        ]
        
        return GrafanaDashboard(
            title="GenAI CloudOps - Kubernetes/OKE",
            tags=["genai-cloudops", "kubernetes", "oke", "containers"],
            panels=panels,
            uid="genai-cloudops-k8s"
        )
    
    def _create_business_dashboard(self) -> GrafanaDashboard:
        """Create business metrics dashboard"""
        panels = [
            GrafanaPanel(
                id=1,
                title="Active Users",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "genai_cloudops_users_active",
                    "legendFormat": "{{time_window}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 8, "x": 0, "y": 0}
            ),
            GrafanaPanel(
                id=2,
                title="Feature Usage",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_feature_usage_total[5m])",
                    "legendFormat": "{{feature}} - {{user_role}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 16, "x": 8, "y": 0}
            ),
            GrafanaPanel(
                id=3,
                title="Alerts Generated",
                type=PanelType.GRAPH.value,
                targets=[{
                    "expr": "rate(genai_cloudops_alerts_generated_total[5m])",
                    "legendFormat": "{{alert_type}} - {{severity}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 0, "y": 8}
            ),
            GrafanaPanel(
                id=4,
                title="Remediation Success Rate",
                type=PanelType.GAUGE.value,
                targets=[{
                    "expr": "genai_cloudops_remediation_success_rate * 100",
                    "legendFormat": "{{remediation_type}}",
                    "refId": "A"
                }],
                grid_pos={"h": 8, "w": 12, "x": 12, "y": 8}
            )
        ]
        
        return GrafanaDashboard(
            title="GenAI CloudOps - Business Metrics",
            tags=["genai-cloudops", "business", "kpi", "analytics"],
            panels=panels,
            uid="genai-cloudops-business"
        )
    
    async def setup_default_configuration(self) -> Dict[str, Any]:
        """Setup default Grafana configuration for GenAI CloudOps"""
        if not self.enabled:
            return {"status": "disabled"}
        
        results = {
            "data_sources": [],
            "dashboards": [],
            "errors": []
        }
        
        try:
            # Create Prometheus data source
            prometheus_ds = GrafanaDataSource(
                name="Prometheus-GenAI-CloudOps",
                type="prometheus",
                url=getattr(settings, 'PROMETHEUS_URL', 'http://localhost:9090'),
                is_default=True
            )
            
            ds_result = await self.create_data_source(prometheus_ds)
            results["data_sources"].append(ds_result)
            
            # Create default dashboards
            dashboards = self.create_genai_cloudops_dashboards()
            
            for dashboard in dashboards:
                dash_result = await self.create_dashboard(dashboard)
                results["dashboards"].append(dash_result)
                
                if dash_result.get("status") == "error":
                    results["errors"].append(f"Failed to create dashboard: {dashboard.title}")
            
            logger.info("Grafana default configuration setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup Grafana configuration: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

# Global service instance
_grafana_service = None

def get_grafana_service() -> GrafanaService:
    """Get global Grafana service instance"""
    global _grafana_service
    if _grafana_service is None:
        _grafana_service = GrafanaService()
    return _grafana_service 