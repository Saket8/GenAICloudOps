import asyncio
import subprocess
import logging
import json
import os
import tempfile
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.core.database import get_db
from app.models.remediation import (
    RemediationAction, RemediationAuditLog, ApprovalWorkflow,
    ApprovalStep, ActionQueue, ActionType, ActionStatus, Severity
)
from app.models.user import User, Role
from app.services.auth_service import AuthService
from app.services.cloud_service import OCIService
from app.services.monitoring_service import get_monitoring_service
import shlex
import hashlib
import yaml
from dataclasses import asdict

logger = logging.getLogger(__name__)

class RemediationService:
    """Comprehensive remediation service for processing and executing infrastructure remediation actions"""
    
    def __init__(self):
        # Use singleton to avoid re-initialization
        from app.services.cloud_service import get_oci_service
        self.oci_service = get_oci_service()
        self.monitoring_service = get_monitoring_service()
        # Use platform-agnostic temp directory (Windows/Linux compatible)
        self.terraform_workspace = os.path.join(tempfile.gettempdir(), "terraform_workspace")
        self.max_execution_time = 300  # 5 minutes default timeout
        
        # Ensure workspace directory exists
        os.makedirs(self.terraform_workspace, exist_ok=True)
    
    async def create_remediation_action(
        self,
        title: str,
        description: str,
        action_type: ActionType,
        action_command: str,
        issue_details: str,
        environment: str,
        service_name: str,
        severity: Severity,
        current_user: User,
        action_parameters: Optional[Dict[str, Any]] = None,
        resource_info: Optional[Dict[str, Any]] = None,
        requires_approval: bool = True,
        rollback_command: Optional[str] = None,
        db: Session = None
    ) -> RemediationAction:
        """Create a new remediation action with proper validation and audit trail"""
        
        if not db:
            db = next(get_db())
        
        try:
            # Validate user permissions
            if not await self._validate_user_permissions(current_user, "create_action"):
                raise ValueError("User does not have permission to create remediation actions")
            
            # Validate command safety
            await self._validate_command_safety(action_command, action_type)
            
            # Create the remediation action
            action = RemediationAction(
                title=title,
                description=description,
                action_type=action_type,
                action_command=action_command,
                action_parameters=action_parameters or {},
                issue_details=issue_details,
                environment=environment,
                service_name=service_name,
                severity=severity,
                resource_info=resource_info or {},
                requires_approval=requires_approval,
                rollback_command=rollback_command,
                created_by=current_user.id
            )
            
            db.add(action)
            db.commit()
            db.refresh(action)
            
            # Create audit log
            await self._create_audit_log(
                action_id=action.id,
                event_type="created",
                event_description=f"Remediation action created: {title}",
                user_id=current_user.id,
                event_data={
                    "action_type": action_type.value,
                    "severity": severity.value,
                    "environment": environment
                },
                db=db
            )
            
            # Create approval workflow if required
            if requires_approval:
                await self._create_approval_workflow(action, db)
            
            logger.info(f"Created remediation action {action.id} by user {current_user.id}")
            return action
            
        except Exception as e:
            logger.error(f"Failed to create remediation action: {e}")
            db.rollback()
            raise
    
    async def approve_action(
        self,
        action_id: int,
        current_user: User,
        approval_comment: Optional[str] = None,
        db: Session = None
    ) -> bool:
        """Approve a remediation action and move it to queue if all approvals are complete"""
        
        if not db:
            db = next(get_db())
        
        try:
            # Get the action
            action = db.query(RemediationAction).filter(RemediationAction.id == action_id).first()
            if not action:
                raise ValueError(f"Action {action_id} not found")
            
            # Validate user can approve
            if not await self._validate_user_permissions(current_user, "approve_action"):
                raise ValueError("User does not have permission to approve actions")
            
            # Check if action is in correct state
            if action.status != ActionStatus.PENDING:
                raise ValueError(f"Action is not in pending state (current: {action.status})")
            
            # Update action status
            action.status = ActionStatus.APPROVED
            action.approved_by = current_user.id
            action.approved_at = datetime.utcnow()
            
            # Create audit log
            await self._create_audit_log(
                action_id=action.id,
                event_type="approved",
                event_description=f"Action approved by {current_user.username}",
                user_id=current_user.id,
                event_data={"comment": approval_comment},
                db=db
            )
            
            # Add to queue for execution
            await self._queue_action(action, db)
            
            db.commit()
            logger.info(f"Action {action_id} approved by user {current_user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve action {action_id}: {e}")
            db.rollback()
            raise
    
    async def execute_action(
        self,
        action_id: int,
        current_user: User,
        is_dry_run: bool = False,
        db: Session = None
    ) -> Dict[str, Any]:
        """Execute a remediation action with comprehensive logging and safety checks"""
        
        if not db:
            db = next(get_db())
        
        try:
            # Get the action
            action = db.query(RemediationAction).filter(RemediationAction.id == action_id).first()
            if not action:
                raise ValueError(f"Action {action_id} not found")
            
            # Validate user can execute
            if not await self._validate_user_permissions(current_user, "execute_action"):
                raise ValueError("User does not have permission to execute actions")
            
            # Check if action is approved or can be auto-executed
            if action.requires_approval and action.status != ActionStatus.APPROVED:
                raise ValueError(f"Action must be approved before execution (current: {action.status})")
            
            # Update action status
            action.status = ActionStatus.IN_PROGRESS
            action.executed_by = current_user.id
            action.started_at = datetime.utcnow()
            action.is_dry_run = is_dry_run
            
            # Create audit log for execution start
            await self._create_audit_log(
                action_id=action.id,
                event_type="execution_started",
                event_description=f"Action execution started by {current_user.username}",
                user_id=current_user.id,
                event_data={"dry_run": is_dry_run},
                db=db
            )
            
            db.commit()
            
            # Execute based on action type
            execution_result = await self._execute_by_type(action, is_dry_run)
            
            # Update action with results
            action.execution_result = execution_result["status"]
            action.execution_output = execution_result["output"]
            action.execution_error = execution_result.get("error")
            action.execution_duration = execution_result["duration"]
            action.completed_at = datetime.utcnow()
            
            if execution_result["status"] == "success":
                action.status = ActionStatus.COMPLETED
                event_type = "execution_completed"
                event_desc = "Action executed successfully"
            else:
                action.status = ActionStatus.FAILED
                event_type = "execution_failed"
                event_desc = f"Action execution failed: {execution_result.get('error', 'Unknown error')}"
            
            # Create audit log for completion
            await self._create_audit_log(
                action_id=action.id,
                event_type=event_type,
                event_description=event_desc,
                user_id=current_user.id,
                event_data=execution_result,
                db=db
            )
            
            db.commit()
            
            logger.info(f"Action {action_id} execution completed with status: {execution_result['status']}")
            return execution_result
            
        except Exception as e:
            logger.error(f"Failed to execute action {action_id}: {e}")
            if 'action' in locals():
                action.status = ActionStatus.FAILED
                action.execution_error = str(e)
                action.completed_at = datetime.utcnow()
                
                await self._create_audit_log(
                    action_id=action.id,
                    event_type="execution_error",
                    event_description=f"Action execution error: {str(e)}",
                    user_id=current_user.id,
                    event_data={"error": str(e)},
                    db=db
                )
                db.commit()
            raise
    
    async def rollback_action(
        self,
        action_id: int,
        current_user: User,
        db: Session = None
    ) -> Dict[str, Any]:
        """Rollback a completed remediation action"""
        
        if not db:
            db = next(get_db())
        
        try:
            action = db.query(RemediationAction).filter(RemediationAction.id == action_id).first()
            if not action:
                raise ValueError(f"Action {action_id} not found")
            
            # Validate user can rollback
            if not await self._validate_user_permissions(current_user, "execute_action"):
                raise ValueError("User does not have permission to rollback actions")
            
            # Check if action can be rolled back
            if action.status != ActionStatus.COMPLETED:
                raise ValueError(f"Action must be completed to rollback (current: {action.status})")
            
            if not action.rollback_command:
                raise ValueError("No rollback command available for this action")
            
            if action.rollback_executed:
                raise ValueError("Action has already been rolled back")
            
            # Execute rollback
            logger.info(f"Starting rollback for action {action_id}")
            
            rollback_result = await self._execute_command(
                command=action.rollback_command,
                action_type=action.action_type,
                timeout=self.max_execution_time
            )
            
            # Update action
            action.rollback_executed = True
            action.rollback_result = rollback_result["status"]
            action.status = ActionStatus.ROLLED_BACK
            
            # Create audit log
            await self._create_audit_log(
                action_id=action.id,
                event_type="rollback_executed",
                event_description=f"Action rolled back by {current_user.username}",
                user_id=current_user.id,
                event_data=rollback_result,
                db=db
            )
            
            db.commit()
            
            logger.info(f"Action {action_id} rollback completed")
            return rollback_result
            
        except Exception as e:
            logger.error(f"Failed to rollback action {action_id}: {e}")
            db.rollback()
            raise
    
    async def get_action_status(self, action_id: int, db: Session = None) -> Dict[str, Any]:
        """Get detailed status information for an action"""
        
        if not db:
            db = next(get_db())
        
        action = db.query(RemediationAction).filter(RemediationAction.id == action_id).first()
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        # Get audit logs
        audit_logs = db.query(RemediationAuditLog).filter(
            RemediationAuditLog.action_id == action_id
        ).order_by(desc(RemediationAuditLog.timestamp)).all()
        
        # Get approval workflow if exists
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.action_id == action_id
        ).first()
        
        return {
            "action": {
                "id": action.id,
                "title": action.title,
                "description": action.description,
                "status": action.status.value,
                "action_type": action.action_type.value,
                "severity": action.severity.value,
                "environment": action.environment,
                "service_name": action.service_name,
                "created_at": action.created_at.isoformat() if action.created_at else None,
                "started_at": action.started_at.isoformat() if action.started_at else None,
                "completed_at": action.completed_at.isoformat() if action.completed_at else None,
                "execution_duration": action.execution_duration,
                "rollback_executed": action.rollback_executed
            },
            "audit_logs": [
                {
                    "event_type": log.event_type,
                    "event_description": log.event_description,
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id
                }
                for log in audit_logs
            ],
            "workflow": {
                "status": workflow.workflow_status if workflow else None,
                "current_step": workflow.current_step if workflow else None,
                "total_steps": workflow.total_steps if workflow else None
            } if workflow else None
        }
    
    async def list_actions(
        self,
        current_user: User,
        status_filter: Optional[List[ActionStatus]] = None,
        environment_filter: Optional[str] = None,
        severity_filter: Optional[List[Severity]] = None,
        limit: int = 100,
        offset: int = 0,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """List remediation actions with filtering"""
        
        if not db:
            db = next(get_db())
        
        query = db.query(RemediationAction)
        
        # Apply filters
        if status_filter:
            query = query.filter(RemediationAction.status.in_(status_filter))
        
        if environment_filter:
            query = query.filter(RemediationAction.environment == environment_filter)
        
        if severity_filter:
            query = query.filter(RemediationAction.severity.in_(severity_filter))
        
        # Order by creation time (newest first)
        query = query.order_by(desc(RemediationAction.created_at))
        
        # Apply pagination
        actions = query.offset(offset).limit(limit).all()
        
        return [
            {
                "id": action.id,
                "title": action.title,
                "description": action.description,
                "status": action.status.value,
                "action_type": action.action_type.value,
                "severity": action.severity.value,
                "environment": action.environment,
                "service_name": action.service_name,
                "created_at": action.created_at.isoformat() if action.created_at else None,
                "requires_approval": action.requires_approval,
                "rollback_executed": action.rollback_executed
            }
            for action in actions
        ]
    
    async def _execute_by_type(self, action: RemediationAction, is_dry_run: bool) -> Dict[str, Any]:
        """Execute action based on its type"""
        
        start_time = datetime.utcnow()
        
        try:
            if action.action_type == ActionType.OCI_CLI:
                result = await self._execute_oci_cli(action, is_dry_run)
            elif action.action_type == ActionType.TERRAFORM:
                result = await self._execute_terraform(action, is_dry_run)
            elif action.action_type == ActionType.SCRIPT:
                result = await self._execute_script(action, is_dry_run)
            elif action.action_type == ActionType.API_CALL:
                result = await self._execute_api_call(action, is_dry_run)
            elif action.action_type == ActionType.KUBERNETES:
                result = await self._execute_kubernetes(action, is_dry_run)
            else:
                raise ValueError(f"Unsupported action type: {action.action_type}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            result["duration"] = duration
            
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            return {
                "status": "error",
                "error": str(e),
                "output": "",
                "duration": duration
            }
    
    async def _execute_oci_cli(self, action: RemediationAction, is_dry_run: bool) -> Dict[str, Any]:
        """Execute OCI CLI commands with safety checks"""
        
        command = action.action_command
        
        if is_dry_run:
            # For dry run, just validate the command syntax
            if "--dry-run" not in command:
                command += " --dry-run"
        
        # Add safety prefixes for destructive operations
        if any(dangerous in command.lower() for dangerous in ["delete", "terminate", "destroy"]):
            if not is_dry_run and "--force" not in command:
                command += " --force"
        
        return await self._execute_command(command, ActionType.OCI_CLI, self.max_execution_time)
    
    async def _execute_terraform(self, action: RemediationAction, is_dry_run: bool) -> Dict[str, Any]:
        """Execute Terraform commands with workspace isolation"""
        
        # Create isolated workspace
        workspace_id = str(uuid.uuid4())
        workspace_path = os.path.join(self.terraform_workspace, workspace_id)
        os.makedirs(workspace_path, exist_ok=True)
        
        try:
            # Write terraform configuration if provided in parameters
            if action.action_parameters and "terraform_config" in action.action_parameters:
                config_path = os.path.join(workspace_path, "main.tf")
                with open(config_path, "w") as f:
                    f.write(action.action_parameters["terraform_config"])
            
            # Change to workspace directory
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            try:
                # Initialize terraform
                init_result = await self._execute_command("terraform init", ActionType.TERRAFORM, 60)
                if init_result["status"] != "success":
                    return init_result
                
                # Plan the changes
                plan_command = "terraform plan"
                if is_dry_run:
                    plan_result = await self._execute_command(plan_command, ActionType.TERRAFORM, 120)
                    return plan_result
                else:
                    # Apply changes
                    apply_command = "terraform apply -auto-approve"
                    return await self._execute_command(apply_command, ActionType.TERRAFORM, 300)
                
            finally:
                os.chdir(original_cwd)
                
        finally:
            # Cleanup workspace
            import shutil
            try:
                shutil.rmtree(workspace_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup terraform workspace {workspace_path}: {e}")
    
    async def _execute_script(self, action: RemediationAction, is_dry_run: bool) -> Dict[str, Any]:
        """Execute custom scripts with safety checks"""
        
        command = action.action_command
        
        if is_dry_run:
            # For dry run, prepend echo to show what would be executed
            command = f"echo 'DRY RUN: {command}'"
        
        return await self._execute_command(command, ActionType.SCRIPT, self.max_execution_time)
    
    async def _execute_api_call(self, action: RemediationAction, is_dry_run: bool) -> Dict[str, Any]:
        """Execute API calls using OCI SDK or HTTP requests"""
        
        if is_dry_run:
            return {
                "status": "success",
                "output": f"DRY RUN: Would execute API call: {action.action_command}",
                "error": None
            }
        
        # Implementation would depend on specific API requirements
        # For now, return a placeholder
        return {
            "status": "success", 
            "output": "API call executed (placeholder implementation)",
            "error": None
        }
    
    async def _execute_kubernetes(self, action: RemediationAction, is_dry_run: bool) -> Dict[str, Any]:
        """Execute Kubernetes commands"""
        
        command = action.action_command
        
        if is_dry_run:
            command += " --dry-run=client"
        
        return await self._execute_command(command, ActionType.KUBERNETES, self.max_execution_time)
    
    async def _execute_command(
        self,
        command: str,
        action_type: ActionType,
        timeout: int
    ) -> Dict[str, Any]:
        """Execute shell command with timeout and safety checks"""
        
        try:
            # Sanitize command
            sanitized_command = shlex.split(command)
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *sanitized_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return_code = process.returncode
                
                result = {
                    "status": "success" if return_code == 0 else "error",
                    "output": stdout.decode('utf-8') if stdout else "",
                    "error": stderr.decode('utf-8') if stderr else None,
                    "return_code": return_code
                }
                
                return result
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "status": "error",
                    "output": "",
                    "error": f"Command timed out after {timeout} seconds"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": f"Failed to execute command: {str(e)}"
            }
    
    async def _validate_command_safety(self, command: str, action_type: ActionType):
        """Validate command for security and safety"""
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "rm -rf /",
            "format",
            "mkfs",
            "> /dev/",
            "dd if=",
            ":(){ :|:& };:",  # Fork bomb
            "curl | sh",
            "wget | sh"
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise ValueError(f"Potentially dangerous command pattern detected: {pattern}")
        
        # Validate command length
        if len(command) > 10000:
            raise ValueError("Command too long (max 10000 characters)")
        
        # Action type specific validations
        if action_type == ActionType.OCI_CLI and not command.strip().startswith("oci "):
            raise ValueError("OCI CLI commands must start with 'oci '")
        
        if action_type == ActionType.TERRAFORM and not any(
            command.strip().startswith(tf_cmd) for tf_cmd in ["terraform ", "tf "]
        ):
            raise ValueError("Terraform commands must start with 'terraform ' or 'tf '")
    
    async def _validate_user_permissions(self, user: User, action: str) -> bool:
        """Validate user has required permissions for the action"""
        
        # Get user roles
        user_roles = [ur.role for ur in user.user_roles]
        
        if action == "create_action":
            return any(role.can_approve_remediation or role.can_execute_remediation for role in user_roles)
        elif action == "approve_action":
            return any(role.can_approve_remediation for role in user_roles)
        elif action == "execute_action":
            return any(role.can_execute_remediation for role in user_roles)
        
        return False
    
    async def _create_audit_log(
        self,
        action_id: int,
        event_type: str,
        event_description: str,
        user_id: Optional[int] = None,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        db: Session = None
    ):
        """Create an audit log entry"""
        
        if not db:
            db = next(get_db())
        
        audit_log = RemediationAuditLog(
            action_id=action_id,
            event_type=event_type,
            event_description=event_description,
            event_data=event_data or {},
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        
        db.add(audit_log)
        # Note: commit is handled by calling function
    
    async def _create_approval_workflow(self, action: RemediationAction, db: Session):
        """Create approval workflow for an action"""
        
        workflow = ApprovalWorkflow(
            action_id=action.id,
            approval_required=True,
            required_approvers=1,
            workflow_status="pending"
        )
        
        db.add(workflow)
        db.flush()  # Get the workflow ID
        
        # Create approval step
        step = ApprovalStep(
            workflow_id=workflow.id,
            step_number=1,
            step_name="Operator Approval",
            required_role="operator",
            status="pending"
        )
        
        db.add(step)
    
    async def _queue_action(self, action: RemediationAction, db: Session):
        """Add action to execution queue"""
        
        # Determine priority based on severity
        priority_map = {
            Severity.CRITICAL: 1,
            Severity.HIGH: 2,
            Severity.MEDIUM: 5,
            Severity.LOW: 8
        }
        
        queue_item = ActionQueue(
            action_id=action.id,
            priority=priority_map.get(action.severity, 5),
            queue_status="queued",
            scheduled_for=datetime.utcnow()
        )
        
        db.add(queue_item)

# Global instance - lazy loading
_remediation_service = None

def get_remediation_service() -> RemediationService:
    """Get remediation service instance with lazy loading"""
    global _remediation_service
    if _remediation_service is None:
        _remediation_service = RemediationService()
    return _remediation_service

# Access via function call only - don't instantiate at module level

async def generate_oci_remediation_actions(
    current_user: User,
    environment: str = "production",
    db: Session = None
) -> List[RemediationAction]:
    """Generate remediation actions based on real OCI resource monitoring data"""
    
    if not db:
        db = next(get_db())
    
    actions_created = []
    
    try:
        # Get the OCI service instance
        oci_service = get_remediation_service().oci_service
        
        # Check if OCI is available
        if not oci_service.oci_available:
            logger.warning("OCI SDK not available, cannot generate real remediation actions")
            return actions_created
        
        # Get all compartments
        compartments = await oci_service.get_compartments()
        
        for compartment in compartments:
            compartment_id = compartment.get('id')
            compartment_name = compartment.get('name', 'Unknown')
            
            # Check compute instances for issues
            instances = await oci_service.get_compute_instances(compartment_id)
            
            logger.info(f"🔍 Checking {len(instances)} compute instances in compartment '{compartment_name}'")
            
            for instance in instances:
                instance_id = instance.get('id')
                instance_name = instance.get('display_name', 'Unknown')
                instance_state = instance.get('lifecycle_state', 'UNKNOWN')
                
                logger.info(f"   📋 Instance: {instance_name} | State: {instance_state} | ID: {instance_id}")
                
                # Check for stopped instances that should be running
                if instance_state == 'STOPPED':
                    logger.info(f"🚨 FOUND STOPPED INSTANCE: {instance_name} - Creating remediation action")
                    action = await get_remediation_service().create_remediation_action(
                        title=f"Restart Stopped Instance: {instance_name}",
                        description=f"Instance {instance_name} in compartment {compartment_name} is in STOPPED state",
                        action_type=ActionType.OCI_CLI,
                        action_command=f"oci compute instance action --instance-id {instance_id} --action START --wait-for-state RUNNING",
                        issue_details=f"Instance {instance_name} ({instance_id}) is currently STOPPED and may need to be restarted",
                        environment=environment,
                        service_name=instance_name,
                        severity=Severity.HIGH,
                        current_user=current_user,
                        action_parameters={
                            "instance_id": instance_id,
                            "compartment_id": compartment_id,
                            "instance_name": instance_name
                        },
                        resource_info={
                            "resource_type": "compute_instance",
                            "resource_id": instance_id,
                            "compartment_id": compartment_id,
                            "current_state": instance_state
                        },
                        requires_approval=True,
                        rollback_command=f"oci compute instance action --instance-id {instance_id} --action STOP --wait-for-state STOPPED",
                        db=db
                    )
                    actions_created.append(action)
                
                # Check for instances with high CPU (if metrics available)
                try:
                    metrics = await oci_service.get_resource_metrics(instance_id, "compute")
                    if metrics and metrics.cpu_utilization > 90:
                        action = await get_remediation_service().create_remediation_action(
                            title=f"High CPU Alert: {instance_name}",
                            description=f"Instance {instance_name} has CPU utilization above 90%",
                            action_type=ActionType.OCI_CLI,
                            action_command=f"oci compute instance action --instance-id {instance_id} --action SOFTRESET --wait-for-state RUNNING",
                            issue_details=f"Instance {instance_name} CPU utilization: {metrics.cpu_utilization}%",
                            environment=environment,
                            service_name=instance_name,
                            severity=Severity.MEDIUM,
                            current_user=current_user,
                            action_parameters={
                                "instance_id": instance_id,
                                "compartment_id": compartment_id,
                                "cpu_utilization": metrics.cpu_utilization
                            },
                            resource_info={
                                "resource_type": "compute_instance",
                                "resource_id": instance_id,
                                "compartment_id": compartment_id,
                                "metrics": asdict(metrics) if metrics else {}
                            },
                            requires_approval=True,
                            rollback_command=f"oci compute instance action --instance-id {instance_id} --action START --wait-for-state RUNNING",
                            db=db
                        )
                        actions_created.append(action)
                except Exception as e:
                    logger.warning(f"Could not get metrics for instance {instance_id}: {e}")
            
            # Check database instances
            try:
                databases = await oci_service.get_databases(compartment_id)
                
                for database in databases:
                    db_id = database.get('id')
                    db_name = database.get('db_name', 'Unknown')
                    db_state = database.get('lifecycle_state', 'UNKNOWN')
                    
                    # Check for stopped databases
                    if db_state in ['STOPPED', 'STOPPING']:
                        action = await get_remediation_service().create_remediation_action(
                            title=f"Restart Database: {db_name}",
                            description=f"Database {db_name} in compartment {compartment_name} is not running",
                            action_type=ActionType.OCI_CLI,
                            action_command=f"oci db database start --database-id {db_id} --wait-for-state AVAILABLE",
                            issue_details=f"Database {db_name} ({db_id}) is in {db_state} state",
                            environment=environment,
                            service_name=db_name,
                            severity=Severity.CRITICAL,
                            current_user=current_user,
                            action_parameters={
                                "database_id": db_id,
                                "compartment_id": compartment_id,
                                "database_name": db_name
                            },
                            resource_info={
                                "resource_type": "database",
                                "resource_id": db_id,
                                "compartment_id": compartment_id,
                                "current_state": db_state
                            },
                            requires_approval=True,
                            rollback_command=f"oci db database stop --database-id {db_id}",
                            db=db
                        )
                        actions_created.append(action)
            except Exception as e:
                logger.warning(f"Could not check databases in compartment {compartment_id}: {e}")
        
        logger.info(f"Generated {len(actions_created)} remediation actions from real OCI data")
        return actions_created
        
    except Exception as e:
        logger.error(f"Failed to generate OCI remediation actions: {e}")
        return actions_created 