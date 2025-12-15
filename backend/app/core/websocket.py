"""
WebSocket Manager for Real-time Data Updates
Handles WebSocket connections, broadcasting, subscriptions, and permission-based access
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.models.user import User
from app.core.exceptions import WebSocketError

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """WebSocket message types"""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    
    # Subscriptions
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    
    # Data streams
    METRICS_UPDATE = "metrics_update"
    ALERT_NOTIFICATION = "alert_notification"
    ACTION_STATUS_UPDATE = "action_status_update"
    RESOURCE_UPDATE = "resource_update"
    COST_UPDATE = "cost_update"
    
    # System messages
    ERROR = "error"
    SUCCESS = "success"
    HEARTBEAT = "heartbeat"

class SubscriptionType(str, Enum):
    """Types of data subscriptions"""
    DASHBOARD_METRICS = "dashboard_metrics"
    ALERTS = "alerts"
    REMEDIATION_ACTIONS = "remediation_actions"
    KUBERNETES_PODS = "kubernetes_pods"
    COST_ANALYSIS = "cost_analysis"
    SYSTEM_HEALTH = "system_health"

@dataclass
class WebSocketMessage:
    """Standard WebSocket message format"""
    type: MessageType
    data: Any
    timestamp: str = None
    subscription: Optional[SubscriptionType] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    websocket: WebSocket
    user: User
    subscriptions: Set[SubscriptionType]
    connected_at: datetime
    last_ping: datetime
    
    def __post_init__(self):
        if not hasattr(self, 'subscriptions'):
            self.subscriptions = set()
        if not hasattr(self, 'connected_at'):
            self.connected_at = datetime.now()
        if not hasattr(self, 'last_ping'):
            self.last_ping = datetime.now()

class WebSocketManager:
    """Manages WebSocket connections and real-time data broadcasting"""
    
    def __init__(self):
        # Active connections: connection_id -> ConnectionInfo
        self.connections: Dict[str, ConnectionInfo] = {}
        
        # Subscription mapping: subscription_type -> set of connection_ids
        self.subscriptions: Dict[SubscriptionType, Set[str]] = {
            subscription_type: set() for subscription_type in SubscriptionType
        }
        
        # Message queue for reliable delivery
        self.message_queue: Dict[str, List[WebSocketMessage]] = {}
        
        # Heartbeat configuration
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 60  # seconds
        
        # Start background tasks
        self._background_tasks = []
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for connection management"""
        # Note: In production, these should be started with the FastAPI lifespan events
        pass
    
    async def connect(self, websocket: WebSocket, user: User) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        connection_id = f"{user.id}_{int(time.time() * 1000)}"
        
        connection_info = ConnectionInfo(
            websocket=websocket,
            user=user,
            subscriptions=set(),
            connected_at=datetime.now(),
            last_ping=datetime.now()
        )
        
        self.connections[connection_id] = connection_info
        
        # Send connection success message
        message = WebSocketMessage(
            type=MessageType.CONNECT,
            data={
                "connection_id": connection_id,
                "user_id": str(user.id),
                "username": user.username,
                "connected_at": connection_info.connected_at.isoformat()
            },
            user_id=str(user.id)
        )
        
        await self._send_to_connection(connection_id, message)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user.username})")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        
        # Remove from all subscriptions
        for subscription_type in connection_info.subscriptions:
            self.subscriptions[subscription_type].discard(connection_id)
        
        # Remove connection
        del self.connections[connection_id]
        
        # Clean up message queue
        self.message_queue.pop(connection_id, None)
        
        logger.info(f"WebSocket disconnected: {connection_id} (user: {connection_info.user.username})")
    
    async def subscribe(self, connection_id: str, subscription_type: SubscriptionType) -> bool:
        """Subscribe a connection to a data stream"""
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        # Check permissions
        if not self._check_subscription_permission(connection_info.user, subscription_type):
            await self._send_error(connection_id, f"Permission denied for subscription: {subscription_type}")
            return False
        
        # Add subscription
        connection_info.subscriptions.add(subscription_type)
        self.subscriptions[subscription_type].add(connection_id)
        
        # Send subscription success
        message = WebSocketMessage(
            type=MessageType.SUBSCRIBE,
            data={
                "subscription": subscription_type.value,
                "status": "subscribed"
            },
            subscription=subscription_type,
            user_id=str(connection_info.user.id)
        )
        
        await self._send_to_connection(connection_id, message)
        
        logger.info(f"Subscription added: {connection_id} -> {subscription_type}")
        return True
    
    async def unsubscribe(self, connection_id: str, subscription_type: SubscriptionType) -> bool:
        """Unsubscribe a connection from a data stream"""
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        # Remove subscription
        connection_info.subscriptions.discard(subscription_type)
        self.subscriptions[subscription_type].discard(connection_id)
        
        # Send unsubscription success
        message = WebSocketMessage(
            type=MessageType.UNSUBSCRIBE,
            data={
                "subscription": subscription_type.value,
                "status": "unsubscribed"
            },
            subscription=subscription_type,
            user_id=str(connection_info.user.id)
        )
        
        await self._send_to_connection(connection_id, message)
        
        logger.info(f"Subscription removed: {connection_id} -> {subscription_type}")
        return True
    
    async def broadcast_to_subscription(self, subscription_type: SubscriptionType, data: Any):
        """Broadcast data to all subscribers of a specific type"""
        if subscription_type not in self.subscriptions:
            return
        
        connection_ids = self.subscriptions[subscription_type].copy()
        
        if not connection_ids:
            return
        
        message = WebSocketMessage(
            type=MessageType.METRICS_UPDATE if subscription_type == SubscriptionType.DASHBOARD_METRICS else MessageType.ALERT_NOTIFICATION,
            data=data,
            subscription=subscription_type
        )
        
        # Send to all subscribers
        disconnect_list = []
        for connection_id in connection_ids:
            try:
                await self._send_to_connection(connection_id, message)
            except Exception as e:
                logger.error(f"Failed to send to {connection_id}: {e}")
                disconnect_list.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnect_list:
            await self.disconnect(connection_id)
    
    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcast an alert notification"""
        await self.broadcast_to_subscription(SubscriptionType.ALERTS, alert_data)
    
    async def broadcast_metrics(self, metrics_data: Dict[str, Any]):
        """Broadcast dashboard metrics"""
        await self.broadcast_to_subscription(SubscriptionType.DASHBOARD_METRICS, metrics_data)
    
    async def broadcast_action_status(self, action_data: Dict[str, Any]):
        """Broadcast remediation action status update"""
        await self.broadcast_to_subscription(SubscriptionType.REMEDIATION_ACTIONS, {
            "type": "action_status_update",
            "data": action_data
        })
    
    async def broadcast_cost_update(self, cost_data: Dict[str, Any]):
        """Broadcast cost analysis update"""
        await self.broadcast_to_subscription(SubscriptionType.COST_ANALYSIS, cost_data)
    
    async def handle_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            message_type = MessageType(message_data.get("type"))
            data = message_data.get("data", {})
            
            if message_type == MessageType.PING:
                await self._handle_ping(connection_id)
            elif message_type == MessageType.SUBSCRIBE:
                subscription_type = SubscriptionType(data.get("subscription"))
                await self.subscribe(connection_id, subscription_type)
            elif message_type == MessageType.UNSUBSCRIBE:
                subscription_type = SubscriptionType(data.get("subscription"))
                await self.unsubscribe(connection_id, subscription_type)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self._send_error(connection_id, f"Invalid message: {str(e)}")
    
    async def _handle_ping(self, connection_id: str):
        """Handle ping message and respond with pong"""
        if connection_id in self.connections:
            self.connections[connection_id].last_ping = datetime.now()
            
            pong_message = WebSocketMessage(
                type=MessageType.PONG,
                data={"timestamp": datetime.now().isoformat()}
            )
            
            await self._send_to_connection(connection_id, pong_message)
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send a message to a specific connection"""
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        websocket = connection_info.websocket
        
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send an error message to a connection"""
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message}
        )
        await self._send_to_connection(connection_id, error_msg)
    
    def _check_subscription_permission(self, user: User, subscription_type: SubscriptionType) -> bool:
        """Check if user has permission for a subscription type"""
        # TODO: Implement proper permission checking based on user roles
        # For now, allow all authenticated users to subscribe to basic streams
        
        permission_map = {
            SubscriptionType.DASHBOARD_METRICS: True,  # All users can view dashboard
            SubscriptionType.ALERTS: getattr(user, 'can_view_alerts', True),
            SubscriptionType.REMEDIATION_ACTIONS: getattr(user, 'can_view_remediation', True),
            SubscriptionType.KUBERNETES_PODS: getattr(user, 'can_view_pod_analyzer', True),
            SubscriptionType.COST_ANALYSIS: getattr(user, 'can_view_cost_analyzer', True),
            SubscriptionType.SYSTEM_HEALTH: True,  # All users can view system health
        }
        
        return permission_map.get(subscription_type, False)
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections based on heartbeat timeout"""
        current_time = datetime.now()
        stale_connections = []
        
        for connection_id, connection_info in self.connections.items():
            time_since_ping = (current_time - connection_info.last_ping).total_seconds()
            
            if time_since_ping > self.connection_timeout:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            logger.info(f"Cleaning up stale connection: {connection_id}")
            await self.disconnect(connection_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections"""
        subscription_counts = {
            sub_type.value: len(connections) 
            for sub_type, connections in self.subscriptions.items()
        }
        
        return {
            "total_connections": len(self.connections),
            "subscription_counts": subscription_counts,
            "active_subscriptions": sum(subscription_counts.values()),
            "connections_by_user": {
                conn_info.user.username: conn_id 
                for conn_id, conn_info in self.connections.items()
            }
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance"""
    return websocket_manager 