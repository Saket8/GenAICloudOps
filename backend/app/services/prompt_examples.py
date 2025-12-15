"""
GenAI Prompt Templates and Examples
==================================

This module provides comprehensive prompt templates and examples for all GenAI CloudOps Dashboard modules.
It includes specialized prompts for infrastructure monitoring, security analysis, cost optimization,
troubleshooting, and various cloud operations scenarios.

Author: GenAI CloudOps Dashboard Team
Created: January 2025
Task: 027 - Develop GenAI Prompt Templates and Examples
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
from .genai_service import PromptType

@dataclass
class PromptExample:
    """Example prompt configuration with metadata"""
    name: str
    description: str
    prompt_type: PromptType
    template: str
    example_parameters: Dict[str, Any]
    expected_output_elements: List[str]
    use_cases: List[str]
    complexity_level: str  # "basic", "intermediate", "advanced"
    performance_notes: str = ""

class PromptExampleLibrary:
    """Comprehensive library of prompt examples for all modules"""
    
    # Infrastructure Monitoring Examples
    INFRASTRUCTURE_MONITORING_EXAMPLES = [
        PromptExample(
            name="OCI Compute Instance Health Analysis",
            description="Analyze the health status of OCI compute instances with performance metrics",
            prompt_type=PromptType.INFRASTRUCTURE_MONITORING,
            template="""
You are an infrastructure monitoring specialist analyzing OCI compute instances. Provide comprehensive health insights.

**Instance Metrics:**
{resource_metrics}

**Monitoring Context:**
- Instance Types: {resource_types}
- Monitoring Period: {monitoring_period}
- Baseline CPU: {baseline_cpu}%
- Baseline Memory: {baseline_memory}%
- Alert Thresholds: CPU > {cpu_threshold}%, Memory > {memory_threshold}%

**Environment Information:**
- Compartment: {compartment_name}
- Region: {region}
- Availability Domain: {availability_domain}

Provide:
1. **Health Assessment**: Overall instance health score (0-100)
2. **Performance Analysis**: CPU, memory, and network utilization patterns
3. **Anomaly Detection**: Unusual metrics or behaviors in the last {monitoring_period}
4. **Trend Analysis**: Performance trends and capacity planning insights
5. **Alert Optimization**: Threshold tuning recommendations
6. **Remediation Actions**: Specific OCI CLI commands for identified issues

Include specific OCI monitoring queries and alert configurations.
""",
            example_parameters={
                "resource_metrics": "Instance-1: CPU 85%, Memory 70%, Network 45MB/s; Instance-2: CPU 45%, Memory 60%, Network 12MB/s",
                "resource_types": "VM.Standard3.Flex, VM.Standard2.2",
                "monitoring_period": "24 hours",
                "baseline_cpu": "45",
                "baseline_memory": "55",
                "cpu_threshold": "80",
                "memory_threshold": "85",
                "compartment_name": "Production-Web-Tier",
                "region": "us-ashburn-1",
                "availability_domain": "AD-1"
            },
            expected_output_elements=[
                "health score", "performance analysis", "anomaly detection", 
                "trend analysis", "alert optimization", "OCI CLI commands"
            ],
            use_cases=[
                "Daily health monitoring", "Capacity planning", "Performance optimization",
                "Alert threshold tuning", "Incident investigation"
            ],
            complexity_level="intermediate",
            performance_notes="Optimized for real-time monitoring dashboards"
        ),
        
        PromptExample(
            name="Multi-Service Resource Correlation",
            description="Correlate performance metrics across multiple OCI services",
            prompt_type=PromptType.INFRASTRUCTURE_MONITORING,
            template="""
You are analyzing correlated performance across multiple OCI services. Identify dependencies and bottlenecks.

**Service Metrics:**
{resource_metrics}

**Service Dependencies:**
{service_dependencies}

**Time Window:** {time_window}
**Baseline Performance:** {baseline_performance}

Provide:
1. **Cross-Service Impact Analysis**: How services affect each other
2. **Bottleneck Identification**: Primary performance constraints
3. **Dependency Chain Analysis**: Critical path identification
4. **Cascade Effect Prediction**: Potential failure propagation
5. **Optimization Recommendations**: Service-specific improvements
6. **Monitoring Strategy**: Key cross-service metrics to track

