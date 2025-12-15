from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .user import Base

class ActionType(str, enum.Enum):
    OCI_CLI = "oci_cli"
    TERRAFORM = "terraform"
    SCRIPT = "script"
    API_CALL = "api_call"
    KUBERNETES = "kubernetes"

class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RemediationAction(Base):
    __tablename__ = "remediation_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Action details
    action_type = Column(Enum(ActionType), nullable=False)
    action_command = Column(Text, nullable=False)  # CLI command or script
    action_parameters = Column(JSON, nullable=True)  # Additional parameters
    
    # Context information
    issue_details = Column(Text, nullable=False)
    environment = Column(String(100), nullable=False)
    service_name = Column(String(100), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    resource_info = Column(JSON, nullable=True)
    
    # Status and workflow
    status = Column(Enum(ActionStatus), default=ActionStatus.PENDING)
    requires_approval = Column(Boolean, default=True)
    is_dry_run = Column(Boolean, default=False)
    
    # User tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    executed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Execution details
    execution_result = Column(Text, nullable=True)
    execution_output = Column(Text, nullable=True)
    execution_error = Column(Text, nullable=True)
    execution_duration = Column(Float, nullable=True)  # seconds
    
    # Rollback information
    rollback_command = Column(Text, nullable=True)
    rollback_executed = Column(Boolean, default=False)
    rollback_result = Column(Text, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    executor = relationship("User", foreign_keys=[executed_by])
    audit_logs = relationship("RemediationAuditLog", back_populates="action", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RemediationAction(id={self.id}, title='{self.title}', status='{self.status}')>"

class RemediationAuditLog(Base):
    __tablename__ = "remediation_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("remediation_actions.id"), nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # created, approved, executed, failed, etc.
    event_description = Column(Text, nullable=False)
    event_data = Column(JSON, nullable=True)  # Additional structured data
    
    # User and timing
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # System context
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Relationships
    action = relationship("RemediationAction", back_populates="audit_logs")
    user = relationship("User")
    
    def __repr__(self):
        return f"<RemediationAuditLog(id={self.id}, action_id={self.action_id}, event_type='{self.event_type}')>"

class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("remediation_actions.id"), nullable=False)
    
    # Workflow configuration
    approval_required = Column(Boolean, default=True)
    auto_approve_conditions = Column(JSON, nullable=True)  # Conditions for auto-approval
    required_approvers = Column(Integer, default=1)
    
    # Current workflow state
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=1)
    workflow_status = Column(String(50), default="pending")
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    workflow_config = Column(JSON, nullable=True)  # Custom workflow configuration
    
    # Relationships
    action = relationship("RemediationAction")
    approvals = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ApprovalWorkflow(id={self.id}, action_id={self.action_id}, status='{self.workflow_status}')>"

class ApprovalStep(Base):
    __tablename__ = "approval_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    
    # Step details
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    required_role = Column(String(50), nullable=True)  # Required role for approval
    required_permissions = Column(JSON, nullable=True)  # Required permissions
    
    # Approval state
    status = Column(String(50), default="pending")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timing constraints
    deadline = Column(DateTime(timezone=True), nullable=True)
    auto_approve_after = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    step_data = Column(JSON, nullable=True)
    
    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="approvals")
    approver = relationship("User")
    
    def __repr__(self):
        return f"<ApprovalStep(id={self.id}, workflow_id={self.workflow_id}, step={self.step_number}, status='{self.status}')>"

class ActionQueue(Base):
    __tablename__ = "action_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("remediation_actions.id"), nullable=False)
    
    # Queue details
    priority = Column(Integer, default=5)  # 1-10, 1 being highest priority
    queue_name = Column(String(100), default="default")
    
    # Scheduling
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Status
    queue_status = Column(String(50), default="queued")
    error_message = Column(Text, nullable=True)
    
    # Timing
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    action = relationship("RemediationAction")
    
    def __repr__(self):
        return f"<ActionQueue(id={self.id}, action_id={self.action_id}, priority={self.priority}, status='{self.queue_status}')>" 