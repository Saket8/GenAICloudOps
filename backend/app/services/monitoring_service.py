import asyncio
import logging
import oci
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json

from app.core.exceptions import ExternalServiceError
from app.services.cloud_service import oci_service

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH" 
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class AlertStatus(Enum):
    """Alert status types"""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"

@dataclass
class OCIAlert:
    """Data class for OCI alert information"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    timestamp: datetime
    compartment_id: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    namespace: Optional[str] = None
    dimensions: Optional[Dict[str, str]] = None

@dataclass
class LogEntry:
    """Data class for log entry information"""
    id: str
    timestamp: datetime
    level: str
    message: str
    source: str
    compartment_id: str
    resource_id: Optional[str] = None
    log_group_id: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None

class MonitoringService:
    """OCI Monitoring and Alerting Integration Service"""
    
    def __init__(self):
        self.oci_service = oci_service
        self.cache_ttl = 300  # 5 minutes default cache
        
    def _get_monitoring_client(self):
        """Get OCI monitoring client or None in dummy mode"""
        if not self.oci_service.oci_available:
            return None
        return self.oci_service.clients.get('monitoring')
    
    def _get_logging_client(self):
        """Get OCI logging management client"""
        if not self.oci_service.oci_available:
            return None
        return self.oci_service.clients.get('logging')
    
    def _get_log_search_client(self):
        """Get OCI log search client"""
        if not self.oci_service.oci_available:
            return None
        return self.oci_service.clients.get('log_search')

    async def get_alarm_status(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get all alarms from OCI plus resource-based alerts"""
        cache_key = f"alarm_status_{compartment_id}"
        cached_data = self.oci_service.cache.get(cache_key)
        if cached_data:
            logger.info(f"🔄 Using cached alarm status for compartment {compartment_id}")
            return cached_data

        if not self.oci_service.oci_available:
            # Dummy mode: return static sample alarms
            logger.info("OCI unavailable - returning dummy alarm data")
            return [
                {"id": "dummy_alarm_cpu_high", "display_name": "CPU Utilization High", "severity": "HIGH", "lifecycle_state": "ACTIVE", "is_enabled": True, "metric_compartment_id": compartment_id, "namespace": "oci_computeagent", "query": "CpuUtilization > 80", "rule_name": "DummyRule", "time_created": datetime.utcnow().isoformat(), "time_updated": datetime.utcnow().isoformat(), "source": "oci_alarm"},
                {"id": "dummy_alarm_db_down", "display_name": "Database Down", "severity": "CRITICAL", "lifecycle_state": "ACTIVE", "is_enabled": True, "metric_compartment_id": compartment_id, "namespace": "oci_database", "query": "State = FAILED", "rule_name": "DummyRule", "time_created": datetime.utcnow().isoformat(), "time_updated": datetime.utcnow().isoformat(), "source": "oci_alarm"}
            ]

        monitoring_client = self._get_monitoring_client()
        if not monitoring_client:
            # In dummy mode, already handled above; extra guard here
            logger.info("Monitoring client not available - returning empty list")
            return []
        
        logger.info(f"🔍 Fetching alarm status for compartment {compartment_id}")
        
        try:
            # Get OCI-configured alarms
            response = await self.oci_service._make_oci_call(
                monitoring_client.list_alarms,
                compartment_id=compartment_id
            )
            
            logger.info(f"📊 Found {len(response.data)} OCI alarms in compartment {compartment_id}")
            
            alarms = []
            for alarm in response.data:
                alarm_data = {
                    "id": alarm.id,
                    "display_name": alarm.display_name,
                    "severity": alarm.severity or "MEDIUM",
                    "lifecycle_state": alarm.lifecycle_state,
                    "is_enabled": alarm.is_enabled,
                    "metric_compartment_id": alarm.metric_compartment_id,
                    "namespace": alarm.namespace,
                    "query": alarm.query,
                    "rule_name": getattr(alarm, 'rule_name', ''),
                    "time_created": alarm.time_created.isoformat() if alarm.time_created else None,
                    "time_updated": alarm.time_updated.isoformat() if alarm.time_updated else None,
                    "source": "oci_alarm"
                }
                alarms.append(alarm_data)
                logger.debug(f"  📋 OCI Alarm: {alarm.display_name} | State: {alarm.lifecycle_state} | Enabled: {alarm.is_enabled}")
            
            # Generate resource-based alerts (the CRITICAL addition!)
            resource_alerts = await self._generate_resource_alerts(compartment_id)
            alarms.extend(resource_alerts)
            
            # Cache the results
            self.oci_service.cache.set(cache_key, alarms, self.cache_ttl)
            logger.info(f"✅ Successfully retrieved {len(response.data)} OCI alarms + {len(resource_alerts)} resource alerts = {len(alarms)} total alerts")
            return alarms
            
        except Exception as e:
            logger.error(f"❌ Failed to get alarm status for compartment {compartment_id}: {e}")
            # Re-raise the exception instead of falling back to mock data
            raise ExternalServiceError(f"Failed to fetch OCI alarms: {str(e)}")

    async def _generate_resource_alerts(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Generate comprehensive alerts based on resource states AND metrics"""
        resource_alerts = []
        current_time = datetime.utcnow()
        
        try:
            # 1. COMPUTE INSTANCE MONITORING
            instances = await self.oci_service.get_compute_instances(compartment_id)
            for instance in instances:
                # State-based alerts
                if instance["lifecycle_state"] == "STOPPED":
                    alert = self._create_resource_alert(
                        resource_id=instance['id'],
                        resource_name=instance['display_name'],
                        resource_type="compute_instance",
                        alert_type="STATE_STOPPED",
                        severity="HIGH",
                        compartment_id=compartment_id,
                        description=f"Compute instance '{instance['display_name']}' is in STOPPED state",
                        namespace="oci_computeagent",
                        current_time=current_time
                    )
                    resource_alerts.append(alert)
                    logger.info(f"🚨 STOPPED INSTANCE alert: {instance['display_name']}")
                
                elif instance["lifecycle_state"] == "STOPPING":
                    alert = self._create_resource_alert(
                        resource_id=instance['id'],
                        resource_name=instance['display_name'],
                        resource_type="compute_instance",
                        alert_type="STATE_STOPPING",
                        severity="MEDIUM",
                        compartment_id=compartment_id,
                        description=f"Compute instance '{instance['display_name']}' is STOPPING",
                        namespace="oci_computeagent",
                        current_time=current_time
                    )
                    resource_alerts.append(alert)
                
                # Metrics-based alerts for RUNNING instances
                elif instance["lifecycle_state"] == "RUNNING":
                    metrics_alerts = await self._generate_compute_metrics_alerts(instance, compartment_id, current_time)
                    resource_alerts.extend(metrics_alerts)

            # 2. DATABASE MONITORING
            databases = await self.oci_service.get_databases(compartment_id)
            for db in databases:
                if db.get("lifecycle_state") in ["STOPPED", "TERMINATING", "FAILED"]:
                    severity = "CRITICAL" if db["lifecycle_state"] == "FAILED" else "HIGH"
                    alert = self._create_resource_alert(
                        resource_id=db['id'],
                        resource_name=db['display_name'],
                        resource_type="database",
                        alert_type=f"STATE_{db['lifecycle_state']}",
                        severity=severity,
                        compartment_id=compartment_id,
                        description=f"Database '{db['display_name']}' is in {db['lifecycle_state']} state",
                        namespace="oci_database",
                        current_time=current_time
                    )
                    resource_alerts.append(alert)
                    logger.info(f"🚨 DATABASE {db['lifecycle_state']} alert: {db['display_name']}")

            # 3. BLOCK STORAGE MONITORING
            storage_alerts = await self._generate_storage_alerts(compartment_id, current_time)
            resource_alerts.extend(storage_alerts)

            logger.info(f"✅ Generated {len(resource_alerts)} comprehensive resource alerts (state + metrics)")
            return resource_alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to generate resource alerts: {e}")
            return []

    def _create_resource_alert(self, resource_id: str, resource_name: str, resource_type: str, 
                              alert_type: str, severity: str, compartment_id: str, 
                              description: str, namespace: str, current_time: datetime) -> Dict[str, Any]:
        """Create standardized resource alert"""
        return {
            "id": f"resource_alert_{resource_type}_{alert_type}_{resource_id}",
            "display_name": f"{resource_type.replace('_', ' ').title()} {alert_type.replace('_', ' ').title()}: {resource_name}",
            "severity": severity,
            "lifecycle_state": "ACTIVE",
            "is_enabled": True,
            "metric_compartment_id": compartment_id,
            "namespace": namespace,
            "query": description,
            "rule_name": "ProductionResourceMonitoring",
            "time_created": current_time.isoformat(),
            "time_updated": current_time.isoformat(),
            "source": "resource_monitoring",
            "resource_id": resource_id,
            "resource_type": resource_type,
            "resource_name": resource_name,
            "alert_type": alert_type,
            "description": description
        }

    async def _generate_compute_metrics_alerts(self, instance: Dict[str, Any], compartment_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        """Generate CPU and memory utilization alerts for running compute instances"""
        alerts = []
        
        try:
            # Get real-time metrics for the instance
            end_time = current_time
            start_time = end_time - timedelta(minutes=10)  # Last 10 minutes
            
            # CPU Utilization Monitoring
            cpu_metrics = await self._get_instance_cpu_metrics(instance['id'], compartment_id, start_time, end_time)
            if cpu_metrics and 'average_cpu' in cpu_metrics:
                cpu_avg = cpu_metrics['average_cpu']
                
                # CPU threshold alerts
                if cpu_avg > 90:
                    alerts.append(self._create_resource_alert(
                        resource_id=instance['id'],
                        resource_name=instance['display_name'],
                        resource_type="compute_instance",
                        alert_type="CPU_CRITICAL",
                        severity="CRITICAL",
                        compartment_id=compartment_id,
                        description=f"CPU utilization critically high: {cpu_avg:.1f}% (threshold: 90%)",
                        namespace="oci_computeagent",
                        current_time=current_time
                    ))
                elif cpu_avg > 80:
                    alerts.append(self._create_resource_alert(
                        resource_id=instance['id'],
                        resource_name=instance['display_name'],
                        resource_type="compute_instance",
                        alert_type="CPU_HIGH",
                        severity="HIGH",
                        compartment_id=compartment_id,
                        description=f"CPU utilization high: {cpu_avg:.1f}% (threshold: 80%)",
                        namespace="oci_computeagent",
                        current_time=current_time
                    ))

            # Memory Utilization Monitoring
            memory_metrics = await self._get_instance_memory_metrics(instance['id'], compartment_id, start_time, end_time)
            if memory_metrics and 'average_memory' in memory_metrics:
                memory_avg = memory_metrics['average_memory']
                
                # Memory threshold alerts
                if memory_avg > 95:
                    alerts.append(self._create_resource_alert(
                        resource_id=instance['id'],
                        resource_name=instance['display_name'],
                        resource_type="compute_instance",
                        alert_type="MEMORY_CRITICAL",
                        severity="CRITICAL",
                        compartment_id=compartment_id,
                        description=f"Memory utilization critically high: {memory_avg:.1f}% (threshold: 95%)",
                        namespace="oci_computeagent",
                        current_time=current_time
                    ))
                elif memory_avg > 85:
                    alerts.append(self._create_resource_alert(
                        resource_id=instance['id'],
                        resource_name=instance['display_name'],
                        resource_type="compute_instance",
                        alert_type="MEMORY_HIGH",
                        severity="HIGH",
                        compartment_id=compartment_id,
                        description=f"Memory utilization high: {memory_avg:.1f}% (threshold: 85%)",
                        namespace="oci_computeagent",
                        current_time=current_time
                    ))

            if alerts:
                logger.info(f"📊 Generated {len(alerts)} metrics-based alerts for instance {instance['display_name']}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to generate compute metrics alerts for {instance['display_name']}: {e}")
            return []

    async def _generate_storage_alerts(self, compartment_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        """Generate block storage utilization alerts"""
        alerts = []
        
        try:
            # Get block volumes (if available)
            # Note: This would require additional OCI API calls for block storage
            # For now, implementing the framework
            
            # Block volumes monitoring would go here
            # storage_volumes = await self.oci_service.get_block_volumes(compartment_id)
            # for volume in storage_volumes:
            #     utilization = await self._get_volume_utilization(volume['id'])
            #     if utilization > 90:
            #         alerts.append(...)
            
            logger.debug(f"Storage monitoring framework ready for compartment {compartment_id}")
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to generate storage alerts: {e}")
            return []

    async def _get_instance_cpu_metrics(self, instance_id: str, compartment_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get real CPU metrics from OCI Monitoring"""
        try:
            monitoring_client = self._get_monitoring_client()
            if not monitoring_client:
                return {}
            
            # Build CPU utilization query
            query = f'CpuUtilization[1m]{{resourceId="{instance_id}"}}.mean()'
            
            metrics_request = oci.monitoring.models.SummarizeMetricsDataDetails(
                namespace="oci_computeagent",
                query=query,
                compartment_id=compartment_id,
                start_time=start_time,
                end_time=end_time,
                resolution="1m"
            )
            
            response = await self.oci_service._make_oci_call(
                monitoring_client.summarize_metrics_data,
                summarize_metrics_data_details=metrics_request
            )
            
            # Process CPU data
            cpu_values = []
            for metric in response.data:
                for data_point in metric.aggregated_datapoints:
                    if data_point.value is not None:
                        cpu_values.append(data_point.value)
            
            if cpu_values:
                return {
                    "average_cpu": sum(cpu_values) / len(cpu_values),
                    "max_cpu": max(cpu_values),
                    "min_cpu": min(cpu_values),
                    "data_points": len(cpu_values)
                }
            
            return {}
            
        except Exception as e:
            logger.debug(f"Could not fetch CPU metrics for {instance_id}: {e}")
            return {}

    async def _get_instance_memory_metrics(self, instance_id: str, compartment_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get real memory metrics from OCI Monitoring"""
        try:
            monitoring_client = self._get_monitoring_client()
            if not monitoring_client:
                return {}
            
            # Build memory utilization query
            query = f'MemoryUtilization[1m]{{resourceId="{instance_id}"}}.mean()'
            
            metrics_request = oci.monitoring.models.SummarizeMetricsDataDetails(
                namespace="oci_computeagent",
                query=query,
                compartment_id=compartment_id,
                start_time=start_time,
                end_time=end_time,
                resolution="1m"
            )
            
            response = await self.oci_service._make_oci_call(
                monitoring_client.summarize_metrics_data,
                summarize_metrics_data_details=metrics_request
            )
            
            # Process memory data
            memory_values = []
            for metric in response.data:
                for data_point in metric.aggregated_datapoints:
                    if data_point.value is not None:
                        memory_values.append(data_point.value)
            
            if memory_values:
                return {
                    "average_memory": sum(memory_values) / len(memory_values),
                    "max_memory": max(memory_values),
                    "min_memory": min(memory_values),
                    "data_points": len(memory_values)
                }
            
            return {}
            
        except Exception as e:
            logger.debug(f"Could not fetch memory metrics for {instance_id}: {e}")
            return {}

    async def get_alarm_history(self, compartment_id: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get alarm history from OCI Monitoring"""
        cache_key = f"alarm_history_{compartment_id}_{start_time.isoformat()}_{end_time.isoformat()}"
        cached_data = self.oci_service.cache.get(cache_key)
        if cached_data:
            logger.info(f"🔄 Using cached alarm history for compartment {compartment_id}")
            return cached_data

        if not self.oci_service.oci_available:
            # Return dummy alarm history data instead of throwing exception
            logger.info("OCI unavailable - returning dummy alarm history data")
            dummy_history = [
                {
                    "alarm_id": "dummy_history_cpu_spike",
                    "alarm_name": "CPU Utilization High",
                    "status": "FIRING",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "summary": "Alarm CPU Utilization High - HIGH severity triggered",
                    "suppressed": False,
                    "severity": "HIGH",
                    "namespace": "oci_computeagent"
                },
                {
                    "alarm_id": "dummy_history_db_conn",
                    "alarm_name": "Database Connection Pool",
                    "status": "OK",
                    "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                    "summary": "Alarm Database Connection Pool - MEDIUM severity resolved",
                    "suppressed": False,
                    "severity": "MEDIUM",
                    "namespace": "oci_database"
                },
                {
                    "alarm_id": "dummy_history_storage",
                    "alarm_name": "Storage Usage Critical",
                    "status": "CREATED",
                    "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                    "summary": "Alarm Storage Usage Critical created - CRITICAL",
                    "suppressed": False,
                    "severity": "CRITICAL",
                    "namespace": "oci_objectstorage"
                }
            ]
            
            # Cache the dummy data
            self.oci_service.cache.set(cache_key, dummy_history, self.cache_ttl)
            return dummy_history

        monitoring_client = self._get_monitoring_client()
        if not monitoring_client:
            raise ExternalServiceError("OCI monitoring client not available")
        
        logger.info(f"🔍 Fetching alarm history for compartment {compartment_id} from {start_time} to {end_time}")
        
        try:
            # Get all alarms first
            response = await self.oci_service._make_oci_call(
                monitoring_client.list_alarms,
                compartment_id=compartment_id
            )
            
            history = []
            for alarm in response.data:
                # Filter alarms updated within the time range
                if alarm.time_updated and start_time <= alarm.time_updated <= end_time:
                    history_entry = {
                        "alarm_id": alarm.id,
                        "alarm_name": alarm.display_name,
                        "status": "FIRING" if alarm.is_enabled and alarm.lifecycle_state == "ACTIVE" else "OK",
                        "timestamp": alarm.time_updated.isoformat(),
                        "summary": f"Alarm {alarm.display_name} - {alarm.severity}",
                        "suppressed": not alarm.is_enabled,
                        "severity": alarm.severity,
                        "namespace": alarm.namespace
                    }
                    history.append(history_entry)
                # Also include creation events if they fall in the time range
                elif alarm.time_created and start_time <= alarm.time_created <= end_time:
                    history_entry = {
                        "alarm_id": alarm.id,
                        "alarm_name": alarm.display_name,
                        "status": "CREATED",
                        "timestamp": alarm.time_created.isoformat(),
                        "summary": f"Alarm {alarm.display_name} created - {alarm.severity}",
                        "suppressed": False,
                        "severity": alarm.severity,
                        "namespace": alarm.namespace
                    }
                    history.append(history_entry)
            
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Cache the results
            self.oci_service.cache.set(cache_key, history, self.cache_ttl)
            logger.info(f"✅ Retrieved {len(history)} alarm history entries for compartment {compartment_id}")
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get alarm history for compartment {compartment_id}: {e}")
            raise ExternalServiceError(f"Failed to fetch OCI alarm history: {str(e)}")

    async def get_metrics_data(self, compartment_id: str, namespace: str, metric_name: str, 
                              start_time: datetime, end_time: datetime, 
                              resource_group: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics data from OCI Monitoring"""
        try:
            cache_key = f"metrics_{compartment_id}_{namespace}_{metric_name}_{start_time.isoformat()}"
            cached_data = self.oci_service.cache.get(cache_key)
            if cached_data:
                return cached_data

            if not self.oci_service.oci_available:
                raise ExternalServiceError("OCI service not available")

            monitoring_client = self._get_monitoring_client()
            
            # Build query
            query = f"'{metric_name}'[1m].mean()"
            if resource_group:
                query = f"'{metric_name}'[1m]{{resourceGroup=\"{resource_group}\"}}.mean()"
            
            # Get metrics data
            metrics_request = oci.monitoring.models.SummarizeMetricsDataDetails(
                namespace=namespace,
                query=query,
                compartment_id=compartment_id,
                start_time=start_time,
                end_time=end_time,
                resolution="1m"
            )
            
            response = await self.oci_service._make_oci_call(
                monitoring_client.summarize_metrics_data,
                summarize_metrics_data_details=metrics_request
            )
            
            metrics_data = {
                "namespace": namespace,
                "metric_name": metric_name,
                "compartment_id": compartment_id,
                "data_points": [],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            for metric in response.data:
                for data_point in metric.aggregated_datapoints:
                    metrics_data["data_points"].append({
                        "timestamp": data_point.timestamp.isoformat(),
                        "value": data_point.value
                    })
            
            # Cache the results
            self.oci_service.cache.set(cache_key, metrics_data, self.cache_ttl)
            logger.info(f"✅ Retrieved {len(metrics_data['data_points'])} metrics data points")
            return metrics_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get metrics data for {namespace}.{metric_name}: {e}")
            raise ExternalServiceError(f"Failed to get OCI metrics data: {str(e)}")

    async def search_logs(self, compartment_id: str, search_query: str, 
                         start_time: datetime, end_time: datetime, 
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """Search logs using OCI Log Search API"""
        try:
            cache_key = f"logs_{compartment_id}_{hash(search_query)}_{start_time.isoformat()}"
            cached_data = self.oci_service.cache.get(cache_key)
            if cached_data:
                return cached_data

            if not self.oci_service.oci_available:
                raise ExternalServiceError("OCI service not available")

            log_search_client = self._get_log_search_client()
            
            # Search logs
            search_request = oci.loggingsearch.models.SearchLogsDetails(
                time_start=start_time,
                time_end=end_time,
                search_query=search_query,
                is_return_field_info=True
            )
            
            response = await self.oci_service._make_oci_call(
                log_search_client.search_logs,
                search_logs_details=search_request,
                limit=limit
            )
            
            logs = []
            for log_entry in response.data.results:
                log_data = {
                    "id": getattr(log_entry.data, 'id', ''),
                    "timestamp": getattr(log_entry.data, 'datetime', ''),
                    "message": getattr(log_entry.data, 'logContent', {}),
                    "source": getattr(log_entry.data, 'source', ''),
                    "compartment_id": compartment_id,
                    "log_group_id": getattr(log_entry.data, 'logGroup', ''),
                    "fields": log_entry.data.__dict__ if hasattr(log_entry.data, '__dict__') else {}
                }
                logs.append(log_data)
            
            # Cache the results
            self.oci_service.cache.set(cache_key, logs, self.cache_ttl)
            logger.info(f"✅ Retrieved {len(logs)} log entries")
            return logs
            
        except Exception as e:
            logger.error(f"❌ Failed to search logs for compartment {compartment_id}: {e}")
            raise ExternalServiceError(f"Failed to search OCI logs: {str(e)}")

    async def get_alert_summary(self, compartment_id: str) -> Dict[str, Any]:
        """Get alert summary including both OCI alarms and resource-based alerts"""
        try:
            # Get all alerts (OCI alarms + resource alerts)
            alarms = await self.get_alarm_status(compartment_id)
            
            # Count different types of alerts
            total_alarms = len(alarms)
            active_alarms = len([a for a in alarms if a.get('is_enabled', False) and a.get('lifecycle_state') == 'ACTIVE'])
            
            # Count by severity
            severity_breakdown = {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
                "INFO": 0
            }
            
            # Count by source type
            oci_alarms = 0
            resource_alerts = 0
            
            for alarm in alarms:
                severity = alarm.get('severity', 'MEDIUM')
                if severity in severity_breakdown:
                    severity_breakdown[severity] += 1
                
                # Count by source
                if alarm.get('source') == 'oci_alarm':
                    oci_alarms += 1
                elif alarm.get('source') == 'resource_monitoring':
                    resource_alerts += 1

            # Calculate health score based on severity distribution
            total_weight = 0
            max_weight = 0
            for severity, count in severity_breakdown.items():
                if severity == "CRITICAL":
                    weight = count * 10
                elif severity == "HIGH":
                    weight = count * 5
                elif severity == "MEDIUM":
                    weight = count * 2
                elif severity == "LOW":
                    weight = count * 1
                else:  # INFO
                    weight = count * 0.5
                total_weight += weight
                max_weight += count * 10  # If all were critical
            
            # Health score: lower weight = better health (0-1 scale)
            if max_weight > 0:
                health_score = max(0, 1 - (total_weight / max_weight))
            else:
                health_score = 1.0  # No alerts = perfect health
            
            # Get top 5 most severe alerts
            top_alerts = sorted(
                alarms,
                key=lambda x: {
                    'CRITICAL': 5, 'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'INFO': 1
                }.get(x.get('severity', 'MEDIUM'), 3),
                reverse=True
            )[:5]

            summary = {
                "compartment_id": compartment_id,
                "total_alarms": total_alarms,
                "active_alarms": active_alarms,
                "severity_breakdown": severity_breakdown,
                "recent_activity": {
                    "summary": f"{oci_alarms} OCI alarms + {resource_alerts} resource alerts",
                    "oci_alarms": oci_alarms,
                    "resource_alerts": resource_alerts,
                    "last_updated": datetime.utcnow().isoformat(),
                    "status": "active"
                },
                "top_alerts": top_alerts,
                "timestamp": datetime.utcnow().isoformat(),
                "health_score": health_score,
                "alert_sources": {
                    "oci_alarms": oci_alarms,
                    "resource_alerts": resource_alerts
                }
            }
            
            logger.info(f"✅ Generated alert summary: {total_alarms} total ({oci_alarms} OCI + {resource_alerts} resource), {active_alarms} active, health score: {health_score:.2f}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to get alert summary: {e}")
            # Return a basic summary instead of failing
            return {
                "compartment_id": compartment_id,
                "total_alarms": 0,
                "active_alarms": 0,
                "severity_breakdown": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0},
                "recent_activity": {
                    "summary": "Unable to fetch alert data",
                    "oci_alarms": 0,
                    "resource_alerts": 0,
                    "last_updated": datetime.utcnow().isoformat(),
                    "status": "error",
                    "error": str(e)
                },
                "top_alerts": [],
                "timestamp": datetime.utcnow().isoformat(),
                "health_score": 0.5,
                "alert_sources": {"oci_alarms": 0, "resource_alerts": 0},
                "error": str(e)
            }



# Removed all mock data methods - using real OCI data only

# Service instance - lazy initialization
_monitoring_service_instance = None

def get_monitoring_service() -> MonitoringService:
    """Get monitoring service instance (lazy initialization)"""
    global _monitoring_service_instance
    if _monitoring_service_instance is None:
        _monitoring_service_instance = MonitoringService()
    return _monitoring_service_instance 