Include service dependency diagrams and monitoring correlation queries.
""",
            example_parameters={
                "resource_metrics": "Load Balancer: 500 req/s, API Gateway: 2ms latency, Database: 80% CPU, Compute: 60% CPU",
                "service_dependencies": "Load Balancer -> API Gateway -> Compute Instances -> Autonomous Database",
                "time_window": "4 hours",
                "baseline_performance": "Load Balancer: 300 req/s, API Gateway: 1.5ms, Database: 50% CPU"
            },
            expected_output_elements=[
                "cross-service analysis", "bottleneck identification", "dependency analysis",
                "cascade prediction", "optimization recommendations", "monitoring strategy"
            ],
            use_cases=[
                "System-wide performance analysis", "Dependency mapping", "Bottleneck identification",
                "Capacity planning", "Service optimization"
            ],
            complexity_level="advanced"
        )
    ]
    
    # Security Analysis Examples
    SECURITY_ANALYSIS_EXAMPLES = [
        PromptExample(
            name="OCI IAM Policy Security Review",
            description="Comprehensive security analysis of OCI IAM policies and access patterns",
            prompt_type=PromptType.SECURITY_ANALYSIS,
            template="""
You are a cloud security analyst specializing in OCI IAM security. Analyze policies for security risks.

**IAM Policy Configuration:**
{security_config}

**Recent Access Patterns:**
{access_patterns}

**Security Context:**
- Environment: {environment_type}
- Compliance Framework: {compliance_framework}
- Data Classification: {data_classification}
- Security Baseline: {security_baseline}

**Audit Findings:**
{audit_findings}

Provide:
1. **High-Risk Policy Analysis**: Overprivileged access and excessive permissions
2. **Access Pattern Anomalies**: Unusual user behaviors and access times
3. **Privilege Escalation Risks**: Potential paths for unauthorized access
4. **Compliance Assessment**: Adherence to {compliance_framework} standards
5. **Policy Hardening**: Specific IAM policy modifications
6. **Monitoring Recommendations**: Security events to track
7. **Incident Response**: Automated response to security violations

Include specific OCI IAM policy JSON and Cloud Guard configurations.
""",
            example_parameters={
                "security_config": "3 Admin users, 12 Regular users, 5 Service accounts, Policies: AdminAccess (3 users), DatabaseAccess (8 users)",
                "access_patterns": "Admin access from 15 different IPs last week, Database access outside business hours: 23 events",
                "environment_type": "Production",
                "compliance_framework": "SOC 2 Type II",
                "data_classification": "Confidential",
                "security_baseline": "CIS OCI Security Benchmark",
                "audit_findings": "2 inactive users with admin access, 1 service account with overprivileged permissions"
            },
            expected_output_elements=[
                "risk analysis", "anomaly detection", "escalation risks",
                "compliance assessment", "policy hardening", "monitoring recommendations"
            ],
            use_cases=[
                "Security audits", "Compliance reporting", "Access review",
                "Policy optimization", "Incident investigation"
            ],
            complexity_level="advanced"
        )
    ]
    
    # Cost Analysis Examples
    COST_ANALYSIS_EXAMPLES = [
        PromptExample(
            name="OCI Cost Optimization Deep Dive",
            description="Comprehensive cost analysis with specific optimization recommendations",
            prompt_type=PromptType.COST_ANALYSIS,
            template="""
You are a cloud cost optimization expert analyzing OCI spending patterns and resource utilization.

**Cost Breakdown:**
{cost_data}

**Resource Utilization:**
{utilization_data}

**Cost Context:**
- Billing Period: {billing_period}
- Budget: ${budget_allocation}
- Previous Period: ${previous_period_cost}
- Department: {business_unit}
- Workload Type: {workload_type}

**Performance Requirements:**
{performance_requirements}

Provide:
1. **Cost Hotspot Analysis**: Top 5 expensive resources with utilization rates
2. **Rightsizing Opportunities**: Specific instance type changes with savings
3. **Reserved Instance Analysis**: RI recommendations with ROI calculations
4. **Storage Optimization**: Archive and lifecycle policy recommendations
5. **Network Cost Analysis**: Data transfer and egress optimization
6. **Automation Opportunities**: Cost-saving automation scripts
7. **Projected Savings**: 6-month cost reduction roadmap with specific amounts

