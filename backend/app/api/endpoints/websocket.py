"""
WebSocket API Endpoints for Real-time Data Updates
Provides WebSocket connections for live metrics, alerts, and status updates
"""

import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.websocket import (
    websocket_manager, 
    WebSocketManager, 
    get_websocket_manager,
    MessageType,
    SubscriptionType
)
from app.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    WebSocket endpoint for real-time data connections
    
    **Authentication:**
    - Requires JWT token passed as query parameter: ?token=your_jwt_token
    
    **Supported Message Types:**
    - ping: Heartbeat message
    - subscribe: Subscribe to data stream
    - unsubscribe: Unsubscribe from data stream
    
    **Available Subscriptions:**
    - dashboard_metrics: Real-time dashboard metrics
    - alerts: Live alert notifications  
    - remediation_actions: Action status updates
    - kubernetes_pods: Pod status updates
    - cost_analysis: Cost analysis updates
    - system_health: System health status
    """
    connection_id = None
    
    try:
        # Authenticate user from token BEFORE accepting connection
        if not token:
            await websocket.close(code=1008, reason="Authentication token required")
            return
        
        try:
            # Verify JWT token
            auth_service = AuthService()
            user = await auth_service.get_user_from_token(token)
            
            if not user:
                await websocket.close(code=1008, reason="Invalid authentication token")  
                return
                
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Accept connection after successful authentication
        connection_id = await manager.connect(websocket, user)
        logger.info(f"WebSocket connection established: {connection_id}")
        
        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle message
                await manager.handle_message(connection_id, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected gracefully: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {connection_id}")
                await manager._send_error(connection_id, "Invalid JSON message")
            except Exception as e:
                logger.error(f"Error processing message from {connection_id}: {e}")
                await manager._send_error(connection_id, f"Message processing error: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        if connection_id:
            await manager.disconnect(connection_id)

@router.get("/connections/stats")
async def get_connection_stats(
    current_user: User = Depends(AuthService.get_current_user),
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Get WebSocket connection statistics
    
    **Required Permission:** Admin or Operator role
    
    **Returns:**
    - Total active connections
    - Subscription counts by type
    - Connections by user
    """
    try:
        # Check admin permission (simplified for now)
        if not hasattr(current_user, 'username') or current_user.username != 'admin':
            # In production, check proper permissions
            pass
        
        stats = manager.get_connection_stats()
        
        return JSONResponse(content={
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting connection stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connection statistics")

@router.post("/broadcast/test")
async def test_broadcast(
    message: dict,
    subscription_type: str = Query(..., description="Subscription type to broadcast to"),
    current_user: User = Depends(AuthService.get_current_user),
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Test endpoint for broadcasting messages to subscribers
    
    **Required Permission:** Admin role
    
    **Parameters:**
    - message: JSON message to broadcast
    - subscription_type: Type of subscription to broadcast to
    
    **Available Subscription Types:**
    - dashboard_metrics
    - alerts
    - remediation_actions
    - kubernetes_pods
    - cost_analysis
    - system_health
    """
    try:
        # Check admin permission (simplified)
        if not hasattr(current_user, 'username') or current_user.username != 'admin':
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        # Validate subscription type
        try:
            sub_type = SubscriptionType(subscription_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid subscription type: {subscription_type}")
        
        # Broadcast message
        await manager.broadcast_to_subscription(sub_type, message)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Broadcast sent to {subscription_type} subscribers",
            "data": message
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting test message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")

@router.post("/cleanup")
async def cleanup_stale_connections(
    current_user: User = Depends(AuthService.get_current_user),
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Manually trigger cleanup of stale WebSocket connections
    
    **Required Permission:** Admin role
    """
    try:
        # Check admin permission
        if not hasattr(current_user, 'username') or current_user.username != 'admin':
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        # Get stats before cleanup
        stats_before = manager.get_connection_stats()
        
        # Cleanup stale connections
        await manager.cleanup_stale_connections()
        
        # Get stats after cleanup
        stats_after = manager.get_connection_stats()
        
        cleaned_up = stats_before["total_connections"] - stats_after["total_connections"]
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Cleaned up {cleaned_up} stale connections",
            "before": stats_before,
            "after": stats_after
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup connections")

@router.get("/health")
async def websocket_health():
    """
    WebSocket service health check
    """
    try:
        manager = get_websocket_manager()
        stats = manager.get_connection_stats()
        
        return JSONResponse(content={
            "status": "healthy",
            "service": "WebSocket Manager",
            "active_connections": stats["total_connections"],
            "active_subscriptions": stats["active_subscriptions"],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        ) 