"""
Auto-Remediation Service
=======================

This service provides automated remediation capabilities with risk assessment,
approval workflows, and safe execution of remediation actions for the
GenAI CloudOps Dashboard.

Author: GenAI CloudOps Dashboard Team
Created: January 2025
Task: 028 - Implement Optional Enhancements
"""

import json
import logging
import asyncio
import subprocess
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import yaml
import tempfile
import os
from pathlib import Path

from app.core.config import settings
from app.services.notification_service import get_notification_service, NotificationSeverity
from app.services.prometheus_service import get_prometheus_service
from app.services.genai_service import get_genai_service, PromptType

logger = logging.getLogger(__name__)

class RemediationRisk(Enum):
    """Risk levels for remediation actions"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RemediationStatus(Enum):
    """Status of remediation execution"""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_APPROVAL = "requires_approval"

class RemediationType(Enum):
    """Types of remediation actions"""
    OCI_CLI = "oci_cli"
    KUBECTL = "kubectl"
    TERRAFORM = "terraform"
    SCRIPT = "script"
    API_CALL = "api_call"
    CONFIGURATION = "configuration"

@dataclass
class RemediationAction:
    """Individual remediation action definition"""
    id: str
    name: str
    type: RemediationType
    command: str
    description: str
    risk_level: RemediationRisk
    timeout_seconds: int = 300
    requires_approval: bool = True
    rollback_command: Optional[str] = None
    verification_command: Optional[str] = None
    pre_conditions: List[str] = None
    post_conditions: List[str] = None
    environment_variables: Dict[str, str] = None

@dataclass
class RemediationPlan:
    """Complete remediation plan with multiple actions"""
    id: str
    title: str
    description: str
    actions: List[RemediationAction]
    overall_risk: RemediationRisk
    estimated_duration_minutes: int
    affected_resources: List[str]
    prerequisites: List[str]
    approval_required: bool
    auto_execute: bool = False

@dataclass
class RemediationExecution:
    """Remediation execution state tracking"""
    plan_id: str
    execution_id: str
    status: RemediationStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    executed_actions: List[str] = None
    failed_actions: List[str] = None
    rollback_actions: List[str] = None
    approval_user: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    execution_logs: List[str] = None
    error_message: Optional[str] = None

@dataclass
class RiskAssessment:
    """Risk assessment for remediation actions"""
    overall_risk: RemediationRisk
    risk_factors: List[str]
    mitigation_strategies: List[str]
    confidence_score: float
    recommendation: str
    manual_review_required: bool

class AutoRemediationService:
    """Comprehensive auto-remediation service with risk assessment"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'AUTO_REMEDIATION_ENABLED', False)
        self.auto_approval_enabled = getattr(settings, 'AUTO_APPROVAL_ENABLED', False)
        self.max_concurrent_executions = getattr(settings, 'MAX_CONCURRENT_REMEDIATIONS', 3)
        self.dry_run_mode = getattr(settings, 'REMEDIATION_DRY_RUN', True)
        
        # Risk thresholds
        self.auto_approve_threshold = RemediationRisk.LOW
        self.auto_execute_threshold = RemediationRisk.VERY_LOW
        
        # Service dependencies
        self.notification_service = get_notification_service()
        self.prometheus_service = get_prometheus_service()
        self.genai_service = get_genai_service()
        
        # Storage
        self.remediation_plans = {}
        self.executions = {}
        self.risk_assessments = {}
        self.execution_queue = asyncio.Queue()
        self.active_executions = {}
        
        # Approval callbacks
        self.approval_callbacks = {}
        
        if self.enabled:
            self._initialize_default_plans()
            self._start_execution_worker()
            logger.info(f"Auto-remediation service initialized (dry_run={self.dry_run_mode})")
        else:
            logger.info("Auto-remediation service disabled")
    
    def _initialize_default_plans(self):
        """Initialize default remediation plans"""
        
        # OCI Instance Restart Plan
        self.add_remediation_plan(RemediationPlan(
            id="oci_instance_restart",
            title="Restart OCI Compute Instance",
            description="Restart an unresponsive OCI compute instance",
            actions=[
                RemediationAction(
                    id="stop_instance",
                    name="Stop Instance",
                    type=RemediationType.OCI_CLI,
                    command="oci compute instance action --instance-id {instance_id} --action STOP --wait-for-state STOPPED",
                    description="Stop the compute instance",
                    risk_level=RemediationRisk.MEDIUM,
                    timeout_seconds=600,
                    verification_command="oci compute instance get --instance-id {instance_id} --query 'data.\"lifecycle-state\"'"
                ),
                RemediationAction(
                    id="start_instance",
                    name="Start Instance",
                    type=RemediationType.OCI_CLI,
                    command="oci compute instance action --instance-id {instance_id} --action START --wait-for-state RUNNING",
                    description="Start the compute instance",
                    risk_level=RemediationRisk.LOW,
                    timeout_seconds=600,
                    verification_command="oci compute instance get --instance-id {instance_id} --query 'data.\"lifecycle-state\"'"
                )
            ],
            overall_risk=RemediationRisk.MEDIUM,
            estimated_duration_minutes=10,
            affected_resources=["compute_instance"],
            prerequisites=["instance_id"],
            approval_required=True
        ))
        
        # Kubernetes Pod Restart Plan
        self.add_remediation_plan(RemediationPlan(
            id="k8s_pod_restart",
            title="Restart Kubernetes Pod",
            description="Restart a failing Kubernetes pod",
            actions=[
                RemediationAction(
                    id="delete_pod",
                    name="Delete Pod",
                    type=RemediationType.KUBECTL,
                    command="kubectl delete pod {pod_name} -n {namespace} --grace-period=30",
                    description="Delete the failing pod to trigger restart",
                    risk_level=RemediationRisk.LOW,
                    timeout_seconds=120,
                    verification_command="kubectl get pod {pod_name} -n {namespace} -o jsonpath='{.status.phase}'"
                )
            ],
            overall_risk=RemediationRisk.LOW,
            estimated_duration_minutes=3,
            affected_resources=["kubernetes_pod"],
            prerequisites=["pod_name", "namespace"],
            approval_required=False,
            auto_execute=True
        ))
        
        # Database Connection Reset Plan
        self.add_remediation_plan(RemediationPlan(
            id="db_connection_reset",
            title="Reset Database Connections",
            description="Reset database connection pool to resolve connection issues",
            actions=[
                RemediationAction(
                    id="flush_connections",
                    name="Flush Database Connections",
                    type=RemediationType.API_CALL,
                    command="POST /api/v1/database/flush-connections",
                    description="Flush all database connections",
                    risk_level=RemediationRisk.VERY_LOW,
                    timeout_seconds=30
                )
            ],
            overall_risk=RemediationRisk.VERY_LOW,
            estimated_duration_minutes=1,
            affected_resources=["database_connections"],
            prerequisites=[],
            approval_required=False,
            auto_execute=True
        ))
        
        # Disk Space Cleanup Plan
        self.add_remediation_plan(RemediationPlan(
            id="disk_space_cleanup",
            title="Clean Up Disk Space",
            description="Clean up temporary files and logs to free disk space",
            actions=[
                RemediationAction(
                    id="clean_temp_files",
                    name="Clean Temporary Files",
                    type=RemediationType.SCRIPT,
                    command="find /tmp -type f -atime +7 -delete",
                    description="Remove temporary files older than 7 days",
                    risk_level=RemediationRisk.LOW,
                    timeout_seconds=300
                ),
                RemediationAction(
                    id="rotate_logs",
                    name="Rotate Application Logs",
                    type=RemediationType.SCRIPT,
                    command="logrotate /etc/logrotate.d/genai-cloudops",
                    description="Rotate and compress application logs",
                    risk_level=RemediationRisk.VERY_LOW,
                    timeout_seconds=60
                )
            ],
            overall_risk=RemediationRisk.LOW,
            estimated_duration_minutes=5,
            affected_resources=["disk_space"],
            prerequisites=[],
            approval_required=False,
            auto_execute=True
        ))
    
    def add_remediation_plan(self, plan: RemediationPlan):
        """Add a remediation plan"""
        self.remediation_plans[plan.id] = plan
        logger.info(f"Added remediation plan: {plan.title}")
    
    def get_remediation_plan(self, plan_id: str) -> Optional[RemediationPlan]:
        """Get a remediation plan by ID"""
        return self.remediation_plans.get(plan_id)
    
    def list_remediation_plans(self) -> List[RemediationPlan]:
        """List all available remediation plans"""
        return list(self.remediation_plans.values())
    
    async def assess_risk(
        self, 
        plan: RemediationPlan, 
        context: Dict[str, Any]
    ) -> RiskAssessment:
        """Assess the risk of executing a remediation plan"""
        
        try:
            # Use GenAI for risk assessment
            risk_prompt_data = {
                "remediation_title": plan.title,
                "remediation_description": plan.description,
                "actions": [action.description for action in plan.actions],
                "affected_resources": plan.affected_resources,
                "environment_context": context.get("environment", "production"),
                "business_impact": context.get("business_impact", "medium"),
                "time_constraints": context.get("time_constraints", "normal")
            }
            
            # Generate risk assessment using GenAI
            risk_analysis = await self.genai_service.get_analysis(
                PromptType.ANALYSIS,
                data=json.dumps(risk_prompt_data),
                context="risk assessment for auto-remediation"
            )
            
            # Parse GenAI response and determine risk factors
            risk_factors = self._extract_risk_factors(plan, context, risk_analysis.content)
            overall_risk = self._calculate_overall_risk(risk_factors)
            
            assessment = RiskAssessment(
                overall_risk=overall_risk,
                risk_factors=risk_factors,
                mitigation_strategies=self._generate_mitigation_strategies(risk_factors),
                confidence_score=0.85,  # Could be enhanced with more sophisticated scoring
                recommendation=self._generate_recommendation(overall_risk, plan),
                manual_review_required=overall_risk.value in [RemediationRisk.HIGH.value, RemediationRisk.CRITICAL.value]
            )
            
            self.risk_assessments[f"{plan.id}_{int(datetime.utcnow().timestamp())}"] = assessment
            
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed for plan {plan.id}: {e}")
            
            # Fallback to conservative assessment
            return RiskAssessment(
                overall_risk=RemediationRisk.HIGH,
                risk_factors=["Risk assessment failed", "Unknown impact"],
                mitigation_strategies=["Manual review required"],
                confidence_score=0.0,
                recommendation="Manual review and approval required due to assessment failure",
                manual_review_required=True
            )
    
    def _extract_risk_factors(
        self, 
        plan: RemediationPlan, 
        context: Dict[str, Any],
        genai_response: str
    ) -> List[str]:
        """Extract risk factors from plan and context"""
        
        risk_factors = []
        
        # Action-based risk factors
        for action in plan.actions:
            if action.risk_level == RemediationRisk.CRITICAL:
                risk_factors.append(f"Critical risk action: {action.name}")
            elif action.risk_level == RemediationRisk.HIGH:
                risk_factors.append(f"High risk action: {action.name}")
        
        # Environment-based risk factors
        environment = context.get("environment", "unknown")
        if environment == "production":
            risk_factors.append("Production environment impact")
        
        # Resource-based risk factors
        if "database" in plan.affected_resources:
            risk_factors.append("Database operations involved")
        
        if "compute_instance" in plan.affected_resources:
            risk_factors.append("Compute instance restart required")
        
        # Time-based risk factors
        business_hours = self._is_business_hours()
        if business_hours and environment == "production":
            risk_factors.append("Execution during business hours")
        
        # GenAI-derived risk factors (simplified parsing)
        if "high risk" in genai_response.lower():
            risk_factors.append("AI-identified high risk factors")
        
        if "data loss" in genai_response.lower():
            risk_factors.append("Potential data loss risk")
        
        return risk_factors
    
    def _calculate_overall_risk(self, risk_factors: List[str]) -> RemediationRisk:
        """Calculate overall risk based on risk factors"""
        
        if not risk_factors:
            return RemediationRisk.VERY_LOW
        
        critical_keywords = ["critical", "data loss", "production", "database"]
        high_keywords = ["high risk", "business hours", "compute instance"]
        medium_keywords = ["restart", "connection", "temporary"]
        
        critical_count = sum(1 for factor in risk_factors 
                           if any(keyword in factor.lower() for keyword in critical_keywords))
        high_count = sum(1 for factor in risk_factors 
                        if any(keyword in factor.lower() for keyword in high_keywords))
        medium_count = sum(1 for factor in risk_factors 
                          if any(keyword in factor.lower() for keyword in medium_keywords))
        
        if critical_count > 0:
            return RemediationRisk.CRITICAL
        elif high_count > 1:
            return RemediationRisk.HIGH
        elif high_count > 0 or medium_count > 2:
            return RemediationRisk.MEDIUM
        elif medium_count > 0:
            return RemediationRisk.LOW
        else:
            return RemediationRisk.VERY_LOW
    
    def _generate_mitigation_strategies(self, risk_factors: List[str]) -> List[str]:
        """Generate mitigation strategies for identified risk factors"""
        
        strategies = []
        
        if any("production" in factor.lower() for factor in risk_factors):
            strategies.append("Schedule during maintenance window")
            strategies.append("Prepare rollback plan")
        
        if any("database" in factor.lower() for factor in risk_factors):
            strategies.append("Create database backup before execution")
            strategies.append("Verify database connections after completion")
        
        if any("business hours" in factor.lower() for factor in risk_factors):
            strategies.append("Consider delaying until off-hours")
            strategies.append("Notify stakeholders before execution")
        
        if any("high risk" in factor.lower() for factor in risk_factors):
            strategies.append("Require manual approval")
            strategies.append("Execute in dry-run mode first")
        
        # Default strategies
        strategies.extend([
            "Monitor execution closely",
            "Have rollback procedures ready",
            "Test in staging environment first"
        ])
        
        return list(set(strategies))  # Remove duplicates
    
    def _generate_recommendation(self, risk: RemediationRisk, plan: RemediationPlan) -> str:
        """Generate recommendation based on risk assessment"""
        
        if risk == RemediationRisk.VERY_LOW:
            return "Safe for automatic execution"
        elif risk == RemediationRisk.LOW:
            if plan.auto_execute:
                return "Approve for automatic execution with monitoring"
            else:
                return "Recommend approval with standard monitoring"
        elif risk == RemediationRisk.MEDIUM:
            return "Requires approval and enhanced monitoring"
        elif risk == RemediationRisk.HIGH:
            return "Requires manual review and approval by senior staff"
        else:  # CRITICAL
            return "Manual execution only - automatic remediation not recommended"
    
    def _is_business_hours(self) -> bool:
        """Check if current time is during business hours"""
        now = datetime.utcnow()
        # Simple check for weekdays 9 AM - 6 PM UTC
        return now.weekday() < 5 and 9 <= now.hour <= 18
    
    async def submit_remediation_request(
        self, 
        plan_id: str, 
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        force_approval: bool = False
    ) -> Dict[str, Any]:
        """Submit a request for remediation execution"""
        
        if not self.enabled:
            return {"status": "disabled", "message": "Auto-remediation is disabled"}
        
        plan = self.get_remediation_plan(plan_id)
        if not plan:
            return {"status": "error", "message": f"Remediation plan {plan_id} not found"}
        
        try:
            # Assess risk
            risk_assessment = await self.assess_risk(plan, context)
            
            # Generate execution ID
            execution_id = f"{plan_id}_{int(datetime.utcnow().timestamp())}"
            
            # Create execution record
            execution = RemediationExecution(
                plan_id=plan_id,
                execution_id=execution_id,
                status=RemediationStatus.PENDING,
                executed_actions=[],
                failed_actions=[],
                rollback_actions=[],
                execution_logs=[]
            )
            
            # Determine if approval is required
            requires_approval = (
                plan.approval_required or 
                risk_assessment.manual_review_required or
                risk_assessment.overall_risk.value in [RemediationRisk.HIGH.value, RemediationRisk.CRITICAL.value]
            )
            
            # Check for auto-approval conditions
            if (not requires_approval or force_approval or 
                (self.auto_approval_enabled and risk_assessment.overall_risk.value in [RemediationRisk.VERY_LOW.value, RemediationRisk.LOW.value])):
                
                execution.status = RemediationStatus.APPROVED
                execution.approval_user = user_id or "system"
                execution.approval_timestamp = datetime.utcnow()
                
                # Queue for execution
                await self.execution_queue.put({
                    "execution_id": execution_id,
                    "plan": plan,
                    "context": context,
                    "risk_assessment": risk_assessment
                })
                
            else:
                execution.status = RemediationStatus.REQUIRES_APPROVAL
                
                # Send notification for approval
                await self.notification_service.send_alert_notification(
                    alert_title=f"Remediation Approval Required: {plan.title}",
                    severity=NotificationSeverity.MEDIUM,
                    description=f"Risk Level: {risk_assessment.overall_risk.value}\n\n{risk_assessment.recommendation}",
                    source="auto_remediation_service",
                    affected_resources=plan.affected_resources,
                    recommended_actions=[f"Review and approve execution {execution_id}"],
                    recipients=["System Administrators"]
                )
            
            # Store execution
            self.executions[execution_id] = execution
            
            # Record metrics
            self.prometheus_service.record_remediation(
                remediation_type=plan_id,
                status="submitted"
            )
            
            return {
                "status": "success",
                "execution_id": execution_id,
                "execution_status": execution.status.value,
                "risk_assessment": asdict(risk_assessment),
                "requires_approval": requires_approval,
                "estimated_duration": plan.estimated_duration_minutes
            }
            
        except Exception as e:
            logger.error(f"Failed to submit remediation request: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def approve_remediation(
        self, 
        execution_id: str, 
        user_id: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """Approve a pending remediation execution"""
        
        execution = self.executions.get(execution_id)
        if not execution:
            return {"status": "error", "message": "Execution not found"}
        
        if execution.status != RemediationStatus.REQUIRES_APPROVAL:
            return {"status": "error", "message": f"Execution is not pending approval (status: {execution.status.value})"}
        
        try:
            # Update execution status
            execution.status = RemediationStatus.APPROVED
            execution.approval_user = user_id
            execution.approval_timestamp = datetime.utcnow()
            execution.execution_logs.append(f"Approved by {user_id}: {comments}")
            
            # Get plan and context (stored separately or reconstructed)
            plan = self.get_remediation_plan(execution.plan_id)
            if not plan:
                return {"status": "error", "message": "Remediation plan not found"}
            
            # Queue for execution
            await self.execution_queue.put({
                "execution_id": execution_id,
                "plan": plan,
                "context": {},  # Context would be stored with execution in real implementation
                "risk_assessment": None
            })
            
            logger.info(f"Remediation {execution_id} approved by {user_id}")
            
            return {
                "status": "success",
                "message": "Remediation approved and queued for execution",
                "execution_id": execution_id
            }
            
        except Exception as e:
            logger.error(f"Failed to approve remediation: {e}")
            return {"status": "error", "message": str(e)}
    
    async def cancel_remediation(
        self, 
        execution_id: str, 
        user_id: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Cancel a pending or executing remediation"""
        
        execution = self.executions.get(execution_id)
        if not execution:
            return {"status": "error", "message": "Execution not found"}
        
        if execution.status in [RemediationStatus.COMPLETED, RemediationStatus.FAILED, RemediationStatus.CANCELLED]:
            return {"status": "error", "message": f"Cannot cancel execution in {execution.status.value} status"}
        
        try:
            execution.status = RemediationStatus.CANCELLED
            execution.execution_logs.append(f"Cancelled by {user_id}: {reason}")
            
            # If currently executing, mark for cancellation
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["cancelled"] = True
            
            logger.info(f"Remediation {execution_id} cancelled by {user_id}")
            
            return {
                "status": "success",
                "message": "Remediation cancelled",
                "execution_id": execution_id
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel remediation: {e}")
            return {"status": "error", "message": str(e)}
    
    def _start_execution_worker(self):
        """Start the remediation execution worker"""
        asyncio.create_task(self._execution_worker())
    
    async def _execution_worker(self):
        """Worker that processes remediation executions"""
        
        while True:
            try:
                # Check if we can start new executions
                if len(self.active_executions) >= self.max_concurrent_executions:
                    await asyncio.sleep(5)
                    continue
                
                # Get next execution from queue
                try:
                    execution_data = await asyncio.wait_for(self.execution_queue.get(), timeout=10)
                except asyncio.TimeoutError:
                    continue
                
                # Start execution
                asyncio.create_task(self._execute_remediation(execution_data))
                
            except Exception as e:
                logger.error(f"Error in execution worker: {e}")
                await asyncio.sleep(5)
    
    async def _execute_remediation(self, execution_data: Dict[str, Any]):
        """Execute a remediation plan"""
        
        execution_id = execution_data["execution_id"]
        plan = execution_data["plan"]
        context = execution_data["context"]
        risk_assessment = execution_data.get("risk_assessment")
        
        execution = self.executions.get(execution_id)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return
        
        # Mark as active
        self.active_executions[execution_id] = {"cancelled": False}
        
        try:
            execution.status = RemediationStatus.EXECUTING
            execution.started_at = datetime.utcnow()
            execution.execution_logs.append(f"Started execution at {execution.started_at}")
            
            # Execute each action
            for action in plan.actions:
                # Check for cancellation
                if self.active_executions[execution_id].get("cancelled"):
                    execution.status = RemediationStatus.CANCELLED
                    execution.execution_logs.append("Execution cancelled by user")
                    break
                
                try:
                    execution.execution_logs.append(f"Executing action: {action.name}")
                    
                    # Execute action based on type
                    success = await self._execute_action(action, context, execution)
                    
                    if success:
                        execution.executed_actions.append(action.id)
                        execution.execution_logs.append(f"Action {action.name} completed successfully")
                    else:
                        execution.failed_actions.append(action.id)
                        execution.execution_logs.append(f"Action {action.name} failed")
                        
                        # Attempt rollback if action has rollback command
                        if action.rollback_command:
                            execution.execution_logs.append(f"Attempting rollback for {action.name}")
                            await self._execute_rollback(action, context, execution)
                        
                        # Fail the entire execution
                        execution.status = RemediationStatus.FAILED
                        break
                        
                except Exception as e:
                    execution.failed_actions.append(action.id)
                    execution.execution_logs.append(f"Action {action.name} failed with error: {str(e)}")
                    execution.status = RemediationStatus.FAILED
                    break
            
            # Mark as completed if not already failed or cancelled
            if execution.status == RemediationStatus.EXECUTING:
                execution.status = RemediationStatus.COMPLETED
                execution.execution_logs.append("All actions completed successfully")
            
            execution.completed_at = datetime.utcnow()
            
            # Send completion notification
            await self._send_completion_notification(execution, plan)
            
            # Record metrics
            self.prometheus_service.record_remediation(
                remediation_type=plan.id,
                status=execution.status.value
            )
            
        except Exception as e:
            execution.status = RemediationStatus.FAILED
            execution.error_message = str(e)
            execution.execution_logs.append(f"Execution failed with error: {str(e)}")
            logger.error(f"Remediation execution {execution_id} failed: {e}")
            
        finally:
            # Remove from active executions
            self.active_executions.pop(execution_id, None)
            
            logger.info(f"Remediation {execution_id} completed with status: {execution.status.value}")
    
    async def _execute_action(
        self, 
        action: RemediationAction, 
        context: Dict[str, Any],
        execution: RemediationExecution
    ) -> bool:
        """Execute a single remediation action"""
        
        try:
            # Format command with context variables
            formatted_command = action.command.format(**context)
            
            if self.dry_run_mode:
                execution.execution_logs.append(f"DRY RUN: Would execute: {formatted_command}")
                await asyncio.sleep(1)  # Simulate execution time
                return True
            
            if action.type == RemediationType.OCI_CLI:
                return await self._execute_oci_cli(formatted_command, action.timeout_seconds)
                
            elif action.type == RemediationType.KUBECTL:
                return await self._execute_kubectl(formatted_command, action.timeout_seconds)
                
            elif action.type == RemediationType.SCRIPT:
                return await self._execute_script(formatted_command, action.timeout_seconds)
                
            elif action.type == RemediationType.API_CALL:
                return await self._execute_api_call(formatted_command, action.timeout_seconds)
                
            elif action.type == RemediationType.TERRAFORM:
                return await self._execute_terraform(formatted_command, action.timeout_seconds)
                
            else:
                execution.execution_logs.append(f"Unsupported action type: {action.type}")
                return False
                
        except Exception as e:
            execution.execution_logs.append(f"Action execution failed: {str(e)}")
            return False
    
    async def _execute_oci_cli(self, command: str, timeout: int) -> bool:
        """Execute OCI CLI command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            if process.returncode == 0:
                logger.info(f"OCI CLI command succeeded: {command}")
                return True
            else:
                logger.error(f"OCI CLI command failed: {command}, stderr: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"OCI CLI command timed out: {command}")
            return False
        except Exception as e:
            logger.error(f"OCI CLI command error: {e}")
            return False
    
    async def _execute_kubectl(self, command: str, timeout: int) -> bool:
        """Execute kubectl command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            if process.returncode == 0:
                logger.info(f"kubectl command succeeded: {command}")
                return True
            else:
                logger.error(f"kubectl command failed: {command}, stderr: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"kubectl command timed out: {command}")
            return False
        except Exception as e:
            logger.error(f"kubectl command error: {e}")
            return False
    
    async def _execute_script(self, command: str, timeout: int) -> bool:
        """Execute shell script"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            if process.returncode == 0:
                logger.info(f"Script command succeeded: {command}")
                return True
            else:
                logger.error(f"Script command failed: {command}, stderr: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"Script command timed out: {command}")
            return False
        except Exception as e:
            logger.error(f"Script command error: {e}")
            return False
    
    async def _execute_api_call(self, command: str, timeout: int) -> bool:
        """Execute API call"""
        # Simplified API call execution
        # In real implementation, this would parse the command and make HTTP requests
        logger.info(f"API call executed: {command}")
        await asyncio.sleep(1)  # Simulate API call
        return True
    
    async def _execute_terraform(self, command: str, timeout: int) -> bool:
        """Execute Terraform command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            if process.returncode == 0:
                logger.info(f"Terraform command succeeded: {command}")
                return True
            else:
                logger.error(f"Terraform command failed: {command}, stderr: {stderr.decode()}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"Terraform command timed out: {command}")
            return False
        except Exception as e:
            logger.error(f"Terraform command error: {e}")
            return False
    
    async def _execute_rollback(
        self, 
        action: RemediationAction, 
        context: Dict[str, Any],
        execution: RemediationExecution
    ):
        """Execute rollback for a failed action"""
        
        if not action.rollback_command:
            return
        
        try:
            formatted_rollback = action.rollback_command.format(**context)
            execution.execution_logs.append(f"Executing rollback: {formatted_rollback}")
            
            # Execute rollback based on action type
            success = await self._execute_action(
                RemediationAction(
                    id=f"{action.id}_rollback",
                    name=f"Rollback {action.name}",
                    type=action.type,
                    command=formatted_rollback,
                    description=f"Rollback for {action.description}",
                    risk_level=RemediationRisk.LOW
                ),
                context,
                execution
            )
            
            if success:
                execution.rollback_actions.append(action.id)
                execution.execution_logs.append(f"Rollback for {action.name} completed")
            else:
                execution.execution_logs.append(f"Rollback for {action.name} failed")
                
        except Exception as e:
            execution.execution_logs.append(f"Rollback failed: {str(e)}")
    
    async def _send_completion_notification(
        self, 
        execution: RemediationExecution, 
        plan: RemediationPlan
    ):
        """Send notification about remediation completion"""
        
        try:
            if execution.status == RemediationStatus.COMPLETED:
                await self.notification_service.send_remediation_notification(
                    remediation_title=plan.title,
                    actions_performed=[action.name for action in plan.actions if action.id in execution.executed_actions],
                    results="All remediation actions completed successfully",
                    verification_status="Execution completed without errors",
                    duration=str(execution.completed_at - execution.started_at) if execution.completed_at and execution.started_at else "Unknown"
                )
            else:
                await self.notification_service.send_alert_notification(
                    alert_title=f"Remediation Failed: {plan.title}",
                    severity=NotificationSeverity.HIGH,
                    description=f"Remediation execution {execution.execution_id} failed",
                    source="auto_remediation_service",
                    affected_resources=plan.affected_resources,
                    recommended_actions=["Review execution logs", "Manual intervention may be required"]
                )
                
        except Exception as e:
            logger.error(f"Failed to send completion notification: {e}")
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a remediation execution"""
        
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "plan_id": execution.plan_id,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "executed_actions": execution.executed_actions,
            "failed_actions": execution.failed_actions,
            "rollback_actions": execution.rollback_actions,
            "approval_user": execution.approval_user,
            "approval_timestamp": execution.approval_timestamp.isoformat() if execution.approval_timestamp else None,
            "execution_logs": execution.execution_logs,
            "error_message": execution.error_message
        }
    
    def list_executions(
        self, 
        status_filter: Optional[RemediationStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List remediation executions with optional status filter"""
        
        executions = list(self.executions.values())
        
        if status_filter:
            executions = [e for e in executions if e.status == status_filter]
        
        # Sort by started_at (newest first)
        executions.sort(
            key=lambda x: x.started_at or datetime.min, 
            reverse=True
        )
        
        return [self.get_execution_status(e.execution_id) for e in executions[:limit]]
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get auto-remediation service status"""
        
        return {
            "enabled": self.enabled,
            "auto_approval_enabled": self.auto_approval_enabled,
            "dry_run_mode": self.dry_run_mode,
            "max_concurrent_executions": self.max_concurrent_executions,
            "statistics": {
                "total_plans": len(self.remediation_plans),
                "total_executions": len(self.executions),
                "active_executions": len(self.active_executions),
                "queued_executions": self.execution_queue.qsize(),
                "risk_assessments": len(self.risk_assessments)
            },
            "risk_thresholds": {
                "auto_approve_threshold": self.auto_approve_threshold.value,
                "auto_execute_threshold": self.auto_execute_threshold.value
            }
        }

# Global service instance
_auto_remediation_service = None

def get_auto_remediation_service() -> AutoRemediationService:
    """Get global auto-remediation service instance"""
    global _auto_remediation_service
    if _auto_remediation_service is None:
        _auto_remediation_service = AutoRemediationService()
    return _auto_remediation_service 