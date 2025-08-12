import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import httpx
from groq import Groq
from app.core.config import settings
from app.core.exceptions import BaseCustomException, RateLimitError, ExternalServiceError
import logging

logger = logging.getLogger(__name__)

class PromptType(Enum):
    """Types of prompts for different use cases"""
    REMEDIATION = "remediation"
    ANALYSIS = "analysis" 
    EXPLANATION = "explanation"
    OPTIMIZATION = "optimization"
    TROUBLESHOOTING = "troubleshooting"
    CHATBOT = "chatbot"
    
    # Enhanced prompt types for specific modules
    INFRASTRUCTURE_MONITORING = "infrastructure_monitoring"
    SECURITY_ANALYSIS = "security_analysis"
    ACCESS_RISK_ASSESSMENT = "access_risk_assessment"
    COST_ANALYSIS = "cost_analysis"
    COST_FORECASTING = "cost_forecasting"
    LOG_ANALYSIS = "log_analysis"
    POD_HEALTH_ANALYSIS = "pod_health_analysis"
    KUBERNETES_TROUBLESHOOTING = "kubernetes_troubleshooting"
    OCI_RESOURCE_ANALYSIS = "oci_resource_analysis"
    ALERT_CORRELATION = "alert_correlation"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    INCIDENT_RESPONSE = "incident_response"
    CAPACITY_PLANNING = "capacity_planning"
    DISASTER_RECOVERY = "disaster_recovery"
    
    # Context-aware prompt types
    CONTEXTUAL_CHATBOT = "contextual_chatbot"
    MULTI_TURN_CONVERSATION = "multi_turn_conversation"
    EXPERT_CONSULTATION = "expert_consultation"