Include OCI cost optimization commands and resource configurations.
""",
            example_parameters={
                "cost_data": "Compute: $2,500/month, Storage: $800/month, Network: $400/month, Database: $1,200/month",
                "utilization_data": "Compute: 35% average CPU, Storage: 60% used, Database: 70% CPU peak",
                "billing_period": "January 2025",
                "budget_allocation": "6000",
                "previous_period_cost": "4700",
                "business_unit": "Engineering",
                "workload_type": "Web Application",
                "performance_requirements": "99.9% uptime, <2s response time, auto-scaling enabled"
            },
            expected_output_elements=[
                "cost hotspots", "rightsizing opportunities", "reserved instance analysis",
                "storage optimization", "network analysis", "automation opportunities", "projected savings"
            ],
            use_cases=[
                "Monthly cost reviews", "Budget planning", "Resource optimization",
                "Finance reporting", "Cost governance"
            ],
            complexity_level="intermediate"
        )
    ]
    
    # Troubleshooting Examples
    TROUBLESHOOTING_EXAMPLES = [
        PromptExample(
            name="OCI Application Performance Issues",
            description="Systematic troubleshooting for application performance problems",
            prompt_type=PromptType.TROUBLESHOOTING,
            template="""
You are a cloud troubleshooting expert diagnosing OCI application performance issues.

**Problem Description:**
{problem}

**Performance Symptoms:**
{symptoms}

**Environment Configuration:**
{environment}

**Error Messages:**
{error_messages}

**Recent Changes:**
{recent_changes}

**Impact Assessment:**
- Affected Users: {affected_users}
- Business Impact: {business_impact}
- SLA Risk: {sla_risk}

**Application Architecture:**
{application_architecture}

Provide:
1. **Initial Triage**: Problem severity classification and immediate actions
2. **Diagnostic Roadmap**: Step-by-step investigation methodology
3. **Root Cause Hypotheses**: Top 3 likely causes with probability rankings
4. **Investigation Commands**: Specific OCI CLI and monitoring queries
5. **Resolution Strategies**: Multiple fix approaches with risk assessment
6. **Verification Plan**: How to confirm resolution and prevent regression
7. **Documentation Template**: Incident report structure

Include complete diagnostic commands and resolution scripts.
""",
            example_parameters={
                "problem": "Web application response times increased from 1.2s to 8.5s over the past 2 hours",
                "symptoms": "High response times, increased error rates (5% vs normal 0.1%), user complaints",
                "environment": "OCI OKE cluster, 3 nodes, Load Balancer, Autonomous Database",
                "error_messages": "HTTP 503 Service Unavailable, Database connection timeouts",
                "recent_changes": "Database maintenance window completed 3 hours ago, new application deployment 6 hours ago",
                "affected_users": "~1000 active users",
                "business_impact": "High - customer-facing application",
                "sla_risk": "Critical - SLA requires <2s response time",
                "application_architecture": "React frontend -> API Gateway -> OKE pods -> Autonomous Database"
            },
            expected_output_elements=[
                "triage assessment", "diagnostic roadmap", "root cause hypotheses",
                "investigation commands", "resolution strategies", "verification plan"
            ],
            use_cases=[
                "Incident response", "Performance troubleshooting", "Root cause analysis",
                "System reliability", "SLA management"
            ],
            complexity_level="advanced"
        )
    ]
    
    # Log Analysis Examples
    LOG_ANALYSIS_EXAMPLES = [
        PromptExample(
            name="OCI Application Log Error Pattern Analysis",
            description="Analyze application logs to identify error patterns and root causes",
            prompt_type=PromptType.LOG_ANALYSIS,
            template="""
You are a log analysis expert specializing in cloud application troubleshooting. Analyze logs to identify issues.

**Log Entries:**
{log_data}

**Log Context:**
- Time Range: {time_range}
- Log Sources: {log_sources}
- Environment: {environment}
- Baseline Error Rate: {baseline_error_rate}

**Filter Criteria:**
{analysis_parameters}

