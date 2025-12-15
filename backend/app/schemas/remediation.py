from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.remediation import ActionType, ActionStatus, Severity

# Base schemas
class RemediationActionBase(BaseModel):
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    action_type: ActionType = Field(..., description="Type of action to execute")
    action_command: str = Field(..., description="Command or script to execute")
    issue_details: str = Field(..., description="Details of the issue being addressed")
    environment: str = Field(..., description="Target environment")
    service_name: str = Field(..., description="Affected service name")
    severity: Severity = Field(..., description="Severity level")
    action_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    resource_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    requires_approval: bool = Field(True, description="Whether action requires approval")
    rollback_command: Optional[str] = Field(None, description="Command to rollback the action")

class RemediationActionCreate(RemediationActionBase):
    pass

class RemediationActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ActionStatus] = None
    action_parameters: Optional[Dict[str, Any]] = None
    resource_info: Optional[Dict[str, Any]] = None

class RemediationAction(RemediationActionBase):
    id: int
    status: ActionStatus
    is_dry_run: bool
    created_by: int
    approved_by: Optional[int]
    executed_by: Optional[int]
    created_at: Optional[datetime]
    approved_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_result: Optional[str]
    execution_output: Optional[str]
    execution_error: Optional[str]
    execution_duration: Optional[float]
    rollback_executed: bool
    rollback_result: Optional[str]

    class Config:
        orm_mode = True

# Audit Log schemas
class RemediationAuditLogBase(BaseModel):
    event_type: str = Field(..., description="Type of event")
    event_description: str = Field(..., description="Description of the event")
    event_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

class RemediationAuditLogCreate(RemediationAuditLogBase):
    action_id: int
    user_id: Optional[int] = None

class RemediationAuditLog(RemediationAuditLogBase):
    id: int
    action_id: int
    user_id: Optional[int]
    timestamp: datetime

    class Config:
        orm_mode = True

# Approval Workflow schemas
class ApprovalWorkflowBase(BaseModel):
    approval_required: bool = True
    auto_approve_conditions: Optional[Dict[str, Any]] = None
    required_approvers: int = 1
    workflow_config: Optional[Dict[str, Any]] = None

class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    action_id: int

class ApprovalWorkflow(ApprovalWorkflowBase):
    id: int
    action_id: int
    current_step: int
    total_steps: int
    workflow_status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True

# Approval Step schemas
class ApprovalStepBase(BaseModel):
    step_name: str = Field(..., description="Name of the approval step")
    required_role: Optional[str] = None
    required_permissions: Optional[Dict[str, Any]] = None
    deadline: Optional[datetime] = None
    auto_approve_after: Optional[datetime] = None
    step_data: Optional[Dict[str, Any]] = None

class ApprovalStepCreate(ApprovalStepBase):
    workflow_id: int
    step_number: int

class ApprovalStepUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[int] = None
    rejection_reason: Optional[str] = None

class ApprovalStep(ApprovalStepBase):
    id: int
    workflow_id: int
    step_number: int
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]

    class Config:
        orm_mode = True

# Action Queue schemas
class ActionQueueBase(BaseModel):
    priority: int = Field(5, description="Priority level (1-10, 1 being highest)")
    queue_name: str = Field("default", description="Queue name")
    scheduled_for: Optional[datetime] = None
    max_retries: int = 3

class ActionQueueCreate(ActionQueueBase):
    action_id: int

class ActionQueueUpdate(BaseModel):
    priority: Optional[int] = None
    queue_status: Optional[str] = None
    retry_count: Optional[int] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None

class ActionQueue(ActionQueueBase):
    id: int
    action_id: int
    retry_count: int
    queue_status: str
    error_message: Optional[str]
    queued_at: datetime
    processed_at: Optional[datetime]

    class Config:
        orm_mode = True

# Combined response schemas
class ActionStatusResponse(BaseModel):
    action: RemediationAction
    audit_logs: List[RemediationAuditLog]
    workflow: Optional[ApprovalWorkflow]
    queue_info: Optional[ActionQueue]

class ActionListResponse(BaseModel):
    actions: List[RemediationAction]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class ExecutionResult(BaseModel):
    status: str = Field(..., description="Execution status")
    output: str = Field(..., description="Command output")
    error: Optional[str] = Field(None, description="Error message if any")
    duration: float = Field(..., description="Execution duration in seconds")
    return_code: Optional[int] = Field(None, description="Command return code")

class ApprovalRequest(BaseModel):
    approval_comment: Optional[str] = Field(None, description="Comment for approval")

class ExecuteActionRequest(BaseModel):
    is_dry_run: bool = Field(False, description="Whether to perform a dry run")
    scheduled_for: Optional[datetime] = Field(None, description="Schedule execution for later")

# Configuration schemas
class ActionTypeInfo(BaseModel):
    type: str
    description: str
    supported_commands: List[str]
    safety_checks: List[str]

class SystemConfiguration(BaseModel):
    max_execution_time: int
    terraform_workspace: str
    supported_action_types: List[ActionTypeInfo]
    approval_workflows: Dict[str, Any]
    notification_settings: Dict[str, Any] 