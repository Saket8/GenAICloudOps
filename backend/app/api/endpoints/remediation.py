from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.remediation_service import get_remediation_service
from app.models.user import User
from app.models.remediation import ActionType, ActionStatus, Severity
from app.core.permissions import require_permissions
import logging
from datetime import datetime
from sqlalchemy import or_

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response

class CreateActionRequest(BaseModel):
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    action_type: ActionType = Field(..., description="Type of action to execute")
    action_command: str = Field(..., description="Command or script to execute")
    issue_details: str = Field(..., description="Details of the issue being addressed")
    environment: str = Field(..., description="Target environment")
    service_name: str = Field(..., description="Affected service name")
    severity: Severity = Field(..., description="Severity level")
    action_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    resource_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Resource information")
    requires_approval: bool = Field(True, description="Whether action requires approval")
    rollback_command: Optional[str] = Field(None, description="Command to rollback the action")

class ActionResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    action_type: str
    severity: str
    environment: str
    service_name: str
    created_at: Optional[str]
    requires_approval: bool
    rollback_executed: bool

class ExecuteActionRequest(BaseModel):
    is_dry_run: bool = Field(False, description="Whether to perform a dry run")

class ApprovalRequest(BaseModel):
    approval_comment: Optional[str] = Field(None, description="Comment for approval")

class ExecutionResult(BaseModel):
    status: str
    output: str
    error: Optional[str]
    duration: float

class ActionStatusResponse(BaseModel):
    action: Dict[str, Any]
    audit_logs: List[Dict[str, Any]]
    workflow: Optional[Dict[str, Any]]

class ListActionsRequest(BaseModel):
    status_filter: Optional[List[ActionStatus]] = Field(None, description="Filter by status")
    environment_filter: Optional[str] = Field(None, description="Filter by environment")
    severity_filter: Optional[List[Severity]] = Field(None, description="Filter by severity")
    limit: int = Field(100, description="Maximum number of results")
    offset: int = Field(0, description="Offset for pagination")

@router.post("/actions", response_model=ActionResponse)
async def create_remediation_action(
    request: CreateActionRequest,
    current_user: User = Depends(require_permissions("can_execute_remediation")),
    db: Session = Depends(get_db)
):
    """
    Create a new remediation action
    
    **Required permissions:** operator or higher
    """
    try:
        remediation_service = get_remediation_service()
        action = await remediation_service.create_remediation_action(
            title=request.title,
            description=request.description,
            action_type=request.action_type,
            action_command=request.action_command,
            issue_details=request.issue_details,
            environment=request.environment,
            service_name=request.service_name,
            severity=request.severity,
            current_user=current_user,
            action_parameters=request.action_parameters,
            resource_info=request.resource_info,
            requires_approval=request.requires_approval,
            rollback_command=request.rollback_command,
            db=db
        )
        
        return ActionResponse(
            id=action.id,
            title=action.title,
            description=action.description,
            status=action.status.value,
            action_type=action.action_type.value,
            severity=action.severity.value,
            environment=action.environment,
            service_name=action.service_name,
            created_at=action.created_at.isoformat() if action.created_at else None,
            requires_approval=action.requires_approval,
            rollback_executed=action.rollback_executed
        )
        
    except Exception as e:
        logger.error(f"Failed to create remediation action: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create action: {str(e)}"
        )

@router.post("/actions/{action_id}/approve")
async def approve_action(
    action_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(require_permissions("can_execute_remediation")),
    db: Session = Depends(get_db)
):
    """
    Approve a remediation action
    
    **Required permissions:** operator or higher
    """
    try:
        remediation_service = get_remediation_service()
        success = await remediation_service.approve_action(
            action_id=action_id,
            current_user=current_user,
            approval_comment=request.approval_comment,
            db=db
        )
        
        return {
            "success": success,
            "message": f"Action {action_id} approved successfully",
            "action_id": action_id
        }
        
    except Exception as e:
        logger.error(f"Failed to approve action {action_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve action: {str(e)}"
        )

@router.post("/actions/{action_id}/execute", response_model=ExecutionResult)
async def execute_action(
    action_id: int,
    request: ExecuteActionRequest,
    current_user: User = Depends(require_permissions("can_execute_remediation")),
    db: Session = Depends(get_db)
):
    """
    Execute a remediation action
    
    **Required permissions:** operator or higher
    """
    try:
        remediation_service = get_remediation_service()
        result = await remediation_service.execute_action(
            action_id=action_id,
            current_user=current_user,
            is_dry_run=request.is_dry_run,
            db=db
        )
        
        return ExecutionResult(
            status=result["status"],
            output=result["output"],
            error=result.get("error"),
            duration=result["duration"]
        )
        
    except Exception as e:
        logger.error(f"Failed to execute action {action_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute action: {str(e)}"
        )