@dataclass
class GenAIRequest:
    """Data class for GenAI requests"""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    prompt_type: PromptType = PromptType.CHATBOT
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass 
class GenAIResponse:
    """Data class for GenAI responses"""
    content: str
    model: str
    tokens_used: int
    response_time: float
    cached: bool = False
    timestamp: datetime = None
    request_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class PromptTemplate:
    """Manages comprehensive prompt templates for different use cases across all modules"""
    
    TEMPLATES = {
        # Core Templates (Enhanced)
        PromptType.REMEDIATION: """
You are an expert cloud operations engineer with extensive experience in OCI and Kubernetes. Analyze the following issue and provide specific, actionable remediation steps.

**Issue Details:**
{issue_details}

**Context:**
- Environment: {environment}
- Service: {service_name}
- Severity: {severity}
- Impact Level: {impact_level}
- Time of Occurrence: {occurrence_time}

**Resource Information:**
{resource_info}

**Current State:**
{current_state}

**Previous Actions Taken:**
{previous_actions}

Provide:
1. **Root Cause Analysis**: Deep dive into the underlying cause
2. **Immediate Remediation Steps**: Step-by-step actions with CLI commands
3. **Prevention Measures**: Long-term solutions to prevent recurrence
4. **Monitoring Recommendations**: Specific metrics and alerts to implement
5. **Rollback Plan**: Steps to revert if remediation fails
6. **Estimated Recovery Time**: Timeline for resolution

Format your response with clear sections and include specific OCI CLI or kubectl commands where applicable.
""",
        
        PromptType.ANALYSIS: """
You are a senior cloud infrastructure analyst specializing in OCI environments. Analyze the following data and provide comprehensive insights.

**Data to Analyze:**
{data}

**Analysis Context:**
{context}

**Time Range:** {time_range}
**Baseline Metrics:** {baseline_metrics}
**Current Environment:** {environment_details}

Provide:
1. **Key Findings**: Most critical observations
2. **Trends and Patterns**: Historical data analysis
3. **Anomaly Detection**: Unusual behaviors or outliers
4. **Performance Insights**: Resource utilization patterns
5. **Potential Issues**: Early warning indicators
6. **Strategic Recommendations**: Long-term improvements
7. **Priority Assessment**: Risk-based ranking of issues

Include specific metrics, thresholds, and actionable next steps.
""",

        PromptType.EXPLANATION: """
You are a technical expert specializing in cloud infrastructure concepts. Explain the following topic in a clear, accessible manner.

**Topic:** {topic}
**Context:** {context}
**Audience Level:** {audience_level}
**Industry/Domain:** {domain}
**Related Technologies:** {related_tech}

Provide:
1. **Clear Definition**: Simple explanation of the concept
2. **How It Works**: Technical mechanism without jargon
3. **Real-World Applications**: Practical use cases in OCI
4. **Benefits and Limitations**: Balanced perspective
5. **Best Practices**: Industry-standard recommendations
6. **Common Pitfalls**: What to avoid
7. **Further Reading**: Related concepts to explore

Adjust technical depth based on audience level (Beginner/Intermediate/Advanced).
""",

        PromptType.OPTIMIZATION: """
You are a cloud cost and performance optimization expert with deep OCI expertise. Analyze the following resource usage and provide comprehensive optimization recommendations.

**Resource Data:**
{resource_data}

**Current Costs:**
{cost_data}

**Performance Metrics:**
{performance_data}

**Business Context:**
- Workload Type: {workload_type}
- Performance Requirements: {performance_requirements}
- Budget Constraints: {budget_constraints}
- Compliance Requirements: {compliance_requirements}

Provide:
1. **Cost Optimization Opportunities**: Specific savings potential with dollar amounts
2. **Performance Improvements**: Bottleneck identification and solutions
3. **Resource Rightsizing**: Detailed instance/service recommendations
4. **Architecture Optimization**: Structural improvements
5. **Implementation Priority**: ROI-based ranking
6. **Risk Assessment**: Potential impacts of changes
7. **Implementation Roadmap**: Phased approach with timelines
8. **Expected Savings**: Quantified benefits per recommendation

Include specific OCI service recommendations and pricing calculations.
""",

        PromptType.TROUBLESHOOTING: """
You are a cloud troubleshooting expert with extensive experience in OCI and Kubernetes environments. Help diagnose and resolve the following issue systematically.

**Problem Description:**
{problem}

**Symptoms:**
{symptoms}

**Environment Details:**
{environment}

**Error Messages:**
{error_messages}

**Logs/Metrics:**
{logs}

**Recent Changes:**
{recent_changes}

**Impact Assessment:**
- Affected Users: {affected_users}
- Business Impact: {business_impact}
- Urgency Level: {urgency_level}

Provide:
1. **Initial Assessment**: Problem severity and scope
2. **Diagnostic Methodology**: Systematic investigation approach
3. **Root Cause Hypotheses**: Ranked list of potential causes
4. **Investigation Steps**: Specific commands and checks
5. **Resolution Strategies**: Multiple solution approaches
6. **Implementation Plan**: Step-by-step execution
7. **Verification Methods**: How to confirm resolution
8. **Post-Incident Actions**: Prevention and documentation

Include specific CLI commands, log analysis techniques, and monitoring queries.
""",

        PromptType.CHATBOT: """
You are an expert cloud operations assistant specializing in OCI and Kubernetes environments. Answer the user's question based on the provided context with practical, actionable advice.

**User Question:** {user_input}

**Current Context:** {context}

**Previous Conversation:** {conversation_history}

**User Role:** {user_role}
**Environment Details:** {environment_details}
**Available Resources:** {available_resources}

Response Guidelines:
- Provide practical, actionable answers
- Include specific commands or configurations when relevant
- Reference OCI documentation links when helpful
- Ask clarifying questions if the request is ambiguous
- Offer multiple solution approaches when applicable
- Consider security implications in recommendations
- Suggest monitoring and validation steps

If you need additional information to provide a complete answer, ask specific clarifying questions.
""",

        # Infrastructure Monitoring Templates
        PromptType.INFRASTRUCTURE_MONITORING: """
You are an infrastructure monitoring specialist. Analyze the following OCI resource metrics and provide comprehensive monitoring insights.

**Resource Metrics:**
{resource_metrics}

**Monitoring Context:**
- Resource Types: {resource_types}
- Monitoring Period: {monitoring_period}
- Baseline Performance: {baseline_performance}
- Alert Thresholds: {alert_thresholds}

**Environment Information:**
{environment_info}

Provide:
1. **Health Assessment**: Overall infrastructure health score
2. **Performance Analysis**: Resource utilization patterns
3. **Anomaly Detection**: Unusual metrics or behaviors
4. **Trend Analysis**: Performance trends over time
5. **Capacity Planning**: Resource scaling recommendations
6. **Alert Optimization**: Threshold tuning suggestions
7. **Monitoring Gaps**: Missing metrics or blind spots
8. **Dashboard Recommendations**: Key metrics to visualize

Include specific monitoring queries and alert configurations for OCI.
""",

        # Security Analysis Templates
        PromptType.SECURITY_ANALYSIS: """
You are a cloud security analyst specializing in OCI and Kubernetes security. Analyze the following security configuration and provide comprehensive security insights.

**Security Configuration:**
{security_config}

**Access Patterns:**
{access_patterns}

**Security Context:**
- Environment Type: {environment_type}
- Compliance Framework: {compliance_framework}
- Data Classification: {data_classification}
- Risk Tolerance: {risk_tolerance}

**Current Security Posture:**
{security_posture}

Provide:
1. **Security Risk Assessment**: Identified vulnerabilities and risks
2. **Compliance Analysis**: Adherence to security standards
3. **Access Control Review**: IAM and RBAC configuration analysis
4. **Network Security**: VCN and security group analysis
5. **Data Protection**: Encryption and backup security
6. **Security Hardening**: Specific improvement recommendations
7. **Incident Response**: Security monitoring and alerting gaps
8. **Remediation Priority**: Risk-based prioritization

Include specific OCI security service configurations and best practices.
""",

        PromptType.ACCESS_RISK_ASSESSMENT: """
You are an access control security expert. Analyze the following IAM and RBAC configurations to identify security risks and provide remediation recommendations.

**IAM Policies:**
{iam_policies}

**RBAC Configuration:**
{rbac_config}

**User Access Patterns:**
{access_patterns}

**Risk Context:**
- Environment Sensitivity: {environment_sensitivity}
- Data Classification: {data_classification}
- Compliance Requirements: {compliance_requirements}
- Recent Access Changes: {recent_changes}

Provide:
1. **High-Risk Access Patterns**: Excessive or inappropriate permissions
2. **Privilege Escalation Risks**: Potential security vulnerabilities
3. **Unused Access Rights**: Dormant or unnecessary permissions
4. **Policy Conflicts**: Conflicting or overlapping access rules
5. **Compliance Violations**: Violations of security standards
6. **Recommended Remediation**: Specific policy changes
7. **Access Review Process**: Ongoing governance recommendations
8. **Risk Scoring**: Quantified risk assessment

Include specific IAM policy modifications and RBAC adjustments.
""",

        # Cost Analysis Templates
        PromptType.COST_ANALYSIS: """
You are a cloud cost optimization expert specializing in OCI billing and cost management. Analyze the following cost data and provide comprehensive cost insights.

**Cost Data:**
{cost_data}

**Resource Utilization:**
{utilization_data}

**Cost Context:**
- Billing Period: {billing_period}
- Budget Allocation: {budget_allocation}
- Previous Period Comparison: {previous_period}
- Business Unit: {business_unit}

**Usage Patterns:**
{usage_patterns}

Provide:
1. **Cost Breakdown Analysis**: Service-wise cost distribution
2. **Cost Trend Analysis**: Spending patterns over time
3. **Anomaly Detection**: Unusual cost spikes or patterns
4. **Utilization Efficiency**: Resource efficiency metrics
5. **Cost Optimization Opportunities**: Specific savings recommendations
6. **Budget Forecast**: Projected spending based on trends
7. **Cost Allocation**: Department/project cost attribution
8. **Savings Roadmap**: Prioritized cost reduction plan

Include specific cost optimization strategies with projected savings amounts.
""",

        PromptType.COST_FORECASTING: """
You are a cloud financial analyst specializing in cost forecasting and budget planning. Analyze historical cost data and provide accurate cost predictions.

**Historical Cost Data:**
{historical_data}

**Usage Trends:**
{usage_trends}

**Forecasting Context:**
- Forecast Period: {forecast_period}
- Planned Changes: {planned_changes}
- Business Growth Projections: {growth_projections}
- Seasonal Patterns: {seasonal_patterns}

**External Factors:**
{external_factors}

Provide:
1. **Cost Forecast**: Detailed spending predictions
2. **Confidence Intervals**: Forecast accuracy ranges
3. **Scenario Analysis**: Best/worst/most likely case projections
4. **Budget Recommendations**: Optimal budget allocation
5. **Cost Drivers**: Key factors influencing costs
6. **Risk Factors**: Potential cost surprises
7. **Optimization Timeline**: When to implement cost controls
8. **Variance Alerts**: Early warning indicators

Include specific budget planning recommendations and variance monitoring strategies.
""",

        # Log Analysis Templates
        PromptType.LOG_ANALYSIS: """
You are a log analysis expert specializing in cloud infrastructure and application logs. Analyze the following log data to identify issues, patterns, and insights.

**Log Data:**
{log_data}

**Log Context:**
- Time Range: {time_range}
- Log Sources: {log_sources}
- Event Type: {event_type}
- Severity Level: {severity_level}

**Analysis Parameters:**
{analysis_parameters}

Provide:
1. **Error Pattern Analysis**: Common error types and frequencies
2. **Performance Insights**: Response times and bottlenecks
3. **Security Events**: Suspicious activities or access patterns
4. **Application Behavior**: User interactions and system usage
5. **Infrastructure Events**: System-level events and changes
6. **Correlation Analysis**: Related events across different systems
7. **Anomaly Detection**: Unusual log patterns or volumes
8. **Actionable Recommendations**: Specific improvement actions

Include log query examples and monitoring alert configurations.
""",

        # Pod Health Analysis Templates
        PromptType.POD_HEALTH_ANALYSIS: """
You are a Kubernetes expert specializing in pod health monitoring and troubleshooting. Analyze the following pod status and provide comprehensive health insights.

**Pod Status Data:**
{pod_status}

**Pod Metrics:**
{pod_metrics}

**Kubernetes Context:**
- Cluster Information: {cluster_info}
- Namespace: {namespace}
- Workload Type: {workload_type}
- Resource Requests/Limits: {resource_limits}

**Recent Events:**
{recent_events}

Provide:
1. **Health Assessment**: Overall pod health evaluation
2. **Resource Analysis**: CPU, memory, and storage utilization
3. **State Analysis**: Pod lifecycle and restart patterns
4. **Performance Issues**: Bottlenecks and optimization opportunities
5. **Configuration Review**: Pod spec and deployment analysis
6. **Troubleshooting Steps**: Specific kubectl commands for investigation
7. **Remediation Actions**: Fix recommendations with implementation steps
8. **Prevention Measures**: Long-term stability improvements

Include specific kubectl commands and Kubernetes resource configurations.
""",

        PromptType.KUBERNETES_TROUBLESHOOTING: """
You are a Kubernetes troubleshooting expert. Analyze the following Kubernetes issue and provide comprehensive diagnostic and resolution guidance.

**Issue Description:**
{issue_description}

**Kubernetes Environment:**
{k8s_environment}

**Error Symptoms:**
{error_symptoms}

**Cluster State:**
{cluster_state}

**Resource Definitions:**
{resource_definitions}

**Recent Changes:**
{recent_changes}

Provide:
1. **Issue Classification**: Problem category and severity
2. **Diagnostic Methodology**: Systematic troubleshooting approach
3. **Investigation Commands**: Specific kubectl commands to run
4. **Root Cause Analysis**: Likely causes ranked by probability
5. **Resolution Steps**: Step-by-step fix procedures
6. **Verification Process**: How to confirm resolution
7. **Prevention Strategy**: Avoiding similar issues
8. **Documentation**: Incident documentation template

Include complete kubectl command sequences and YAML configurations.
""",

        # OCI Resource Analysis Templates
        PromptType.OCI_RESOURCE_ANALYSIS: """
You are an OCI resource specialist. Analyze the following OCI resource configuration and usage to provide comprehensive insights and recommendations.

**Resource Configuration:**
{resource_config}

**Usage Metrics:**
{usage_metrics}

**OCI Context:**
- Compartment Structure: {compartment_structure}
- Region/AD Distribution: {region_distribution}
- Service Dependencies: {service_dependencies}
- Compliance Requirements: {compliance_requirements}

**Performance Data:**
{performance_data}

Provide:
1. **Resource Optimization**: Configuration and sizing recommendations
2. **Performance Analysis**: Bottlenecks and improvement opportunities
3. **Cost Efficiency**: Cost optimization for current usage patterns
4. **High Availability**: Resilience and availability improvements
5. **Security Posture**: Security configuration analysis
6. **Compliance Assessment**: Adherence to governance policies
7. **Scaling Strategy**: Auto-scaling and capacity planning
8. **Migration Opportunities**: Service upgrade or migration options

Include specific OCI service configurations and Terraform code examples.
""",

        # Alert Correlation Templates
        PromptType.ALERT_CORRELATION: """
You are an alert correlation specialist. Analyze the following alerts and provide intelligent correlation and root cause analysis.

**Alert Data:**
{alert_data}

**Alert Context:**
- Time Window: {time_window}
- Affected Services: {affected_services}
- Alert Severity: {alert_severity}
- Environment Impact: {environment_impact}

**System Dependencies:**
{system_dependencies}

**Historical Patterns:**
{historical_patterns}

Provide:
1. **Alert Correlation**: Related alerts and dependencies
2. **Root Cause Analysis**: Primary cause identification
3. **Impact Assessment**: Scope and severity of the issue
4. **Escalation Recommendations**: When and how to escalate
5. **Resolution Priority**: Which alerts to address first
6. **Communication Plan**: Stakeholder notification strategy
7. **Suppression Rules**: Alert noise reduction recommendations
8. **Process Improvements**: Alert tuning and optimization

Include alert correlation queries and automated response configurations.
""",

        # Performance Analysis Templates
        PromptType.PERFORMANCE_ANALYSIS: """
You are a performance analysis expert specializing in cloud infrastructure optimization. Analyze the following performance data and provide comprehensive insights.

**Performance Metrics:**
{performance_metrics}

**Baseline Data:**
{baseline_data}

**Performance Context:**
- Workload Characteristics: {workload_characteristics}
- SLA Requirements: {sla_requirements}
- Performance Goals: {performance_goals}
- Resource Constraints: {resource_constraints}

**Environment Configuration:**
{environment_config}

Provide:
1. **Performance Assessment**: Current vs. target performance
2. **Bottleneck Identification**: System constraints and limitations
3. **Optimization Opportunities**: Specific improvement recommendations
4. **Capacity Planning**: Resource scaling recommendations
5. **Configuration Tuning**: System and application optimizations
6. **Monitoring Strategy**: Key metrics and alerting thresholds
7. **Performance Roadmap**: Improvement implementation plan
8. **SLA Compliance**: Meeting performance objectives

Include performance tuning configurations and monitoring queries.
""",

        # Context-Aware Templates
        PromptType.CONTEXTUAL_CHATBOT: """
You are an intelligent cloud operations assistant with deep contextual awareness. Provide responses that consider the user's current situation, environment, and previous interactions.

**User Query:** {user_input}

**User Context:**
- Role: {user_role}
- Experience Level: {experience_level}
- Current Task: {current_task}
- Preferred Learning Style: {learning_style}

**Environmental Context:**
{environment_context}

**Session Context:**
{session_context}

**Recent Activities:**
{recent_activities}

Response Strategy:
- Adapt technical depth to user experience level
- Reference previous conversation context
- Provide solutions relevant to current environment
- Suggest related actions based on user's typical workflow
- Include appropriate level of detail and explanation
- Offer multiple approaches when suitable
- Consider user's time constraints and urgency

Provide a contextually appropriate response with actionable next steps.
""",

        PromptType.MULTI_TURN_CONVERSATION: """
You are managing a multi-turn conversation about cloud operations. Maintain conversation continuity and build upon previous exchanges.

**Current Question:** {current_question}

**Conversation History:**
{conversation_history}

**Conversation Context:**
- Original Topic: {original_topic}
- User Goals: {user_goals}
- Progress So Far: {progress_status}
- Remaining Questions: {remaining_questions}

**Knowledge State:**
{knowledge_state}

Conversation Management:
- Reference previous answers and build upon them
- Track the user's understanding and adjust accordingly
- Identify when the conversation topic shifts
- Summarize key points when appropriate
- Guide the conversation toward the user's goals
- Ask clarifying questions to maintain focus
- Provide connection between different conversation threads

Continue the conversation naturally while maintaining context and momentum.
""",

        PromptType.EXPERT_CONSULTATION: """
You are providing expert-level consultation on complex cloud operations challenges. Deliver deep technical insights with strategic perspectives.

**Consultation Request:**
{consultation_request}

**Technical Challenge:**
{technical_challenge}

**Business Context:**
- Organization Size: {organization_size}
- Industry Requirements: {industry_requirements}
- Strategic Goals: {strategic_goals}
- Technology Constraints: {tech_constraints}

**Current Architecture:**
{current_architecture}

**Decision Criteria:**
{decision_criteria}

Expert Consultation Approach:
- Provide multiple solution architectures with trade-offs
- Include implementation complexity and timeline estimates
- Consider long-term maintenance and scalability
- Address regulatory and compliance requirements
- Provide risk assessment for each approach
- Include industry best practices and lessons learned
- Suggest proof-of-concept or pilot approaches
- Recommend vendor selection criteria when applicable

Deliver strategic recommendations with detailed implementation guidance.
"""
    }
    
    @classmethod
    def format_prompt(cls, prompt_type: PromptType, **kwargs) -> str:
        """Format a prompt template with provided parameters"""
        template = cls.TEMPLATES.get(prompt_type, cls.TEMPLATES[PromptType.CHATBOT])
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing template parameter: {e}")
            # Return template with available parameters
            available_params = {k: v for k, v in kwargs.items() if f"{{{k}}}" in template}
            return template.format(**available_params)

    @classmethod
    def get_template_parameters(cls, prompt_type: PromptType) -> List[str]:
        """Get list of required parameters for a template"""
        template = cls.TEMPLATES.get(prompt_type, "")
        import re
        return re.findall(r'\{(\w+)\}', template)

    @classmethod
    def validate_template_parameters(cls, prompt_type: PromptType, **kwargs) -> Dict[str, Any]:
        """Validate that all required parameters are provided"""
        required_params = cls.get_template_parameters(prompt_type)
        missing_params = [param for param in required_params if param not in kwargs]
        
        return {
            "valid": len(missing_params) == 0,
            "missing_parameters": missing_params,
            "provided_parameters": list(kwargs.keys()),
            "required_parameters": required_params
        }

