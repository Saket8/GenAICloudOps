"""
Notification Service
==================

This service provides comprehensive notification capabilities including email and Slack
notifications for critical issues, alerts, and system events in the GenAI CloudOps Dashboard.

Author: GenAI CloudOps Dashboard Team
Created: January 2025
Task: 028 - Implement Optional Enhancements
"""

import json
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import httpx
from pathlib import Path

# Optional dependency: jinja2
try:
    import jinja2
    JINJA_AVAILABLE = True
except Exception:
    JINJA_AVAILABLE = False
    class _DummyTemplate:
        def __init__(self, tpl: str):
            self.tpl = tpl
        def render(self, **kwargs):
            # Very naive replacement for {{ var }} tokens
            result = self.tpl
            for k, v in kwargs.items():
                result = result.replace(f"{{{{ {k} }}}}", str(v))
            return result
    class _DummyLoader:
        def __init__(self):
            self.mapping = {}
        def get(self, name, default=None):
            return self.mapping.get(name, default)
    class _DummyEnv:
        def __init__(self):
            self.loader = _DummyLoader()
        def get_template(self, name: str):
            tpl = self.loader.get(name, "")
            return _DummyTemplate(tpl)

from app.core.config import settings
from app.services.prometheus_service import get_prometheus_service

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    ALERT = "alert"
    INCIDENT = "incident"
    REMEDIATION = "remediation"
    SYSTEM = "system"
    BUSINESS = "business"
    MAINTENANCE = "maintenance"

