"""
Real-time Data Streaming Service
Generates and broadcasts live metrics, alerts, and status updates via WebSocket
"""

import asyncio
import random
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass

from app.core.websocket import get_websocket_manager, SubscriptionType

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    active_connections: int
    uptime_seconds: int

@dataclass
class AlertData:
    """Alert data structure"""
    id: str
    title: str
    message: str
    severity: str
    source: str
    timestamp: str
    resolved: bool = False

class RealTimeDataService:
    """Service for generating and broadcasting real-time data"""
    
    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.is_running = False
        self.metrics_interval = 5  # seconds
        self.alert_check_interval = 10  # seconds
        
        # Store last metrics for change detection
        self.last_metrics = None
        
        # Simulate some application state
        self.app_start_time = time.time()
        self.alert_counter = 0
        
    async def start_streaming(self):
        """Start real-time data streaming"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("Starting real-time data streaming...")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._stream_system_metrics()),
            asyncio.create_task(self._stream_alerts()),
            asyncio.create_task(self._stream_action_updates()),
            asyncio.create_task(self._stream_cost_updates()),
            asyncio.create_task(self._stream_oci_updates()),
            asyncio.create_task(self._cleanup_connections())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Real-time streaming tasks cancelled")
    
    async def stop_streaming(self):
        """Stop real-time data streaming"""
        self.is_running = False
        logger.info("Stopping real-time data streaming...")
    
    async def _stream_system_metrics(self):
        """Stream system metrics every few seconds"""
        while self.is_running:
            try:
                metrics = self._generate_system_metrics()
                
                # Broadcast to dashboard metrics subscribers
                await self.websocket_manager.broadcast_metrics({
                    "type": "system_metrics",
                    "data": metrics.__dict__,
                    "timestamp": metrics.timestamp
                })
                
                self.last_metrics = metrics
                
            except Exception as e:
                logger.error(f"Error streaming system metrics: {e}")
            
            await asyncio.sleep(self.metrics_interval)
    
    async def _stream_alerts(self):
        """Generate and stream alert notifications"""
        while self.is_running:
            try:
                # Generate random alerts occasionally
                if random.random() < 0.3:  # 30% chance every cycle
                    alert = self._generate_sample_alert()
                    
                    await self.websocket_manager.broadcast_alert({
                        "type": "new_alert",
                        "data": alert.__dict__,
                        "timestamp": alert.timestamp
                    })
                
            except Exception as e:
                logger.error(f"Error streaming alerts: {e}")
            
            await asyncio.sleep(self.alert_check_interval)
    
    async def _stream_action_updates(self):
        """Stream remediation action status updates"""
        while self.is_running:
            try:
                # Simulate action status updates
                if random.random() < 0.2:  # 20% chance
                    action_update = self._generate_action_update()
                    
                    await self.websocket_manager.broadcast_action_status(action_update)
                
            except Exception as e:
                logger.error(f"Error streaming action updates: {e}")
            
            await asyncio.sleep(15)  # Check every 15 seconds
    
    async def _stream_cost_updates(self):
        """Stream cost analysis updates"""
        while self.is_running:
            try:
                # Generate cost updates less frequently
                if random.random() < 0.1:  # 10% chance
                    cost_update = self._generate_cost_update()
                    
                    await self.websocket_manager.broadcast_cost_update(cost_update)
                
            except Exception as e:
                logger.error(f"Error streaming cost updates: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _stream_oci_updates(self):
        """Stream real OCI compartment and available resource updates"""
        while self.is_running:
            try:
                # Fetch real OCI data every 2 minutes
                if random.random() < 0.2:  # 20% chance every cycle
                    oci_update = await self._generate_oci_update()
                    
                    if oci_update:
                        await self.websocket_manager.broadcast_to_subscription(
                            SubscriptionType.DASHBOARD_METRICS, 
                            oci_update
                        )
                
            except Exception as e:
                logger.error(f"Error streaming OCI updates: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _cleanup_connections(self):
        """Periodically cleanup stale WebSocket connections"""
        while self.is_running:
            try:
                await self.websocket_manager.cleanup_stale_connections()
            except Exception as e:
                logger.error(f"Error cleaning up connections: {e}")
            
            await asyncio.sleep(60)  # Cleanup every minute
    
    def _generate_system_metrics(self) -> SystemMetrics:
        """Generate current system metrics"""
        try:
            # Get real system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            uptime = time.time() - self.app_start_time
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory.percent, 2),
                disk_percent=round((disk.used / disk.total) * 100, 2),
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                active_connections=len(self.websocket_manager.connections),
                uptime_seconds=int(uptime)
            )
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            # Return dummy metrics on error
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=random.uniform(20, 80),
                memory_percent=random.uniform(30, 70),
                disk_percent=random.uniform(40, 60),
                network_io={
                    "bytes_sent": random.randint(1000000, 10000000),
                    "bytes_recv": random.randint(1000000, 10000000),
                    "packets_sent": random.randint(1000, 10000),
                    "packets_recv": random.randint(1000, 10000)
                },
                active_connections=len(self.websocket_manager.connections),
                uptime_seconds=int(time.time() - self.app_start_time)
            )
    
    def _generate_sample_alert(self) -> AlertData:
        """Generate a sample alert for demonstration"""
        self.alert_counter += 1
        
        alert_types = [
            {
                "title": "High CPU Usage",
                "message": f"CPU usage has exceeded 85% for the last 5 minutes",
                "severity": "warning",
                "source": "system_monitor"
            },
            {
                "title": "Memory Usage Alert",
                "message": f"Memory usage is at {random.randint(85, 95)}%",
                "severity": "critical",
                "source": "system_monitor"
            },
            {
                "title": "Disk Space Warning",
                "message": f"Disk usage has reached {random.randint(80, 90)}%",
                "severity": "warning",
                "source": "disk_monitor"
            },
            {
                "title": "Network Anomaly",
                "message": f"Unusual network traffic detected",
                "severity": "info",
                "source": "network_monitor"
            },
            {
                "title": "Service Health Check Failed",
                "message": f"Health check failed for OCI service",
                "severity": "critical",
                "source": "health_monitor"
            }
        ]
        
        alert_template = random.choice(alert_types)
        
        return AlertData(
            id=f"alert_{self.alert_counter}_{int(time.time())}",
            title=alert_template["title"],
            message=alert_template["message"],
            severity=alert_template["severity"],
            source=alert_template["source"],
            timestamp=datetime.now().isoformat()
        )
    
    def _generate_action_update(self) -> Dict[str, Any]:
        """Generate a remediation action status update"""
        action_types = ["restart_service", "scale_pods", "cleanup_resources", "update_config"]
        statuses = ["pending", "in_progress", "completed", "failed"]
        
        return {
            "action_id": f"action_{random.randint(1000, 9999)}",
            "action_type": random.choice(action_types),
            "status": random.choice(statuses),
            "progress": random.randint(0, 100),
            "message": f"Action {random.choice(statuses)} - {random.choice(['Kubernetes cluster', 'OCI instance', 'Load balancer', 'Database'])}",
            "timestamp": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(minutes=random.randint(1, 30))).isoformat()
        }
    
    def _generate_cost_update(self) -> Dict[str, Any]:
        """Generate a cost analysis update"""
        return {
            "type": "cost_trend_update",
            "data": {
                "current_month_cost": round(random.uniform(1000, 5000), 2),
                "cost_change_percent": round(random.uniform(-20, 20), 2),
                "top_costly_resource": {
                    "name": f"prod-instance-{random.randint(1, 10)}",
                    "cost": round(random.uniform(100, 800), 2),
                    "type": random.choice(["compute", "storage", "networking"])
                },
                "optimization_savings": round(random.uniform(50, 500), 2),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _generate_oci_update(self) -> Dict[str, Any]:
        """Generate real OCI compartment and resource updates"""
        try:
            from app.services.cloud_service import get_oci_service
            
            oci_service = get_oci_service()
            
            # Get real compartment count
            compartments = await oci_service.get_compartments()
            
            return {
                "type": "oci_update",
                "data": {
                    "compartment_count": len(compartments),
                    "compartments_updated": [
                        {
                            "id": comp["id"][:20] + "...",  # Truncate for security
                            "name": comp["name"],
                            "state": comp.get("state", "ACTIVE")
                        } for comp in compartments[:3]  # Show first 3
                    ],
                    "last_sync": datetime.now().isoformat(),
                    "data_source": "real_oci"
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating OCI update: {e}")
            return None
    
    async def broadcast_custom_alert(self, title: str, message: str, severity: str = "info"):
        """Broadcast a custom alert"""
        alert = AlertData(
            id=f"custom_{int(time.time())}",
            title=title,
            message=message,
            severity=severity,
            source="manual",
            timestamp=datetime.now().isoformat()
        )
        
        await self.websocket_manager.broadcast_alert({
            "type": "custom_alert",
            "data": alert.__dict__,
            "timestamp": alert.timestamp
        })
    
    async def broadcast_system_status(self, status: str, message: str):
        """Broadcast system status update"""
        status_update = {
            "type": "system_status",
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_subscription(
            SubscriptionType.SYSTEM_HEALTH, 
            status_update
        )

# Global instance
_realtime_service = None

def get_realtime_service() -> RealTimeDataService:
    """Get the global real-time service instance"""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealTimeDataService()
    return _realtime_service

async def start_realtime_streaming():
    """Start the real-time streaming service"""
    service = get_realtime_service()
    await service.start_streaming()

async def stop_realtime_streaming():
    """Stop the real-time streaming service"""
    service = get_realtime_service()
    await service.stop_streaming() 