class PromptVersioning:
    """Manages prompt template versioning and A/B testing"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.versions = {}
        
    def register_prompt_version(
        self, 
        prompt_type: PromptType, 
        version: str, 
        template: str, 
        metadata: Dict[str, Any] = None
    ):
        """Register a new version of a prompt template"""
        version_key = f"{prompt_type.value}_v{version}"
        
        version_data = {
            "template": template,
            "version": version,
            "prompt_type": prompt_type.value,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.versions[version_key] = version_data
        
        if self.redis:
            try:
                self.redis.hset(
                    "prompt_versions",
                    version_key,
                    json.dumps(version_data)
                )
            except Exception as e:
                logger.warning(f"Failed to store prompt version in Redis: {e}")
    
    def get_prompt_version(self, prompt_type: PromptType, version: str = "latest") -> Optional[str]:
        """Get a specific version of a prompt template"""
        version_key = f"{prompt_type.value}_v{version}"
        
        # Try local cache first
        if version_key in self.versions:
            return self.versions[version_key]["template"]
        
        # Try Redis
        if self.redis:
            try:
                data = self.redis.hget("prompt_versions", version_key)
                if data:
                    version_data = json.loads(data)
                    return version_data["template"]
            except Exception as e:
                logger.warning(f"Failed to get prompt version from Redis: {e}")
        
        # Fallback to default template
        return PromptTemplate.TEMPLATES.get(prompt_type)
    
    def list_versions(self, prompt_type: PromptType) -> List[Dict[str, Any]]:
        """List all versions of a prompt type"""
        prefix = f"{prompt_type.value}_v"
        versions = []
        
        for key, data in self.versions.items():
            if key.startswith(prefix):
                versions.append(data)
        
        return sorted(versions, key=lambda x: x["created_at"], reverse=True)

class PromptOptimization:
    """Handles prompt optimization and A/B testing"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.test_results = {}
        
    def create_ab_test(
        self, 
        prompt_type: PromptType,
        variant_a: str,
        variant_b: str,
        test_name: str,
        traffic_split: float = 0.5
    ) -> str:
        """Create an A/B test for prompt optimization"""
        test_id = f"test_{prompt_type.value}_{test_name}_{int(time.time())}"
        
        test_config = {
            "test_id": test_id,
            "prompt_type": prompt_type.value,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "traffic_split": traffic_split,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "metrics": {
                "variant_a": {"requests": 0, "success_rate": 0, "avg_response_time": 0},
                "variant_b": {"requests": 0, "success_rate": 0, "avg_response_time": 0}
            }
        }
        
        self.test_results[test_id] = test_config
        
        if self.redis:
            try:
                self.redis.hset("ab_tests", test_id, json.dumps(test_config))
            except Exception as e:
                logger.warning(f"Failed to store A/B test in Redis: {e}")
        
        return test_id
    
    def get_prompt_variant(self, test_id: str, user_id: str) -> str:
        """Get the appropriate prompt variant for a user"""
        test_config = self.test_results.get(test_id)
        if not test_config:
            return "variant_a"  # Default
        
        # Simple hash-based assignment for consistent user experience
        import hashlib
        user_hash = int(hashlib.md5(f"{user_id}_{test_id}".encode()).hexdigest(), 16)
        assignment = (user_hash % 100) / 100.0
        
        return "variant_b" if assignment < test_config["traffic_split"] else "variant_a"
    
    def record_test_result(
        self, 
        test_id: str, 
        variant: str, 
        success: bool, 
        response_time: float
    ):
        """Record the result of a prompt test"""
        if test_id not in self.test_results:
            return
        
        metrics = self.test_results[test_id]["metrics"][variant]
        metrics["requests"] += 1
        
        # Update success rate
        old_success_rate = metrics["success_rate"]
        old_requests = metrics["requests"] - 1
        new_success_rate = (old_success_rate * old_requests + (1 if success else 0)) / metrics["requests"]
        metrics["success_rate"] = new_success_rate
        
        # Update average response time
        old_avg_time = metrics["avg_response_time"]
        new_avg_time = (old_avg_time * old_requests + response_time) / metrics["requests"]
        metrics["avg_response_time"] = new_avg_time
        
        # Update in Redis
        if self.redis:
            try:
                self.redis.hset("ab_tests", test_id, json.dumps(self.test_results[test_id]))
            except Exception as e:
                logger.warning(f"Failed to update A/B test results in Redis: {e}")