Provide:
1. **Error Pattern Summary**: Most frequent errors with occurrence counts
2. **Timeline Analysis**: Error distribution and spike correlation
3. **Severity Classification**: Critical vs. warning vs. informational
4. **Root Cause Indicators**: Error sequences suggesting underlying issues
5. **User Impact Assessment**: Errors affecting user experience
6. **Resolution Recommendations**: Specific fixes for identified patterns
7. **Monitoring Alerts**: Log-based alert configurations
8. **Prevention Strategies**: Code and configuration improvements

Include log parsing queries and monitoring alert configurations.
""",
            example_parameters={
                "log_data": "[ERROR] Database connection timeout after 30s; [WARN] High memory usage 85%; [ERROR] API rate limit exceeded; [INFO] User authentication successful",
                "time_range": "Last 4 hours",
                "log_sources": "API Gateway, OKE pods, Load Balancer, Database",
                "environment": "Production",
                "baseline_error_rate": "0.1%",
                "analysis_parameters": "Filter: ERROR and WARN levels, Exclude: Authentication logs"
            },
            expected_output_elements=[
                "error patterns", "timeline analysis", "severity classification",
                "root cause indicators", "impact assessment", "resolution recommendations"
            ],
            use_cases=[
                "Error investigation", "Performance analysis", "System monitoring",
                "Quality assurance", "Incident post-mortem"
            ],
            complexity_level="intermediate"
        )
    ]
    
    # Kubernetes/Pod Health Examples
    KUBERNETES_EXAMPLES = [
        PromptExample(
            name="OKE Pod Health and Performance Analysis",
            description="Comprehensive analysis of Kubernetes pod health in OKE clusters",
            prompt_type=PromptType.POD_HEALTH_ANALYSIS,
            template="""
You are a Kubernetes expert analyzing pod health and performance in OCI OKE clusters.

**Pod Status Information:**
{pod_status}

**Resource Metrics:**
{pod_metrics}

**Cluster Context:**
- Cluster: {cluster_info}
- Namespace: {namespace}
- Node Configuration: {node_config}
- Resource Quotas: {resource_quotas}

**Recent Events:**
{recent_events}

**Performance Baselines:**
{performance_baselines}

Provide:
1. **Pod Health Summary**: Overall health status with problem identification
2. **Resource Utilization Analysis**: CPU, memory, and storage usage patterns
3. **Performance Bottlenecks**: Limiting factors and optimization opportunities
4. **Stability Assessment**: Restart patterns and failure analysis
5. **Scaling Recommendations**: HPA and VPA configuration suggestions
6. **Troubleshooting Commands**: Specific kubectl commands for investigation
7. **Remediation Actions**: Step-by-step fixes with YAML configurations
8. **Monitoring Strategy**: Pod-level monitoring and alerting setup

Include complete kubectl commands and Kubernetes resource manifests.
""",
            example_parameters={
                "pod_status": "webapp-pod-1: Running (2 restarts), webapp-pod-2: CrashLoopBackOff, db-pod: Running (stable)",
                "pod_metrics": "webapp-pod-1: CPU 150m/500m, Memory 800Mi/1Gi; webapp-pod-2: CPU 450m/500m, Memory 950Mi/1Gi",
                "cluster_info": "OKE cluster v1.24.8, 3 worker nodes",
                "namespace": "production",
                "node_config": "VM.Standard3.Flex 4 OCPU, 32GB RAM per node",
                "resource_quotas": "CPU: 6 cores, Memory: 24Gi, Storage: 100Gi",
                "recent_events": "Image pull errors, OOM kills, Node pressure",
                "performance_baselines": "Normal CPU: 100m, Normal Memory: 500Mi, Expected restarts: 0"
            },
            expected_output_elements=[
                "health summary", "resource analysis", "bottleneck identification",
                "stability assessment", "scaling recommendations", "kubectl commands"
            ],
            use_cases=[
                "Pod troubleshooting", "Performance optimization", "Capacity planning",
                "Health monitoring", "Resource management"
            ],
            complexity_level="advanced"
        )
    ]
    
    # Conversational Agent Examples
    CONVERSATIONAL_EXAMPLES = [
        PromptExample(
            name="Multi-Context Cloud Operations Assistant",
            description="Context-aware conversational agent for complex cloud operations",
            prompt_type=PromptType.CONTEXTUAL_CHATBOT,
            template="""
You are an intelligent cloud operations assistant with deep contextual awareness of the user's environment and needs.

