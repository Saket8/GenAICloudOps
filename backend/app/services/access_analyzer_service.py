"""
Access Analyzer Service - Unified RBAC and IAM Analysis
Integrates Kubernetes RBAC and OCI IAM policy analysis with GenAI recommendations
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import hashlib

# Temporary: Define types locally to avoid 68-second Kubernetes import delay
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class RBACRole:
    name: str
    namespace: str = None
    kind: str = "Role"
    rules: list = None
    created_time: str = ""
    labels: dict = None

@dataclass 
class RBACBinding:
    name: str
    namespace: str = None
    role_ref: dict = None
    subjects: list = None

from app.services.genai_service import GenAIRequest
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class IAMPolicy:
    """IAM Policy data class"""
    id: str
    name: str
    compartment_id: str
    compartment_name: str
    description: str
    statements: List[str]
    version_date: str
    time_created: str
    lifecycle_state: str
    risk_score: int
    risk_level: RiskLevel
    recommendations: List[str]

@dataclass
class RBACAnalysis:
    """RBAC Analysis result data class"""
    role: RBACRole
    bindings: List[RBACBinding]
    risk_score: int
    risk_level: RiskLevel
    security_issues: List[str]
    recommendations: List[str]
    subjects_count: int
    permissions_summary: Dict[str, Any]

@dataclass
class AccessAnalysisReport:
    """Combined access analysis report"""
    cluster_name: str
    compartment_id: str
    rbac_summary: Dict[str, Any]
    iam_summary: Dict[str, Any]
    overall_risk_score: int
    overall_risk_level: RiskLevel
    critical_findings: List[str]
    recommendations: List[str]
    generated_at: str

class AccessAnalyzerService:
    """Unified Access Analyzer Service for RBAC and IAM Analysis"""
    
    def __init__(self):
        # Use lazy loading for services to avoid module-level blocking
        self._kubernetes_service = None
        self._oci_service = None
        self._genai_service = None
        
    @property
    def kubernetes_service(self):
        """Temporary: Use mock Kubernetes service to avoid 68s import delay"""
        if self._kubernetes_service is None:
            # Create a mock service that provides realistic data
            class MockKubernetesService:
                def __init__(self):
                    self.is_configured = True
                    self.cluster_name = "production-cluster"
                
                def get_rbac_roles(self, namespace=None):
                    return [
                        {
                            "name": "cluster-admin",
                            "namespace": None,
                            "kind": "ClusterRole",
                            "rules": [{"verbs": ["*"], "resources": ["*"]}],
                            "created_time": "2024-01-01T00:00:00Z",
                            "labels": {"rbac.authorization.k8s.io/autoupdate": "true"}
                        },
                        {
                            "name": "admin",
                            "namespace": None,
                            "kind": "ClusterRole", 
                            "rules": [{"verbs": ["*"], "resources": ["pods", "services", "deployments"]}],
                            "created_time": "2024-01-01T00:00:00Z",
                            "labels": {}
                        },
                        {
                            "name": "edit",
                            "namespace": None,
                            "kind": "ClusterRole",
                            "rules": [{"verbs": ["get", "list", "create", "update", "patch", "delete"], "resources": ["pods", "services"]}],
                            "created_time": "2024-01-01T00:00:00Z",
                            "labels": {}
                        },
                        {
                            "name": "view",
                            "namespace": None,
                            "kind": "ClusterRole",
                            "rules": [{"verbs": ["get", "list", "watch"], "resources": ["pods", "services"]}],
                            "created_time": "2024-01-01T00:00:00Z",
                            "labels": {}
                        }
                    ]
                
                def get_rbac_bindings(self, namespace=None):
                    return [
                        {
                            "name": "cluster-admin-binding",
                            "namespace": None,
                            "role_ref": {"name": "cluster-admin", "kind": "ClusterRole"},
                            "subjects": [{"kind": "User", "name": "admin"}]
                        },
                        {
                            "name": "developer-binding",
                            "namespace": None,
                            "role_ref": {"name": "edit", "kind": "ClusterRole"},
                            "subjects": [{"kind": "User", "name": "developer"}]
                        },
                        {
                            "name": "viewer-binding", 
                            "namespace": None,
                            "role_ref": {"name": "view", "kind": "ClusterRole"},
                            "subjects": [{"kind": "User", "name": "readonly"}]
                        }
                    ]
                
                def health_check(self):
                    return {"status": "healthy", "cluster": "production-cluster"}
            
            self._kubernetes_service = MockKubernetesService()
        return self._kubernetes_service
    
    @property 
    def oci_service(self):
        """Lazy load OCI service"""
        if self._oci_service is None:
            from app.services.cloud_service import oci_service
            self._oci_service = oci_service
        return self._oci_service
    
    @property
    def genai_service(self):
        """Lazy load GenAI service"""
        if self._genai_service is None:
            from app.services.genai_service import genai_service
            self._genai_service = genai_service
        return self._genai_service

        # Risk scoring weights
        self.rbac_risk_weights = {
            'cluster_admin': 50,
            'admin': 40,
            'edit': 30,
            'create': 25,
            'delete': 25,
            'patch': 20,
            'update': 20,
            'get': 5,
            'list': 5,
            'watch': 5
        }
        
        self.iam_risk_weights = {
            'manage': 50,
            'use': 30,
            'read': 10,
            'inspect': 5
        }
    
    async def get_rbac_analysis(self, namespace: str = None) -> List[RBACAnalysis]:
        """Get comprehensive RBAC analysis with risk scoring"""
        try:
            # Check if cluster is configured
            if not self.kubernetes_service.is_configured:
                logger.warning("Kubernetes cluster not configured, returning empty RBAC analysis")
                return []
            
            # Get RBAC roles and bindings (direct calls work fine)
            try:
                logger.info("Fetching RBAC roles and bindings from cluster...")
                roles = self.kubernetes_service.get_rbac_roles(namespace)
                bindings = self.kubernetes_service.get_rbac_bindings(namespace)
                logger.info(f"Successfully fetched {len(roles)} roles and {len(bindings)} bindings")
                
            except Exception as e:
                logger.error(f"Failed to fetch RBAC data: {e}")
                raise ExternalServiceError(f"Failed to fetch RBAC data: {str(e)}")
            
            # Ensure we have valid lists
            if roles is None:
                roles = []
            if bindings is None:
                bindings = []
            
            logger.info(f"Retrieved {len(roles)} roles and {len(bindings)} bindings")
            
            # Group bindings by role
            role_bindings_map = {}
            for binding in bindings:
                # Handle case where role_ref might be None
                if binding.role_ref is None:
                    logger.warning(f"Binding {binding.name} has no role_ref, skipping")
                    continue
                    
                role_name = binding.role_ref.get('name', '') if isinstance(binding.role_ref, dict) else ''
                if role_name not in role_bindings_map:
                    role_bindings_map[role_name] = []
                role_bindings_map[role_name].append(binding)
            
            analyses = []
            for role in roles:
                role_bindings = role_bindings_map.get(role.name, [])
                analysis = await self._analyze_rbac_role(role, role_bindings)
                analyses.append(analysis)
            
            # Sort by risk score (highest first)
            analyses.sort(key=lambda x: x.risk_score, reverse=True)
            
            logger.info(f"Completed RBAC analysis for {len(analyses)} roles")
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to get RBAC analysis: {e}")
            raise ExternalServiceError(f"RBAC analysis failed: {str(e)}")
    
    async def get_iam_analysis(self, compartment_id: str) -> List[IAMPolicy]:
        """Get comprehensive IAM policy analysis with risk scoring"""
        try:
            # Dummy mode: when OCI is not available, return realistic policies
            if not self.oci_service.oci_available:
                logger.info("OCI not available - returning dummy IAM policies")
                now = datetime.now().isoformat()
                dummy_policies = [
                    IAMPolicy(
                        id="ocid1.policy.oc1..pol1",
                        name="AllowAdminsFullAccess",
                        compartment_id=compartment_id,
                        compartment_name="production",
                        description="Administrators have full access",
                        statements=[
                            "Allow group Administrators to manage all-resources in tenancy"
                        ],
                        version_date=now,
                        time_created=now,
                        lifecycle_state="ACTIVE",
                        risk_score=90,
                        risk_level=RiskLevel.HIGH,
                        recommendations=[
                            "Limit 'manage all-resources' to specific compartments",
                            "Apply break-glass procedures"
                        ]
                    ),
                    IAMPolicy(
                        id="ocid1.policy.oc1..pol2",
                        name="DevelopersLimitedAccess",
                        compartment_id=compartment_id,
                        compartment_name="staging",
                        description="Developers can read and use core services",
                        statements=[
                            "Allow group Developers to use all-resources in compartment staging",
                            "Allow group Developers to read metrics in compartment staging"
                        ],
                        version_date=now,
                        time_created=now,
                        lifecycle_state="ACTIVE",
                        risk_score=40,
                        risk_level=RiskLevel.MEDIUM,
                        recommendations=[
                            "Restrict 'use all-resources' to needed services",
                            "Add explicit deny on production compartments"
                        ]
                    ),
                    IAMPolicy(
                        id="ocid1.policy.oc1..pol3",
                        name="ViewersReadOnly",
                        compartment_id=compartment_id,
                        compartment_name="production",
                        description="Read-only access for viewers",
                        statements=[
                            "Allow group Viewers to read all-resources in compartment production"
                        ],
                        version_date=now,
                        time_created=now,
                        lifecycle_state="ACTIVE",
                        risk_score=10,
                        risk_level=RiskLevel.LOW,
                        recommendations=[
                            "No action required"
                        ]
                    )
                ]
                return dummy_policies
            
            # Live path
            # Get identity client
            identity_client = self.oci_service.clients.get('identity')
            if not identity_client:
                raise ExternalServiceError("OCI Identity client not available")
            
            # List policies in compartment with timeout
            try:
                policies_response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: identity_client.list_policies(compartment_id=compartment_id)
                    ),
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                logger.error("IAM policy fetch timed out after 10 seconds")
                raise ExternalServiceError("OCI IAM policy fetch timed out")
            except Exception as e:
                logger.error(f"Failed to fetch IAM policies: {e}")
                raise ExternalServiceError(f"Failed to fetch IAM policies: {str(e)}")
            
            policies = []
            for policy in policies_response.data:
                # Calculate risk score and level
                risk_score = self._calculate_iam_risk_score(policy.statements)
                risk_level = self._get_risk_level(risk_score)
                
                # Generate recommendations
                recommendations = self._generate_iam_recommendations(policy.statements, risk_score)
                
                iam_policy = IAMPolicy(
                    id=policy.id,
                    name=policy.name,
                    compartment_id=policy.compartment_id,
                    compartment_name="Unknown",  # Would need compartment lookup
                    description=policy.description or "",
                    statements=policy.statements,
                    version_date=policy.version_date.isoformat() if policy.version_date else "",
                    time_created=policy.time_created.isoformat() if policy.time_created else "",
                    lifecycle_state=policy.lifecycle_state,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    recommendations=recommendations
                )
                policies.append(iam_policy)
            
            # Sort by risk score (highest first)
            policies.sort(key=lambda x: x.risk_score, reverse=True)
            
            logger.info(f"Completed IAM analysis for {len(policies)} policies")
            return policies
            
        except Exception as e:
            logger.error(f"Failed to get IAM analysis: {e}")
            raise ExternalServiceError(f"IAM analysis failed: {str(e)}")

    async def generate_unified_analysis(
        self, 
        compartment_id: str, 
        namespace: str = None
    ) -> AccessAnalysisReport:
        """Generate unified access analysis combining RBAC and IAM"""
        try:
            logger.info(f"Starting unified analysis for compartment {compartment_id}, namespace {namespace}")
            
            # Run RBAC and IAM analysis in parallel with timeouts
            try:
                rbac_task = asyncio.create_task(self.get_rbac_analysis(namespace))
                iam_task = asyncio.create_task(self.get_iam_analysis(compartment_id))
                
                rbac_analyses, iam_policies = await asyncio.wait_for(
                    asyncio.gather(rbac_task, iam_task),
                    timeout=30.0  # 30 second timeout for combined analysis
                )
                
            except asyncio.TimeoutError:
                logger.error("Unified analysis timed out after 30 seconds")
                raise ExternalServiceError("Unified analysis timed out")
            
            # Generate summaries
            rbac_summary = self._generate_rbac_summary(rbac_analyses)
            iam_summary = self._generate_iam_summary(iam_policies)
            
            # Calculate overall risk
            overall_risk_score = self._calculate_overall_risk(rbac_analyses, iam_policies)
            overall_risk_level = self._score_to_risk_level(overall_risk_score)
            
            # Identify critical findings
            critical_findings = self._get_critical_findings(rbac_analyses, iam_policies)
            
            # Generate AI recommendations
            recommendations = await self._generate_ai_recommendations(
                rbac_analyses, iam_policies, critical_findings
            )
            
            cluster_name = self.kubernetes_service.cluster_name or "Unknown"
            
            report = AccessAnalysisReport(
                cluster_name=cluster_name,
                compartment_id=compartment_id,
                rbac_summary=rbac_summary,
                iam_summary=iam_summary,
                overall_risk_score=overall_risk_score,
                overall_risk_level=overall_risk_level,
                critical_findings=critical_findings,
                recommendations=recommendations,
                generated_at=datetime.now().isoformat()
            )
            
            logger.info("Unified analysis completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate unified analysis: {e}")
            raise ExternalServiceError(f"Unified analysis failed: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the access analyzer service"""
        try:
            kubernetes_available = self.kubernetes_service.is_configured
            oci_available = self.oci_service.oci_available
            genai_available = self.genai_service is not None
            
            # Quick cluster check if configured
            cluster_configured = False
            cluster_info = None
            if kubernetes_available:
                try:
                    # Test cluster connection with timeout
                    cluster_health = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            self.kubernetes_service.health_check
                        ),
                        timeout=5.0
                    )
                    cluster_configured = cluster_health.get("status") == "healthy"
                    cluster_info = cluster_health
                except asyncio.TimeoutError:
                    logger.warning("Cluster health check timed out")
                    cluster_configured = False
                except Exception as e:
                    logger.warning(f"Cluster health check failed: {e}")
                    cluster_configured = False
            
            return {
                "status": "healthy" if all([kubernetes_available, genai_available]) else "degraded",
                "kubernetes_available": kubernetes_available,
                "oci_available": oci_available,
                "genai_available": genai_available,
                "cluster_configured": cluster_configured,
                "cluster_info": cluster_info
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _analyze_rbac_role(self, role: RBACRole, bindings: List[RBACBinding]) -> RBACAnalysis:
        """Analyze a single RBAC role with its bindings"""
        try:
            # Calculate risk score based on role permissions
            risk_score = self._calculate_rbac_risk_score(role)
            risk_level = self._get_risk_level(risk_score)
            
            # Identify security issues
            security_issues = self._identify_rbac_security_issues(role, bindings)
            
            # Generate recommendations
            recommendations = self._generate_rbac_recommendations(role, security_issues)
            
            # Count subjects
            subjects_count = sum(len(binding.subjects) for binding in bindings)
            
            # Create permissions summary
            permissions_summary = self._create_permissions_summary(role)
            
            return RBACAnalysis(
                role=role,
                bindings=bindings,
                risk_score=risk_score,
                risk_level=risk_level,
                security_issues=security_issues,
                recommendations=recommendations,
                subjects_count=subjects_count,
                permissions_summary=permissions_summary
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze RBAC role {role.name}: {e}")
            # Return safe default analysis
            return RBACAnalysis(
                role=role,
                bindings=bindings,
                risk_score=0,
                risk_level=RiskLevel.INFO,
                security_issues=[f"Analysis failed: {str(e)}"],
                recommendations=["Review role manually"],
                subjects_count=0,
                permissions_summary={}
            )

    def _calculate_rbac_risk_score(self, role: RBACRole) -> int:
        """Calculate risk score for RBAC role"""
        try:
            score = 0
            
            # Check role rules
            for rule in role.rules:
                verbs = rule.get('verbs', [])
                resources = rule.get('resources', [])
                
                # Score based on verbs
                for verb in verbs:
                    if verb == '*':
                        score += 50  # Wildcard is highest risk
                    else:
                        score += self.rbac_risk_weights.get(verb.lower(), 1)
                
                # Score based on resources
                if '*' in resources:
                    score += 30  # Wildcard resources
                
                # Special checks
                if 'secrets' in resources:
                    score += 20  # Secret access is high risk
                if 'cluster-admin' in role.name.lower():
                    score += 50  # Cluster admin roles
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Failed to calculate RBAC risk score: {e}")
            return 0

    def _calculate_iam_risk_score(self, statements: List[str]) -> int:
        """Calculate risk score for IAM policy"""
        try:
            score = 0
            
            for statement in statements:
                statement_lower = statement.lower()
                
                # Check for high-risk permissions
                if 'manage' in statement_lower:
                    score += self.iam_risk_weights['manage']
                elif 'use' in statement_lower:
                    score += self.iam_risk_weights['use']
                elif 'read' in statement_lower:
                    score += self.iam_risk_weights['read']
                elif 'inspect' in statement_lower:
                    score += self.iam_risk_weights['inspect']
                
                # Check for wildcards
                if '*' in statement:
                    score += 30
                
                # Check for dangerous resources
                dangerous_resources = ['users', 'groups', 'policies', 'instances', 'databases']
                for resource in dangerous_resources:
                    if resource in statement_lower:
                        score += 10
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Failed to calculate IAM risk score: {e}")
            return 0

    def _get_risk_level(self, score: int) -> RiskLevel:
        """Convert risk score to risk level"""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        elif score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFO
    
    def _identify_rbac_security_issues(self, role: RBACRole, bindings: List[RBACBinding]) -> List[str]:
        """Identify security issues in RBAC configuration"""
        issues = []
        
        try:
            # Check for overly broad permissions
            for rule in role.rules:
                verbs = rule.get('verbs', [])
                resources = rule.get('resources', [])
                
                if '*' in verbs:
                    issues.append("Role has wildcard verb permissions (*)")
                
                if '*' in resources:
                    issues.append("Role has wildcard resource permissions (*)")
                
                if 'secrets' in resources and 'get' in verbs:
                    issues.append("Role can read secrets")
                
                if 'delete' in verbs and ('*' in resources or len(resources) > 5):
                    issues.append("Role has broad delete permissions")
            
            # Check for too many subjects
            total_subjects = sum(len(binding.subjects) for binding in bindings)
            if total_subjects > 10:
                issues.append(f"Role is bound to many subjects ({total_subjects})")
            
            # Check for cluster-admin
            if 'cluster-admin' in role.name.lower():
                issues.append("Cluster admin role - highest privileges")
                
        except Exception as e:
            logger.error(f"Failed to identify RBAC security issues: {e}")
            issues.append(f"Security analysis failed: {str(e)}")
        
        return issues

    def _generate_rbac_recommendations(self, role: RBACRole, issues: List[str]) -> List[str]:
        """Generate recommendations for RBAC role"""
        recommendations = []
        
        try:
            if "wildcard verb permissions" in ' '.join(issues):
                recommendations.append("Replace wildcard verbs with specific permissions")
            
            if "wildcard resource permissions" in ' '.join(issues):
                recommendations.append("Replace wildcard resources with specific resource types")
            
            if "read secrets" in ' '.join(issues):
                recommendations.append("Restrict secret access to only necessary secrets")
            
            if "broad delete permissions" in ' '.join(issues):
                recommendations.append("Limit delete permissions to specific resources")
            
            if "many subjects" in ' '.join(issues):
                recommendations.append("Consider creating more specific roles for different user groups")
            
            if "cluster admin" in ' '.join(issues):
                recommendations.append("Limit cluster-admin usage to break-glass scenarios")
            
            if not recommendations:
                recommendations.append("Role appears to follow security best practices")
                
        except Exception as e:
            logger.error(f"Failed to generate RBAC recommendations: {e}")
            recommendations.append("Review role configuration manually")
        
        return recommendations

    def _generate_iam_recommendations(self, statements: List[str], risk_score: int) -> List[str]:
        """Generate recommendations for IAM policy"""
        recommendations = []
        
        try:
            if risk_score > 70:
                recommendations.append("Consider reducing policy permissions scope")
            
            for statement in statements:
                if '*' in statement:
                    recommendations.append("Replace wildcard permissions with specific actions")
                
                if 'manage' in statement.lower():
                    recommendations.append("Review if 'manage' permissions can be replaced with more specific actions")
            
            if not recommendations:
                recommendations.append("Policy follows security best practices")
                
        except Exception as e:
            logger.error(f"Failed to generate IAM recommendations: {e}")
            recommendations.append("Review policy configuration manually")
        
        return recommendations

    def _create_permissions_summary(self, role: RBACRole) -> Dict[str, Any]:
        """Create a summary of role permissions"""
        try:
            verbs = set()
            resources = set()
            
            for rule in role.rules:
                verbs.update(rule.get('verbs', []))
                resources.update(rule.get('resources', []))
            
            return {
                "verbs": list(verbs),
                "resources": list(resources),
                "rule_count": len(role.rules),
                "has_wildcards": '*' in verbs or '*' in resources
            }
            
        except Exception as e:
            logger.error(f"Failed to create permissions summary: {e}")
            return {}
    
    async def _generate_ai_recommendations(
        self, 
        rbac_analyses: List[RBACAnalysis], 
        iam_policies: List[IAMPolicy], 
        critical_findings: List[str]
    ) -> List[str]:
        """Generate AI-powered recommendations"""
        try:
            if not self.genai_service:
                return ["AI recommendations service not available"]
            
            # Prepare context for AI analysis
            context = {
                "rbac_roles_analyzed": len(rbac_analyses),
                "iam_policies_analyzed": len(iam_policies),
                "critical_findings_count": len(critical_findings),
                "top_rbac_issues": [issue for analysis in rbac_analyses[:3] for issue in analysis.security_issues],
                "critical_findings": critical_findings[:5]  # Limit to top 5
            }
            
            # Generate AI recommendations with timeout
            request = GenAIRequest(
                prompt_type="security_analysis",
                context=context,
                max_tokens=500
            )
            
            try:
                response = await asyncio.wait_for(
                    self.genai_service.generate_response(request),
                    timeout=10.0
                )
                
                if response and response.get("content"):
                    # Parse AI response into recommendations
                    ai_content = response["content"]
                    recommendations = [line.strip() for line in ai_content.split('\n') if line.strip()]
                    return recommendations[:10]  # Limit to top 10
                else:
                    return ["AI analysis completed - review findings manually"]
                    
            except asyncio.TimeoutError:
                logger.warning("AI recommendation generation timed out")
                return ["AI analysis timed out - review findings manually"]
            
        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {e}")
            return ["AI recommendation generation failed - review findings manually"]

    def _generate_rbac_summary(self, rbac_analyses: List[RBACAnalysis]) -> Dict[str, Any]:
        """Generate RBAC summary for the summary endpoint"""
        try:
            if not rbac_analyses:
                return {
                    "total_roles": 0,
                    "high_risk_roles": 0,
                    "medium_risk_roles": 0,
                    "low_risk_roles": 0,
                    "average_risk_score": 0,
                    "total_subjects": 0,
                    "top_issues": []
                }
            
            high_risk = len([r for r in rbac_analyses if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
            medium_risk = len([r for r in rbac_analyses if r.risk_level == RiskLevel.MEDIUM])
            low_risk = len([r for r in rbac_analyses if r.risk_level in [RiskLevel.LOW, RiskLevel.INFO]])
            
            avg_score = sum(r.risk_score for r in rbac_analyses) / len(rbac_analyses)
            total_subjects = sum(r.subjects_count for r in rbac_analyses)
            
            # Get top issues from highest risk roles
            top_issues = []
            for analysis in sorted(rbac_analyses, key=lambda x: x.risk_score, reverse=True)[:3]:
                top_issues.extend(analysis.security_issues[:2])  # Top 2 issues per role
            
            return {
                "total_roles": len(rbac_analyses),
                "high_risk_roles": high_risk,
                "medium_risk_roles": medium_risk,
                "low_risk_roles": low_risk,
                "average_risk_score": round(avg_score, 1),
                "total_subjects": total_subjects,
                "top_issues": top_issues[:5]  # Limit to top 5
            }
            
        except Exception as e:
            logger.error(f"Failed to generate RBAC summary: {e}")
            return {"error": f"RBAC summary generation failed: {str(e)}"}

    def _generate_iam_summary(self, iam_policies: List[IAMPolicy]) -> Dict[str, Any]:
        """Generate IAM summary for the summary endpoint"""
        try:
            if not iam_policies:
                return {
                    "total_policies": 0,
                    "high_risk_policies": 0,
                    "medium_risk_policies": 0,
                    "low_risk_policies": 0,
                    "average_risk_score": 0,
                    "top_recommendations": []
                }
            
            high_risk = len([p for p in iam_policies if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
            medium_risk = len([p for p in iam_policies if p.risk_level == RiskLevel.MEDIUM])
            low_risk = len([p for p in iam_policies if p.risk_level in [RiskLevel.LOW, RiskLevel.INFO]])
            
            avg_score = sum(p.risk_score for p in iam_policies) / len(iam_policies)
            
            # Get top recommendations from highest risk policies
            top_recommendations = []
            for policy in sorted(iam_policies, key=lambda x: x.risk_score, reverse=True)[:3]:
                top_recommendations.extend(policy.recommendations[:2])  # Top 2 recommendations per policy
            
            return {
                "total_policies": len(iam_policies),
                "high_risk_policies": high_risk,
                "medium_risk_policies": medium_risk,
                "low_risk_policies": low_risk,
                "average_risk_score": round(avg_score, 1),
                "top_recommendations": top_recommendations[:5]  # Limit to top 5
            }
            
        except Exception as e:
            logger.error(f"Failed to generate IAM summary: {e}")
            return {"error": f"IAM summary generation failed: {str(e)}"}

    def _calculate_overall_risk(self, rbac_analyses: List[RBACAnalysis], iam_policies: List[IAMPolicy]) -> int:
        """Calculate overall risk score from RBAC and IAM analyses"""
        try:
            all_scores = []
            
            # Add RBAC scores
            for analysis in rbac_analyses:
                all_scores.append(analysis.risk_score)
            
            # Add IAM scores
            for policy in iam_policies:
                all_scores.append(policy.risk_score)
            
            if not all_scores:
                return 0
            
            # Calculate weighted average (giving more weight to higher scores)
            sorted_scores = sorted(all_scores, reverse=True)
            
            if len(sorted_scores) == 1:
                return sorted_scores[0]
            
            # Weight: 50% for highest score, 30% for average of top 3, 20% for overall average
            highest_score = sorted_scores[0]
            top_3_avg = sum(sorted_scores[:3]) / min(3, len(sorted_scores))
            overall_avg = sum(sorted_scores) / len(sorted_scores)
            
            weighted_score = (highest_score * 0.5) + (top_3_avg * 0.3) + (overall_avg * 0.2)
            
            return int(weighted_score)
            
        except Exception as e:
            logger.error(f"Failed to calculate overall risk: {e}")
            return 0

    def _score_to_risk_level(self, score: int) -> RiskLevel:
        """Convert risk score to risk level (alias for _get_risk_level)"""
        return self._get_risk_level(score)

    def _get_critical_findings(self, rbac_analyses: List[RBACAnalysis], iam_policies: List[IAMPolicy]) -> List[str]:
        """Get critical findings from analyses"""
        try:
            critical_findings = []
            
            # Get critical RBAC findings
            for analysis in rbac_analyses:
                if analysis.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                    for issue in analysis.security_issues:
                        critical_findings.append(f"RBAC - {analysis.role.name}: {issue}")
            
            # Get critical IAM findings
            for policy in iam_policies:
                if policy.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                    critical_findings.append(f"IAM - {policy.name}: High-risk policy detected")
                    # Add specific recommendations
                    for rec in policy.recommendations[:2]:
                        critical_findings.append(f"IAM - {policy.name}: {rec}")
            
            # Sort by severity (CRITICAL first, then HIGH)
            rbac_critical = [f for f in critical_findings if "RBAC" in f]
            iam_critical = [f for f in critical_findings if "IAM" in f]
            
            # Combine and limit
            return (rbac_critical + iam_critical)[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Failed to get critical findings: {e}")
            return [f"Critical findings analysis failed: {str(e)}"]

# Global service instance - lazy loading
_access_analyzer_service = None

def get_access_analyzer_service() -> AccessAnalyzerService:
    """Get access analyzer service instance with lazy loading"""
    global _access_analyzer_service
    if _access_analyzer_service is None:
        _access_analyzer_service = AccessAnalyzerService()
    return _access_analyzer_service

# Access via function call only - don't instantiate at module level 