class PromptQualityMetrics:
    """Measures and tracks prompt quality metrics"""
    
    def __init__(self):
        self.metrics_cache = {}
        
    def calculate_prompt_score(
        self, 
        response: str, 
        expected_elements: List[str] = None,
        response_time: float = None,
        user_feedback: float = None
    ) -> Dict[str, float]:
        """Calculate quality score for a prompt response"""
        scores = {}
        
        # Length appropriateness (penalize too short or too long responses)
        length_score = self._calculate_length_score(response)
        scores["length_appropriateness"] = length_score
        
        # Structure score (presence of numbered lists, headers, etc.)
        structure_score = self._calculate_structure_score(response)
        scores["structure_quality"] = structure_score
        
        # Content coverage (if expected elements provided)
        if expected_elements:
            coverage_score = self._calculate_coverage_score(response, expected_elements)
            scores["content_coverage"] = coverage_score
        
        # Response time score
        if response_time:
            time_score = self._calculate_time_score(response_time)
            scores["response_time"] = time_score
        
        # User feedback score
        if user_feedback is not None:
            scores["user_satisfaction"] = user_feedback
        
        # Overall score (weighted average)
        weights = {
            "length_appropriateness": 0.2,
            "structure_quality": 0.3,
            "content_coverage": 0.3 if expected_elements else 0,
            "response_time": 0.1 if response_time else 0,
            "user_satisfaction": 0.4 if user_feedback is not None else 0
        }
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            normalized_weights = {k: v/total_weight for k, v in weights.items()}
            overall_score = sum(scores.get(k, 0) * weight for k, weight in normalized_weights.items())
            scores["overall_quality"] = overall_score
        
        return scores
    
    def _calculate_length_score(self, response: str) -> float:
        """Calculate score based on response length appropriateness"""
        length = len(response)
        if length < 50:
            return 0.3  # Too short
        elif length < 200:
            return 0.7  # Acceptable but brief
        elif length < 1000:
            return 1.0  # Good length
        elif length < 2000:
            return 0.8  # Acceptable but long
        else:
            return 0.5  # Too long
    
    def _calculate_structure_score(self, response: str) -> float:
        """Calculate score based on response structure quality"""
        score = 0.0
        
        # Check for numbered lists
        if "1." in response and "2." in response:
            score += 0.3
        
        # Check for headers/sections
        if "**" in response or "#" in response:
            score += 0.3
        
        # Check for bullet points
        if "- " in response or "* " in response:
            score += 0.2
        
        # Check for clear sections
        if any(keyword in response.lower() for keyword in ["provide:", "include:", "steps:", "recommendations:"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_coverage_score(self, response: str, expected_elements: List[str]) -> float:
        """Calculate score based on content coverage"""
        if not expected_elements:
            return 1.0
        
        covered_elements = 0
        response_lower = response.lower()
        
        for element in expected_elements:
            if element.lower() in response_lower:
                covered_elements += 1
        
        return covered_elements / len(expected_elements)
    
    def _calculate_time_score(self, response_time: float) -> float:
        """Calculate score based on response time"""
        if response_time < 2.0:
            return 1.0  # Excellent
        elif response_time < 5.0:
            return 0.8  # Good
        elif response_time < 10.0:
            return 0.6  # Acceptable
        elif response_time < 20.0:
            return 0.4  # Slow
        else:
            return 0.2  # Very slow

class ConversationContext:
    """Manages conversation context and history"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get conversation context for a session"""
        try:
            context_key = f"genai:context:{session_id}"
            context_data = self.redis.get(context_key)
            if context_data:
                return json.loads(context_data)
            return {"messages": [], "metadata": {}}
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {"messages": [], "metadata": {}}
    
    def update_context(self, session_id: str, message: Dict[str, Any], max_messages: int = 10):
        """Update conversation context with new message"""
        try:
            context = self.get_context(session_id)
            context["messages"].append({
                "content": message.get("content", ""),
                "role": message.get("role", "user"),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep only recent messages
            if len(context["messages"]) > max_messages:
                context["messages"] = context["messages"][-max_messages:]
            
            context_key = f"genai:context:{session_id}"
            self.redis.setex(
                context_key, 
                timedelta(hours=24), 
                json.dumps(context)
            )
        except Exception as e:
            logger.error(f"Error updating context: {e}")
    
    def clear_context(self, session_id: str):
        """Clear conversation context for a session"""
        try:
            context_key = f"genai:context:{session_id}"
            self.redis.delete(context_key)
        except Exception as e:
            logger.error(f"Error clearing context: {e}")

class GenAIService:
    """Centralized GenAI service for handling AI operations"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.primary_model = settings.GENAI_PRIMARY_MODEL
        self.fallback_model = settings.GENAI_FALLBACK_MODEL
        self.max_retries = settings.GENAI_MAX_RETRIES
        self.timeout = settings.GENAI_TIMEOUT
        
        # Initialize AI client
        if self.groq_api_key:
            self.client = Groq(api_key=self.groq_api_key)
        else:
            self.client = None
            logger.warning("Groq API key not found. GenAI service will use fallback responses.")
        
        # Initialize Redis for caching and context management
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test Redis connection
            self.redis.ping()
            logger.info("Connected to Redis for GenAI caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Proceeding without caching.")
            self.redis = None
        
        # Initialize conversation context manager
        self.context_manager = ConversationContext(self.redis) if self.redis else None
        
        # Initialize advanced prompt management features
        self.prompt_versioning = PromptVersioning(self.redis)
        self.prompt_optimization = PromptOptimization(self.redis)
        self.quality_metrics = PromptQualityMetrics()
        
        # Initialize request tracking
        self.request_count = 0
        self.rate_limiter = {}
        
        # Cache settings
        self.cache_ttl = 300  # 5 minutes default
        self.enable_caching = True

    async def test_redis_connection(self) -> bool:
        """Test Redis connection asynchronously on-demand"""
        if not self.redis:
            return False
            
        try:
            # Test Redis connection with timeout
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, self.redis.ping),
                timeout=2.0
            )
            logger.info("✅ Redis connection test successful")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis connection test failed: {e}")
            self.redis = None
            return False
    
    def _generate_cache_key(self, request: GenAIRequest) -> str:
        """Generate cache key for request"""
        request_dict = asdict(request)
        # Remove session-specific data for caching
        request_dict.pop("user_id", None)
        request_dict.pop("session_id", None)
        
        # Convert enum to string for JSON serialization
        if "prompt_type" in request_dict and hasattr(request_dict["prompt_type"], "value"):
            request_dict["prompt_type"] = request_dict["prompt_type"].value
        
        request_str = json.dumps(request_dict, sort_keys=True, default=str)
        return f"genai:cache:{hashlib.md5(request_str.encode()).hexdigest()}"
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        if not user_id:
            return True
            
        current_minute = int(time.time()) // 60
        key = f"{user_id}:{current_minute}"
        
        if key not in self.rate_limiter:
            self.rate_limiter[key] = 0
            
        # Clean old entries
        old_keys = [k for k in self.rate_limiter.keys() 
                   if int(k.split(':')[1]) < current_minute - 1]
        for old_key in old_keys:
            del self.rate_limiter[old_key]
            
        if self.rate_limiter[key] >= settings.GENAI_RATE_LIMIT_PER_MINUTE:
            return False
            
        self.rate_limiter[key] += 1
        return True
    
    def _get_cached_response(self, cache_key: str) -> Optional[GenAIResponse]:
        """Get cached response if available"""
        if not self.redis:
            return None
            
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                data["cached"] = True
                return GenAIResponse(**data)
        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")
        return None
    
    def _cache_response(self, cache_key: str, response: GenAIResponse):
        """Cache the response"""
        if not self.redis:
            return
            
        try:
            # Don't cache the "cached" flag itself
            response_dict = asdict(response)
            response_dict["cached"] = False
            response_dict["timestamp"] = response_dict["timestamp"].isoformat()
            
            self.redis.setex(
                cache_key,
                timedelta(seconds=settings.GENAI_CACHE_TTL),
                json.dumps(response_dict)
            )
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    async def generate_response(self, request: GenAIRequest) -> GenAIResponse:
        """Generate AI response for a single request"""
        start_time = time.time()
        
        # Check rate limiting
        if not self._check_rate_limit(request.user_id):
            raise RateLimitError("Rate limit exceeded. Please try again later.")
        
        # Check cache
        if self.enable_caching:
            cache_key = self._generate_cache_key(request)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        # Prepare request parameters
        model = request.model or self.primary_model
        max_tokens = request.max_tokens or settings.GROQ_MAX_TOKENS
        temperature = request.temperature or settings.GROQ_TEMPERATURE
        
        try:
            # Call Groq API
            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": request.prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response = GenAIResponse(
                content=completion.choices[0].message.content,
                model=model,
                tokens_used=completion.usage.total_tokens,
                response_time=time.time() - start_time,
                request_id=f"req_{int(time.time() * 1000)}"
            )
            
            # Cache the response
            if self.enable_caching:
                self._cache_response(cache_key, response)
            
            # Update conversation context
            if request.session_id and self.context_manager:
                self.context_manager.update_context(
                    request.session_id,
                    {"role": "user", "content": request.prompt}
                )
                self.context_manager.update_context(
                    request.session_id,
                    {"role": "assistant", "content": response.content}
                )
            
            return response
            
        except Exception as e:
            # Try fallback model if available
            if self.client and self.fallback_model:
                logger.warning(f"Primary model failed, trying fallback: {e}")
                request.model = self.fallback_model
                try:
                    return await self.generate_response(request)
                except Exception as fallback_error:
                    logger.warning(f"Fallback model also failed: {fallback_error}")
            
            # If both models fail, provide a helpful fallback response
            logger.warning(f"GenAI API error, using fallback response: {e}")
            return GenAIResponse(
                content=self._get_fallback_response(request),
                model="fallback-local",
                tokens_used=0,
                response_time=time.time() - start_time,
                request_id=f"fallback_{int(time.time() * 1000)}"
            )
    
    async def batch_generate(self, requests: List[GenAIRequest]) -> List[GenAIResponse]:
        """Generate responses for multiple requests"""
        if not settings.GENAI_ENABLE_BATCHING or len(requests) == 1:
            return [await self.generate_response(req) for req in requests]
        
        responses = []
        for i in range(0, len(requests), settings.GENAI_BATCH_SIZE):
            batch = requests[i:i + settings.GENAI_BATCH_SIZE]
            batch_responses = await asyncio.gather(*[
                self.generate_response(req) for req in batch
            ])
            responses.extend(batch_responses)
            
            # Small delay between batches to respect rate limits
            if i + settings.GENAI_BATCH_SIZE < len(requests):
                await asyncio.sleep(0.1)
        
        return responses
    
    def generate_prompt(self, prompt_type: PromptType, **kwargs) -> str:
        """Generate a formatted prompt using templates"""
        return PromptTemplate.format_prompt(prompt_type, **kwargs)
    
    def generate_versioned_prompt(
        self, 
        prompt_type: PromptType, 
        version: str = "latest", 
        **kwargs
    ) -> str:
        """Generate a prompt using a specific version"""
        template = self.prompt_versioning.get_prompt_version(prompt_type, version)
        if template:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing parameter for versioned prompt: {e}")
                return self.generate_prompt(prompt_type, **kwargs)
        return self.generate_prompt(prompt_type, **kwargs)
    
    def validate_prompt_parameters(self, prompt_type: PromptType, **kwargs) -> Dict[str, Any]:
        """Validate prompt parameters before generation"""
        return PromptTemplate.validate_template_parameters(prompt_type, **kwargs)
    
    async def generate_with_quality_tracking(
        self, 
        request: GenAIRequest,
        expected_elements: List[str] = None,
        user_feedback: float = None
    ) -> Tuple[GenAIResponse, Dict[str, float]]:
        """Generate response and calculate quality metrics"""
        start_time = time.time()
        response = await self.generate_response(request)
        response_time = time.time() - start_time
        
        # Calculate quality metrics
        quality_scores = self.quality_metrics.calculate_prompt_score(
            response.content,
            expected_elements=expected_elements,
            response_time=response_time,
            user_feedback=user_feedback
        )
        
        # Update response with quality data
        response.response_time = response_time
        
        return response, quality_scores
    
    async def generate_with_ab_testing(
        self, 
        test_id: str,
        user_id: str,
        prompt_type: PromptType,
        **kwargs
    ) -> GenAIResponse:
        """Generate response using A/B testing framework"""
        # Get the appropriate variant for this user
        variant = self.prompt_optimization.get_prompt_variant(test_id, user_id)
        
        # Get test configuration
        test_config = self.prompt_optimization.test_results.get(test_id)
        if not test_config:
            # Fall back to standard prompt generation
            prompt = self.generate_prompt(prompt_type, **kwargs)
        else:
            # Use the variant prompt
            variant_prompt = test_config.get(variant, "")
            if variant_prompt:
                try:
                    prompt = variant_prompt.format(**kwargs)
                except KeyError:
                    prompt = self.generate_prompt(prompt_type, **kwargs)
            else:
                prompt = self.generate_prompt(prompt_type, **kwargs)
        
        # Create request with the selected prompt
        request = GenAIRequest(
            prompt=prompt,
            prompt_type=prompt_type,
            user_id=user_id,
            context=kwargs
        )
        
        # Generate response and measure success
        start_time = time.time()
        try:
            response = await self.generate_response(request)
            response_time = time.time() - start_time
            success = True
        except Exception as e:
            response_time = time.time() - start_time
            success = False
            raise e
        finally:
            # Record test result
            self.prompt_optimization.record_test_result(
                test_id, variant, success, response_time
            )
        
        return response
    
    def create_prompt_ab_test(
        self,
        prompt_type: PromptType,
        baseline_template: str,
        variant_template: str,
        test_name: str,
        traffic_split: float = 0.5
    ) -> str:
        """Create a new A/B test for prompt optimization"""
        return self.prompt_optimization.create_ab_test(
            prompt_type=prompt_type,
            variant_a=baseline_template,
            variant_b=variant_template,
            test_name=test_name,
            traffic_split=traffic_split
        )
    
    def get_ab_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get results from an A/B test"""
        return self.prompt_optimization.test_results.get(test_id)
    
    def register_prompt_version(
        self,
        prompt_type: PromptType,
        version: str,
        template: str,
        metadata: Dict[str, Any] = None
    ):
        """Register a new version of a prompt template"""
        self.prompt_versioning.register_prompt_version(
            prompt_type, version, template, metadata
        )
    
    async def chat_completion(
        self, 
        message: str, 
        session_id: str, 
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> GenAIResponse:
        """Handle chat completion with context management"""
        
        # Get conversation history
        conversation_history = ""
        if self.context_manager:
            ctx = self.context_manager.get_context(session_id)
            recent_messages = ctx.get("messages", [])[-5:]  # Last 5 messages
            conversation_history = "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in recent_messages
            ])
        
        # Format chat prompt
        formatted_prompt = self.generate_prompt(
            PromptType.CHATBOT,
            user_input=message,
            context=json.dumps(context or {}),
            conversation_history=conversation_history
        )
        
        request = GenAIRequest(
            prompt=formatted_prompt,
            context=context,
            prompt_type=PromptType.CHATBOT,
            user_id=user_id,
            session_id=session_id
        )
        
        return await self.generate_response(request)
    
    async def get_remediation_suggestions(
        self,
        issue_details: str,
        environment: str,
        service_name: str,
        severity: str,
        resource_info: Dict[str, Any]
    ) -> GenAIResponse:
        """Get AI-powered remediation suggestions"""
        
        formatted_prompt = self.generate_prompt(
            PromptType.REMEDIATION,
            issue_details=issue_details,
            environment=environment,
            service_name=service_name,
            severity=severity,
            resource_info=json.dumps(resource_info, indent=2)
        )
        
        request = GenAIRequest(
            prompt=formatted_prompt,
            prompt_type=PromptType.REMEDIATION
        )
        
        return await self.generate_response(request)
    
    async def analyze_metrics(
        self,
        data: Dict[str, Any],
        context: str = ""
    ) -> GenAIResponse:
        """Analyze metrics and provide insights"""
        
        formatted_prompt = self.generate_prompt(
            PromptType.ANALYSIS,
            data=json.dumps(data, indent=2),
            context=context
        )
        
        request = GenAIRequest(
            prompt=formatted_prompt,
            prompt_type=PromptType.ANALYSIS
        )
        
        return await self.generate_response(request)
    
    def _get_fallback_response(self, request: GenAIRequest) -> str:
        """Generate a fallback response when AI service is unavailable"""
        base_message = request.prompt.lower()
        
        # Provide helpful responses based on content
        if any(word in base_message for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm your CloudOps assistant. I'm currently running in offline mode, but I can still help you with basic information. What would you like to know about your cloud infrastructure?"
        
        if any(word in base_message for word in ['instance', 'server', 'compute']):
            return "I can help you with instance-related queries! Here are some common tasks:\n\n• Check instance status and health\n• Analyze performance metrics\n• Review resource utilization\n• Troubleshoot connectivity issues\n\nFor real-time AI assistance, please ensure the GenAI service is properly configured."
        
        if any(word in base_message for word in ['cost', 'billing', 'expense']):
            return "For cost analysis, I recommend:\n\n• Review your current billing dashboard\n• Check resource usage patterns\n• Look for unused or underutilized resources\n• Consider rightsizing recommendations\n\nI'm currently in offline mode. For detailed AI-powered cost analysis, please check the GenAI service configuration."
        
        if any(word in base_message for word in ['error', 'problem', 'issue', 'down']):
            return "I understand you're experiencing an issue. Here's how I can help:\n\n• Check system logs and monitoring dashboards\n• Review recent changes or deployments\n• Verify service health and connectivity\n• Check resource availability and limits\n\nI'm currently running in offline mode. For advanced AI troubleshooting, please ensure the GenAI service is available."
        
        return "I'm your CloudOps assistant, currently running in offline mode. I can help you with:\n\n• Infrastructure status queries\n• Cost optimization guidance\n• Troubleshooting workflows\n• Best practices recommendations\n\nFor full AI-powered assistance, please check that the GenAI service is properly configured with a valid API key."

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "service": "GenAI Service",
            "provider": "Groq",
            "model": self.primary_model,
            "fallback_model": self.fallback_model,
            "caching_enabled": self.enable_caching,
            "batching_enabled": settings.GENAI_ENABLE_BATCHING,
            "rate_limit_per_minute": settings.GENAI_RATE_LIMIT_PER_MINUTE,
            "cache_ttl_seconds": settings.GENAI_CACHE_TTL,
            "supported_prompt_types": [pt.value for pt in PromptType]
        }

# Global service instance
genai_service = GenAIService()

def get_genai_service() -> GenAIService:
    return genai_service 