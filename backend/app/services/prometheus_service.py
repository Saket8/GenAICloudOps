"""
Prometheus Metrics Collection Service
===================================

This service provides comprehensive metrics collection for the GenAI CloudOps Dashboard
using Prometheus client library. It tracks application performance, GenAI usage,
OCI resource monitoring, and system health metrics.

Author: GenAI CloudOps Dashboard Team
Created: January 2025
Task: 028 - Implement Optional Enhancements
"""

import time
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import psutil
import redis

# Safe import guard for optional dependency
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info, Summary,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        multiprocess, REGISTRY
    )
    from prometheus_client.openmetrics.exposition import openmetrics_content_type
    PROMETHEUS_AVAILABLE = True
except Exception as e:
    PROMETHEUS_AVAILABLE = False
    # Define minimal stand-ins to avoid NameErrors when disabled
    Counter = Histogram = Gauge = Info = Summary = object  # type: ignore
    CollectorRegistry = object  # type: ignore
    REGISTRY = None  # type: ignore
    def generate_latest(*args, **kwargs):
        return ""  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    def openmetrics_content_type(*args, **kwargs):
        return CONTENT_TYPE_LATEST

from app.core.config import settings

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics for different application areas"""
    SYSTEM = "system"
    APPLICATION = "application"
    GENAI = "genai"
    OCI = "oci"
    KUBERNETES = "kubernetes"
    USER = "user"
    BUSINESS = "business"

@dataclass
class MetricDefinition:
    """Definition of a custom metric"""
    name: str
    metric_type: str  # counter, histogram, gauge, summary
    description: str
    labels: List[str]
    buckets: Optional[List[float]] = None  # For histograms
    unit: str = ""

class PrometheusMetricsService:
    """Comprehensive Prometheus metrics collection service"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        # Disable if package missing or config disabled
        self.enabled = getattr(settings, 'PROMETHEUS_ENABLED', True) and PROMETHEUS_AVAILABLE
        if not PROMETHEUS_AVAILABLE:
            logger.info("prometheus_client not installed; Prometheus metrics disabled")
        self.registry = registry or (REGISTRY if PROMETHEUS_AVAILABLE else None)
        self.metrics = {}
        self.custom_metrics = {}
        
        if self.enabled:
            self._initialize_core_metrics()
            self._initialize_genai_metrics()
            self._initialize_oci_metrics()
            self._initialize_kubernetes_metrics()
            self._initialize_business_metrics()
            logger.info("Prometheus metrics service initialized")
        else:
            logger.info("Prometheus metrics disabled")
    
    def _initialize_core_metrics(self):
        """Initialize core application metrics"""
        
        # HTTP Request metrics
        self.metrics['http_requests_total'] = Counter(
            'genai_cloudops_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.metrics['http_request_duration'] = Histogram(
            'genai_cloudops_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
            registry=self.registry
        )
        
        # System Performance metrics
        self.metrics['cpu_usage'] = Gauge(
            'genai_cloudops_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.metrics['memory_usage'] = Gauge(
            'genai_cloudops_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],  # total, available, used
            registry=self.registry
        )
        
        self.metrics['disk_usage'] = Gauge(
            'genai_cloudops_disk_usage_bytes',
            'Disk usage in bytes',
            ['mount_point', 'type'],  # total, used, free
            registry=self.registry
        )
        
        # Database metrics
        self.metrics['db_connections'] = Gauge(
            'genai_cloudops_db_connections_active',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.metrics['db_query_duration'] = Histogram(
            'genai_cloudops_db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self.registry
        )
        
        # Redis metrics
        self.metrics['redis_operations'] = Counter(
            'genai_cloudops_redis_operations_total',
            'Total Redis operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.metrics['redis_connections'] = Gauge(
            'genai_cloudops_redis_connections_active',
            'Active Redis connections',
            registry=self.registry
        )
    
    def _initialize_genai_metrics(self):
        """Initialize GenAI service metrics"""
        
        # GenAI Request metrics
        self.metrics['genai_requests_total'] = Counter(
            'genai_cloudops_genai_requests_total',
            'Total GenAI requests',
            ['prompt_type', 'model', 'status'],
            registry=self.registry
        )
        
        self.metrics['genai_request_duration'] = Histogram(
            'genai_cloudops_genai_request_duration_seconds',
            'GenAI request duration in seconds',
            ['prompt_type', 'model'],
            buckets=[1.0, 2.5, 5.0, 10.0, 15.0, 30.0, 60.0, 120.0],
            registry=self.registry
        )
        
        self.metrics['genai_tokens_used'] = Counter(
            'genai_cloudops_genai_tokens_used_total',
            'Total tokens used in GenAI requests',
            ['prompt_type', 'model'],
            registry=self.registry
        )
        
        self.metrics['genai_cache_hits'] = Counter(
            'genai_cloudops_genai_cache_hits_total',
            'Total GenAI cache hits',
            ['prompt_type'],
            registry=self.registry
        )
        
        self.metrics['genai_quality_score'] = Histogram(
            'genai_cloudops_genai_quality_score',
            'GenAI response quality scores',
            ['prompt_type'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # A/B Testing metrics
        self.metrics['genai_ab_test_assignments'] = Counter(
            'genai_cloudops_genai_ab_test_assignments_total',
            'Total A/B test assignments',
            ['test_id', 'variant'],
            registry=self.registry
        )
    
    def _initialize_oci_metrics(self):
        """Initialize OCI service metrics"""
        
        # OCI API metrics
        self.metrics['oci_api_calls'] = Counter(
            'genai_cloudops_oci_api_calls_total',
            'Total OCI API calls',
            ['service', 'operation', 'status'],
            registry=self.registry
        )
        
        self.metrics['oci_api_duration'] = Histogram(
            'genai_cloudops_oci_api_duration_seconds',
            'OCI API call duration in seconds',
            ['service', 'operation'],
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0],
            registry=self.registry
        )
        
        # OCI Resource metrics
        self.metrics['oci_resources_discovered'] = Gauge(
            'genai_cloudops_oci_resources_discovered',
            'Number of OCI resources discovered',
            ['compartment', 'resource_type'],
            registry=self.registry
        )
        
        self.metrics['oci_resource_health'] = Gauge(
            'genai_cloudops_oci_resource_health_score',
            'OCI resource health score (0-100)',
            ['compartment', 'resource_type', 'resource_id'],
            registry=self.registry
        )
        
        # OCI Cost metrics
        self.metrics['oci_cost_current'] = Gauge(
            'genai_cloudops_oci_cost_current_dollars',
            'Current OCI cost in dollars',
            ['compartment', 'service'],
            registry=self.registry
        )
        
        self.metrics['oci_cost_alerts'] = Counter(
            'genai_cloudops_oci_cost_alerts_total',
            'Total OCI cost alerts',
            ['compartment', 'severity'],
            registry=self.registry
        )
    
    def _initialize_kubernetes_metrics(self):
        """Initialize Kubernetes/OKE metrics"""
        
        # Pod metrics
        self.metrics['k8s_pods_total'] = Gauge(
            'genai_cloudops_k8s_pods_total',
            'Total Kubernetes pods',
            ['namespace', 'status'],
            registry=self.registry
        )
        
        self.metrics['k8s_pod_restarts'] = Counter(
            'genai_cloudops_k8s_pod_restarts_total',
            'Total pod restarts',
            ['namespace', 'pod'],
            registry=self.registry
        )
        
        # Cluster metrics
        self.metrics['k8s_cluster_health'] = Gauge(
            'genai_cloudops_k8s_cluster_health_score',
            'Kubernetes cluster health score (0-100)',
            ['cluster'],
            registry=self.registry
        )
        
        self.metrics['k8s_resource_usage'] = Gauge(
            'genai_cloudops_k8s_resource_usage_percent',
            'Kubernetes resource usage percentage',
            ['cluster', 'resource_type'],  # cpu, memory, storage
            registry=self.registry
        )
    
    def _initialize_business_metrics(self):
        """Initialize business and user metrics"""
        
        # User activity metrics
        self.metrics['users_active'] = Gauge(
            'genai_cloudops_users_active',
            'Number of active users',
            ['time_window'],  # 1h, 24h, 7d
            registry=self.registry
        )
        
        self.metrics['user_sessions'] = Counter(
            'genai_cloudops_user_sessions_total',
            'Total user sessions',
            ['user_role'],
            registry=self.registry
        )
        
        # Feature usage metrics
        self.metrics['feature_usage'] = Counter(
            'genai_cloudops_feature_usage_total',
            'Total feature usage',
            ['feature', 'user_role'],
            registry=self.registry
        )
        
        # Alert metrics
        self.metrics['alerts_generated'] = Counter(
            'genai_cloudops_alerts_generated_total',
            'Total alerts generated',
            ['alert_type', 'severity', 'source'],
            registry=self.registry
        )
        
        self.metrics['alerts_resolved'] = Counter(
            'genai_cloudops_alerts_resolved_total',
            'Total alerts resolved',
            ['alert_type', 'resolution_method'],
            registry=self.registry
        )
        
        # Remediation metrics
        self.metrics['remediations_executed'] = Counter(
            'genai_cloudops_remediations_executed_total',
            'Total remediations executed',
            ['remediation_type', 'status'],
            registry=self.registry
        )
        
        self.metrics['remediation_success_rate'] = Gauge(
            'genai_cloudops_remediation_success_rate',
            'Remediation success rate (0-1)',
            ['remediation_type'],
            registry=self.registry
        )
    
    # Metric recording methods
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not self.enabled:
            return
            
        self.metrics['http_requests_total'].labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()
        
        self.metrics['http_request_duration'].labels(
            method=method, endpoint=endpoint
        ).observe(duration)
    
    def record_genai_request(
        self, 
        prompt_type: str, 
        model: str, 
        status: str, 
        duration: float,
        tokens_used: int,
        quality_score: Optional[float] = None,
        cached: bool = False
    ):
        """Record GenAI request metrics"""
        if not self.enabled:
            return
            
        self.metrics['genai_requests_total'].labels(
            prompt_type=prompt_type, model=model, status=status
        ).inc()
        
        self.metrics['genai_request_duration'].labels(
            prompt_type=prompt_type, model=model
        ).observe(duration)
        
        self.metrics['genai_tokens_used'].labels(
            prompt_type=prompt_type, model=model
        ).inc(tokens_used)
        
        if cached:
            self.metrics['genai_cache_hits'].labels(prompt_type=prompt_type).inc()
        
        if quality_score is not None:
            self.metrics['genai_quality_score'].labels(
                prompt_type=prompt_type
            ).observe(quality_score)
    
    def record_oci_api_call(
        self, 
        service: str, 
        operation: str, 
        status: str, 
        duration: float
    ):
        """Record OCI API call metrics"""
        if not self.enabled:
            return
            
        self.metrics['oci_api_calls'].labels(
            service=service, operation=operation, status=status
        ).inc()
        
        self.metrics['oci_api_duration'].labels(
            service=service, operation=operation
        ).observe(duration)
    
    def update_oci_resource_metrics(
        self, 
        compartment: str, 
        resource_type: str, 
        count: int,
        health_data: Optional[Dict[str, float]] = None
    ):
        """Update OCI resource metrics"""
        if not self.enabled:
            return
            
        self.metrics['oci_resources_discovered'].labels(
            compartment=compartment, resource_type=resource_type
        ).set(count)
        
        if health_data:
            for resource_id, health_score in health_data.items():
                self.metrics['oci_resource_health'].labels(
                    compartment=compartment, 
                    resource_type=resource_type,
                    resource_id=resource_id
                ).set(health_score)
    
    def update_system_metrics(self):
        """Update system performance metrics"""
        if not self.enabled:
            return
            
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].labels(type='total').set(memory.total)
            self.metrics['memory_usage'].labels(type='available').set(memory.available)
            self.metrics['memory_usage'].labels(type='used').set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics['disk_usage'].labels(mount_point='/', type='total').set(disk.total)
            self.metrics['disk_usage'].labels(mount_point='/', type='used').set(disk.used)
            self.metrics['disk_usage'].labels(mount_point='/', type='free').set(disk.free)
            
        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")
    
    def record_user_activity(self, user_role: str, feature: str):
        """Record user activity metrics"""
        if not self.enabled:
            return
            
        self.metrics['feature_usage'].labels(
            feature=feature, user_role=user_role
        ).inc()
    
    def record_alert(
        self, 
        alert_type: str, 
        severity: str, 
        source: str, 
        action: str = "generated"
    ):
        """Record alert metrics"""
        if not self.enabled:
            return
            
        if action == "generated":
            self.metrics['alerts_generated'].labels(
                alert_type=alert_type, severity=severity, source=source
            ).inc()
        elif action == "resolved":
            self.metrics['alerts_resolved'].labels(
                alert_type=alert_type, resolution_method=source
            ).inc()
    
    def record_remediation(
        self, 
        remediation_type: str, 
        status: str, 
        success_rate: Optional[float] = None
    ):
        """Record remediation metrics"""
        if not self.enabled:
            return
            
        self.metrics['remediations_executed'].labels(
            remediation_type=remediation_type, status=status
        ).inc()
        
        if success_rate is not None:
            self.metrics['remediation_success_rate'].labels(
                remediation_type=remediation_type
            ).set(success_rate)
    
    def create_custom_metric(self, definition: MetricDefinition) -> Any:
        """Create a custom metric"""
        if not self.enabled:
            return None
            
        metric_class_map = {
            'counter': Counter,
            'histogram': Histogram,
            'gauge': Gauge,
            'summary': Summary
        }
        
        metric_class = metric_class_map.get(definition.metric_type.lower())
        if not metric_class:
            raise ValueError(f"Unsupported metric type: {definition.metric_type}")
        
        kwargs = {
            'name': f'genai_cloudops_{definition.name}',
            'documentation': definition.description,
            'labelnames': definition.labels,
            'registry': self.registry
        }
        
        if definition.metric_type.lower() == 'histogram' and definition.buckets:
            kwargs['buckets'] = definition.buckets
        
        metric = metric_class(**kwargs)
        self.custom_metrics[definition.name] = metric
        
        return metric
    
    def get_custom_metric(self, name: str) -> Optional[Any]:
        """Get a custom metric by name"""
        return self.custom_metrics.get(name)
    
    async def start_system_monitoring(self, interval: int = 30):
        """Start periodic system monitoring"""
        if not self.enabled:
            return
            
        logger.info(f"Starting system monitoring with {interval}s interval")
        
        while True:
            try:
                self.update_system_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(interval)
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        if not self.enabled:
            return ""
            
        try:
            return generate_latest(self.registry)
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return ""
    
    def get_metrics_content_type(self) -> str:
        """Get the appropriate content type for metrics"""
        return CONTENT_TYPE_LATEST
    
    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        if not self.enabled:
            return
            
        for metric in self.metrics.values():
            if hasattr(metric, 'clear'):
                metric.clear()
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get application health metrics summary"""
        if not self.enabled:
            return {"enabled": False}
            
        try:
            # Get basic system info
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "enabled": True,
                "system": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "disk_usage_percent": (disk.used / disk.total) * 100,
                    "uptime_seconds": time.time() - psutil.boot_time()
                },
                "metrics": {
                    "total_metrics": len(self.metrics) + len(self.custom_metrics),
                    "custom_metrics": len(self.custom_metrics),
                    "last_export": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get health metrics: {e}")
            return {"enabled": True, "error": str(e)}

class MetricsMiddleware:
    """Middleware for automatic HTTP request metrics collection"""
    
    def __init__(self, prometheus_service: PrometheusMetricsService):
        self.prometheus = prometheus_service
    
    async def __call__(self, request, call_next):
        """Process request and record metrics"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record HTTP metrics
            self.prometheus.record_http_request(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record failed request
            self.prometheus.record_http_request(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=500,
                duration=duration
            )
            
            raise e
    
    def _get_endpoint_name(self, request) -> str:
        """Extract endpoint name from request"""
        path = request.url.path
        
        # Normalize dynamic path segments
        normalized_segments = []
        for segment in path.split('/'):
            if segment.isdigit() or self._looks_like_id(segment):
                normalized_segments.append('{id}')
            else:
                normalized_segments.append(segment)
        
        return '/'.join(normalized_segments)
    
    def _looks_like_id(self, segment: str) -> bool:
        """Check if segment looks like an ID"""
        if len(segment) > 20:  # UUID-like
            return True
        if segment.startswith('task-') or segment.startswith('user-'):
            return True
        return False

# Global service instance
_prometheus_service = None

def get_prometheus_service() -> PrometheusMetricsService:
    """Get global Prometheus service instance"""
    global _prometheus_service
    if _prometheus_service is None:
        _prometheus_service = PrometheusMetricsService()
    return _prometheus_service

def init_prometheus_service() -> PrometheusMetricsService:
    """Initialize Prometheus service"""
    return get_prometheus_service() 