@router.post("/actions/{action_id}/rollback", response_model=ExecutionResult)
async def rollback_action(
    action_id: int,
    current_user: User = Depends(require_permissions("can_execute_remediation")),
    db: Session = Depends(get_db)
):
    """
    Rollback a completed remediation action
    
    **Required permissions:** operator or higher
    """
    try:
        remediation_service = get_remediation_service()
        result = await remediation_service.rollback_action(
            action_id=action_id,
            current_user=current_user,
            db=db
        )
        
        return ExecutionResult(
            status=result["status"],
            output=result["output"],
            error=result.get("error"),
            duration=result.get("duration", 0)
        )
        
    except Exception as e:
        logger.error(f"Failed to rollback action {action_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to rollback action: {str(e)}"
        )

@router.get("/actions/{action_id}/status", response_model=ActionStatusResponse)
async def get_action_status(
    action_id: int,
    current_user: User = Depends(require_permissions("can_view_dashboard")),
    db: Session = Depends(get_db)
):
    """
    Get detailed status information for an action
    
    **Required permissions:** viewer or higher
    """
    try:
        remediation_service = get_remediation_service()
        status_info = await remediation_service.get_action_status(
            action_id=action_id,
            db=db
        )
        
        return ActionStatusResponse(
            action=status_info["action"],
            audit_logs=status_info["audit_logs"],
            workflow=status_info["workflow"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get action status {action_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action not found or error retrieving status: {str(e)}"
        )

@router.get("/actions", response_model=List[ActionResponse])
async def list_actions(
    status_filter: Optional[str] = Query(None, description="Comma-separated list of statuses"),
    environment_filter: Optional[str] = Query(None, description="Environment filter"),
    severity_filter: Optional[str] = Query(None, description="Comma-separated list of severities"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    auto_generate: bool = Query(True, description="Automatically generate from OCI if no actions exist"),
    current_user: User = Depends(require_permissions("can_view_dashboard")),
    db: Session = Depends(get_db)
):
    """
    List remediation actions with filtering and optional auto-generation
    
    **Required permissions:** viewer or higher
    """
    try:
        remediation_service = get_remediation_service()
        # Parse filter parameters
        status_list = None
        if status_filter:
            status_list = [ActionStatus(s.strip()) for s in status_filter.split(",")]
        
        severity_list = None
        if severity_filter:
            severity_list = [Severity(s.strip()) for s in severity_filter.split(",")]
        
        actions = await remediation_service.list_actions(
            current_user=current_user,
            status_filter=status_list,
            environment_filter=environment_filter,
            severity_filter=severity_list,
            limit=limit,
            offset=offset,
            db=db
        )
        
        # Auto-generate from OCI if no actions exist and user has permission
        if auto_generate and len(actions) == 0:
            try:
                # Check if user can execute remediation (needed for auto-generation)
                if hasattr(current_user, 'user_roles') and any(
                    role.role.can_execute_remediation for role in current_user.user_roles
                ):
                    logger.info("🔄 No actions found, auto-generating from OCI data...")
                    from app.services.remediation_service import generate_oci_remediation_actions
                    
                    generated_actions = await generate_oci_remediation_actions(
                        current_user=current_user,
                        environment=environment_filter or "production",
                        db=db
                    )
                    
                    if generated_actions:
                        # Reload actions to include the newly generated ones
                        actions = await remediation_service.list_actions(
                            current_user=current_user,
                            status_filter=status_list,
                            environment_filter=environment_filter,
                            severity_filter=severity_list,
                            limit=limit,
                            offset=offset,
                            db=db
                        )
                        logger.info(f"✅ Auto-generated {len(generated_actions)} remediation actions")
                    
            except Exception as e:
                logger.warning(f"Auto-generation failed: {e}")
                # Continue without auto-generation if it fails
        
        return [
            ActionResponse(
                id=action["id"],
                title=action["title"],
                description=action["description"],
                status=action["status"],
                action_type=action["action_type"],
                severity=action["severity"],
                environment=action["environment"],
                service_name=action["service_name"],
                created_at=action["created_at"],
                requires_approval=action["requires_approval"],
                rollback_executed=action["rollback_executed"]
            )
            for action in actions
        ]
        
    except Exception as e:
        logger.error(f"Failed to list actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list actions: {str(e)}"
        )

@router.delete("/actions/{action_id}")
async def cancel_action(
    action_id: int,
    current_user: User = Depends(require_permissions("can_execute_remediation")),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending remediation action
    
    **Required permissions:** operator or higher
    """
    try:
        remediation_service = get_remediation_service()
        from app.models.remediation import RemediationAction
        
        action = db.query(RemediationAction).filter(RemediationAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        # Only allow cancellation of pending or queued actions
        if action.status not in [ActionStatus.PENDING, ActionStatus.QUEUED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel action in {action.status} state"
            )
        
        action.status = ActionStatus.CANCELLED
        
        # Create audit log
        await remediation_service._create_audit_log(
            action_id=action.id,
            event_type="cancelled",
            event_description=f"Action cancelled by {current_user.username}",
            user_id=current_user.id,
            db=db
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Action {action_id} cancelled successfully",
            "action_id": action_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel action {action_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel action: {str(e)}"
        )

@router.get("/actions/types")
async def get_action_types(
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get available action types
    
    **Required permissions:** viewer or higher
    """
    remediation_service = get_remediation_service()
    return {
        "action_types": [
            {
                "type": at.value,
                "description": f"Execute {at.value.replace('_', ' ').title()} commands"
            }
            for at in ActionType
        ]
    }

@router.get("/actions/statuses")
async def get_action_statuses(
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get available action statuses
    
    **Required permissions:** viewer or higher
    """
    remediation_service = get_remediation_service()
    return {
        "statuses": [
            {
                "status": status.value,
                "description": f"Action is {status.value.replace('_', ' ')}"
            }
            for status in ActionStatus
        ]
    }

@router.get("/actions/severities")
async def get_severities(
    current_user: User = Depends(require_permissions("can_view_dashboard"))
):
    """
    Get available severity levels
    
    **Required permissions:** viewer or higher
    """
    remediation_service = get_remediation_service()
    return {
        "severities": [
            {
                "severity": sev.value,
                "description": f"{sev.value.title()} priority level"
            }
            for sev in Severity
        ]
    }

@router.get("/health")
async def remediation_health():
    """Check remediation service health"""
    try:
        remediation_service = get_remediation_service()
        # Basic health check
        health_status = {
            "status": "healthy",
            "service": "Remediation",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "unknown",
                "oci_service": "unknown",
                "terraform": "unknown"
            }
        }
        
        # Check database connectivity
        try:
            db = next(get_db())
            from app.models.remediation import RemediationAction
            db.query(RemediationAction).count()
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        
        # Check OCI service
        try:
            if remediation_service.oci_service.oci_available:
                health_status["checks"]["oci_service"] = "healthy"
            else:
                health_status["checks"]["oci_service"] = "unavailable"
        except Exception as e:
            health_status["checks"]["oci_service"] = f"unhealthy: {str(e)}"
        
        # Check terraform availability
        try:
            import shutil
            if shutil.which("terraform"):
                health_status["checks"]["terraform"] = "available"
            else:
                health_status["checks"]["terraform"] = "not_installed"
        except Exception as e:
            health_status["checks"]["terraform"] = f"error: {str(e)}"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Remediation health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Remediation service unhealthy: {str(e)}"
        )

@router.post("/actions/generate-from-oci")
async def generate_oci_remediation_actions(
    environment: str = Query("production", description="Target environment"),
    current_user: User = Depends(require_permissions("can_execute_remediation")),
    db: Session = Depends(get_db)
):
    """
    Generate remediation actions based on real OCI resource monitoring data
    
    **Required permissions:** operator or higher
    """
    try:
        from app.services.remediation_service import generate_oci_remediation_actions
        actions = await generate_oci_remediation_actions(
            current_user=current_user,
            environment=environment,
            db=db
        )
        
        return {
            "success": True,
            "message": f"Generated {len(actions)} remediation actions from real OCI data",
            "actions_created": len(actions),
            "actions": [
                {
                    "id": action.id,
                    "title": action.title,
                    "severity": action.severity.value,
                    "environment": action.environment,
                    "service_name": action.service_name
                }
                for action in actions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to generate OCI remediation actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OCI remediation actions: {str(e)}"
        )

@router.delete("/actions/cleanup-test-data")
async def cleanup_test_data(
    current_user: User = Depends(require_permissions("admin")),
    db: Session = Depends(get_db)
):
    """
    Clean up test/mock remediation data
    
    **Required permissions:** admin
    """
    try:
        remediation_service = get_remediation_service()
        from app.models.remediation import RemediationAction, RemediationAuditLog
        
        # Delete test actions (actions with test data patterns)
        test_patterns = [
            "Test OCI Instance Restart",
            "test",
            "mock",
            "demo",
            "ocid1.instance.test"
        ]
        
        deleted_count = 0
        
        for pattern in test_patterns:
            # Find actions matching test patterns
            test_actions = db.query(RemediationAction).filter(
                or_(
                    RemediationAction.title.ilike(f"%{pattern}%"),
                    RemediationAction.action_command.ilike(f"%{pattern}%"),
                    RemediationAction.service_name.ilike(f"%{pattern}%")
                )
            ).all()
            
            for action in test_actions:
                # Delete associated audit logs first
                db.query(RemediationAuditLog).filter(
                    RemediationAuditLog.action_id == action.id
                ).delete()
                
                # Delete the action
                db.delete(action)
                deleted_count += 1
        
        # Create audit log for cleanup
        await remediation_service._create_audit_log(
            action_id=0,  # System action
            event_type="test_data_cleanup",
            event_description=f"Cleaned up {deleted_count} test remediation actions",
            user_id=current_user.id,
            event_data={"deleted_count": deleted_count, "patterns": test_patterns},
            db=db
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} test remediation actions",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup test data: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup test data: {str(e)}"
        ) 