**User Question:** {user_input}

**User Profile:**
- Role: {user_role}
- Experience: {experience_level}
- Current Focus: {current_task}
- Preferred Style: {learning_style}

**Environmental Context:**
- OCI Region: {region}
- Active Compartments: {compartments}
- Running Services: {active_services}
- Recent Alerts: {recent_alerts}

**Session Context:**
- Previous Topics: {session_topics}
- Completed Actions: {completed_actions}
- Open Issues: {open_issues}

**Knowledge Base:**
{knowledge_context}

Response Strategy:
- Match technical depth to user's experience level
- Reference specific resources in their environment
- Build upon previous conversation context
- Provide actionable next steps
- Include relevant OCI documentation links
- Suggest related best practices
- Consider current system state and alerts

Provide a comprehensive, contextually appropriate response with specific examples from their environment.
""",
            example_parameters={
                "user_input": "How can I optimize the performance of my web application?",
                "user_role": "DevOps Engineer",
                "experience_level": "Intermediate",
                "current_task": "Performance troubleshooting",
                "learning_style": "Hands-on with examples",
                "region": "us-ashburn-1",
                "compartments": "web-tier, database-tier",
                "active_services": "OKE cluster, Load Balancer, Autonomous Database",
                "recent_alerts": "High CPU usage alert on web-tier instances",
                "session_topics": "Performance monitoring, Resource scaling",
                "completed_actions": "Enabled detailed monitoring, Reviewed metrics",
                "open_issues": "Database connection timeouts",
                "knowledge_context": "OCI performance best practices, Database optimization guides"
            },
            expected_output_elements=[
                "contextual analysis", "specific recommendations", "environment references",
                "actionable steps", "documentation links", "best practices"
            ],
            use_cases=[
                "Interactive troubleshooting", "Learning assistance", "Best practice guidance",
                "Environment-specific advice", "Complex problem solving"
            ],
            complexity_level="advanced"
        )
    ]

class PromptTemplateManager:
    """Manager for organizing and accessing prompt templates"""
    
    def __init__(self):
        self.examples = {
            "infrastructure_monitoring": PromptExampleLibrary.INFRASTRUCTURE_MONITORING_EXAMPLES,
            "security_analysis": PromptExampleLibrary.SECURITY_ANALYSIS_EXAMPLES,
            "cost_analysis": PromptExampleLibrary.COST_ANALYSIS_EXAMPLES,
            "troubleshooting": PromptExampleLibrary.TROUBLESHOOTING_EXAMPLES,
            "log_analysis": PromptExampleLibrary.LOG_ANALYSIS_EXAMPLES,
            "kubernetes": PromptExampleLibrary.KUBERNETES_EXAMPLES,
            "conversational": PromptExampleLibrary.CONVERSATIONAL_EXAMPLES
        }
    
    def get_examples_by_type(self, prompt_type: PromptType) -> List[PromptExample]:
        """Get all examples for a specific prompt type"""
        all_examples = []
        for category_examples in self.examples.values():
            all_examples.extend([ex for ex in category_examples if ex.prompt_type == prompt_type])
        return all_examples
    
    def get_examples_by_complexity(self, complexity: str) -> List[PromptExample]:
        """Get examples by complexity level"""
        all_examples = []
        for category_examples in self.examples.values():
            all_examples.extend([ex for ex in category_examples if ex.complexity_level == complexity])
        return all_examples
    
    def get_example_by_name(self, name: str) -> PromptExample:
        """Get a specific example by name"""
        for category_examples in self.examples.values():
            for example in category_examples:
                if example.name == name:
                    return example
        return None
    
    def get_use_case_examples(self, use_case: str) -> List[PromptExample]:
        """Get examples that support a specific use case"""
        matching_examples = []
        for category_examples in self.examples.values():
            for example in category_examples:
                if any(use_case.lower() in uc.lower() for uc in example.use_cases):
                    matching_examples.append(example)
        return matching_examples
    
    def generate_example_prompt(self, example_name: str) -> str:
        """Generate a complete prompt using an example"""
        example = self.get_example_by_name(example_name)
        if example:
            return example.template.format(**example.example_parameters)
        return ""

# Global instance for easy access
prompt_template_manager = PromptTemplateManager() 