class NotificationSeverity(Enum):
    """Notification severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"  # Future implementation

@dataclass
class NotificationRecipient:
    """Notification recipient configuration"""
    name: str
    email: Optional[str] = None
    slack_user_id: Optional[str] = None
    phone: Optional[str] = None
    channels: List[str] = None
    severity_filter: List[str] = None  # Only receive notifications of these severities

@dataclass
class NotificationTemplate:
    """Notification template configuration"""
    name: str
    notification_type: NotificationType
    channel: NotificationChannel
    subject_template: str
    body_template: str
    variables: List[str]
    severity_levels: List[NotificationSeverity]
    
@dataclass
class EscalationRule:
    """Escalation rule configuration"""
    id: str
    name: str
    severity: NotificationSeverity
    initial_recipients: List[str]
    escalation_recipients: List[str]
    escalation_delay_minutes: int
    max_escalations: int
    conditions: Dict[str, Any]

@dataclass
class NotificationRequest:
    """Notification request data"""
    notification_type: NotificationType
    severity: NotificationSeverity
    title: str
    message: str
    data: Dict[str, Any]
    recipients: List[str]
    channels: List[NotificationChannel]
    urgent: bool = False
    template_name: Optional[str] = None
    escalation_rule_id: Optional[str] = None

class NotificationService:
    """Comprehensive notification service"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'NOTIFICATIONS_ENABLED', True)
        
        # Email configuration
        self.email_enabled = getattr(settings, 'EMAIL_ENABLED', False)
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.smtp_use_tls = getattr(settings, 'SMTP_USE_TLS', True)
        self.sender_email = getattr(settings, 'SENDER_EMAIL', 'noreply@genai-cloudops.com')
        self.sender_name = getattr(settings, 'SENDER_NAME', 'GenAI CloudOps Dashboard')
        
        # Slack configuration
        self.slack_enabled = getattr(settings, 'SLACK_ENABLED', False)
        self.slack_token = getattr(settings, 'SLACK_BOT_TOKEN', '')
        self.slack_webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '')
        self.slack_channel = getattr(settings, 'SLACK_DEFAULT_CHANNEL', '#alerts')
        
        # Templates and rules
        self.templates = {}
        self.recipients = {}
        self.escalation_rules = {}
        self.notification_history = []
        
        # HTTP client for Slack/webhook notifications
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Template engine
        if JINJA_AVAILABLE:
            self.jinja_env = jinja2.Environment(
                loader=jinja2.DictLoader({}),
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
        else:
            logger.info("jinja2 not installed; using simple template fallback")
            self.jinja_env = _DummyEnv()
        
        if self.enabled:
            self._initialize_default_templates()
            self._initialize_default_recipients()
            self._initialize_escalation_rules()
            logger.info("Notification service initialized")
        else:
            logger.info("Notifications disabled in configuration")
    
    def _initialize_default_templates(self):
        """Initialize default notification templates"""
        
        # Critical Alert Template
        self.add_template(NotificationTemplate(
            name="critical_alert",
            notification_type=NotificationType.ALERT,
            channel=NotificationChannel.EMAIL,
            subject_template="🚨 CRITICAL ALERT: {{ alert_title }}",
            body_template="""
<h2>Critical Alert Notification</h2>
<p><strong>Alert:</strong> {{ alert_title }}</p>
<p><strong>Severity:</strong> {{ severity }}</p>
<p><strong>Time:</strong> {{ timestamp }}</p>
<p><strong>Source:</strong> {{ source }}</p>

<h3>Description:</h3>
<p>{{ description }}</p>

<h3>Affected Resources:</h3>
<ul>
{% for resource in affected_resources %}
    <li>{{ resource }}</li>
{% endfor %}
</ul>

<h3>Recommended Actions:</h3>
<ol>
{% for action in recommended_actions %}
    <li>{{ action }}</li>
{% endfor %}
</ol>

<p><strong>Dashboard Link:</strong> <a href="{{ dashboard_url }}">View in Dashboard</a></p>

<hr>
<p><em>This is an automated notification from GenAI CloudOps Dashboard.</em></p>
""",
            variables=["alert_title", "severity", "timestamp", "source", "description", "affected_resources", "recommended_actions", "dashboard_url"],
            severity_levels=[NotificationSeverity.CRITICAL, NotificationSeverity.HIGH]
        ))
        
        # Slack Alert Template
        self.add_template(NotificationTemplate(
            name="slack_alert",
            notification_type=NotificationType.ALERT,
            channel=NotificationChannel.SLACK,
            subject_template="",
            body_template="""{
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚨 {{ severity.upper() }} ALERT"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Alert:*\\n{{ alert_title }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Time:*\\n{{ timestamp }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Source:*\\n{{ source }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Severity:*\\n{{ severity }}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Description:*\\n{{ description }}"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Dashboard"
                    },
                    "url": "{{ dashboard_url }}",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Acknowledge"
                    },
                    "action_id": "acknowledge_alert",
                    "value": "{{ alert_id }}"
                }
            ]
        }
    ]
}""",
            variables=["alert_title", "severity", "timestamp", "source", "description", "dashboard_url", "alert_id"],
            severity_levels=[NotificationSeverity.CRITICAL, NotificationSeverity.HIGH, NotificationSeverity.MEDIUM]
        ))
        
        # Remediation Success Template
        self.add_template(NotificationTemplate(
            name="remediation_success",
            notification_type=NotificationType.REMEDIATION,
            channel=NotificationChannel.EMAIL,
            subject_template="✅ Remediation Successful: {{ remediation_title }}",
            body_template="""
<h2>Remediation Completed Successfully</h2>
<p><strong>Remediation:</strong> {{ remediation_title }}</p>
<p><strong>Time:</strong> {{ timestamp }}</p>
<p><strong>Duration:</strong> {{ duration }}</p>

<h3>Actions Performed:</h3>
<ul>
{% for action in actions_performed %}
    <li>{{ action }}</li>
{% endfor %}
</ul>

<h3>Results:</h3>
<p>{{ results }}</p>

<h3>Verification:</h3>
<p>{{ verification_status }}</p>

<p><strong>Dashboard Link:</strong> <a href="{{ dashboard_url }}">View in Dashboard</a></p>

<hr>
<p><em>This is an automated notification from GenAI CloudOps Dashboard.</em></p>
""",
            variables=["remediation_title", "timestamp", "duration", "actions_performed", "results", "verification_status", "dashboard_url"],
            severity_levels=[NotificationSeverity.INFO, NotificationSeverity.MEDIUM]
        ))
        
        # System Maintenance Template
        self.add_template(NotificationTemplate(
            name="maintenance_notification",
            notification_type=NotificationType.MAINTENANCE,
            channel=NotificationChannel.EMAIL,
            subject_template="🔧 Scheduled Maintenance: {{ maintenance_title }}",
            body_template="""
<h2>Scheduled Maintenance Notification</h2>
<p><strong>Maintenance:</strong> {{ maintenance_title }}</p>
<p><strong>Scheduled Time:</strong> {{ scheduled_time }}</p>
<p><strong>Expected Duration:</strong> {{ expected_duration }}</p>

<h3>Affected Services:</h3>
<ul>
{% for service in affected_services %}
    <li>{{ service }}</li>
{% endfor %}
</ul>

<h3>Impact:</h3>
<p>{{ impact_description }}</p>

<h3>Actions Required:</h3>
<ul>
{% for action in required_actions %}
    <li>{{ action }}</li>
{% endfor %}
</ul>

<p><strong>Contact:</strong> {{ contact_info }}</p>

<hr>
<p><em>This is an automated notification from GenAI CloudOps Dashboard.</em></p>
""",
            variables=["maintenance_title", "scheduled_time", "expected_duration", "affected_services", "impact_description", "required_actions", "contact_info"],
            severity_levels=[NotificationSeverity.INFO, NotificationSeverity.LOW]
        ))
    
    def _initialize_default_recipients(self):
        """Initialize default notification recipients"""
        
        # Admin recipients
        self.add_recipient(NotificationRecipient(
            name="System Administrators",
            email=getattr(settings, 'ADMIN_EMAIL', 'admin@genai-cloudops.com'),
            slack_user_id=getattr(settings, 'ADMIN_SLACK_ID', ''),
            channels=[NotificationChannel.EMAIL.value, NotificationChannel.SLACK.value],
            severity_filter=[NotificationSeverity.CRITICAL.value, NotificationSeverity.HIGH.value]
        ))
        
        # DevOps team
        self.add_recipient(NotificationRecipient(
            name="DevOps Team",
            email=getattr(settings, 'DEVOPS_EMAIL', 'devops@genai-cloudops.com'),
            channels=[NotificationChannel.EMAIL.value, NotificationChannel.SLACK.value],
            severity_filter=[NotificationSeverity.CRITICAL.value, NotificationSeverity.HIGH.value, NotificationSeverity.MEDIUM.value]
        ))
        
        # Business stakeholders
        self.add_recipient(NotificationRecipient(
            name="Business Stakeholders",
            email=getattr(settings, 'BUSINESS_EMAIL', 'business@genai-cloudops.com'),
            channels=[NotificationChannel.EMAIL.value],
            severity_filter=[NotificationSeverity.CRITICAL.value]
        ))
    
    def _initialize_escalation_rules(self):
        """Initialize escalation rules"""
        
        # Critical issue escalation
        self.add_escalation_rule(EscalationRule(
            id="critical_escalation",
            name="Critical Issue Escalation",
            severity=NotificationSeverity.CRITICAL,
            initial_recipients=["System Administrators"],
            escalation_recipients=["DevOps Team", "Business Stakeholders"],
            escalation_delay_minutes=15,
            max_escalations=2,
            conditions={"unresolved_after_minutes": 15}
        ))
        
        # High priority escalation
        self.add_escalation_rule(EscalationRule(
            id="high_priority_escalation",
            name="High Priority Escalation",
            severity=NotificationSeverity.HIGH,
            initial_recipients=["DevOps Team"],
            escalation_recipients=["System Administrators"],
            escalation_delay_minutes=30,
            max_escalations=1,
            conditions={"unresolved_after_minutes": 30}
        ))
    
    def add_template(self, template: NotificationTemplate):
        """Add a notification template"""
        self.templates[template.name] = template
        
        # Add template to Jinja environment
        if template.channel == NotificationChannel.EMAIL:
            self.jinja_env.loader.mapping[f"{template.name}_subject"] = template.subject_template
            self.jinja_env.loader.mapping[f"{template.name}_body"] = template.body_template
    
    def add_recipient(self, recipient: NotificationRecipient):
        """Add a notification recipient"""
        self.recipients[recipient.name] = recipient
    
    def add_escalation_rule(self, rule: EscalationRule):
        """Add an escalation rule"""
        self.escalation_rules[rule.id] = rule
    
    async def send_notification(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send a notification through specified channels"""
        if not self.enabled:
            return {"status": "disabled", "message": "Notifications disabled"}
        
        results = {}
        
        try:
            # Get recipients
            recipients = self._resolve_recipients(request.recipients, request.severity)
            
            # Send through each channel
            for channel in request.channels:
                if channel == NotificationChannel.EMAIL and self.email_enabled:
                    email_result = await self._send_email_notification(request, recipients)
                    results["email"] = email_result
                
                elif channel == NotificationChannel.SLACK and self.slack_enabled:
                    slack_result = await self._send_slack_notification(request, recipients)
                    results["slack"] = slack_result
            
            # Record metrics
            prometheus_service = get_prometheus_service()
            prometheus_service.record_alert(
                alert_type=request.notification_type.value,
                severity=request.severity.value,
                source="notification_service"
            )
            
            # Store in history
            self._record_notification_history(request, results)
            
            # Check for escalation
            if request.escalation_rule_id:
                await self._check_escalation(request)
            
            return {
                "status": "success",
                "notification_id": self._generate_notification_id(),
                "results": results,
                "recipients_count": len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _send_email_notification(
        self, 
        request: NotificationRequest, 
        recipients: List[NotificationRecipient]
    ) -> Dict[str, Any]:
        """Send email notification"""
        
        try:
            # Get template
            template_name = request.template_name or self._get_default_template_name(
                request.notification_type, NotificationChannel.EMAIL
            )
            template = self.templates.get(template_name)
            
            if not template:
                return {"status": "error", "message": f"Template {template_name} not found"}
            
            # Render email content
            subject = self._render_template(f"{template_name}_subject", request.data)
            body = self._render_template(f"{template_name}_body", request.data)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            
            # Get email recipients
            email_recipients = [r.email for r in recipients if r.email and NotificationChannel.EMAIL.value in r.channels]
            
            if not email_recipients:
                return {"status": "warning", "message": "No email recipients found"}
            
            msg['To'] = ", ".join(email_recipients)
            
            # Attach HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls(context=context)
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {len(email_recipients)} recipients")
            
            return {
                "status": "success",
                "recipients": email_recipients,
                "subject": subject
            }
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _send_slack_notification(
        self, 
        request: NotificationRequest, 
        recipients: List[NotificationRecipient]
    ) -> Dict[str, Any]:
        """Send Slack notification"""
        
        try:
            # Get template
            template_name = request.template_name or self._get_default_template_name(
                request.notification_type, NotificationChannel.SLACK
            )
            template = self.templates.get(template_name)
            
            if not template:
                return {"status": "error", "message": f"Template {template_name} not found"}
            
            # Render Slack message
            message_content = self._render_template(f"{template_name}_body", request.data)
            
            # Parse JSON if template is structured
            try:
                slack_payload = json.loads(message_content)
            except json.JSONDecodeError:
                # Fallback to simple text message
                slack_payload = {
                    "text": message_content,
                    "channel": self.slack_channel
                }
            
            # Send via webhook if configured
            if self.slack_webhook_url:
                response = await self.http_client.post(
                    self.slack_webhook_url,
                    json=slack_payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                logger.info("Slack notification sent via webhook")
                
                return {
                    "status": "success",
                    "method": "webhook",
                    "channel": self.slack_channel
                }
            
            # Send via Bot API if token is configured
            elif self.slack_token:
                headers = {
                    "Authorization": f"Bearer {self.slack_token}",
                    "Content-Type": "application/json"
                }
                
                response = await self.http_client.post(
                    "https://slack.com/api/chat.postMessage",
                    json=slack_payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                if not result.get("ok"):
                    raise Exception(f"Slack API error: {result.get('error')}")
                
                logger.info("Slack notification sent via Bot API")
                
                return {
                    "status": "success",
                    "method": "bot_api",
                    "channel": result.get("channel"),
                    "timestamp": result.get("ts")
                }
            
            else:
                return {
                    "status": "error",
                    "message": "No Slack webhook URL or bot token configured"
                }
                
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _resolve_recipients(
        self, 
        recipient_names: List[str], 
        severity: NotificationSeverity
    ) -> List[NotificationRecipient]:
        """Resolve recipient names to recipient objects with severity filtering"""
        
        resolved = []
        
        for name in recipient_names:
            recipient = self.recipients.get(name)
            if recipient:
                # Check severity filter
                if not recipient.severity_filter or severity.value in recipient.severity_filter:
                    resolved.append(recipient)
        
        return resolved
    
    def _get_default_template_name(
        self, 
        notification_type: NotificationType, 
        channel: NotificationChannel
    ) -> str:
        """Get default template name for notification type and channel"""
        
        template_map = {
            (NotificationType.ALERT, NotificationChannel.EMAIL): "critical_alert",
            (NotificationType.ALERT, NotificationChannel.SLACK): "slack_alert",
            (NotificationType.REMEDIATION, NotificationChannel.EMAIL): "remediation_success",
            (NotificationType.MAINTENANCE, NotificationChannel.EMAIL): "maintenance_notification"
        }
        
        return template_map.get((notification_type, channel), "critical_alert")
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render Jinja template with data"""
        
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return f"Error rendering template: {e}"
    
    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        import uuid
        return f"notif_{int(datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    def _record_notification_history(
        self, 
        request: NotificationRequest, 
        results: Dict[str, Any]
    ):
        """Record notification in history"""
        
        history_entry = {
            "id": self._generate_notification_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "type": request.notification_type.value,
            "severity": request.severity.value,
            "title": request.title,
            "recipients": request.recipients,
            "channels": [c.value for c in request.channels],
            "results": results
        }
        
        self.notification_history.append(history_entry)
        
        # Keep only last 1000 entries
        if len(self.notification_history) > 1000:
            self.notification_history = self.notification_history[-1000:]
    
    async def _check_escalation(self, request: NotificationRequest):
        """Check and handle escalation rules"""
        
        rule = self.escalation_rules.get(request.escalation_rule_id)
        if not rule or rule.severity != request.severity:
            return
        
        # Schedule escalation check (simplified implementation)
        asyncio.create_task(self._handle_escalation_delay(request, rule))
    
    async def _handle_escalation_delay(
        self, 
        request: NotificationRequest, 
        rule: EscalationRule
    ):
        """Handle escalation after delay"""
        
        await asyncio.sleep(rule.escalation_delay_minutes * 60)
        
        # Check if issue is still unresolved (simplified check)
        # In real implementation, this would check alert status
        
        escalation_request = NotificationRequest(
            notification_type=NotificationType.ALERT,
            severity=NotificationSeverity.CRITICAL,
            title=f"ESCALATED: {request.title}",
            message=f"Escalated alert: {request.message}",
            data=request.data,
            recipients=rule.escalation_recipients,
            channels=request.channels,
            urgent=True
        )
        
        await self.send_notification(escalation_request)
        logger.info(f"Escalated notification for rule: {rule.name}")
    
    async def send_alert_notification(
        self, 
        alert_title: str,
        severity: NotificationSeverity,
        description: str,
        source: str,
        affected_resources: List[str],
        recommended_actions: List[str],
        dashboard_url: str = "",
        recipients: List[str] = None
    ) -> Dict[str, Any]:
        """Convenience method for sending alert notifications"""
        
        data = {
            "alert_title": alert_title,
            "severity": severity.value,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "source": source,
            "description": description,
            "affected_resources": affected_resources,
            "recommended_actions": recommended_actions,
            "dashboard_url": dashboard_url or getattr(settings, 'DASHBOARD_URL', 'http://localhost:3000'),
            "alert_id": self._generate_notification_id()
        }
        
        request = NotificationRequest(
            notification_type=NotificationType.ALERT,
            severity=severity,
            title=alert_title,
            message=description,
            data=data,
            recipients=recipients or ["System Administrators", "DevOps Team"],
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            escalation_rule_id="critical_escalation" if severity == NotificationSeverity.CRITICAL else None
        )
        
        return await self.send_notification(request)
    
    async def send_remediation_notification(
        self,
        remediation_title: str,
        actions_performed: List[str],
        results: str,
        verification_status: str,
        duration: str,
        recipients: List[str] = None
    ) -> Dict[str, Any]:
        """Convenience method for sending remediation notifications"""
        
        data = {
            "remediation_title": remediation_title,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "duration": duration,
            "actions_performed": actions_performed,
            "results": results,
            "verification_status": verification_status,
            "dashboard_url": getattr(settings, 'DASHBOARD_URL', 'http://localhost:3000')
        }
        
        request = NotificationRequest(
            notification_type=NotificationType.REMEDIATION,
            severity=NotificationSeverity.INFO,
            title=remediation_title,
            message=results,
            data=data,
            recipients=recipients or ["DevOps Team"],
            channels=[NotificationChannel.EMAIL]
        )
        
        return await self.send_notification(request)
    
    def get_notification_history(
        self, 
        limit: int = 100,
        notification_type: Optional[NotificationType] = None,
        severity: Optional[NotificationSeverity] = None
    ) -> List[Dict[str, Any]]:
        """Get notification history with optional filters"""
        
        history = self.notification_history.copy()
        
        # Apply filters
        if notification_type:
            history = [h for h in history if h["type"] == notification_type.value]
        
        if severity:
            history = [h for h in history if h["severity"] == severity.value]
        
        # Sort by timestamp (newest first) and limit
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get notification service status"""
        
        return {
            "enabled": self.enabled,
            "email": {
                "enabled": self.email_enabled,
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "sender_email": self.sender_email
            },
            "slack": {
                "enabled": self.slack_enabled,
                "webhook_configured": bool(self.slack_webhook_url),
                "bot_token_configured": bool(self.slack_token),
                "default_channel": self.slack_channel
            },
            "statistics": {
                "templates_count": len(self.templates),
                "recipients_count": len(self.recipients),
                "escalation_rules_count": len(self.escalation_rules),
                "history_entries": len(self.notification_history)
            }
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

# Global service instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service 